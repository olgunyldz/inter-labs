# P01 — Kademeli yük
STAGES=$(profile_val "${P01_STAGES_QUICK:-100,300,600,900}" "${P01_STAGES_FULL:-100,250,500,750,1000,1250,1500,2000}")
DUR=$(profile_val 30 60); GAP=5; WARM=5
IFS=, read -r -a RATES <<<"$STAGES"
PH=$(printf "%s:${DUR}s," "${RATES[@]}"); PH=${PH%,}
TOTAL=$(( ${#RATES[@]} * (DUR + GAP) ))
metric stages "${#RATES[@]}" adet "aşama sayısı"
metric stage_duration_s "$DUR" sn

S=$(k6_run stages load.js "$TOTAL" PHASES="$PH" GAP=$GAP)
T0=$(jq -r .setup_data.t0 "$S" | cut -d. -f1)
prom_settle 25

SLO=${P01_SLO_P99_MS:-100}
knee_slo=""; knee_sat=""; prev=0
for i in "${!RATES[@]}"; do
  r=${RATES[$i]}
  s=$(( T0 + i * (DUR + GAP) )); e=$(( s + DUR ))
  cnt=$(k6_val "$S" http_reqs count "phase:$i")
  rps=$(awk -v c="$cnt" -v d="$DUR" 'BEGIN{printf "%.1f", c/d}')
  err=$(k6_val "$S" http_req_failed rate "phase:$i")
  drop=$(k6_val "$S" dropped_iterations count "scenario:p$i"); [ "$drop" = null ] && drop=0
  p50=$(k6_val "$S" http_req_duration med "phase:$i"); p95=$(k6_val "$S" http_req_duration "p(95)" "phase:$i")
  p99=$(k6_val "$S" http_req_duration "p(99)" "phase:$i"); p999=$(k6_val "$S" http_req_duration "p(99.9)" "phase:$i")
  metric "stage$i.target_rps" "$r" RPS; metric "stage$i.rps" "$rps" RPS "gerçekleşen"
  metric "stage$i.p50_ms" "$p50" ms; metric "stage$i.p95_ms" "$p95" ms; metric "stage$i.p99_ms" "$p99" ms
  metric "stage$i.p999_ms" "$p999" ms; metric "stage$i.error_rate" "$err" oran; metric "stage$i.dropped" "$drop" istek
  metric "stage$i.start" "$s" unix; metric "stage$i.end" "$e" unix
  resources_snapshot "stage$i" $(( s + WARM )) "$e"
  if [ -z "$knee_slo" ] && awk -v p="$p99" -v s="$SLO" -v er="$err" -v a="$rps" -v t="$r" \
       'BEGIN{exit !(p > s || er > 0.01 || a < 0.95*t)}'; then knee_slo=$prev; fi
  if [ -z "$knee_sat" ] && awk -v er="$err" -v a="$rps" -v t="$r" \
       'BEGIN{exit !(er > 0.01 || a < 0.95*t)}'; then knee_sat=$prev; fi
  prev=$r
  # servis başına gecikme: ikinci aşamada (orta yük)
  if [ "$i" -eq 1 ]; then
    while read -r svc v; do
      [ -n "$svc" ] && metric "hop.$svc.p50_ms" "$v" ms "mesh'in ölçtüğü servis gecikmesi (aşama 1)"
    done < <(mesh_hop_latency $(( s + WARM )) "$e" 0.5)
  fi
done
[ -z "$knee_sat" ] && knee_sat=$prev && finding "Doyma noktasına ulaşılmadı: en yüksek aşama ($prev RPS) hatasız karşılandı; profil 'full' ile daha yüksek hızlar denenebilir."
[ -z "$knee_slo" ] && knee_slo=$prev
metric knee_slo_rps "$knee_slo" RPS "p99 <= ${SLO} ms SLO'sunu sağlayan en yüksek aşama"
metric knee_sat_rps "$knee_sat" RPS "hatasız (<%1) ve hedef hızda karşılanan en yüksek aşama"
metric slo_p99_ms "$SLO" ms "SLO eşiği"
check_le "ilk aşama hata oranı" "$(k6_val "$S" http_req_failed rate phase:0)" 0.01
# Grafikler için zaman serileri
END=$(( T0 + TOTAL ))
prom_save k6_p99 "max(k6_http_req_duration_p99{run=\"$(basename "$RUN_DIR")\"})" "$T0" "$END"
prom_save k6_rps "sum(rate(k6_http_reqs_total{run=\"$(basename "$RUN_DIR")\"}[15s]))" "$T0" "$END"

# Aşırı yük sonrası toparlanma: son aşamadan 30 sn sonra zincir kendiliğinden sağlıklı mı
sleep 30
if chain_ok probe-gateway; then
  metric post_overload_healthy 1 bool "aşırı yükten 30 sn sonra zincir kendiliğinden sağlıklı"
else
  metric post_overload_healthy 0 bool "aşırı yükten 30 sn sonra zincir kendiliğinden sağlıklı"
  finding "$MESH: en yüksek aşamadan sonra servis zinciri kendiliğinden toparlanmadı (30 sn sonra hâlâ 5xx); yeniden başlatma gerekti. Mesh'siz referansla kıyaslanmalı."
fi
