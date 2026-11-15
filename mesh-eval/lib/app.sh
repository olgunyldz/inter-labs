# Test ortamı: node yerleşimi, CPU sabitleme, shop servis zinciri, DMZ girişi

# Node'ları ayrı CPU çekirdeklerine sabitler ve worker'ları ayırır (taint)
bench_nodes() {
  local n
  log "Node yerleşimi ve CPU sabitleme"
  for n in $(kind get nodes --name "$BENCH_CLUSTER"); do
    case $n in
      *-worker)        docker update --cpuset-cpus "$CPUSET_APP" "$n" >/dev/null; ok "$n -> CPU $CPUSET_APP (servisler)" ;;
      *-worker2)       docker update --cpuset-cpus "$CPUSET_LOADGEN" "$n" >/dev/null; ok "$n -> CPU $CPUSET_LOADGEN (k6)" ;;
      *-control-plane) docker update --cpuset-cpus "$CPUSET_CONTROL" "$n" >/dev/null; ok "$n -> CPU $CPUSET_CONTROL (kontrol düzlemi)" ;;
    esac
  done
  for n in $(docker ps --format '{{.Names}}' | grep -E -- '-control-plane$|^edge-lb$' | grep -v "^$BENCH_CLUSTER-"); do
    docker update --cpuset-cpus "$CPUSET_OTHER" "$n" >/dev/null
  done
  ok "diğer cluster'lar + edge LB -> CPU $CPUSET_OTHER"
  # Worker'lara yalnızca test bileşenleri yerleşir; geri kalan her şey control-plane'de
  kb taint nodes "$BENCH_CLUSTER-worker" mesh-eval.role=app:NoSchedule --overwrite >/dev/null
  kb taint nodes "$BENCH_CLUSTER-worker2" mesh-eval.role=loadgen:NoSchedule --overwrite >/dev/null
  kb taint nodes "$BENCH_CLUSTER-control-plane" node-role.kubernetes.io/control-plane:NoSchedule- >/dev/null 2>&1 || true
  # taint'ten önce worker'lara düşmüş lab pod'larını control-plane'e taşı
  if kb -n demo get pods -o wide --no-headers 2>/dev/null | grep -q -- '-worker'; then
    kb -n demo rollout restart deployment/demo-app >/dev/null
    kb -n demo rollout status deployment/demo-app --timeout=120s >/dev/null
  fi
  ok "worker taint'leri: app / loadgen"
}

app_deploy() {
  local data_ip
  log "Servis zinciri (shop) + istemciler"
  bash "$MEVAL_ROOT/apps/shop/render.sh" | kb apply -f - >/dev/null
  data_ip=$(node_ip_of data-control-plane "$NET_DATA")
  kb apply -f - >/dev/null <<YAML
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: postgres-data
  namespace: $SHOP_NS
  labels: { kubernetes.io/service-name: postgres, endpointslice.kubernetes.io/managed-by: mesh-eval }
addressType: IPv4
ports: [{ name: tcp-postgres, port: 5432, protocol: TCP }]
endpoints: [{ addresses: ["$data_ip"], conditions: { ready: true } }]
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: redis-data
  namespace: $SHOP_NS
  labels: { kubernetes.io/service-name: redis, endpointslice.kubernetes.io/managed-by: mesh-eval }
addressType: IPv4
ports: [{ name: tcp-redis, port: 6379, protocol: TCP }]
endpoints: [{ addresses: ["$data_ip"], conditions: { ready: true } }]
YAML
  ok "manifest'ler uygulandı (data: $data_ip)"
  egress_targets
  app_wait
  dmz_deploy
}

app_wait() {
  local d
  for d in $(kb -n "$SHOP_NS" get deploy -o name); do
    kb -n "$SHOP_NS" rollout status "$d" --timeout=240s >/dev/null || die "$d hazır olmadı"
  done
  kb -n "$OUTSIDE_NS" rollout status deploy/probe-outside --timeout=120s >/dev/null
  ok "shop: $(kb -n "$SHOP_NS" get pods --no-headers | grep -c Running) pod çalışıyor"
}

# DMZ: shop.localtest.me -> cluster-a ingress (lab'daki app-a ile aynı yol)
dmz_deploy() {
  local c
  for c in dmz-a dmz-b; do
    kubectl --context "kind-$c" apply -f - >/dev/null <<'YAML'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop
  namespace: edge
  annotations:
    nginx.ingress.kubernetes.io/upstream-vhost: shop.localtest.me
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "2"
spec:
  ingressClassName: nginx
  tls: [{ hosts: [shop.localtest.me], secretName: edge-tls }]
  rules:
    - host: shop.localtest.me
      http:
        paths:
          - { path: /, pathType: Prefix, backend: { service: { name: cluster-a, port: { name: http } } } }
YAML
  done
  ok "DMZ: https://shop.localtest.me -> cluster-a"
}

