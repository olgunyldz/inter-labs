# T01 — Kademeli yayın
N=400
on_exit kb -n "$SHOP_NS" delete httproutes.gateway.networking.k8s.io catalog-canary --ignore-not-found
on_exit kb -n "$SHOP_NS" delete deploy catalog-v2 --ignore-not-found
on_exit kb -n "$SHOP_NS" delete svc catalog-v1 catalog-v2 --ignore-not-found
kb -n "$SHOP_NS" get deploy catalog -o json | jq '
  .metadata = {name: "catalog-v2", namespace: .metadata.namespace} | .spec.replicas = 1
  | .spec.selector.matchLabels.version = "v2" | .spec.template.metadata.labels.version = "v2"
  | .spec.template.spec.containers[0].env |= map(if .name == "MESSAGE" then .value = "catalog v2" else . end)
  | del(.status)' | kb apply -f - >/dev/null
for v in v1 v2; do
  kb -n "$SHOP_NS" apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Service
metadata: { name: catalog-$v, namespace: $SHOP_NS }
spec:
  selector: { app: catalog, version: $v }
  ports: [{ name: http, port: 9090, targetPort: 9090, appProtocol: http }]
YAML
done
kb -n "$SHOP_NS" rollout status deploy/catalog-v2 --timeout=120s >/dev/null
# v2_share <ek-curl-arg...>: N istekte "catalog v2" cevabı oranı (probe-gateway -> catalog doğrudan)
v2_share() {
  kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- bash -c \
    "for i in \$(seq $N); do curl -s --max-time 3 $* http://catalog.$SHOP_NS.svc:9090/ | grep -o '\"body\": *\"catalog v[12]\"' ; done | sort | uniq -c" > "$(raw share.txt)"
  awk -v n=$N '/v2/ {v2=$1} END {printf "%.3f", v2/n}' "$(raw share.txt)"
}
base=$(v2_share)
metric baseline.v2_share "$base" oran "kural yokken v2 payı (3 replikadan 1'i -> ~0.33)"
if [ "$MESH" = none ] || [ "$MESH" = istio-ambient ]; then
  na "L7 yönlendirme için mesh L7 proxy'si gerekir ($MESH); yalnızca replika oranında dağılım (v2 payı $base)"
fi
kb apply -f policies/route-weighted.yaml >/dev/null; sleep 10
w=$(v2_share); metric weighted.v2_share "$w" oran "hedef 0.10"
check_ge "ağırlıklı: v2 payı >= 0.05" "$w" 0.05
check_le "ağırlıklı: v2 payı <= 0.15" "$w" 0.15
h=$(v2_share -H x-canary:true); metric header.v2_share "$h" oran "hedef 1.00"
check "başlık bazlı: tüm istekler v2" 1.000 "$h"
kb apply -f policies/route-mirror.yaml >/dev/null; sleep 10
# yansıtma: cevaplar v1 olmalı, v2'ye istek gitmeli (v2 pod'unun mesh metriği)
t0=$(date +%s); m=$(v2_share); t1=$(date +%s); prom_settle 20
metric mirror.v2_share_in_responses "$m" oran "yansıtmada cevapların v2 payı (0 olmalı)"
case $MESH in
  istio-sidecar) q="sum(increase(istio_requests_total{$C,reporter=\"destination\",destination_workload=\"catalog-v2\"}[$((t1 - t0 + 5))s]))" ;;
  istio-ambient-l7) q="sum(increase(istio_requests_total{$C,reporter=\"waypoint\",destination_workload=\"catalog-v2\"}[$((t1 - t0 + 5))s]))" ;;
  linkerd) q="sum(increase(request_total{$C,namespace=\"$SHOP_NS\",direction=\"inbound\",deployment=\"catalog-v2\"}[$((t1 - t0 + 5))s]))" ;;
esac
rcv=$(prom_scalar "$q" "$t1"); [ "$rcv" = null ] && rcv=0
metric mirror.v2_received "$rcv" istek "yansıtma süresince v2'ye ulaşan istek"
st=$(kb -n "$SHOP_NS" get httproutes.gateway.networking.k8s.io catalog-canary -o json | jq -r '[.status.parents[]?.conditions[]? | select(.type=="Accepted" or .type=="ResolvedRefs") | "\(.type)=\(.status):\(.reason)"] | join(" ")')
echo "$st" > "$(raw mirror-route-status.txt)"
if awk -v r="$rcv" -v n=$N 'BEGIN{exit !(r >= 0.8*n)}'; then
  metric mirror.supported 1 bool; check "yansıtma: cevaplar v1" 0.000 "$m"
else
  metric mirror.supported 0 bool
  finding "$MESH: trafik yansıtma (RequestMirror) çalışmadı: v2'ye $rcv istek ulaştı (beklenen ~$N). Route durumu: $st"
fi
