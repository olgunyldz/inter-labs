# R01 — Timeout / retry / outlier detection
FAM=$(mesh_family "$MESH"); D=$(profile_val 40 90)
on_exit kb -n "$SHOP_NS" set env deploy/pricing ERROR_RATE- ERROR_TYPE- ERROR_DELAY- ERROR_CODE-
on_exit kb -n "$SHOP_NS" delete deploy pricing-bad --ignore-not-found
on_exit kb -n "$SHOP_NS" delete virtualservice,destinationrule pricing --ignore-not-found
on_exit kb -n "$SHOP_NS" delete httproutes.gateway.networking.k8s.io pricing --ignore-not-found
on_exit kb -n "$SHOP_NS" annotate svc pricing balancer.linkerd.io/failure-accrual- balancer.linkerd.io/failure-accrual-consecutive-max-failures-
# pricing'e gelen istek sayısı (mesh metriği; none'da ölçülemez)
pricing_reqs() { # <zaman> <pencere-sn>
  case $MESH in
    istio-sidecar)    prom_scalar "sum(increase(istio_requests_total{$C,reporter=\"destination\",destination_workload=\"pricing\"}[$2s]))" "$1" ;;
    istio-ambient-l7) prom_scalar "sum(increase(istio_requests_total{$C,reporter=\"waypoint\",destination_workload=\"pricing\"}[$2s]))" "$1" ;;
    linkerd)          prom_scalar "sum(increase(request_total{$C,namespace=\"$SHOP_NS\",direction=\"inbound\",app=\"pricing\"}[$2s]))" "$1" ;;
    *) echo null ;;
  esac
}
run_load() { # run_load <ad> -> metrikler
  local S T0 reqs pr
  S=$(k6_run "$1" load.js "$D" PHASES="100:${D}s" GAP=0)
  T0=$(jq -r .setup_data.t0 "$S" | cut -d. -f1)
  metric "$1.p50_ms" "$(jq -r '.metrics.http_req_duration.values.med' "$S")" ms
  metric "$1.p99_ms" "$(jq -r '.metrics.http_req_duration.values["p(99)"]' "$S")" ms
  metric "$1.error_rate" "$(jq -r '.metrics.http_req_failed.values.rate' "$S")" oran
  reqs=$(jq -r '.metrics.http_reqs.values.count' "$S")
  prom_settle 20
  pr=$(pricing_reqs $((T0 + D)) "$D")
  [ "$pr" != null ] && metric "$1.amplification" "$(awk -v a="$pr" -v b="$reqs" 'BEGIN{printf "%.3f", a/b}')" kat "pricing'e gelen / gateway'e gelen istek"
}
supports_l7() { [ "$MESH" = istio-sidecar ] || [ "$MESH" = istio-ambient-l7 ] || [ "$MESH" = linkerd ]; }

log "A) yavaş bağımlılık: pricing isteklerinin %20'si 1 sn"
kb -n "$SHOP_NS" set env deploy/pricing ERROR_RATE=0.2 ERROR_TYPE=delay ERROR_DELAY=1s >/dev/null
kb -n "$SHOP_NS" rollout status deploy/pricing --timeout=120s >/dev/null; sleep 5
run_load A.none
if supports_l7; then
  case $FAM in istio) kb apply -f policies/istio.yaml >/dev/null ;; linkerd) kb apply -f policies/linkerd.yaml >/dev/null ;; esac
  sleep 10
  run_load A.policy
  check_le "A: politikayla p99 (ms)" "$(jq -s -r '.[] | select(.key=="A.policy.p99_ms") | .value' "$RUN_DIR/metrics.jsonl")" 1000
fi
kb -n "$SHOP_NS" delete virtualservice pricing --ignore-not-found >/dev/null 2>&1 || true
kb -n "$SHOP_NS" delete httproutes.gateway.networking.k8s.io pricing --ignore-not-found >/dev/null 2>&1 || true
kb -n "$SHOP_NS" set env deploy/pricing ERROR_RATE- ERROR_TYPE- ERROR_DELAY- >/dev/null
kb -n "$SHOP_NS" rollout status deploy/pricing --timeout=120s >/dev/null

log "B) hatalı replika: 2 sağlam + 1 sürekli 503"
kb -n "$SHOP_NS" get deploy pricing -o json | jq '
  .metadata = {name: "pricing-bad", namespace: .metadata.namespace} | .spec.replicas = 1
  | .spec.selector.matchLabels.version = "bad" | .spec.template.metadata.labels.version = "bad"
  | .spec.template.spec.containers[0].env += [{name:"ERROR_RATE",value:"1"},{name:"ERROR_CODE",value:"503"}]
  | del(.status)' | kb apply -f - >/dev/null
kb -n "$SHOP_NS" rollout status deploy/pricing-bad --timeout=120s >/dev/null; sleep 5
run_load B.none
b0=$(jq -s -r '.[] | select(.key=="B.none.error_rate") | .value' "$RUN_DIR/metrics.jsonl")
awk -v e="$b0" 'BEGIN{exit !(e > 0.45)}' && finding "$MESH: 3 replikadan 1'i sürekli hata verirken uçtan uca hata oranı %$(awk -v e="$b0" 'BEGIN{printf "%.0f", e*100}') (replika oranına göre beklenen ~%33). Hızlı hata dönen replika yük dengeleyici tarafından tercih ediliyor; outlier detection / failure accrual olmadan hatalı pod trafiği çeker."
if supports_l7; then
  case $FAM in
    istio) kb apply -f policies/istio-outlier.yaml >/dev/null ;;
    linkerd) kb -n "$SHOP_NS" annotate svc pricing balancer.linkerd.io/failure-accrual=consecutive balancer.linkerd.io/failure-accrual-consecutive-max-failures=3 --overwrite >/dev/null ;;
  esac
  sleep 10
  run_load B.policy
  b0=$(jq -s -r '.[] | select(.key=="B.none.error_rate") | .value' "$RUN_DIR/metrics.jsonl")
  b1=$(jq -s -r '.[] | select(.key=="B.policy.error_rate") | .value' "$RUN_DIR/metrics.jsonl")
  check_le "B: outlier detection ile hata oranı (politikasızın yarısı)" "$b1" "$(awk -v a="$b0" 'BEGIN{print a/2}')"
else
  na "timeout/retry/outlier detection için L7 proxy gerekir ($MESH); politikasız ölçümler kaydedildi"
fi
