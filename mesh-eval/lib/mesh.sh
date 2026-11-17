# Mesh profilleri: kurulum / kaldırma / uygulamayı mesh'e alma / doğrulama
#   none              : mesh yok (referans ölçüm)
#   istio-ambient     : Istio ambient, yalnızca L4 (ztunnel)
#   istio-ambient-l7  : Istio ambient + shop namespace'i için waypoint (L7)
#   istio-sidecar     : Istio klasik sidecar (her pod'a Envoy)
#   linkerd           : Linkerd (edge), her pod'a linkerd2-proxy
# Tüm mesh'lerde güvenli varsayılan: mesh içi trafik zorunlu mTLS (Istio STRICT,
# Linkerd default-inbound-policy=all-authenticated).

MESH_NAMESPACES=("$SHOP_NS" "$LOADGEN_NS")
INSTALL_TIMES="$STATE_DIR/install-times.json"

record_install_time() { # <profil> <saniye>
  local f=$INSTALL_TIMES
  [ -f "$f" ] || echo '{}' > "$f"
  jq --arg p "$1" --argjson s "$2" '.[$p] = $s' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
}

gateway_api_crds() {
  kb apply --server-side -f \
    "https://github.com/kubernetes-sigs/gateway-api/releases/download/$GATEWAY_API_VERSION/standard-install.yaml" >/dev/null
  ok "Gateway API CRD'leri $GATEWAY_API_VERSION"
}

# --- Istio ------------------------------------------------------------------
istio_charts() { echo "$(istio_dir "$1")/manifests/charts"; }

istio_cacerts() {
  local d
  d=$(pki_istio cluster-a)
  kb create namespace istio-system --dry-run=client -o yaml | kb apply -f - >/dev/null
  kb -n istio-system create secret generic cacerts \
    --from-file=ca-cert.pem="$d/ca-cert.pem" --from-file=ca-key.pem="$d/ca-key.pem" \
    --from-file=root-cert.pem="$d/root-cert.pem" --from-file=cert-chain.pem="$d/cert-chain.pem" \
    --dry-run=client -o yaml | kb apply -f - >/dev/null
  ok "plug-in CA (cacerts) yüklendi"
}

# istio_install <ambient|sidecar> [sürüm] [revizyon]
istio_install() {
  local mode=$1 v=${2:-$ISTIO_VERSION} rev=${3:-} ch profile=() revargs=()
  fetch_istio "$v"
  ch=$(istio_charts "$v")
  [ "$mode" = ambient ] && profile=(--set profile=ambient)
  [ -n "$rev" ] && revargs=(--set revision="$rev")
  log "Istio $v kuruluyor ($mode${rev:+, revizyon $rev})"
  gateway_api_crds
  istio_cacerts
  hb upgrade --install istio-base "$ch/base" -n istio-system --set defaultRevision="${rev:-default}" --wait >/dev/null
  hb upgrade --install "istiod${rev:+-$rev}" "$ch/istio-control/istio-discovery" -n istio-system \
    "${profile[@]}" "${revargs[@]}" -f "$MEVAL_ROOT/meshes/istio/istiod-values.yaml" \
    --set global.hub="$ISTIO_HUB" --set global.tag="$v" --wait --timeout 5m >/dev/null
  ok "istiod${rev:+-$rev}"
  if [ "$mode" = ambient ]; then
    hb upgrade --install istio-cni "$ch/istio-cni" -n istio-system "${profile[@]}" \
      --set global.hub="$ISTIO_HUB" --set global.tag="$v" --wait --timeout 5m >/dev/null
    ok "istio-cni"
    hb upgrade --install ztunnel "$ch/ztunnel" -n istio-system \
      --set hub="$ISTIO_HUB" --set tag="$v" -f "$MEVAL_ROOT/meshes/istio/ztunnel-values.yaml" --wait --timeout 5m >/dev/null
    ok "ztunnel"
  fi
}

