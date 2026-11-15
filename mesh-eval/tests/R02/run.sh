# R02 — Hata enjeksiyonu
D=$(profile_val 45 120)
on_exit kb -n "$SHOP_NS" delete virtualservice catalog-fault --ignore-not-found
on_exit kb -n "$SHOP_NS" delete httproutes.gateway.networking.k8s.io catalog-fault --ignore-not-found
on_exit kb -n "$SHOP_NS" delete deploy,svc catalog-err catalog-slow --ignore-not-found
case $MESH in
  istio-ambient) na "fault injection L7 proxy gerektirir; ambient L4 (waypoint'siz) profilde yok" ;;
  istio-*) kb apply -f policies/istio.yaml >/dev/null; metric method 0 - "Istio VirtualService fault (yerleşik)" ;;
  linkerd)
    finding "Linkerd'de yerleşik hata enjeksiyonu yok; hatalı/yavaş backend'ler kurulup HTTPRoute ağırlığıyla yönlendirilerek yapıldı (ek dağıtım ve bakım gerektirir, gecikme/hata ayrı ayrı oranlanamaz)."
    for v in err:"ERROR_RATE=1 ERROR_CODE=503" slow:"TIMING_50_PERCENTILE=200ms TIMING_90_PERCENTILE=200ms TIMING_99_PERCENTILE=200ms"; do
      n=catalog-${v%%:*}
      kb -n "$SHOP_NS" create deploy "$n" --image="$FAKE_SERVICE_IMAGE" --dry-run=client -o json | jq --arg n "$n" '
        .spec.template.spec.nodeSelector={"mesh-eval.role":"app"}
        | .spec.template.spec.tolerations=[{key:"mesh-eval.role",operator:"Equal",value:"app",effect:"NoSchedule"}]
        | .spec.template.spec.serviceAccountName="catalog"' | kb apply -f - >/dev/null
      kb -n "$SHOP_NS" set env "deploy/$n" NAME="$n" ${v#*:} >/dev/null
      kb -n "$SHOP_NS" create service clusterip "$n" --tcp=9090:9090 --dry-run=client -o yaml | kb apply -f - >/dev/null
      kb -n "$SHOP_NS" rollout status "deploy/$n" --timeout=120s >/dev/null
    done
    kb apply -f policies/linkerd.yaml >/dev/null
    metric method 1 - "HTTPRoute ağırlıklı yönlendirme + hatalı backend" ;;
esac
sleep 10
S=$(k6_run fault load.js "$D" PHASES="100:${D}s" GAP=0)
err=$(jq -r '.metrics.http_req_failed.values.rate' "$S")
metric observed_error_rate "$err" oran "gateway'de gözlenen hata oranı (hedef 0.10)"
metric p50_ms "$(jq -r '.metrics.http_req_duration.values.med' "$S")" ms
metric p90_ms "$(jq -r '.metrics.http_req_duration.values["p(90)"]' "$S")" ms
p95=$(jq -r '.metrics.http_req_duration.values["p(95)"]' "$S"); metric p95_ms "$p95" ms
check_ge "gözlenen hata oranı >= 0.07" "$err" 0.07
check_le "gözlenen hata oranı <= 0.13" "$err" 0.13
check_ge "gecikme enjeksiyonu görünüyor (p95 ms)" "$p95" 200
