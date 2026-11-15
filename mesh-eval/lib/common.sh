# mesh-eval ortak fonksiyonları (bin/meval ve tests/*/run.sh tarafından source edilir)
set -euo pipefail

MEVAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_ROOT="$(cd "$MEVAL_ROOT/.." && pwd)"
source "$LAB_ROOT/config.env"
source "$MEVAL_ROOT/config.env"
[ -f "$MEVAL_ROOT/config.local.env" ] && source "$MEVAL_ROOT/config.local.env"

TOOLS="$MEVAL_ROOT/.tools"
RESULTS_DIR="${MEVAL_RESULTS_DIR:-$MEVAL_ROOT/results}"
STATE_DIR="$MEVAL_ROOT/.state"
mkdir -p "$TOOLS" "$RESULTS_DIR" "$STATE_DIR"
export PATH="$TOOLS/bin:$PATH"

MESH_PROFILES=(none istio-ambient istio-ambient-l7 istio-sidecar linkerd)

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*" >&2; }
ok()   { printf '  \033[32m[ok]\033[0m %s\n' "$*" >&2; }
warn() { printf '  \033[33m[!]\033[0m %s\n' "$*" >&2; }
fail() { printf '  \033[31m[x]\033[0m %s\n' "$*" >&2; }
die()  { fail "$*"; exit 1; }

# kb: bench cluster'ına kubectl; km: mgmt cluster'ına kubectl
kb() { kubectl --context "kind-$BENCH_CLUSTER" "$@"; }
km() { kubectl --context kind-mgmt "$@"; }
hb() { helm --kube-context "kind-$BENCH_CLUSTER" "$@"; }
hm() { helm --kube-context kind-mgmt "$@"; }

node_ip_of() { # node_ip_of <node-container> <network>
  docker inspect -f "{{with index .NetworkSettings.Networks \"$2\"}}{{.IPAddress}}{{end}}" "$1"
}

retry() { # retry <deneme> <bekleme-sn> <komut...>
  local n=$1 s=$2 i; shift 2
  for ((i = 1; i <= n; i++)); do
    "$@" && return 0
    sleep "$s"
  done
  return 1
}

# wait_for <sn> <açıklama> <komut...>: komut başarılı olana kadar bekler
wait_for() {
  local t=$1 d=$2 i; shift 2
  for ((i = 0; i < t; i++)); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  fail "zaman aşımı ($t sn): $d"; return 1
}

# --- Aktif mesh profili -----------------------------------------------------
current_mesh() { cat "$STATE_DIR/mesh" 2>/dev/null || echo none; }
set_current_mesh() { echo "$1" > "$STATE_DIR/mesh"; }
mesh_family() { # none | istio | linkerd
  case $1 in istio-*) echo istio ;; linkerd) echo linkerd ;; *) echo none ;; esac
}

# --- Prometheus (mgmt) ------------------------------------------------------
PROM_URL="${PROM_URL:-https://prometheus.localtest.me:9443}"
prom_curl() { curl -sk --max-time 30 --resolve prometheus.localtest.me:9443:127.0.0.1 "$@"; }
# prom_query <promql> [zaman(unix)] -> JSON
prom_query() {
  if [ -n "${2:-}" ]; then
    prom_curl "$PROM_URL/api/v1/query" --data-urlencode "query=$1" --data-urlencode "time=$2"
  else
    prom_curl "$PROM_URL/api/v1/query" --data-urlencode "query=$1"
  fi
}
# prom_range <promql> <başlangıç> <bitiş> <adım-sn> -> JSON
prom_range() {
  prom_curl "$PROM_URL/api/v1/query_range" --data-urlencode "query=$1" \
    --data-urlencode "start=$2" --data-urlencode "end=$3" --data-urlencode "step=$4"
}
# prom_scalar <promql> [zaman]: tek değer (yoksa "null")
prom_scalar() {
  prom_query "$@" | jq -r '(.data.result[0].value[1] // "null")'
}

# --- Sürüm envanteri (meta.json'a yazılır) ---------------------------------
versions_json() {
  jq -n \
    --arg istio "$ISTIO_VERSION" --arg linkerd "$LINKERD_VERSION" \
    --arg k6 "$K6_IMAGE" --arg app "$FAKE_SERVICE_IMAGE" --arg gw "$GATEWAY_API_VERSION" \
    --arg k8s "$(kb version -o json 2>/dev/null | jq -r .serverVersion.gitVersion)" \
    --arg kind "$(kind version 2>/dev/null | awk '{print $2}')" \
    --arg ingress "$INGRESS_NGINX_CHART_VERSION" \
    '{istio:$istio, linkerd:$linkerd, k6:$k6, app:$app, gateway_api:$gw, kubernetes:$k8s, kind:$kind, ingress_nginx_chart:$ingress}'
}