istio_uninstall() {
  local r
  for r in $(hb list -n istio-system -q 2>/dev/null); do hb uninstall "$r" -n istio-system --wait >/dev/null 2>&1 || true; done
  kb delete namespace istio-system --ignore-not-found --wait=true >/dev/null 2>&1 || true
  kb get crd -o name | grep -E 'istio\.io' | while read -r o; do kb delete "$o" --ignore-not-found >/dev/null 2>&1 || true; done || true
  kb delete mutatingwebhookconfiguration,validatingwebhookconfiguration -l app=sidecar-injector --ignore-not-found >/dev/null 2>&1 || true
  # revision/tag ile oluşan webhook'lar (ör. istiod-default-validator, istio-revision-tag-default) helm
  # kaldırmasında geride kalabilir ve sonraki istio-base kurulumunu engeller
  kb get mutatingwebhookconfiguration,validatingwebhookconfiguration -o name 2>/dev/null \
    | grep -E '/(istio|istiod)-' | while read -r o; do kb delete "$o" --ignore-not-found >/dev/null 2>&1 || true; done || true
}

# --- Linkerd ----------------------------------------------------------------
lk() { "$(linkerd_bin "${LK_VERSION:-$LINKERD_VERSION}")" --context "kind-$BENCH_CLUSTER" "$@"; }

linkerd_install() {
  local v=${1:-$LINKERD_VERSION} d
  fetch_linkerd "$v"
  log "Linkerd $v kuruluyor"
  gateway_api_crds
  d=$(pki_linkerd issuer)
  LK_VERSION=$v lk install --crds | kb apply -f - >/dev/null
  LK_VERSION=$v lk install \
    --identity-trust-anchors-file "$d/root-cert.pem" \
    --identity-issuer-certificate-file "$d/ca-cert.pem" \
    --identity-issuer-key-file "$d/ca-key.pem" \
    -f "$MEVAL_ROOT/meshes/linkerd/values.yaml" | kb apply -f - >/dev/null
  LK_VERSION=$v lk check --wait 5m >/dev/null || { LK_VERSION=$v lk check; die "linkerd check başarısız"; }
  ok "linkerd control plane (linkerd check geçti)"
}

linkerd_uninstall() {
  if kb get ns linkerd >/dev/null 2>&1; then
    lk uninstall 2>/dev/null | kb delete --ignore-not-found -f - >/dev/null 2>&1 || true
  fi
  kb delete namespace linkerd --ignore-not-found --wait=true >/dev/null 2>&1 || true
  kb get crd -o name | grep -E 'linkerd\.io' | while read -r o; do kb delete "$o" --ignore-not-found >/dev/null 2>&1 || true; done || true
}

# --- Uygulamayı mesh'e alma -------------------------------------------------
# ingress-nginx (bench) pod'unu mesh'e dahil eden ek helm değerleri
ingress_values_for() {
  case $1 in
    istio-sidecar) echo "$MEVAL_ROOT/meshes/istio/ingress-sidecar.yaml" ;;
    linkerd)       echo "$MEVAL_ROOT/meshes/linkerd/ingress.yaml" ;;
    *)             echo "" ;;
  esac
}

ingress_reconfigure() {
  local extra=() f
  f=$(ingress_values_for "$1")
  [ -n "$f" ] && extra=(-f "$f")
  hb upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version "$INGRESS_NGINX_CHART_VERSION" \
    -n ingress-nginx -f "$LAB_ROOT/platform/ingress-nginx/values-common.yaml" \
    -f "$LAB_ROOT/platform/ingress-nginx/values-app.yaml" "${extra[@]}" --wait --timeout 5m >/dev/null
  kb -n ingress-nginx rollout status deploy/ingress-nginx-controller --timeout=180s >/dev/null
}

