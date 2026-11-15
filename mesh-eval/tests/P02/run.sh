# P02 — Sabit uzun yük
RATE=$(profile_val "${P02_RATE_QUICK:-200}" "${P02_RATE_FULL:-300}")
Q=$(profile_val 30 300)   # çeyrek süresi (sn)
PH="$RATE:${Q}s,$RATE:${Q}s,$RATE:${Q}s,$RATE:${Q}s"
metric rate_rps "$RATE" RPS; metric duration_s $((4 * Q)) sn
S=$(k6_run soak load.js $((4 * Q)) PHASES="$PH" GAP=0)
T0=$(jq -r .setup_data.t0 "$S" | cut -d. -f1)
prom_settle 25
tot=0; errsum=0
for i in 0 1 2 3; do
  metric "q$i.p99_ms" "$(k6_val "$S" http_req_duration "p(99)" "phase:$i")" ms "çeyrek $((i+1))"
  metric "q$i.p50_ms" "$(k6_val "$S" http_req_duration med "phase:$i")" ms
done
p99_first=$(k6_val "$S" http_req_duration "p(99)" phase:0); p99_last=$(k6_val "$S" http_req_duration "p(99)" phase:3)
drift=$(awk -v a="$p99_last" -v b="$p99_first" 'BEGIN{printf "%.3f", a/b}')
metric p50_ms "$(jq -r '.metrics.http_req_duration.values.med' "$S")" ms
metric p99_ms "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric error_rate "$err" oran
metric p99_drift "$drift" kat "son çeyrek p99 / ilk çeyrek p99"
s1=$((T0 + 5)); e1=$((T0 + Q)); s4=$((T0 + 3 * Q)); e4=$((T0 + 4 * Q))
for r in app sidecar ztunnel waypoint control; do
  [ "$(role_count "$r" "$e4")" = 0 ] && continue
  m1=$(role_mem "$r" "$s1" "$e1"); m4=$(role_mem "$r" "$s4" "$e4")
  metric "$r.mem_first_mib" "$m1" MiB; metric "$r.mem_last_mib" "$m4" MiB
  metric "$r.mem_growth_mib" "$(awk -v a="$m4" -v b="$m1" 'BEGIN{printf "%.1f", a-b}')" MiB "son - ilk çeyrek"
done
resources_snapshot load "$s1" "$e4"
check_le "hata oranı" "$err" 0.01
# kayma sınırı: ilk çeyreğin 1.5 katı veya +10 ms (küçük değerlerde göreli oran gürültüye duyarlı)
lim=$(awk -v f="$p99_first" 'BEGIN{a=1.5*f; b=f+10; printf "%.3f", (a>b)?a:b}')
metric p99_drift_limit_ms "$lim" ms
check_le "son çeyrek p99 (ms) kayma sınırı içinde" "$p99_last" "$lim"
prom_save k6_p99 "max(k6_http_req_duration_p99{run=\"$(basename "$RUN_DIR")\"})" "$T0" "$e4" 15
prom_save mem_by_role "sum by (container) (container_memory_working_set_bytes{$C,namespace=\"$SHOP_NS\",container=~\"app|istio-proxy|linkerd-proxy\"})" "$T0" "$e4" 15
