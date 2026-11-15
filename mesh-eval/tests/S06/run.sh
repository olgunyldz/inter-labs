# S06 — Atlatma denemeleri
on_exit authz_clear
on_exit kb -n "$SHOP_NS" delete deploy probe-optout --wait=false
on_exit kb -n "$OUTSIDE_NS" delete deploy probe-host --wait=false
[ "$MESH" != none ] && { authz_render "$MESH" > "$(raw policy.yaml)"; kb apply -f "$(raw policy.yaml)" >/dev/null; }
# Mesh'ten çıkarılmış pod: gateway kimliğiyle (SA) ama proxy'siz
case $MESH in
  istio-sidecar) optout='{"metadata":{"annotations":{"sidecar.istio.io/inject":"false"}}}' ;;
  istio-ambient*) optout='{"metadata":{"labels":{"istio.io/dataplane-mode":"none"}}}' ;;
  linkerd) optout='{"metadata":{"annotations":{"linkerd.io/inject":"disabled"}}}' ;;
  *) optout='{}' ;;
esac
probe_pod probe-optout "$SHOP_NS" gateway gateway "$optout"
probe_pod probe-host "$OUTSIDE_NS" default host '{"spec":{"hostNetwork":true}}'
sleep 15
POD_IP=$(kb -n "$SHOP_NS" get pod -l app=order -o jsonpath='{.items[0].status.podIP}')
O="http://order.$SHOP_NS.svc:9090/"
expect_access "mesh dışı namespace -> order"                       ret probe-outside "$OUTSIDE_NS" "$O"
expect_access "mesh'ten çıkarılmış pod (gateway SA) -> order"      ret probe-optout  "$SHOP_NS" "$O"
expect_access "host ağı (node) -> order pod IP"                    ret probe-host    "$OUTSIDE_NS" "http://$POD_IP:9090/"
expect_access "rogue -> order pod IP (Service'i atlayarak)"        ret probe-rogue   "$SHOP_NS" "http://$POD_IP:9090/"
expect_access "rogue + sahte Istio kimlik başlığı (XFCC) -> order" ret probe-rogue   "$SHOP_NS" "$O" \
  -H "X-Forwarded-Client-Cert: By=spiffe://cluster.local/ns/shop/sa/order;URI=spiffe://cluster.local/ns/shop/sa/gateway"
expect_access "rogue + sahte Linkerd kimlik başlığı (l5d-client-id) -> order" ret probe-rogue "$SHOP_NS" "$O" \
  -H "l5d-client-id: gateway.shop.serviceaccount.identity.linkerd.cluster.local"
# Proxy yönetim portları (bilgi sızıntısı / yönetim erişimi)
admin=""
for port in 15000 15020 15021 4191; do
  c=$(http_code probe-rogue "$SHOP_NS" "http://$POD_IP:$port/")
  admin+="$port=$c "
  [ "$port" = 15000 ] || [ "$port" = 4191 ] && metric "admin_port_$port" "$(is_2xx "$c" && echo 1 || echo 0)" bool "rogue'dan proxy yönetim portuna erişim"
done
echo "$admin" > "$(raw admin-ports.txt)"
case $MESH in
  istio-*) expect_access "rogue -> Envoy admin (15000)"       ret probe-rogue "$SHOP_NS" "http://$POD_IP:15000/config_dump" ;;
  linkerd) expect_access "rogue -> linkerd-proxy admin (4191)" ret probe-rogue "$SHOP_NS" "http://$POD_IP:4191/metrics" ;;
esac