mesh_enroll() {
  local p=$1 ns
  log "Uygulama mesh'e alınıyor: $p"
  for ns in "${MESH_NAMESPACES[@]}" ingress-nginx observability; do
    kb label ns "$ns" istio-injection- istio.io/dataplane-mode- istio.io/use-waypoint- >/dev/null 2>&1 || true
    kb annotate ns "$ns" linkerd.io/inject- config.linkerd.io/default-inbound-policy- >/dev/null 2>&1 || true
  done
  kb -n "$SHOP_NS" delete peerauthentication --all --ignore-not-found >/dev/null 2>&1 || true
  case $p in
    istio-sidecar)
      for ns in "${MESH_NAMESPACES[@]}"; do kb label ns "$ns" istio-injection=enabled --overwrite >/dev/null; done ;;
    istio-ambient|istio-ambient-l7)
      for ns in "${MESH_NAMESPACES[@]}" ingress-nginx; do kb label ns "$ns" istio.io/dataplane-mode=ambient --overwrite >/dev/null; done ;;
    linkerd)
      for ns in "${MESH_NAMESPACES[@]}"; do
        kb annotate ns "$ns" linkerd.io/inject=enabled config.linkerd.io/default-inbound-policy=all-authenticated --overwrite >/dev/null
      done ;;
  esac
  if [ "$(mesh_family "$p")" = istio ]; then
    kb apply -f - >/dev/null <<YAML
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: strict, namespace: $SHOP_NS }
spec: { mtls: { mode: STRICT } }
YAML
    ok "PeerAuthentication STRICT ($SHOP_NS)"
  fi
  # Linkerd: all-authenticated politikası proxy metrik portunu da (4191) kapsar. Prometheus agent mesh'e
  # alınır -> metrikleri mTLS ile (kimlikli) toplar. Admin portuna Server tanımlamak kubelet probe'larını bozar.
  if [ "$p" = linkerd ]; then
    kb annotate ns observability linkerd.io/inject=enabled --overwrite >/dev/null
    ok "Linkerd: Prometheus agent mesh'e alındı (metrik toplama kimlikli)"
  fi
  kb -n observability rollout restart deploy >/dev/null 2>&1 || true
  ingress_reconfigure "$p"
  ok "ingress-nginx ($BENCH_CLUSTER) yeniden yapılandırıldı"
  kb -n "$SHOP_NS" rollout restart deploy >/dev/null
  app_wait
  if [ "$p" = istio-ambient-l7 ]; then
    istioctl_v "$ISTIO_VERSION" --context "kind-$BENCH_CLUSTER" waypoint apply -n "$SHOP_NS" --enroll-namespace --wait >/dev/null
    kb -n "$SHOP_NS" patch deploy waypoint --type merge -p \
      '{"spec":{"template":{"spec":{"nodeSelector":{"mesh-eval.role":"app"},"tolerations":[{"key":"mesh-eval.role","operator":"Equal","value":"app","effect":"NoSchedule"}]}}}}' >/dev/null 2>&1 || true
    kb -n "$SHOP_NS" rollout status deploy/waypoint --timeout=120s >/dev/null
    ok "waypoint ($SHOP_NS) -> tüm servisler L7 üzerinden"
  else
    kb -n "$SHOP_NS" delete gateway waypoint --ignore-not-found >/dev/null 2>&1 || true
  fi
}

mesh_uninstall_all() {
  log "Mevcut mesh bileşenleri kaldırılıyor"
  kb -n "$SHOP_NS" delete gateway waypoint --ignore-not-found >/dev/null 2>&1 || true
  istio_uninstall
  linkerd_uninstall
  ok "temizlendi"
}

mesh_install() {
  local p=$1 t0=$SECONDS
  case $p in
    none) ;;
    istio-ambient|istio-ambient-l7) istio_install ambient ;;
    istio-sidecar) istio_install sidecar ;;
    linkerd) linkerd_install ;;
    *) die "bilinmeyen profil: $p" ;;
  esac
  record_install_time "$p" $((SECONDS - t0))
}