# exec_probe <pod-deploy> <ns> <komut...>
exec_probe() {
  local d=$1 ns=$2; shift 2
  kb -n "$ns" exec "deploy/$d" -c probe -- "$@"
}

app_verify() {
  local out
  log "Servis zinciri doğrulama"
  out=$(exec_probe probe-gateway "$SHOP_NS" curl -s --max-time 10 http://gateway.$SHOP_NS.svc:9090/)
  local n
  n=$(jq '[.. | objects | select(has("name")) | .name] | unique | length' <<<"$out" 2>/dev/null || echo 0)
  [ "$n" -eq 8 ] && ok "gateway -> 8 servisin hepsi cevap verdi (zincir tam)" \
    || { fail "zincir eksik: $n/8 servis ($out)"; return 1; }
  jq -e '[.. | objects | select(has("code")) | (if .type == "gRPC" then .code == 0 else .code == 200 end)] | all' <<<"$out" >/dev/null \
    && ok "tüm kademeler başarılı (HTTP 200 / gRPC OK)" || { fail "kademelerde hata var"; return 1; }
  out=$(curl -sk --max-time 10 --resolve shop.localtest.me:443:127.0.0.1 https://shop.localtest.me/)
  jq -e '.name == "gateway"' <<<"$out" >/dev/null \
    && ok "uçtan uca: https://shop.localtest.me (edge -> DMZ -> cluster-a -> gateway)" \
    || { fail "uçtan uca erişim yok: $out"; return 1; }
  out=$(exec_probe probe-gateway "$SHOP_NS" bash -c "echo | timeout 3 nc banner.$SHOP_NS.svc 7000 2>/dev/null" 2>/dev/null || true)
  grep -q BANNER-READY <<<"$out" && ok "server-first TCP (banner:7000)" || { fail "banner servisi cevap vermedi"; return 1; }
  exec_probe probe-gateway "$SHOP_NS" bash -c "timeout 3 bash -c '</dev/tcp/postgres.$SHOP_NS.svc/5432'" \
    && ok "shop -> postgres (data cluster) TCP" || { fail "postgres erişimi yok"; return 1; }
}

# http_code <probe-deploy> <ns> <url> [curl-arg...]: HTTP durum kodu (bağlantı hatasında 000)
http_code() {
  local d=$1 ns=$2 url=$3; shift 3
  kb -n "$ns" exec "deploy/$d" -c probe -- curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$@" "$url" 2>/dev/null || true
}
# allowed <kod>: 2xx -> 0
is_2xx() { [[ "$1" =~ ^2 ]]; }

# ns_mesh_labels <kaynak-ns> <hedef-ns>: mesh etiket/annotation'larını kopyalar (yeni test namespace'leri için)
ns_mesh_labels() {
  local l a
  l=$(kb get ns "$1" -o json | jq -r '.metadata.labels // {} | to_entries[] | select(.key|test("istio|dataplane")) | "\(.key)=\(.value)"')
  a=$(kb get ns "$1" -o json | jq -r '.metadata.annotations // {} | to_entries[] | select(.key|test("linkerd")) | "\(.key)=\(.value)"')
  [ -n "$l" ] && kb label ns "$2" $l --overwrite >/dev/null
  [ -n "$a" ] && kb annotate ns "$2" $a --overwrite >/dev/null
  return 0
}

# Geçici test istemcisi: probe_pod <ad> <ns> <sa> <shop.role> [ek-yaml-alanları-json]
#   ek json ile pod şablonuna metadata/spec eklenir (ör. hostNetwork, mesh dışı annotation)
probe_pod() {
  local name=$1 ns=$2 sa=$3 role=$4 extra=${5:-'{}'}
  jq -n --arg n "$name" --arg ns "$ns" --arg sa "$sa" --arg role "$role" --arg img "$NETSHOOT_IMAGE" --argjson x "$extra" '{
    apiVersion: "apps/v1", kind: "Deployment",
    metadata: {name: $n, namespace: $ns},
    spec: {replicas: 1, selector: {matchLabels: {app: $n}},
      template: {
        metadata: ({labels: {app: $n, "shop.role": $role}} * ($x.metadata // {})),
        spec: ({serviceAccountName: $sa, nodeSelector: {"mesh-eval.role": "app"},
          tolerations: [{key: "mesh-eval.role", operator: "Equal", value: "app", effect: "NoSchedule"}],
          terminationGracePeriodSeconds: 1,
          containers: [{name: "probe", image: $img, command: ["sleep", "infinity"],
            securityContext: ($x.securityContext // {})}]} * ($x.spec // {}))}}}' | kb apply -f - >/dev/null
  kb -n "$ns" rollout status "deploy/$name" --timeout=120s >/dev/null
}

# shop pod'larının tamamı Ready mi (politikalar kubelet probe'larını kesmiş olabilir)
shop_all_ready() {
  kb -n "$SHOP_NS" get pods -l mesh-eval/part-of=shop -o json | jq -e '
    [.items[] | select(.metadata.deletionTimestamp == null) | (.status.conditions[]? | select(.type=="Ready") | .status)] | all(. == "True")' >/dev/null
}

# chain_ok <probe> : gateway üzerinden 8 servisin hepsi başarılı mı
chain_ok() {
  local out
  out=$(exec_probe "$1" "$SHOP_NS" curl -s --max-time 10 "http://gateway.$SHOP_NS.svc:9090/" 2>/dev/null)
  jq -e '([.. | objects | select(has("name")) | .name] | unique | length) == 8 and
         ([.. | objects | select(has("code")) | (if .type == "gRPC" then .code == 0 else .code == 200 end)] | all)' <<<"$out" >/dev/null 2>&1
}
e2e_ok() { [ "$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 --resolve shop.localtest.me:443:127.0.0.1 https://shop.localtest.me/)" = 200 ]; }

# expect_access <ad> <izin|ret> <probe> <ns> <url> [curl-arg...]
expect_access() {
  local name=$1 want=$2 p=$3 ns=$4 url=$5 code got; shift 5
  code=$(http_code "$p" "$ns" "$url" "$@")
  if is_2xx "$code"; then got=izin; else got=ret; fi
  check "$name [$code]" "$want" "$got"
}

# Dış çıkış (egress) hedefleri: cluster dışında, lab-app segmentinde iki HTTPS sunucusu.
# Cluster DNS'inde (CoreDNS) adları tanımlanır -> internet bağımlılığı olmadan FQDN bazlı egress testi (S07).
EGRESS_ALLOWED_IP=172.28.20.250
EGRESS_DENIED_IP=172.28.20.251
egress_targets() {
  local d="$STATE_DIR/egress" n ip
  mkdir -p "$d"
  [ -f "$d/tls.crt" ] || openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=*.ext.test" \
    -addext "subjectAltName=DNS:*.ext.test" -keyout "$d/tls.key" -out "$d/tls.crt" 2>/dev/null
  cat > "$d/default.conf" <<'NGX'
server { listen 443 ssl; ssl_certificate /certs/tls.crt; ssl_certificate_key /certs/tls.key;
  location / { default_type text/plain; return 200 "ext-target $hostname\n"; } }
NGX
  for n in allowed denied; do
    ip=$([ $n = allowed ] && echo $EGRESS_ALLOWED_IP || echo $EGRESS_DENIED_IP)
    if ! docker inspect "meval-ext-$n" >/dev/null 2>&1; then
      docker run -d --name "meval-ext-$n" --restart unless-stopped --network "$NET_APP" --ip "$ip" \
        --hostname "$n.ext.test" -v "$d:/certs:ro" -v "$d/default.conf:/etc/nginx/conf.d/default.conf:ro" \
        nginx:1.27-alpine >/dev/null
    fi
  done
  # CoreDNS: ext.test bölgesi
  kb -n kube-system get configmap coredns -o json | jq --arg a "$EGRESS_ALLOWED_IP" --arg b "$EGRESS_DENIED_IP" '
    .data.Corefile |= (if test("ext.test:53") then . else . + "\next.test:53 {\n    hosts {\n        \($a) allowed.ext.test\n        \($b) denied.ext.test\n    }\n}\n" end)
    | .data.Corefile |= (if test("\nlocal:53") then . else . + "\n# node resolv.conf search local: .local sorguları upstream DNS tarafında zaman aşımına uğruyor -> hızlı NXDOMAIN\nlocal:53 {\n    template ANY ANY {\n        rcode NXDOMAIN\n    }\n}\n" end)' \
    | kb apply -f - >/dev/null
  ok "egress hedefleri: allowed.ext.test ($EGRESS_ALLOWED_IP), denied.ext.test ($EGRESS_DENIED_IP)"
}
