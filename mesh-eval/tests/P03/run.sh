# P03 — Ani yük
SPIKE=$(profile_val "${P03_SPIKE_QUICK:-700}" "${P03_SPIKE_FULL:-1200}")
SD=$(profile_val 20 30)
PH="100:30s,$SPIKE:${SD}s,100:60s"
metric spike_rps "$SPIKE" RPS; metric spike_duration_s "$SD" sn
S=$(k6_run spike load.js $((90 + SD)) PHASES="$PH" GAP=0)
T0=$(jq -r .setup_data.t0 "$S" | cut -d. -f1)
prom_settle 25
n=0
for ph in before spike after; do
  metric "$ph.p50_ms" "$(k6_val "$S" http_req_duration med "phase:$n")" ms
  metric "$ph.p99_ms" "$(k6_val "$S" http_req_duration "p(99)" "phase:$n")" ms
  metric "$ph.error_rate" "$(k6_val "$S" http_req_failed rate "phase:$n")" oran
  metric "$ph.dropped" "$(k6_val "$S" dropped_iterations count "scenario:p$n" | sed 's/null/0/')" istek
  n=$((n + 1))
done
base=$(k6_val "$S" http_req_duration "p(99)" phase:0)
spike_end=$((T0 + 30 + SD))
prom_save k6_p99 "max(k6_http_req_duration_p99{run=\"$(basename "$RUN_DIR")\"})" "$T0" $((spike_end + 60)) 5
rec=$(jq -r --argjson se "$spike_end" --argjson b "$base" '
  [.data.result[0].values[]? | select((.[0]|floor) > $se) | {t: (.[0]|floor), v: (.[1]|tonumber)}]
  | (map(select(.v <= 2*$b)) | first | .t // null) as $t | if $t == null then "null" else ($t - $se) end' "$(raw prom-k6_p99.json)")
metric recovery_s "$rec" sn "sıçrama bitiminden p99 <= 2x taban'a dönüşe kadar"
[ "$rec" = null ] && finding "Sıçrama sonrası 60 sn içinde p99 tabana (2x) dönmedi."
check_le "sıçrama sonrası hata oranı" "$(k6_val "$S" http_req_failed rate phase:2)" 0.01
