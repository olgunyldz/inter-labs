# Ortak fonksiyonlar (up.sh / verify.sh / down.sh tarafından source edilir)
set -euo pipefail

# Git Bash'te Windows exe'lerine (kubectl, helm, kind) C:/... formunda path ver
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && (pwd -W 2>/dev/null || pwd))"
source "$ROOT/config.env"

CLUSTERS=(mgmt data cluster-a cluster-b dmz-a dmz-b)
DMZ_CLUSTERS=(dmz-a dmz-b)

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m[ok]\033[0m %s\n' "$*"; }
fail() { printf '  \033[31m[x]\033[0m %s\n' "$*"; }

k() { local c=$1; shift; kubectl --context "kind-$c" "$@"; }

node_name() { echo "$1-control-plane"; }

# node_ip <cluster> <network>: node'un o network'teki IP'si (bağlı değilse boş)
node_ip() {
  docker inspect -f "{{with index .NetworkSettings.Networks \"$2\"}}{{.IPAddress}}{{end}}" "$(node_name "$1")"
}

primary_net() {
  case $1 in
    dmz-a|dmz-b) echo "$NET_DMZ" ;;
    cluster-a|cluster-b) echo "$NET_APP" ;;
    data) echo "$NET_DATA" ;;
    mgmt) echo "$NET_MGMT" ;;
  esac
}

zone_of() {
  case $1 in
    dmz-a|dmz-b) echo dmz ;;
    cluster-a|cluster-b) echo app ;;
    *) echo "$1" ;;
  esac
}

# retry <deneme> <komut...>: webhook henüz hazır değilken apply gibi işlemler için
retry() {
  local n=$1 i; shift
  for ((i = 1; i <= n; i++)); do
    "$@" && return 0
    echo "  ...tekrar deneniyor ($i/$n)"; sleep 5
  done
  return 1
}

# endpointslice <ns> <service> <port-adı> <port> <ip...>
# Selector'sız bir Service'i cluster dışındaki IP'lere yönlendirir
endpointslice() {
  local ns=$1 svc=$2 pname=$3 port=$4 ip; shift 4
  cat <<EOF
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: $svc-static
  namespace: $ns
  labels:
    kubernetes.io/service-name: $svc
    endpointslice.kubernetes.io/managed-by: inter-labs
addressType: IPv4
ports:
  - { name: $pname, port: $port, protocol: TCP }
endpoints:
EOF
  for ip in "$@"; do
    echo "  - { addresses: [\"$ip\"], conditions: { ready: true } }"
  done
}
