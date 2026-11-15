# O02 — Metrik maliyeti
S=$(k6_run o02 load.js 60 PHASES="100:60s" GAP=0)
prom_settle 30
t=$(date +%s)
L="cluster=\"$BENCH_CLUSTER\",mesh=\"$MESH\""
tot=$(prom_scalar "count({$L})" "$t")
mesh_series=$(prom_scalar "count({$L,__name__=~\"istio_.*|envoy_.*|pilot_.*|ztunnel_.*\"} or {$L,job=~\"linkerd-.*\"})" "$t")
[ "$mesh_series" = null ] && mesh_series=0
pods=$(prom_scalar "count(kube_pod_info{$L,namespace=\"$SHOP_NS\"})" "$t")
sps=$(prom_scalar "sum(rate(prometheus_remote_storage_samples_total{$L}[2m]))" "$t")
metric series_total "$tot" seri "bench cluster'ından gelen aktif seri"
metric series_mesh "$mesh_series" seri "mesh'e ait metrik aileleri"
metric shop_pods "$pods" adet
metric series_mesh_per_pod "$(awk -v a="$mesh_series" -v b="$pods" 'BEGIN{ if (b>0) printf "%.1f", a/b; else print 0 }')" seri "uygulama pod'u başına mesh serisi"
metric samples_per_s "$sps" örnek/sn "agent remote-write hızı"
prom_query "topk(15, count by (__name__) ({$L}))" "$t" | jq -r '.data.result[] | "\(.value[1]) \(.metric.__name__)"' | sort -rn > "$(raw top-metrics.txt)"
check_true "ölçüm tamamlandı" test "$tot" != null
