# T02 — Protokol desteği
on_exit kb -n "$SHOP_NS" scale deploy fraud --replicas="$SVC_REPLICAS"
on_exit kb -n "$SHOP_NS" delete svc banner-raw --ignore-not-found
log "1) gRPC yük dağılımı (payment -> fraud, kalıcı bağlantı)"
kb -n "$SHOP_NS" scale deploy fraud --replicas=3 >/dev/null; kb -n "$SHOP_NS" rollout status deploy/fraud --timeout=120s >/dev/null
sleep 10
kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- bash -c \
  "for i in \$(seq 300); do curl -s --max-time 3 http://payment.$SHOP_NS.svc:9090/; echo; done" > "$(raw grpc-responses.jsonl)"
jq -r 'select(.upstream_calls) | .upstream_calls[] | select(.name=="fraud") | .ip_addresses[0]' "$(raw grpc-responses.jsonl)" 2>/dev/null \
  | sort | uniq -c > "$(raw grpc-distribution.txt)" || true
used=$(wc -l < "$(raw grpc-distribution.txt)")
share=$(awk '{s+=$1; if ($1>m) m=$1} END {if (s>0) printf "%.3f", m/s; else print 1}' "$(raw grpc-distribution.txt)")
metric grpc.pods_used "$used" adet "3 fraud pod'undan trafik alan"
metric grpc.max_share "$share" oran "en çok yük alan pod'un payı (ideal 0.33)"
if [ "$used" -lt 3 ] || awk -v s="$share" 'BEGIN{exit !(s > 0.5)}'; then
  finding "$MESH: gRPC (HTTP/2 kalıcı bağlantı) trafiği istek bazlı dağıtılmıyor: 3 pod'dan $used tanesi trafik aldı, en yüklü pod payı $share. Bağlantı bazlı (L4) dengeleme."
fi
log "2) server-first TCP (banner)"
kb -n "$SHOP_NS" apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Service
metadata: { name: banner-raw, namespace: $SHOP_NS }
spec:
  selector: { app: banner }
  ports: [{ name: raw, port: 7001, targetPort: 7000 }]
YAML
sleep 5
banner_ms() { # <host> <port>
  kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- bash -c "
    S=\$EPOCHREALTIME; exec 3<>/dev/tcp/$1/$2 || exit 1; read -t 20 -r l <&3; E=\$EPOCHREALTIME
    [ \"\$l\" = BANNER-READY ] && echo \"\$S \$E\" | awk '{printf \"%.0f\", (\$2-\$1)*1000}' || echo fail" 2>/dev/null || echo fail
}
h=(); n=()
for i in 1 2 3; do h+=("$(banner_ms banner.$SHOP_NS.svc 7000)"); n+=("$(banner_ms banner-raw.$SHOP_NS.svc 7001)"); done
med() { printf '%s\n' "$@" | { grep -v fail || true; } | sort -n | awk '{a[NR]=$1} END{if (NR) print a[int((NR+1)/2)]}'; }
hm=$(med "${h[@]}"); nm=$(med "${n[@]}")
echo "ipuçlu: ${h[*]}  ipuçsuz: ${n[*]}" > "$(raw banner.txt)"
metric banner.hint_ms "${hm:-null}" ms "appProtocol: tcp ile ilk bayt süresi"
metric banner.nohint_ms "${nm:-null}" ms "protokol ipucu olmadan ilk bayt süresi"
check_le "server-first (ipuçlu) ilk bayt (ms)" "${hm:-99999}" 1000
if [ -z "$nm" ] || awk -v v="$nm" 'BEGIN{exit !(v > 1000)}'; then
  if [ -z "$nm" ]; then w="sunucunun ilk baytı 20 sn içinde hiç gelmedi (bağlantı kullanılamaz)"; else w="ilk bayt $nm ms sonra geldi"; fi
  finding "$MESH: protokol ipucu (appProtocol) olmayan server-first TCP portunda $w — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla ${hm:-?} ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.)."
fi
log "3) veri tabanı trafiği (data cluster)"
r=$(kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- bash -c "exec 3<>/dev/tcp/redis.$SHOP_NS.svc/6379; printf 'PING\r\n' >&3; read -t 5 -r l <&3; echo \$l" 2>/dev/null | tr -d '\r')
check "Redis PING" +PONG "$r"
check_true "Postgres TCP bağlantısı" kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- bash -c "timeout 5 bash -c '</dev/tcp/postgres.$SHOP_NS.svc/5432'"
