# Kaynak tüketimi: konteynerleri "rol"lere ayırıp CPU/bellek ölçer (cAdvisor + kube-state-metrics)
#   app          : shop servislerinin uygulama konteynerleri
#   sidecar      : pod içi proxy (istio-proxy, linkerd-proxy)          -> veri düzlemi
#   ztunnel      : Istio ambient node proxy'si (DaemonSet)             -> veri düzlemi
#   waypoint     : Istio ambient L7 proxy'si                            -> veri düzlemi
#   cni          : istio-cni node ajanı                                 -> veri düzlemi altyapısı
#   control      : istiod / linkerd kontrol düzlemi (kendi proxy'leri dahil)
#   ingress      : bench ingress-nginx (+ mesh proxy'si)
#   loadgen      : k6 pod'u (kendi proxy'si dahil, pod cgroup'u)
#   node_app / node_loadgen / node_control : node'un toplam CPU'su (kernel ağ işleme dahil)
#     -> uygulama+proxy toplamının ötesindeki kısım mesh'in gizli maliyetidir (iptables/eBPF, softirq)

C="cluster=\"$BENCH_CLUSTER\""
declare -A ROLE_SEL=(
  [app]="namespace=\"$SHOP_NS\",container=\"app\""
  [sidecar]="namespace=\"$SHOP_NS\",container=~\"istio-proxy|linkerd-proxy\",pod!~\"waypoint-.*\""
  [ztunnel]="namespace=\"istio-system\",pod=~\"ztunnel-.*\",container!=\"\""
  [waypoint]="namespace=\"$SHOP_NS\",pod=~\"waypoint-.*\",container!=\"\""
  [cni]="namespace=\"istio-system\",pod=~\"istio-cni-node-.*\",container!=\"\""
  [control]="namespace=~\"istio-system|linkerd\",pod!~\"ztunnel-.*|istio-cni-node-.*\",container!=\"\""
  [ingress]="namespace=\"ingress-nginx\",container!=\"\""
  [loadgen]="namespace=\"$LOADGEN_NS\",container=\"\",image=\"\",pod=~\"k6-.*\""
  [node_app]="id=\"/\",instance=\"$BENCH_CLUSTER-worker\""
  [node_loadgen]="id=\"/\",instance=\"$BENCH_CLUSTER-worker2\""
  [node_control]="id=\"/\",instance=\"$BENCH_CLUSTER-control-plane\""
)
ROLES=(app sidecar ztunnel waypoint cni control ingress loadgen node_app node_loadgen node_control)

