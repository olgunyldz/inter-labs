# O01 — Gözlemlenebilirlik
SVCS=(gateway order inventory payment pricing catalog fraud ledger)
gf() { curl -sk --max-time 20 --resolve grafana.localtest.me:9443:127.0.0.1 -u admin:mesh-eval "https://grafana.localtest.me:9443/api/datasources/proxy/uid/tempo$1"; }
S=$(k6_run o01 load.js 60 PHASES="100:60s" GAP=0)
T1=$(( $(jq -r .setup_data.t0 "$S" | cut -d. -f1) + 60 )); prom_settle 20
l7=0; l4=0
for s in "${SVCS[@]}"; do
  case $MESH in
    istio-sidecar) q7="sum(istio_requests_total{$C,reporter=\"destination\",destination_workload=\"$s\"})"; q4="sum(istio_tcp_connections_opened_total{$C,destination_workload=\"$s\"})" ;;
    istio-ambient) q7="sum(istio_requests_total{$C,destination_workload=\"$s\"})"; q4="sum(istio_tcp_connections_opened_total{$C,destination_workload=\"$s\"})" ;;
    istio-ambient-l7) q7="sum(istio_requests_total{$C,reporter=\"waypoint\",destination_workload=\"$s\"})"; q4="sum(istio_tcp_connections_opened_total{$C,destination_workload=\"$s\"})" ;;
    linkerd) q7="sum(response_total{$C,namespace=\"$SHOP_NS\",direction=\"inbound\",app=\"$s\"})"; q4="sum(tcp_open_total{$C,namespace=\"$SHOP_NS\",direction=\"inbound\",app=\"$s\"})" ;;
  esac
  [ "$(prom_scalar "$q7" "$T1")" != null ] && l7=$((l7 + 1))
  [ "$(prom_scalar "$q4" "$T1")" != null ] && l4=$((l4 + 1))
done
metric services_l7_metrics "$l7" "/8" "istek/başarı/gecikme metriği olan servis"
metric services_l4_metrics "$l4" "/8" "TCP (bağlantı/bayt) metriği olan servis"
check_ge "tüm servisler için en az L4 metrik" "$(( l7 > l4 ? l7 : l4 ))" 8
[ "$l7" -lt 8 ] && finding "$MESH: $l7/8 servis için L7 (istek, başarı oranı, gecikme) metriği var; diğerleri için yalnızca TCP metrikleri. Altın metrikler için L7 proxy (waypoint) gerekir."
# Doğruluk: gateway gelen isteklerinde mesh p99 / k6 p99
case $MESH in
  istio-sidecar) qa="histogram_quantile(0.99, sum by (le) (rate(istio_request_duration_milliseconds_bucket{$C,reporter=\"destination\",destination_workload=\"gateway\"}[60s])))" ;;
  istio-ambient-l7) qa="histogram_quantile(0.99, sum by (le) (rate(istio_request_duration_milliseconds_bucket{$C,reporter=\"waypoint\",destination_workload=\"gateway\"}[60s])))" ;;
  linkerd) qa="histogram_quantile(0.99, sum by (le) (rate(response_latency_ms_bucket{$C,namespace=\"$SHOP_NS\",direction=\"inbound\",app=\"gateway\"}[60s])))" ;;
  *) qa="" ;;
esac
if [ -n "$qa" ]; then
  mp=$(prom_scalar "$qa" "$T1"); kp=$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")
  metric mesh_p99_ms "$mp" ms "mesh'in gateway için ölçtüğü p99"; metric k6_p99_ms "$kp" ms
  [ "$mp" != null ] && metric latency_accuracy_ratio "$(awk -v a="$mp" -v b="$kp" 'BEGIN{printf "%.2f", a/b}')" kat "mesh p99 / k6 p99 (histogram kova çözünürlüğü dahil)"
fi

log "Dağıtık izleme (geçici olarak açılıyor)"
on_exit kb -n "$SHOP_NS" set env deploy -l mesh-eval/part-of=shop TRACING_ZIPKIN=
on_exit kb -n "$SHOP_NS" delete telemetry o01 --ignore-not-found
case $MESH in
  istio-*) kb apply -f policies/istio-telemetry.yaml >/dev/null ;;
  linkerd)
    on_exit "lk jaeger uninstall | kb delete -f - --ignore-not-found"
    if lk jaeger install --set collector.enabled=false --set jaeger.enabled=false \
         --set webhook.collectorSvcAddr=tempo.observability.svc.cluster.local:4317 \
         --set webhook.collectorTraceProtocol=opentelemetry --set webhook.collectorSvcAccount=default 2> "$(raw jaeger-install.err)" \
         | kb apply -f - >/dev/null 2>>"$(raw jaeger-install.err)"; then
      kb -n linkerd-jaeger rollout status deploy/jaeger-injector --timeout=120s >/dev/null || true
      kb annotate ns "$SHOP_NS" config.linkerd.io/trace-collector- >/dev/null 2>&1 || true
      kb label ns "$SHOP_NS" linkerd.io/extension- >/dev/null 2>&1 || true
    else
      finding "linkerd-jaeger eklentisi kurulamadı: $(head -c 200 "$(raw jaeger-install.err)")"
    fi ;;
