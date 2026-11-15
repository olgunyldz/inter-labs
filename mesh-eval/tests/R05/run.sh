# R05 — Yük altında mesh güncellemesi
FAM=$(mesh_family "$MESH")
case $FAM in
  istio) FROM=$ISTIO_PREV_VERSION; TO=$ISTIO_VERSION ;;
  linkerd) FROM=$LINKERD_PREV_VERSION; TO=$LINKERD_VERSION ;;
esac
metric from_version 0 - "$FROM"; metric to_version 0 - "$TO"
log "Hazırlık: $MESH $FROM sürümüyle yeniden kuruluyor"
mesh_uninstall_all
case $MESH in
  istio-sidecar) istio_install sidecar "$FROM" ;;
  istio-ambient*) istio_install ambient "$FROM" ;;
  linkerd) linkerd_install "$FROM" ;;
esac
mesh_enroll "$MESH"
chain_ok probe-gateway || die "eski sürümde zincir çalışmıyor"
ok "eski sürüm hazır ($FROM)"
restarts0=$(kb -n "$SHOP_NS" get pods -o json | jq '[.items[].metadata.uid] | length')
DUR=$(profile_val 420 600)
POD=$(k6_start upgrade load.js PHASES="150:${DUR}s" GAP=0)
sleep 20
log "Güncelleme: $FROM -> $TO"
t0=$(date +%s); steps=0
step() { steps=$((steps + 1)); log "adım $steps: $1"; }
ch=$(istio_charts "$TO" 2>/dev/null || true)
case $MESH in
  istio-sidecar)
    fetch_istio "$TO"; ch=$(istio_charts "$TO"); REV=${TO//./-}
    step "istio-base (CRD) güncelle"
    hb upgrade istio-base "$ch/base" -n istio-system --set defaultRevision=default --wait >/dev/null
    step "yeni revizyonlu istiod ($REV) kur"
    hb upgrade --install "istiod-$REV" "$ch/istio-control/istio-discovery" -n istio-system --set revision="$REV" \
      -f "$MEVAL_ROOT/meshes/istio/istiod-values.yaml" --set global.hub="$ISTIO_HUB" --set global.tag="$TO" --wait --timeout 5m >/dev/null
    step "varsayılan enjeksiyon etiketini yeni revizyona taşı"
    istioctl_v "$TO" --context "kind-$BENCH_CLUSTER" tag set default --revision "$REV" --overwrite >/dev/null
    step "uygulama deployment'larını sırayla yeniden başlat"
    for d in $(kb -n "$SHOP_NS" get deploy -o name); do kb -n "$SHOP_NS" rollout restart "$d" >/dev/null; kb -n "$SHOP_NS" rollout status "$d" --timeout=180s >/dev/null; done
    step "ingress-nginx'i yeniden başlat"
    kb -n ingress-nginx rollout restart deploy/ingress-nginx-controller >/dev/null; kb -n ingress-nginx rollout status deploy/ingress-nginx-controller --timeout=180s >/dev/null
    step "eski istiod'u kaldır"
    hb uninstall istiod -n istio-system --wait >/dev/null ;;
  istio-ambient*)
    fetch_istio "$TO"; ch=$(istio_charts "$TO")
    step "istio-base"; hb upgrade istio-base "$ch/base" -n istio-system --wait >/dev/null
    step "istiod"; hb upgrade istiod "$ch/istio-control/istio-discovery" -n istio-system --set profile=ambient \
      -f "$MEVAL_ROOT/meshes/istio/istiod-values.yaml" --set global.hub="$ISTIO_HUB" --set global.tag="$TO" --wait --timeout 5m >/dev/null
    step "istio-cni"; hb upgrade istio-cni "$ch/istio-cni" -n istio-system --set profile=ambient \
      --set global.hub="$ISTIO_HUB" --set global.tag="$TO" --wait --timeout 5m >/dev/null
    step "ztunnel (DaemonSet, node node)"; hb upgrade ztunnel "$ch/ztunnel" -n istio-system --set hub="$ISTIO_HUB" --set tag="$TO" \
      -f "$MEVAL_ROOT/meshes/istio/ztunnel-values.yaml" --wait --timeout 5m >/dev/null
    kb -n istio-system rollout status ds/ztunnel --timeout=180s >/dev/null
    if [ "$MESH" = istio-ambient-l7 ]; then
      step "waypoint (istiod tarafından güncellenir, hazır olması beklenir)"
      sleep 15; kb -n "$SHOP_NS" rollout status deploy/waypoint --timeout=180s >/dev/null
    fi ;;
  linkerd)
    fetch_linkerd "$TO"
    step "linkerd CRD'leri"; LK_VERSION=$TO lk upgrade --crds | kb apply -f - >/dev/null
    step "linkerd kontrol düzlemi"; LK_VERSION=$TO lk upgrade | kb apply -f - >/dev/null
    LK_VERSION=$TO lk check --wait 5m >/dev/null || warn "linkerd check uyarı verdi"
    step "uygulama deployment'larını sırayla yeniden başlat (yeni proxy)"
    for d in $(kb -n "$SHOP_NS" get deploy -o name); do kb -n "$SHOP_NS" rollout restart "$d" >/dev/null; kb -n "$SHOP_NS" rollout status "$d" --timeout=180s >/dev/null; done
    step "ingress-nginx'i yeniden başlat"
    kb -n ingress-nginx rollout restart deploy/ingress-nginx-controller >/dev/null; kb -n ingress-nginx rollout status deploy/ingress-nginx-controller --timeout=180s >/dev/null ;;
esac
t1=$(date +%s)
metric upgrade_duration_s $((t1 - t0)) sn "güncelleme komutlarının toplam süresi"
metric steps "$steps" adım
restarted=$(kb -n "$SHOP_NS" get pods -o json | jq --argjson t "$t0" '[.items[] | select((.metadata.creationTimestamp | fromdate) > $t)] | length')
metric restarted_pods "$restarted" adet "güncelleme için yeniden başlatılan uygulama pod'u"
# proxy sürümleri
case $MESH in
  istio-sidecar) v=$(kb -n "$SHOP_NS" get pods -o json | jq -r '[.items[].spec.initContainers[]?, .items[].spec.containers[] | select(.name=="istio-proxy") | .image | split(":")[1]] | unique | join(",")') ;;
  istio-ambient*) v=$(kb -n istio-system get ds ztunnel -o jsonpath='{.spec.template.spec.containers[0].image}' | awk -F: '{print $NF}') ;;
  linkerd) v=$(kb -n "$SHOP_NS" get pods -o json | jq -r '[.items[].spec.initContainers[]?, .items[].spec.containers[] | select(.name=="linkerd-proxy") | .image | split(":")[1]] | unique | join(",")') ;;
esac
echo "$v" > "$(raw dataplane-versions.txt)"
check "veri düzlemi yeni sürümde" "$TO" "$v"
log "k6 bitişi bekleniyor"
S=$(k6_wait "$POD" upgrade $((DUR + 60)))
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric failed_requests "$(jq -r '.metrics.http_req_failed.values.passes' "$S")" istek
metric error_rate "$err" oran
metric p99_ms "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
metric max_ms "$(jq -r '.metrics.http_req_duration.values.max' "$S")" ms
check_le "güncelleme sırasında hata oranı" "$err" 0.01
check_true "güncelleme sonrası zincir çalışıyor" chain_ok probe-gateway
