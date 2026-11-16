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
hc=$(http_code probe-host "$OUTSIDE_NS" "http://$POD_IP:9090/")
is_2xx "$hc" && [ "$MESH" != none ] && finding "$MESH: aynı node'un host ağından pod IP'sine düz (mTLS'siz) istek, zorunlu mTLS ve yetki politikasına rağmen kabul edildi (HTTP $hc). Mesh, node'dan gelen trafiği (kubelet sağlık kontrolleri için) muaf tutuyor; hostNetwork pod'ları ve node üzerindeki ajanlar politikayı atlayabilir. Prod'da hostNetwork kullanımı Pod Security ile kısıtlanmalı."
expect_access "rogue -> order pod IP (Service'i atlayarak)"        ret probe-rogue   "$SHOP_NS" "http://$POD_IP:9090/"
expect_access "rogue + sahte Istio kimlik başlığı (XFCC) -> order" ret probe-rogue   "$SHOP_NS" "$O" \
  -H "X-Forwarded-Client-Cert: By=spiffe://cluster.local/ns/shop/sa/order;URI=spiffe://cluster.local/ns/shop/sa/gateway"
expect_access "rogue + sahte Linkerd kimlik başlığı (l5d-client-id) -> order" ret probe-rogue "$SHOP_NS" "$O" \
  -H "l5d-client-id: gateway.shop.serviceaccount.identity.linkerd.cluster.local"
# Proxy yönetim uçları: yapılandırma dökümü (kritik) ve metrikler (bilgi sızıntısı, ölçüm olarak)
case $MESH in
  istio-sidecar) expect_access "rogue -> Envoy yapılandırma dökümü (15000/config_dump)" ret probe-rogue "$SHOP_NS" "http://$POD_IP:15000/config_dump"
                 mu="http://$POD_IP:15020/stats/prometheus" ;;
  istio-ambient*) mu="http://$POD_IP:15020/stats/prometheus" ;;
  linkerd) mu="http://$POD_IP:4191/metrics" ;;
  *) mu="" ;;
esac
if [ -n "$mu" ]; then
  c=$(http_code probe-rogue "$SHOP_NS" "$mu")
  metric proxy_metrics_exposed "$(is_2xx "$c" && echo 1 || echo 0)" bool "rogue başka pod'un proxy metriklerini okuyabildi mi ($mu -> $c)"
  is_2xx "$c" && finding "$MESH: proxy metrik ucu ($mu) yetkisiz bir pod'dan okunabiliyor (servis adları, istek sayıları sızar). Prod'da NetworkPolicy ile yalnızca izleme sistemine açılmalı."
fi
true
