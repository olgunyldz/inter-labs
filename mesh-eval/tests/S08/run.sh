# S08 — Sertifika yönetimi ve CA rotasyonu
source "$MEVAL_ROOT/lib/pki.sh"
IC=(--context "kind-$BENCH_CLUSTER")
# leaf_pem <pod>: order pod'unun iş yükü sertifikası (PEM, yaprak)
leaf_pem() {
  local pod=$1
  case $MESH in
    istio-sidecar)
      istioctl_v "$ISTIO_VERSION" "${IC[@]}" proxy-config secret "$pod.$SHOP_NS" -o json \
        | jq -r '.dynamicActiveSecrets[] | select(.name=="default") | .secret.tlsCertificate.certificateChain.inlineBytes' \
        | base64 -d | awk '/BEGIN/{n++} n==1' ;;
    istio-ambient*)
      local node; node=$(kb -n "$SHOP_NS" get pod "$pod" -o jsonpath='{.spec.nodeName}')
      istioctl_v "$ISTIO_VERSION" "${IC[@]}" ztunnel-config certificate --node "$node" -o json > "$(raw ztunnel-certs.json)"
      jq -r --arg id "spiffe://cluster.local/ns/$SHOP_NS/sa/order" '
        [.[] | select(.identity == $id)][0].certChain[0].pem' "$(raw ztunnel-certs.json)" \
        | { read -r v; if [[ "$v" == -----BEGIN* ]]; then printf '%s\n' "$v"; cat; else echo "$v" | base64 -d; fi; } ;;
    linkerd)
      # linkerd identity yalnızca metin verir; PEM, proxy'nin inbound portundaki TLS el sıkışmasından alınır
      local ip; ip=$(kb -n "$SHOP_NS" get pod "$pod" -o jsonpath='{.status.podIP}')
      kb -n "$OUTSIDE_NS" exec deploy/probe-outside -- bash -c \
        "echo | timeout 5 openssl s_client -connect $ip:4143 -servername order.$SHOP_NS.serviceaccount.identity.linkerd.cluster.local 2>/dev/null | openssl x509" 2>/dev/null ;;
  esac
}
order_pod() { kb -n "$SHOP_NS" get pod -l app=order -o json | jq -r '[.items[] | select(.metadata.deletionTimestamp == null)][0].metadata.name'; }
cert_info() { # PEM stdin -> "issuerCN|ttl_saat|san|aki"
  local f; f=$(mktemp); cat > "$f"
  local iss nb na san aki
  iss=$(openssl x509 -in "$f" -noout -issuer -nameopt multiline 2>/dev/null | sed -n 's/^ *commonName *= *//p')
  nb=$(date -d "$(openssl x509 -in "$f" -noout -startdate | cut -d= -f2)" +%s)
  na=$(date -d "$(openssl x509 -in "$f" -noout -enddate | cut -d= -f2)" +%s)
  san=$(openssl x509 -in "$f" -noout -ext subjectAltName 2>/dev/null | tail -1 | sed 's/^ *//')
  aki=$(openssl x509 -in "$f" -noout -ext authorityKeyIdentifier 2>/dev/null | tail -1 | tr -d ' :' | sed 's/^keyid//')
  rm -f "$f"; echo "$iss|$(( (na - nb) / 3600 ))|$san|$aki"
}
ski_of() { openssl x509 -in "$1" -noout -ext subjectKeyIdentifier | tail -1 | tr -d ' :'; }

P=$(order_pod)
leaf_pem "$P" > "$(raw leaf-before.pem)"
[ -s "$(raw leaf-before.pem)" ] || die "iş yükü sertifikası alınamadı ($MESH)"
IFS='|' read -r iss ttl san aki <<<"$(cert_info < "$(raw leaf-before.pem)")"
metric cert_ttl_h "$ttl" saat "iş yükü sertifikası geçerlilik süresi"
echo "$iss" > "$(raw issuer.txt)"; echo "$san" > "$(raw san.txt)"
case $MESH in
  istio-*) CA_DIR=$(pki_istio cluster-a); want_san="spiffe://cluster.local/ns/$SHOP_NS/sa/order" ;;
  linkerd) CA_DIR=$(pki_linkerd issuer); want_san="order.$SHOP_NS.serviceaccount.identity.linkerd.cluster.local" ;;
esac
# Beklenen ara CA: cluster'da yüklü olan (önceki tekrarın rotasyonu kalıcıdır); yoksa ilk kurulumdaki
CUR_CA=$(mktemp)
case $MESH in
  istio-*) kb -n istio-system get secret cacerts -o jsonpath='{.data.ca-cert\.pem}' | base64 -d > "$CUR_CA" ;;
  linkerd) kb -n linkerd get secret linkerd-identity-issuer -o jsonpath='{.data.crt\.pem}' | base64 -d > "$CUR_CA" ;;
esac
[ -s "$CUR_CA" ] || cp "$CA_DIR/ca-cert.pem" "$CUR_CA"
check "sertifika kurumsal ara CA'dan (AKI = ara CA SKI)" "$(ski_of "$CUR_CA")" "$aki"
rm -f "$CUR_CA"
check_le "sertifika ömrü (saat)" "$ttl" 24
check "kimlik (SAN)" var "$(grep -qF "$want_san" <<<"$san" && echo var || echo yok)"

