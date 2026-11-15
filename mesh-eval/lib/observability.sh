# Gözlem altyapısı: mgmt'de Prometheus/Grafana/Tempo, bench cluster'ında Prometheus agent

obs_install_mgmt() {
  log "Gözlem (mgmt): Prometheus, Tempo, Grafana"
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update >/dev/null
  helm repo add grafana https://grafana.github.io/helm-charts --force-update >/dev/null
  helm repo update prometheus-community grafana >/dev/null
  # mgmt ingress'inin TCP portları (9090/9411/4317) için ingress-nginx'i güncelle
  hm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version "$INGRESS_NGINX_CHART_VERSION" \
    -n ingress-nginx -f "$LAB_ROOT/platform/ingress-nginx/values-common.yaml" \
    -f "$LAB_ROOT/platform/ingress-nginx/values-mgmt.yaml" --wait --timeout 5m >/dev/null
  hm upgrade --install prometheus prometheus-community/prometheus --version "$PROMETHEUS_CHART_VERSION" \
    -n observability --create-namespace -f "$MEVAL_ROOT/observability/prometheus-mgmt.yaml" --wait --timeout 6m >/dev/null
  ok "prometheus"
  hm upgrade --install tempo grafana/tempo --version "$TEMPO_CHART_VERSION" \
    -n observability -f "$MEVAL_ROOT/observability/tempo.yaml" --wait --timeout 6m >/dev/null
  ok "tempo"
  km -n observability create configmap grafana-dashboards-mesh-eval \
    --from-file="$MEVAL_ROOT/observability/dashboards/" --dry-run=client -o yaml | km apply -f - >/dev/null
  hm upgrade --install grafana grafana/grafana --version "$GRAFANA_CHART_VERSION" \
    -n observability -f "$MEVAL_ROOT/observability/grafana.yaml" --wait --timeout 6m >/dev/null
  ok "grafana"
}

# Bench cluster'ında mgmt'yi temsil eden selector'sız servisler (lab'daki data servisleri gibi)
obs_bridge_bench() {
  local ip
  ip=$(node_ip_of mgmt-control-plane "$NET_APP")
  [ -n "$ip" ] || die "mgmt node'unun $NET_APP IP'si bulunamadı"
  kb create namespace observability --dry-run=client -o yaml | kb apply -f - >/dev/null
  kb apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Service
metadata: { name: prometheus, namespace: observability }
spec:
  ports: [{ name: http, port: 9090, targetPort: 9090, appProtocol: http }]
---
apiVersion: v1
kind: Service
metadata: { name: tempo, namespace: observability }
spec:
  ports:
    - { name: zipkin, port: 9411, targetPort: 9411, appProtocol: http }
    - { name: otlp-grpc, port: 4317, targetPort: 4317, appProtocol: grpc }
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: prometheus-mgmt
  namespace: observability
  labels: { kubernetes.io/service-name: prometheus, endpointslice.kubernetes.io/managed-by: mesh-eval }
addressType: IPv4
ports: [{ name: http, port: 9090, protocol: TCP }]
endpoints: [{ addresses: ["$ip"], conditions: { ready: true } }]
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: tempo-mgmt
  namespace: observability
  labels: { kubernetes.io/service-name: tempo, endpointslice.kubernetes.io/managed-by: mesh-eval }
addressType: IPv4
ports:
  - { name: zipkin, port: 9411, protocol: TCP }
  - { name: otlp-grpc, port: 4317, protocol: TCP }
endpoints: [{ addresses: ["$ip"], conditions: { ready: true } }]
YAML
  ok "bench -> mgmt köprüsü (prometheus/tempo -> $ip)"
}

# obs_install_agent [mesh-profili]: agent'ı kurar/günceller (mesh etiketi dış etikete yazılır)
obs_install_agent() {
  local mesh=${1:-$(current_mesh)}
  log "Gözlem ($BENCH_CLUSTER): Prometheus agent (mesh=$mesh)"
  obs_bridge_bench
  hb upgrade --install prom-agent prometheus-community/prometheus --version "$PROMETHEUS_CHART_VERSION" \
    -n observability -f "$MEVAL_ROOT/observability/prometheus-agent.yaml" \
    --set-string "server.global.external_labels.mesh=$mesh" --wait --timeout 5m >/dev/null
  ok "prom-agent (external_labels: cluster=$BENCH_CLUSTER, mesh=$mesh)"
}

obs_verify() {
  local n
  log "Gözlem doğrulama"
  wait_for 60 "Prometheus API" bash -c "prom_curl() { curl -sk --max-time 5 --resolve prometheus.localtest.me:9443:127.0.0.1 \"\$@\"; }; prom_curl $PROM_URL/-/ready | grep -qi ready" \
    && ok "Prometheus hazır ($PROM_URL)"
  wait_for 90 "bench cluster metrikleri mgmt'ye ulaşıyor" \
    bash -c "[ \"\$(curl -sk --resolve prometheus.localtest.me:9443:127.0.0.1 '$PROM_URL/api/v1/query' --data-urlencode 'query=count(up{cluster=\"$BENCH_CLUSTER\"})' | jq -r '.data.result[0].value[1] // 0')\" -gt 0 ]"
  n=$(prom_scalar "count(up{cluster=\"$BENCH_CLUSTER\"} == 1)")
  ok "bench cluster'ından $n hedef toplanıyor (remote-write çalışıyor)"
  n=$(prom_scalar "count(container_cpu_usage_seconds_total{cluster=\"$BENCH_CLUSTER\",container!=\"\"})")
  [ "$n" != null ] && ok "cAdvisor konteyner metrikleri: $n seri" || { fail "cAdvisor metrikleri yok"; return 1; }
  n=$(prom_scalar "count(kube_pod_info{cluster=\"$BENCH_CLUSTER\"})")
  [ "$n" != null ] && ok "kube-state-metrics: $n pod" || { fail "kube-state-metrics yok"; return 1; }
  curl -sk --max-time 5 --resolve grafana.localtest.me:9443:127.0.0.1 https://grafana.localtest.me:9443/api/health | grep -q '"database": *"ok"' \
    && ok "Grafana hazır (https://grafana.localtest.me:9443)" || { fail "Grafana cevap vermiyor"; return 1; }
  curl -sk --max-time 5 --resolve grafana.localtest.me:9443:127.0.0.1 -u admin:mesh-eval \
    "https://grafana.localtest.me:9443/api/datasources/uid/tempo/health" | grep -qi '"status": *"OK"' \
    && ok "Grafana -> Tempo datasource" || warn "Tempo datasource sağlık kontrolü geçmedi (trace yoksa normal olabilir)"
}
