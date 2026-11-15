# P05 — Kaynak tüketimi
IDLE=$(profile_val 45 120); LOAD=$(profile_val 90 300); RATE=${P05_RATE:-250}
metric rate_rps "$RATE" RPS
log "Boşta ölçüm ($IDLE sn)"
s=$(date +%s); sleep "$IDLE"; e=$(date +%s)
prom_settle 20
resources_snapshot idle $((s + 5)) "$e"
log "Yük altında ölçüm ($RATE RPS x $LOAD sn)"
S=$(k6_run load load.js "$LOAD" PHASES="$RATE:${LOAD}s" GAP=0)
T0=$(jq -r .setup_data.t0 "$S" | cut -d. -f1); ls=$((T0 + 10)); le=$((T0 + LOAD))
prom_settle 25
resources_snapshot load "$ls" "$le"
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric load.error_rate "$err" oran
metric load.p50_ms "$(jq -r '.metrics.http_req_duration.values.med' "$S")" ms
metric load.p99_ms "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
rps=$(awk -v c="$(jq -r '.metrics.http_reqs.values.count' "$S")" -v d="$LOAD" 'BEGIN{printf "%.1f", c/d}')
metric load.rps "$rps" RPS
for r in app sidecar ztunnel waypoint cni control; do
  [ "$(role_count "$r" "$le")" = 0 ] && continue
  metric "req.$r.cpu_cores" "$(role_requests "$r" cpu "$le")" çekirdek "ayrılan CPU (requests)"
  metric "req.$r.mem_mib" "$(role_requests "$r" memory "$le")" MiB "ayrılan bellek (requests)"
done
# Türetilmiş değerler: veri düzlemi = sidecar + ztunnel + waypoint (+ cni)
dp_cpu=0; dp_mem_idle=0
for r in sidecar ztunnel waypoint cni; do
  [ "$(role_count "$r" "$le")" = 0 ] && continue
  dp_cpu=$(awk -v a="$dp_cpu" -v b="$(role_cpu "$r" "$ls" "$le")" 'BEGIN{print a+b}')
  dp_mem_idle=$(awk -v a="$dp_mem_idle" -v b="$(role_mem "$r" $((s + 5)) "$e")" 'BEGIN{print a+b}')
done
pods=$(prom_scalar "count(kube_pod_info{$C,namespace=\"$SHOP_NS\"})" "$le")
metric shop_pods "$pods" adet
metric dataplane.cpu_cores "$dp_cpu" çekirdek "yük altında veri düzlemi CPU"
metric dataplane.cpu_per_1k_rps "$(awk -v c="$dp_cpu" -v r="$rps" 'BEGIN{ if (r>0) printf "%.4f", c*1000/r; else print 0 }')" çekirdek "1000 RPS (giriş) başına veri düzlemi CPU"
metric dataplane.mem_idle_mib "$dp_mem_idle" MiB "boşta veri düzlemi belleği"
metric dataplane.mem_per_pod_mib "$(awk -v m="$dp_mem_idle" -v p="$pods" 'BEGIN{ if (p>0) printf "%.2f", m/p; else print 0 }')" MiB "uygulama pod'u başına veri düzlemi belleği (boşta)"
app_cpu=$(role_cpu app "$ls" "$le"); node_cpu=$(role_cpu node_app "$ls" "$le")
metric node_overhead_cores "$(awk -v n="$node_cpu" -v a="$app_cpu" -v d="$dp_cpu" 'BEGIN{printf "%.3f", n-a-d}')" çekirdek "servis node'unda app+proxy dışı CPU (kernel ağ, kubelet...)"
check_le "yük altında hata oranı" "$err" 0.01
