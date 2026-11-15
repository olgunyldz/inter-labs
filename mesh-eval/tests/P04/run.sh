# P04 — Uçtan uca yol (k6 host'ta, lab-edge segmentinde)
STAGES=$(profile_val "100,250" "100,250,400"); DUR=$(profile_val 30 60)
IFS=, read -r -a RATES <<<"$STAGES"
PH=$(printf "%s:${DUR}s," "${RATES[@]}"); PH=${PH%,}
EDGE_IP=$(node_ip_of "$EDGE_LB" "$NET_EDGE")
docker run --rm --name "k6-p04-$$" --network "$NET_EDGE" --cpuset-cpus "$CPUSET_LOADGEN" \
  --add-host "shop.localtest.me:$EDGE_IP" -v "$TESTS_DIR/k6:/scripts:ro" \
  -e PHASES="$PH" -e GAP=5 -e TARGET=https://shop.localtest.me/ \
  "$K6_IMAGE" run --quiet --no-color /scripts/load.js > "$(raw e2e-k6.log)" 2>&1 || true
sed -n '/==K6SUMMARY==/,/==END==/p' "$(raw e2e-k6.log)" | sed '1d;$d' > "$(raw e2e-summary.json)"
S=$(raw e2e-summary.json); jq -e . "$S" >/dev/null || die "k6 özeti okunamadı"
for i in "${!RATES[@]}"; do
  metric "stage$i.target_rps" "${RATES[$i]}" RPS
  metric "stage$i.p50_ms" "$(k6_val "$S" http_req_duration med "phase:$i")" ms
  metric "stage$i.p95_ms" "$(k6_val "$S" http_req_duration "p(95)" "phase:$i")" ms
  metric "stage$i.p99_ms" "$(k6_val "$S" http_req_duration "p(99)" "phase:$i")" ms
  metric "stage$i.error_rate" "$(k6_val "$S" http_req_failed rate "phase:$i")" oran
done
metric tls_handshake_p50_ms "$(jq -r '.metrics.http_req_tls_handshaking.values.med // "null"' "$S")" ms
check_le "ilk aşama hata oranı" "$(k6_val "$S" http_req_failed rate phase:0)" 0.01
