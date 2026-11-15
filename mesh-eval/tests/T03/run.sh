# T03 — Gateway API ingress
if [ "$MESH" = linkerd ]; then
  kb get gatewayclass -o name > "$(raw gatewayclasses.txt)" 2>&1 || true
  finding "Linkerd küme girişi (north-south) için Gateway API uygulaması sunmuyor; ingress-nginx'in yerine ayrı bir ürün (ör. Envoy Gateway, Contour) seçilip mesh'e dahil edilmesi gerekir. Kayıtlı GatewayClass: $(paste -sd, "$(raw gatewayclasses.txt)")"
  na "Linkerd'de ingress Gateway API uygulaması yok"
fi
on_exit kb delete -f policies/gateway.yaml --ignore-not-found
kb apply -f policies/gateway.yaml >/dev/null
prog=0; acc=0
kb -n "$SHOP_NS" wait --for=condition=Programmed gateway/shop-gw --timeout=120s >/dev/null 2>&1 && prog=1
sleep 5
kb -n "$SHOP_NS" get httproute shop-gw -o json | jq -e '[.status.parents[]?.conditions[]? | select(.type=="Accepted" and .status=="True")] | length > 0' >/dev/null && acc=1
check "Gateway hazır (Programmed)" 1 "$prog"
check "HTTPRoute kabul edildi" 1 "$acc"
out=$(kb -n "$OUTSIDE_NS" exec deploy/probe-outside -- curl -s --max-time 10 "http://shop-gw-istio.$SHOP_NS.svc/" 2>/dev/null || true)
n=$(jq '[.. | objects | select(has("name")) | .name] | unique | length' <<<"$out" 2>/dev/null || echo 0)
check "mesh dışından Gateway üzerinden zincir (8 servis)" 8 "$n"
t=$(kb -n "$OUTSIDE_NS" exec deploy/probe-outside -- bash -c "for i in \$(seq 50); do curl -s -o /dev/null -w '%{time_total}\n' http://shop-gw-istio.$SHOP_NS.svc/; done" | sort -n | sed -n 25p)
metric p50_ms "$(awk -v t="$t" 'BEGIN{printf "%.2f", t*1000}')" ms "Gateway üzerinden zincir gecikmesi (medyan, 50 istek)"