esac
# Uygulama B3 başlıklarını taşısın + kendi span'larını yollasın (zincir tek trace olsun)
for s in "${SVCS[@]}"; do kb -n "$SHOP_NS" set env "deploy/$s" TRACING_ZIPKIN=http://tempo.observability.svc:9411 >/dev/null; done
for s in "${SVCS[@]}"; do kb -n "$SHOP_NS" rollout status "deploy/$s" --timeout=180s >/dev/null; done
sleep 10
for i in $(seq 30); do http_code probe-gateway "$SHOP_NS" "http://gateway.$SHOP_NS.svc:9090/" >/dev/null; done
sleep 25
gf "/api/search?tags=service.name%3Dgateway&limit=20&start=$(( $(date +%s) - 300 ))&end=$(date +%s)" > "$(raw tempo-search.json)"
tid=$(jq -r '[.traces[]? | select(.rootServiceName != null)] | max_by(.spanSet.matched // 0 | tostring) | .traceID // empty' "$(raw tempo-search.json)" 2>/dev/null)
[ -z "$tid" ] && tid=$(jq -r '.traces[0].traceID // empty' "$(raw tempo-search.json)")
if [ -n "$tid" ]; then
  gf "/api/traces/$tid" > "$(raw trace.json)"
  spans=$(jq '[.. | objects | select(has("spanId") or has("spanID"))] | length' "$(raw trace.json)")
  svcs=$(jq -r '[.. | objects | select(has("key") and .key=="service.name") | .value.stringValue] | unique | join(",")' "$(raw trace.json)")
  nsvc=$(tr ',' '\n' <<<"$svcs" | grep -c . || true)
  mesh_sp=$(tr ',' '\n' <<<"$svcs" | grep -cE '\.shop$|\.shop\.|waypoint|linkerd|proxy' || true)
  metric trace.spans "$spans" span; metric trace.services "$nsvc" adet "trace'teki servis adı sayısı"
  metric trace.mesh_spans "$mesh_sp" adet "mesh proxy'lerinin ürettiği servis adları"
  echo "$svcs" > "$(raw trace-services.txt)"
  check "trace Tempo'da bulundu" var var
  [ "$mesh_sp" = 0 ] && finding "$MESH: trace yalnızca uygulamanın ürettiği span'lardan oluştu; mesh proxy'leri span üretmedi (servisler: $svcs)."
else
  check "trace Tempo'da bulundu" var yok
fi

log "Erişim logu"
al=0
case $MESH in
  istio-sidecar) kb -n "$SHOP_NS" logs deploy/order -c istio-proxy --since=60s 2>/dev/null | grep -q '"GET / ' && al=1 ;;
  istio-ambient) kb -n istio-system logs -l app=ztunnel --since=60s 2>/dev/null | grep -q 'shop/sa/order\|order' && al=1 ;;
  istio-ambient-l7) kb -n "$SHOP_NS" logs deploy/waypoint --since=60s 2>/dev/null | grep -q '"GET / ' && al=1 ;;
  linkerd)
    kb -n "$SHOP_NS" annotate deploy order config.alpha.linkerd.io/access-log=json --overwrite >/dev/null 2>&1 || true
    kb -n "$SHOP_NS" patch deploy order --type merge -p '{"spec":{"template":{"metadata":{"annotations":{"config.alpha.linkerd.io/access-log":"json"}}}}}' >/dev/null
    on_exit "kb -n $SHOP_NS patch deploy order --type json -p '[{\"op\":\"remove\",\"path\":\"/spec/template/metadata/annotations/config.alpha.linkerd.io~1access-log\"}]'"
    kb -n "$SHOP_NS" rollout status deploy/order --timeout=120s >/dev/null; sleep 5
    for i in $(seq 10); do http_code probe-gateway "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/" >/dev/null; done
    kb -n "$SHOP_NS" logs deploy/order -c linkerd-proxy --since=60s 2>/dev/null | grep -q '"request.uri\|"uri\|GET' && al=1 ;;
esac
metric access_log "$al" bool "proxy erişim logu üretebildi"
