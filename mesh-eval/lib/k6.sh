# k6 yük üretici: loadgen node'unda, aktif mesh'e dahil bir pod olarak çalışır.
# Script'ler tests/k6/*.js -> ConfigMap. Özet JSON pod logundan (işaretçiler arası) çıkarılır.
# Ayrıca metrikler canlı olarak mgmt Prometheus'a yazılır (Grafana'da izlenebilir).

k6_sync_scripts() {
  kb -n "$LOADGEN_NS" create configmap k6-scripts --from-file="$TESTS_DIR/k6/" \
    --dry-run=client -o yaml | kb apply -f - >/dev/null
}

# k6_start <ad> <script.js> [KEY=VAL...] -> pod adı (arka planda çalışır)
k6_start() {
  local name=$1 script=$2 pod env_json='[]' kv; shift 2
  pod="k6-$(echo "${TEST_ID:-x}-$name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9\n' '-' | cut -c1-40)-$RANDOM"
  for kv in "$@" "MESH=${MESH:-$(current_mesh)}" "TARGET=${K6_TARGET:-http://gateway.$SHOP_NS.svc:9090/}"; do
    env_json=$(jq -c --arg k "${kv%%=*}" --arg v "${kv#*=}" '. + [{name:$k, value:$v}]' <<<"$env_json")
  done
  k6_sync_scripts
  kb -n "$LOADGEN_NS" delete pod "$pod" --ignore-not-found >/dev/null 2>&1
  jq -n --arg pod "$pod" --arg ns "$LOADGEN_NS" --arg img "$K6_IMAGE" --arg script "$script" \
    --arg run "$(basename "${RUN_DIR:-adhoc}")" --arg mesh "${MESH:-$(current_mesh)}" --arg test "${TEST_ID:-adhoc}" \
    --argjson env "$env_json" '{
    apiVersion: "v1", kind: "Pod",
    metadata: {name: $pod, namespace: $ns, labels: {app: "k6", "mesh-eval/run": ($run|.[0:63])}},
    spec: {
      serviceAccountName: "k6", restartPolicy: "Never",
      nodeSelector: {"mesh-eval.role": "loadgen"},
      tolerations: [{key: "mesh-eval.role", operator: "Equal", value: "loadgen", effect: "NoSchedule"}],
      containers: [{
        name: "k6", image: $img,
        args: ["run", "--quiet", "--no-color", "--out", "experimental-prometheus-rw",
               "--tag", ("mesh=" + $mesh), "--tag", ("test=" + $test), "--tag", ("run=" + $run),
               ("/scripts/" + $script)],
        env: ($env + [
          {name: "K6_PROMETHEUS_RW_SERVER_URL", value: "http://prometheus.observability.svc:9090/api/v1/write"},
          {name: "K6_PROMETHEUS_RW_TREND_STATS", value: "p(50),p(95),p(99),max"},
          {name: "K6_PROMETHEUS_RW_PUSH_INTERVAL", value: "5s"}]),
        volumeMounts: [{name: "scripts", mountPath: "/scripts"}]
      }],
      volumes: [{name: "scripts", configMap: {name: "k6-scripts"}}]
    }}' | kb apply -f - >/dev/null
  echo "$pod"
}

# k6_wait <pod> <ad> <zaman-aşımı-sn>: bitmesini bekler, özeti raw/<ad>-summary.json'a yazar
k6_wait() {
  local pod=$1 name=$2 timeout=$3 i state
  for ((i = 0; i < timeout; i += 3)); do
    state=$(kb -n "$LOADGEN_NS" get pod "$pod" -o json 2>/dev/null \
      | jq -r '.status.containerStatuses[]? | select(.name == "k6") | .state | keys[0]')
    [ "$state" = terminated ] && break
    sleep 3
  done
  kb -n "$LOADGEN_NS" logs "$pod" -c k6 > "$(raw "$name-k6.log")" 2>&1 || true
  if [ "$state" != terminated ]; then
    kb -n "$LOADGEN_NS" describe pod "$pod" > "$(raw "$name-k6-pod.txt")" 2>&1 || true
    kb -n "$LOADGEN_NS" delete pod "$pod" --wait=false >/dev/null 2>&1 || true
    die "k6 zaman aşımı ($timeout sn): $pod (ayrıntı: raw/$name-k6-pod.txt)"
  fi
  kb -n "$LOADGEN_NS" delete pod "$pod" --wait=false >/dev/null 2>&1 || true
  sed -n '/==K6SUMMARY==/,/==END==/p' "$(raw "$name-k6.log")" | sed '1d;$d' > "$(raw "$name-summary.json")"
  jq -e . "$(raw "$name-summary.json")" >/dev/null 2>&1 || die "k6 özeti okunamadı: $(raw "$name-k6.log")"
  echo "$(raw "$name-summary.json")"
}

# k6_run <ad> <script.js> <tahmini-süre-sn> [KEY=VAL...] -> özet dosyası
k6_run() {
  local name=$1 script=$2 dur=$3 pod; shift 3
  pod=$(k6_start "$name" "$script" "$@")
  k6_wait "$pod" "$name" $((dur + 180))
}

# k6 özetinden alt metrik: k6_val <özet> <metrik> <istatistik> [etiket-filtresi]
#   ör. k6_val s.json http_req_duration "p(99)" "stage:3"
k6_val() {
  local key=$2
  [ -n "${4:-}" ] && key="$2{$4}"
  jq -r --arg k "$key" --arg s "$3" '.metrics[$k].values[$s] // "null"' "$1"
}
