#!/usr/bin/env bash
# Kurulumu uçtan uca doğrular: trafik akışı, data erişimi, segmentasyon, mgmt erişimi
source "$(dirname "$0")/lib.sh"
set +e

FAILED=0
check() { # check <açıklama> <komut...>
  local desc=$1; shift
  if "$@" >/dev/null 2>&1; then ok "$desc"; else fail "$desc"; FAILED=$((FAILED + 1)); fi
}
expect_fail() { # expect_fail <açıklama> <komut...>
  local desc=$1; shift
  if "$@" >/dev/null 2>&1; then fail "$desc (ERİŞİLEBİLİR!)"; FAILED=$((FAILED + 1)); else ok "$desc"; fi
}
get() { curl -sk --max-time 5 --resolve "$1:443:127.0.0.1" "https://$1/"; }
# getdmz <host>: cevabı veren DMZ cluster'ı + uygulama cluster'ı ("dmz-a cluster-b")
getdmz() {
  curl -sk -D - --max-time 5 --resolve "$1:443:127.0.0.1" "https://$1/" \
    | tr -d '\r' | sed -n 's/^[Xx]-[Dd]mz: //p; s/.*"cluster":"\([^"]*\)".*/\1/p' | paste -sd' '
}
# probe <cluster> <image> <komut...>: cluster içinde tek seferlik pod çalıştırır
probe() {
  local c=$1 img=$2; shift 2
  k "$c" run "probe-$RANDOM" -n default --rm -i --restart=Never --quiet \
    --image="$img" --command -- "$@"
}

log "İnternet -> edge LB -> DMZ A/B -> A/B (https://app.localtest.me)"
out=$(for i in $(seq 12); do getdmz app.localtest.me; done)
echo "$out" | sort | uniq -c | sed 's/^/    /'
check "dmz-a trafik alıyor"     grep -q '^dmz-a ' <<<"$out"
check "dmz-b trafik alıyor"     grep -q '^dmz-b ' <<<"$out"
check "cluster-a trafik alıyor" grep -q ' cluster-a$' <<<"$out"
check "cluster-b trafik alıyor" grep -q ' cluster-b$' <<<"$out"
check "edge LB: iki DMZ backend'i de UP" \
  bash -c "[ \$(curl -s 'http://127.0.0.1:9404/;csv' | grep -E '^dmz_https,dmz-[ab],' | grep -c ',UP,') -eq 2 ]"
check "app-a.localtest.me -> cluster-a" bash -c "curl -sk --resolve app-a.localtest.me:443:127.0.0.1 https://app-a.localtest.me/ | grep -q cluster-a"
check "app-b.localtest.me -> cluster-b" bash -c "curl -sk --resolve app-b.localtest.me:443:127.0.0.1 https://app-b.localtest.me/ | grep -q cluster-b"
echo "    örnek cevap: $(get app.localtest.me)"

log "App -> Data (data ingress TCP portları üzerinden)"
for c in cluster-a cluster-b; do
  check "$c -> postgres.demo.svc:5432" probe "$c" postgres:16-alpine pg_isready -h postgres.demo.svc -p 5432 -t 5
  check "$c -> redis.demo.svc:6379"    probe "$c" redis:7-alpine sh -c 'redis-cli -h redis.demo.svc ping | grep -q PONG'
done

log "Segmentasyon (bu erişimlerin ENGELLİ olması beklenir)"
data_ip=$(node_ip data "$NET_DATA")
a_ip=$(node_ip cluster-a "$NET_APP")
expect_fail "edge LB -/-> cluster-a ($a_ip:80)"   docker exec "$EDGE_LB" nc -z -w 3 "$a_ip" 80
expect_fail "dmz-a -/-> data ($data_ip:5432)"      probe dmz-a busybox:1.36 nc -z -w 3 "$data_ip" 5432
expect_fail "data -/-> cluster-a ($a_ip:80)"       probe data busybox:1.36 nc -z -w 3 "$a_ip" 80

log "Mgmt -> cluster API server'ları"
for c in dmz-a dmz-b cluster-a cluster-b data; do
  ip=$(node_ip "$c" "$(primary_net "$c")")
  check "mgmt -> $c ($ip:6443)" probe mgmt busybox:1.36 nc -z -w 3 "$ip" 6443
done

echo
if [ "$FAILED" -eq 0 ]; then ok "Tüm kontroller geçti"; else fail "$FAILED kontrol başarısız"; exit 1; fi
