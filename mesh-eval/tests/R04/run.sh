# R04 — Kontrol düzlemi kaybı ve node proxy'si
case $(mesh_family "$MESH") in
  istio) CP_NS=istio-system; CP_DEPLOYS=(istiod) ;;
  linkerd) CP_NS=linkerd; CP_DEPLOYS=(linkerd-destination linkerd-identity linkerd-proxy-injector) ;;
esac
cp_scale() { local d; for d in "${CP_DEPLOYS[@]}"; do kb -n "$CP_NS" scale deploy "$d" --replicas="$1" >/dev/null; done; }
on_exit cp_scale 1
on_exit kb -n "$SHOP_NS" scale deploy catalog --replicas="$SVC_REPLICAS"

log "A) kontrol düzlemi kaybı"
POD=$(k6_start cp-outage load.js PHASES="150:100s" GAP=0)
sleep 15
cp_scale 0
for d in "${CP_DEPLOYS[@]}"; do kb -n "$CP_NS" wait --for=delete pod -l "app=$d" --timeout=60s >/dev/null 2>&1 || true; done
kb -n "$CP_NS" wait --for=delete pod -l app=istiod --timeout=60s >/dev/null 2>&1 || true
ok "kontrol düzlemi kapalı: ${CP_DEPLOYS[*]}"
sleep 10
before=$(kb -n "$SHOP_NS" get pods -l app=catalog -o name | sort)
kb -n "$SHOP_NS" scale deploy catalog --replicas=$((SVC_REPLICAS + 1)) >/dev/null
sleep 30
newpod=$(comm -13 <(echo "$before") <(kb -n "$SHOP_NS" get pods -l app=catalog -o name | sort) | head -1)
created=0; meshed=0; serving=0; ready=0
if [ -n "$newpod" ]; then
  created=1
  pj=$(kb -n "$SHOP_NS" get "$newpod" -o json)
  jq -e '[.status.conditions[]? | select(.type=="Ready" and .status=="True")] | length > 0' <<<"$pj" >/dev/null && ready=1
  case $MESH in
    istio-sidecar) jq -e '[.spec.containers[].name, (.spec.initContainers // [])[].name] | index("istio-proxy")' <<<"$pj" >/dev/null && meshed=1 ;;
    istio-ambient*) jq -e '.metadata.annotations["ambient.istio.io/redirection"] == "enabled"' <<<"$pj" >/dev/null && meshed=1 ;;
    linkerd) jq -e '[.spec.containers[].name, (.spec.initContainers // [])[].name] | index("linkerd-proxy")' <<<"$pj" >/dev/null && meshed=1 ;;
  esac
  ip=$(jq -r '.status.podIP // empty' <<<"$pj")
  [ -n "$ip" ] && is_2xx "$(http_code probe-gateway "$SHOP_NS" "http://$ip:9090/")" && serving=1
else
  kb -n "$SHOP_NS" get events --field-selector reason=FailedCreate -o json | jq -r '.items[-1].message // ""' | head -c 400 > "$(raw failedcreate.txt)"
fi
metric A.new_pod_created "$created" bool "kontrol düzlemi yokken yeni pod oluşturulabildi"
metric A.new_pod_ready "$ready" bool
metric A.new_pod_meshed "$meshed" bool "yeni pod mesh'e dahil (proxy / ambient yönlendirme)"
metric A.new_pod_serving "$serving" bool "yeni pod mesh içinden trafik alabiliyor"
[ "$created" = 0 ] && finding "$MESH: kontrol düzlemi yokken yeni pod oluşturulamadı (enjeksiyon webhook'u hata veriyor: $(cat "$(raw failedcreate.txt)" | head -c 200)). Ölçeklenme ve yeniden başlatmalar durur."
[ "$created" = 1 ] && [ "$meshed" = 0 ] && finding "$MESH: kontrol düzlemi yokken yeni pod mesh'e GİRMEDEN açıldı (proxy'siz). Zorunlu mTLS altında bu pod diğer servislerle konuşamaz / güvenlik açığı oluşturur."
[ "$created" = 1 ] && [ "$meshed" = 1 ] && [ "$serving" = 0 ] && finding "$MESH: kontrol düzlemi yokken yeni pod mesh'e girdi ama trafik alamadı (kimlik/yapılandırma dağıtılamadı)."
sleep 5
cp_scale 1
for d in "${CP_DEPLOYS[@]}"; do kb -n "$CP_NS" rollout status deploy "$d" --timeout=180s >/dev/null; done
ok "kontrol düzlemi geri geldi"
S=$(k6_wait "$POD" cp-outage 240)
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric A.error_rate "$err" oran "kontrol düzlemi kaybı boyunca mevcut trafikte hata oranı"
metric A.failed_requests "$(jq -r '.metrics.http_req_failed.values.passes' "$S")" istek
metric A.p99_ms "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
check_le "A: kontrol düzlemi kaybında mevcut trafik hata oranı" "$err" 0.01
kb -n "$SHOP_NS" scale deploy catalog --replicas="$SVC_REPLICAS" >/dev/null

if [[ "$MESH" == istio-ambient* ]]; then
  log "B) ztunnel yeniden başlaması (app node'u)"
  sleep 20
  POD=$(k6_start ztunnel-restart load.js PHASES="150:60s" GAP=0)
  sleep 20
  zt=$(kb -n istio-system get pod -l app=ztunnel --field-selector spec.nodeName="$BENCH_CLUSTER-worker" -o name)
  t0=$(date +%s); kb -n istio-system delete "$zt" >/dev/null
  kb -n istio-system rollout status ds/ztunnel --timeout=120s >/dev/null
  metric B.ztunnel_restart_s $(( $(date +%s) - t0 )) sn "ztunnel pod'unun yeniden hazır olma süresi"
  S=$(k6_wait "$POD" ztunnel-restart 200)
  metric B.failed_requests "$(jq -r '.metrics.http_req_failed.values.passes' "$S")" istek "ztunnel yeniden başlarken başarısız istek"
  metric B.error_rate "$(jq -r '.metrics.http_req_failed.values.rate' "$S")" oran
  metric B.pods_on_node "$(kb -n "$SHOP_NS" get pods --field-selector spec.nodeName="$BENCH_CLUSTER-worker" --no-headers | wc -l)" adet "aynı ztunnel'e bağlı pod sayısı (etki alanı)"
fi