# --- Doğrulama --------------------------------------------------------------
mesh_verify() {
  local p n out total
  p=$(current_mesh)
  log "Mesh doğrulama: $p"
  # yalnızca aktif pod'lar (rollout sırasında kapanmakta olanlar hariç)
  shop_pods() { kb -n "$SHOP_NS" get pods -l mesh-eval/part-of=shop -o json | jq '{items: [.items[] | select(.metadata.deletionTimestamp == null)]}'; }
  total=$(shop_pods | jq '.items | length')
  case $p in
    istio-sidecar)
      n=$(shop_pods | jq '[.items[] | select([.spec.containers[].name, (.spec.initContainers // [])[].name] | index("istio-proxy"))] | length')
      [ "$n" -eq "$total" ] && ok "tüm shop pod'larında istio-proxy ($n/$total)" || { fail "sidecar eksik ($n/$total)"; return 1; } ;;
    istio-ambient|istio-ambient-l7)
      n=$(shop_pods | jq '[.items[] | select(.metadata.annotations["ambient.istio.io/redirection"] == "enabled")] | length')
      [ "$n" -eq "$total" ] && ok "tüm shop pod'ları ambient'te ($n/$total)" || { fail "ambient eksik ($n/$total)"; return 1; }
      out=$(istioctl_v "$ISTIO_VERSION" --context "kind-$BENCH_CLUSTER" ztunnel-config workloads --workload-namespace "$SHOP_NS" 2>/dev/null | awk 'NR>1 {print $NF}' | sort | uniq -c | tr '\n' ' ')
      grep -q HBONE <<<"$out" && ok "ztunnel: iş yükleri HBONE (mTLS) ile ($out)" || { fail "HBONE görünmüyor: $out"; return 1; }
      if [ "$p" = istio-ambient-l7 ]; then
        kb -n "$SHOP_NS" get gateway waypoint >/dev/null 2>&1 && ok "waypoint mevcut" || { fail "waypoint yok"; return 1; }
      fi ;;
    linkerd)
      n=$(shop_pods | jq '[.items[] | select([.spec.containers[].name, (.spec.initContainers // [])[].name] | index("linkerd-proxy"))] | length')
      [ "$n" -eq "$total" ] && ok "tüm shop pod'larında linkerd-proxy ($n/$total)" || { fail "proxy eksik ($n/$total)"; return 1; }
      lk check --proxy -n "$SHOP_NS" >/dev/null 2>&1 && ok "linkerd check --proxy" || { fail "linkerd check --proxy"; return 1; } ;;
  esac
  app_verify || return 1
  # Mesh dışından düz (şifresiz) erişim reddedilmeli
  if kb -n "$OUTSIDE_NS" exec deploy/probe-outside -- curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://order.$SHOP_NS.svc:9090/" 2>/dev/null | grep -q '^200$'; then
    fail "mesh dışından düz HTTP erişimi KABUL edildi (mTLS zorunlu değil)"; return 1
  else
    ok "mesh dışından düz HTTP erişimi reddedildi (mTLS zorunlu)"
  fi
  # Mesh metrikleri Prometheus'a ulaşıyor mu
  local q
  case $(mesh_family "$p") in
    istio)
      if [ "$p" = istio-ambient ]; then q="sum(istio_tcp_connections_opened_total{cluster=\"$BENCH_CLUSTER\",mesh=\"$p\"})"
      else q="sum(istio_requests_total{cluster=\"$BENCH_CLUSTER\",mesh=\"$p\"})"; fi ;;
    linkerd) q="sum(request_total{cluster=\"$BENCH_CLUSTER\",mesh=\"$p\",namespace=\"$SHOP_NS\"})" ;;
  esac
  wait_for 90 "mesh metrikleri ($q)" bash -c "[ \"\$(curl -sk --resolve prometheus.localtest.me:9443:127.0.0.1 '$PROM_URL/api/v1/query' --data-urlencode 'query=$q' | jq -r '.data.result[0].value[1] // \"null\"')\" != null ]" \
    && ok "mesh metrikleri Prometheus'ta: $q = $(prom_scalar "$q")"
}

# --- Komutlar ---------------------------------------------------------------
cmd_mesh() {
  local sub=${1:-list}; shift || true
  case $sub in
    list)
      printf '%s\n' "${MESH_PROFILES[@]}" | sed "s/^$(current_mesh)\$/& (aktif)/" ;;
    use)
      local p=${1:?profil gerekli} fresh=0
      [ "${2:-}" = --fresh ] && fresh=1
      printf '%s\n' "${MESH_PROFILES[@]}" | grep -qx "$p" || die "bilinmeyen profil: $p"
      if [ $fresh = 1 ]; then
        log "Temiz ortam: bench cluster'ı yeniden kuruluyor"
        kind delete cluster --name "$BENCH_CLUSTER" >/dev/null
        bash "$LAB_ROOT/scripts/up.sh" >/dev/null
        set_current_mesh none
        bench_nodes; obs_install_agent none; app_deploy
      else
        mesh_uninstall_all
      fi
      mesh_install "$p"
      set_current_mesh "$p"
      obs_install_agent "$p"
      mesh_enroll "$p"
      cmd_verify ;;
    verify) mesh_verify ;;
    status)
      echo "aktif profil: $(current_mesh)"
      kb get pods -A -o wide --no-headers | grep -E 'istio-system|linkerd|waypoint' || echo "(mesh bileşeni yok)" ;;
    *) die "mesh: bilinmeyen alt komut $sub" ;;
  esac
}
