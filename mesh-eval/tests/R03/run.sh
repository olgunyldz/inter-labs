# R03 — Yük altında pod kaybı
POD=$(k6_start failover load.js PHASES="200:100s" GAP=0)
sleep 25
for s in order catalog fraud; do
  p=$(kb -n "$SHOP_NS" get pod -l app=$s -o jsonpath='{.items[0].metadata.name}')
  log "pod siliniyor: $p"
  kb -n "$SHOP_NS" delete pod "$p" --wait=false >/dev/null
  sleep 20
done
S=$(k6_wait "$POD" failover 240)
fails=$(jq -r '.metrics.http_req_failed.values.passes' "$S")
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric failed_requests "$fails" istek "toplam başarısız istek"
metric error_rate "$err" oran
metric p99_ms "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
metric max_ms "$(jq -r '.metrics.http_req_duration.values.max' "$S")" ms
check_le "pod kaybında hata oranı" "$err" 0.01
kb -n "$SHOP_NS" rollout status deploy/order --timeout=120s >/dev/null
