#!/usr/bin/env bash
# Tüm demo ortamını kurar. Idempotent: yarıda kalırsa tekrar çalıştırılabilir.
source "$(dirname "$0")/lib.sh"

preflight() {
  log "Ön kontroller"
  local t
  for t in docker kind kubectl helm openssl curl; do
    command -v "$t" >/dev/null || { fail "$t bulunamadı"; exit 1; }
  done
  docker info >/dev/null 2>&1 || { fail "Docker çalışmıyor"; exit 1; }
  # 6 kind cluster'ı için inotify limitleri (Docker VM'i yeniden başlarsa sıfırlanır)
  docker run --rm --privileged --pid=host alpine:3.20 nsenter -t 1 -m -u -n -i \
    sysctl -w fs.inotify.max_user_instances=1024 fs.inotify.max_user_watches=1048576 >/dev/null
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx --force-update >/dev/null
  helm repo update ingress-nginx >/dev/null
  ok "araçlar ve helm repoları hazır"
}

create_networks() {
  log "Zone network'leri"
  local spec name subnet
  for spec in "$NET_EDGE=$NET_EDGE_SUBNET" "$NET_DMZ=$NET_DMZ_SUBNET" "$NET_APP=$NET_APP_SUBNET" \
              "$NET_DATA=$NET_DATA_SUBNET" "$NET_MGMT=$NET_MGMT_SUBNET"; do
    name=${spec%%=*} subnet=${spec#*=}
    if ! docker network inspect "$name" >/dev/null 2>&1; then
      docker network create --driver bridge --subnet "$subnet" "$name" >/dev/null
    fi
    ok "$name ($subnet)"
  done
}

create_cluster() {
  local c=$1
  if kind get clusters 2>/dev/null | grep -qx "$c"; then
    ok "$c zaten var"; return
  fi
  log "Cluster: $c ($(primary_net "$c"))"
  KIND_EXPERIMENTAL_DOCKER_NETWORK="$(primary_net "$c")" \
    kind create cluster --config "$ROOT/clusters/$c.yaml" --wait 180s
}

# attach <cluster> <network>: node'u ek bir zone network'üne bağlar
attach() {
  if [ -z "$(node_ip "$1" "$2")" ]; then
    docker network connect "$2" "$(node_name "$1")"
  fi
  ok "$1 -> $2 ($(node_ip "$1" "$2"))"
}

attach_networks() {
  log "Zone'lar arası bağlantılar"
  attach dmz-a "$NET_APP"
  attach dmz-b "$NET_APP"
  attach cluster-a "$NET_DATA"
  attach cluster-b "$NET_DATA"
  attach mgmt "$NET_DMZ"
  attach mgmt "$NET_APP"
  attach mgmt "$NET_DATA"
}

install_ingress() {
  local c=$1 extra=()
  log "ingress-nginx: $c (zone: $(zone_of "$c"))"
  # DMZ cevaplarına hangi cluster'dan geçtiğini ekle (edge LB dağılımını görmek için)
  [ "$(zone_of "$c")" = dmz ] && extra=(--set-string "controller.addHeaders.X-Dmz=$c")
  helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
    --version "$INGRESS_NGINX_CHART_VERSION" \
    --kube-context "kind-$c" -n ingress-nginx --create-namespace \
    -f "$ROOT/platform/ingress-nginx/values-common.yaml" \
    -f "$ROOT/platform/ingress-nginx/values-$(zone_of "$c").yaml" \
    "${extra[@]}" --wait --timeout 6m
}

deploy_data() {
  log "Data: Postgres + Redis"
  retry 6 k data apply -k "$ROOT/workloads/data"
  k data -n data rollout status statefulset/postgres --timeout=300s
  k data -n data rollout status deployment/redis --timeout=180s
}

deploy_apps() {
  local data_ip c
  data_ip=$(node_ip data "$NET_DATA")
  for c in cluster-a cluster-b; do
    log "App: $c (data ingress: $data_ip)"
    retry 6 k "$c" apply -k "$ROOT/workloads/app/overlays/$c"
    endpointslice demo postgres postgres 5432 "$data_ip" | k "$c" apply -f -
    endpointslice demo redis redis 6379 "$data_ip" | k "$c" apply -f -
    k "$c" -n demo rollout status deployment/demo-app --timeout=180s
  done
}

ensure_cert() {
  local dir="$ROOT/.certs"
  [ -f "$dir/tls.crt" ] && return
  mkdir -p "$dir"
  MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 825 \
    -subj "/CN=*.localtest.me" \
    -addext "subjectAltName=DNS:*.localtest.me,DNS:localtest.me" \
    -keyout "$dir/tls.key" -out "$dir/tls.crt" 2>/dev/null
}

# tls_secret <cluster> <namespace> <isim>
tls_secret() {
  k "$1" -n "$2" create secret tls "$3" \
    --cert "$ROOT/.certs/tls.crt" --key "$ROOT/.certs/tls.key" \
    --dry-run=client -o yaml | k "$1" apply -f -
}

deploy_dmz() {
  local a_ip b_ip c
  a_ip=$(node_ip cluster-a "$NET_APP")
  b_ip=$(node_ip cluster-b "$NET_APP")
  ensure_cert
  for c in "${DMZ_CLUSTERS[@]}"; do
    log "DMZ: $c -> cluster-a ($a_ip), cluster-b ($b_ip)"
    retry 6 k "$c" apply -k "$ROOT/workloads/dmz"
    tls_secret "$c" edge edge-tls
    endpointslice edge app-pool http 80 "$a_ip" "$b_ip" | k "$c" apply -f -
    endpointslice edge cluster-a http 80 "$a_ip" | k "$c" apply -f -
    endpointslice edge cluster-b http 80 "$b_ip" | k "$c" apply -f -
  done
}

# Edge LB: HAProxy container'ı; host 80/443 -> dmz-a / dmz-b ingress (L4 + PROXY protocol)
deploy_edge() {
  local a_ip b_ip cfg="$ROOT/.edge/haproxy.cfg"
  a_ip=$(node_ip dmz-a "$NET_DMZ")
  b_ip=$(node_ip dmz-b "$NET_DMZ")
  log "Edge LB: $EDGE_LB -> dmz-a ($a_ip), dmz-b ($b_ip)"
  mkdir -p "$ROOT/.edge"
  sed -e "s/__DMZ_A__/$a_ip/g" -e "s/__DMZ_B__/$b_ip/g" "$ROOT/edge/haproxy.cfg.tpl" > "$cfg"
  docker rm -f "$EDGE_LB" >/dev/null 2>&1 || true
  MSYS_NO_PATHCONV=1 docker run -d --name "$EDGE_LB" --restart unless-stopped \
    --network "$NET_EDGE" --sysctl net.ipv4.ip_unprivileged_port_start=0 \
    -p 127.0.0.1:80:80 -p 127.0.0.1:443:443 -p 127.0.0.1:9404:8404 \
    -v "$cfg:/usr/local/etc/haproxy/haproxy.cfg:ro" "$HAPROXY_IMAGE" >/dev/null
  docker network connect "$NET_DMZ" "$EDGE_LB"
  ok "$EDGE_LB çalışıyor ($NET_EDGE + $NET_DMZ)"
}

summary() {
  log "Hazır"
  cat <<EOF
  Uygulama (edge -> DMZ A/B -> A/B): https://app.localtest.me
  Edge LB istatistikleri          : http://127.0.0.1:9404
  Sadece cluster-a / cluster-b    : https://app-a.localtest.me  /  https://app-b.localtest.me
  kubectl context'leri            : $(printf 'kind-%s ' "${CLUSTERS[@]}")
  Doğrulama                       : bash scripts/verify.sh
EOF
}

preflight
create_networks
for c in "${CLUSTERS[@]}"; do create_cluster "$c"; done
attach_networks
for c in "${CLUSTERS[@]}"; do install_ingress "$c"; done
deploy_data
deploy_apps
deploy_dmz
deploy_edge
summary