log "Yük altında ara CA rotasyonu"
POD=$(k6_start rotation load.js PHASES="200:$( [[ "$MESH" == istio-ambient* ]] && echo 160 || echo 100 )s" GAP=0)
sleep 20
TS=$(date +%s); restart_needed=0
case $MESH in
  istio-*)
    pki_intermediate istio "rot-$TS" rsa "istio intermediate rot-$TS"
    N="$PKI_DIR/istio/rot-$TS"
    kb -n istio-system create secret generic cacerts \
      --from-file=ca-cert.pem="$N/ca-cert.pem" --from-file=ca-key.pem="$N/ca-key.pem" \
      --from-file=root-cert.pem="$N/root-cert.pem" --from-file=cert-chain.pem="$N/cert-chain.pem" \
      --dry-run=client -o yaml | kb apply -f - >/dev/null ;;
  linkerd)
    pki_intermediate linkerd "rot-$TS" ec identity.linkerd.cluster.local 365
    N="$PKI_DIR/linkerd/rot-$TS"
    # linkerd install ile gelen issuer secret'ı: Opaque, crt.pem / key.pem
    kb -n linkerd create secret generic linkerd-identity-issuer \
      --from-file=crt.pem="$N/ca-cert.pem" --from-file=key.pem="$N/ca-key.pem" \
      --dry-run=client -o yaml | kb apply -f - >/dev/null ;;
esac
sleep 15
kb -n "$SHOP_NS" rollout restart deploy/order >/dev/null; kb -n "$SHOP_NS" rollout status deploy/order --timeout=120s >/dev/null
sleep 5
NP=$(order_pod); leaf_pem "$NP" > "$(raw leaf-after.pem)"
IFS='|' read -r iss2 ttl2 san2 aki2 <<<"$(cert_info < "$(raw leaf-after.pem)")"
if [ "$aki2" != "$(ski_of "$N/ca-cert.pem")" ]; then
  # CA otomatik yeniden yüklenmedi -> kontrol düzlemini yeniden başlat
  restart_needed=1
  case $MESH in
    istio-*) kb -n istio-system rollout restart deploy/istiod >/dev/null; kb -n istio-system rollout status deploy/istiod --timeout=120s >/dev/null ;;
    linkerd) kb -n linkerd rollout restart deploy/linkerd-identity >/dev/null; kb -n linkerd rollout status deploy/linkerd-identity --timeout=120s >/dev/null ;;
  esac
  kb -n "$SHOP_NS" rollout restart deploy/order >/dev/null; kb -n "$SHOP_NS" rollout status deploy/order --timeout=120s >/dev/null
  sleep 5; NP=$(order_pod); leaf_pem "$NP" > "$(raw leaf-after.pem)"
  IFS='|' read -r iss2 ttl2 san2 aki2 <<<"$(cert_info < "$(raw leaf-after.pem)")"
  finding "$MESH: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti."
fi
# Ambient: sertifikalar kimlik başına node'daki ztunnel'de önbelleklidir; yeni pod aynı kimlik için eski
# sertifikayı alır. Yeni CA için ztunnel'lerin yeniden başlatılması gerekir (DaemonSet, node node).
zt_restart=0
if [[ "$MESH" == istio-ambient* ]] && [ "$aki2" != "$(ski_of "$N/ca-cert.pem")" ]; then
  zt_restart=1
  log "ambient: ztunnel DaemonSet yeniden başlatılıyor (yük altında)"
  kb -n istio-system rollout restart ds/ztunnel >/dev/null; kb -n istio-system rollout status ds/ztunnel --timeout=180s >/dev/null
  sleep 5; NP=$(order_pod); leaf_pem "$NP" > "$(raw leaf-after.pem)"
  IFS='|' read -r iss2 ttl2 san2 aki2 <<<"$(cert_info < "$(raw leaf-after.pem)")"
  finding "$MESH: CA rotasyonunda yeni pod bile eski ara CA'nın sertifikasını kullandı (ztunnel kimlik başına önbellekte tutuyor). Yeni CA'nın devreye girmesi için ztunnel DaemonSet'inin yeniden başlatılması gerekti; bu sırada node'daki tüm pod'ların trafiği etkilenir."
fi
metric rotation.needed_restart "$restart_needed" bool "yeni CA için kontrol düzlemi yeniden başlatıldı mı"
metric rotation.ztunnel_restart "$zt_restart" bool "yeni CA için ztunnel yeniden başlatıldı mı (ambient)"
check "rotasyon: yeni pod yeni ara CA'dan sertifika aldı" "$(ski_of "$N/ca-cert.pem")" "$aki2"
check_true "rotasyon: eski ve yeni sertifikalı pod'lar konuşuyor (zincir)" chain_ok probe-gateway
S=$(k6_wait "$POD" rotation 240)
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric rotation.error_rate "$err" oran "rotasyon sırasında hata oranı"
metric rotation.p99_ms "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
if [ "$zt_restart" = 1 ] && awk -v e="$err" 'BEGIN{exit !(e > 0.01)}'; then
  finding "$MESH: CA rotasyonu için gereken ztunnel yeniden başlatması yük altında kesinti yarattı: hata oranı %$(awk -v e="$err" 'BEGIN{printf "%.1f", e*100}'), $(jq -r '.metrics.http_req_failed.values.passes' "$S") başarısız istek, p99 $(jq -r '.metrics.http_req_duration.values["p(99)"] | floor' "$S") ms. Waypoint üzerinden geçen tüneller node proxy'si yeniden başlarken kopuyor."
fi
check_le "rotasyon sırasında hata oranı" "$err" 0.01