# role_cpu <rol> <başlangıç> <bitiş>: pencere boyunca ortalama çekirdek
role_cpu() {
  local w=$(( $3 - $2 ))
  prom_scalar "sum(rate(container_cpu_usage_seconds_total{$C,${ROLE_SEL[$1]}}[${w}s]))" "$3" | sed 's/^null$/0/'
}
# role_mem <rol> <başlangıç> <bitiş>: pencere boyunca ortalama bellek (MiB)
role_mem() {
  local w=$(( $3 - $2 )) v
  v=$(prom_scalar "sum(avg_over_time(container_memory_working_set_bytes{$C,${ROLE_SEL[$1]}}[${w}s]))" "$3")
  [ "$v" = null ] && echo 0 || awk -v b="$v" 'BEGIN{printf "%.1f", b/1048576}'
}
# role_count <rol> <zaman>: konteyner sayısı
role_count() {
  prom_scalar "count(last_over_time(container_memory_working_set_bytes{$C,${ROLE_SEL[$1]}}[1m]))" "$2" | sed 's/^null$/0/'
}
# role_requests <rol> <cpu|memory> <zaman>: kaynak istekleri (requests) toplamı (çekirdek / MiB)
role_requests() {
  local sel=${ROLE_SEL[$1]} r=$2 v
  sel=${sel//container!=\"\"/container=~\".+\"}
  # native sidecar'lar (Istio 1.31, Linkerd edge) init container olarak görünür -> iki metrik toplanır
  local run="* on(namespace,pod) group_left() (max by (namespace,pod) (last_over_time(kube_pod_status_phase{$C,phase=\"Running\"}[1m])) == 1)"
  v=$(prom_scalar "(sum(last_over_time(kube_pod_container_resource_requests{$C,resource=\"$r\",${sel}}[1m]) $run) or vector(0)) + (sum(last_over_time(kube_pod_init_container_resource_requests{$C,resource=\"$r\",${sel}}[1m]) $run) or vector(0))" "$3")
  [ "$v" = null ] && { echo 0; return; }
  [ "$r" = memory ] && awk -v b="$v" 'BEGIN{printf "%.1f", b/1048576}' || echo "$v"
}

# resources_snapshot <önek> <başlangıç> <bitiş>: tüm roller için metrik yazar
resources_snapshot() {
  local p=$1 s=$2 e=$3 r cpu mem cnt
  for r in "${ROLES[@]}"; do
    cpu=$(role_cpu "$r" "$s" "$e"); mem=$(role_mem "$r" "$s" "$e"); cnt=$(role_count "$r" "$e")
    [ "$cnt" = 0 ] && continue
    metric "$p.$r.cpu_cores" "$cpu" çekirdek "$r ortalama CPU"
    metric "$p.$r.mem_mib" "$mem" MiB "$r ortalama bellek"
    metric "$p.$r.containers" "$cnt" adet "$r konteyner sayısı"
  done
}

# Prometheus sorgusunun ham sonucunu kaydet: prom_save <ad> <promql> <başlangıç> <bitiş> [adım]
prom_save() {
  prom_range "$2" "$3" "$4" "${5:-5}" > "$(raw "prom-$1.json")"
}

# Zaman senkronu: Prometheus'un remote-write gecikmesi için pencere sonrası bekleme
prom_settle() { sleep "${1:-20}"; }

# mesh_hop_latency <başlangıç> <bitiş> <quantile>: servis başına (inbound) gecikme, ms
#   Istio (sidecar / waypoint): istio_request_duration_milliseconds, reporter=destination|waypoint
#   Linkerd: response_latency_ms, direction=inbound
#   none ve ambient L4: HTTP seviyesinde mesh metriği yoktur (boş döner)
mesh_hop_latency() {
  local s=$1 e=$2 q=$3 w=$(( $2 - $1 )) expr
  case ${MESH:-$(current_mesh)} in
    istio-sidecar) expr="histogram_quantile($q, sum by (le, destination_workload) (rate(istio_request_duration_milliseconds_bucket{$C,reporter=\"destination\",destination_workload_namespace=\"$SHOP_NS\"}[${w}s])))" ;;
    istio-ambient-l7) expr="histogram_quantile($q, sum by (le, destination_workload) (rate(istio_request_duration_milliseconds_bucket{$C,reporter=\"waypoint\",destination_workload_namespace=\"$SHOP_NS\"}[${w}s])))" ;;
    linkerd) expr="label_replace(histogram_quantile($q, sum by (le, app) (rate(response_latency_ms_bucket{$C,namespace=\"$SHOP_NS\",direction=\"inbound\",app!~\"probe-.*\"}[${w}s]))), \"destination_workload\", \"\$1\", \"app\", \"(.*)\")" ;;
    *) return 0 ;;
  esac
  prom_query "$expr" "$e" | jq -r '.data.result[] | "\(.metric.destination_workload) \(.value[1])"'
}

# role_req_count <rol> <zaman>: çalışan pod'lardaki konteyner sayısı (kube-state-metrics; requests ile aynı kaynak)
role_req_count() {
  local sel=${ROLE_SEL[$1]}
  sel=${sel//container!=\"\"/container=~\".+\"}
  local run="* on(namespace,pod) group_left() (max by (namespace,pod) (last_over_time(kube_pod_status_phase{$C,phase=\"Running\"}[1m])) == 1)"
  prom_scalar "(count(last_over_time(kube_pod_container_info{$C,${sel}}[1m]) $run) or vector(0)) + (count(last_over_time(kube_pod_init_container_info{$C,${sel}}[1m]) $run) or vector(0))" "$2" | sed 's/^null$/0/'
}
# shop_pods_cad <başlangıç> <bitiş>: pencerede yaşayan shop pod'u sayısı (cAdvisor; bellek ölçümüyle aynı kaynak)
shop_pods_cad() {
  prom_scalar "count(max by (pod) (max_over_time(container_memory_working_set_bytes{$C,namespace=\"$SHOP_NS\",container!=\"\",container!~\"istio-proxy|linkerd-proxy|istio-init|linkerd-init|istio-validation\"}[$(( $2 - $1 ))s])))" "$2" | sed 's/^null$/0/'
}
