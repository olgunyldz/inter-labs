# S05 — DMZ'de endpoint whitelisting
admin_ingress() { # admin_ingress <izinli-cidr>
  local c
  for c in dmz-a dmz-b; do
    kubectl --context "kind-$c" apply -f - >/dev/null <<YAML
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop-admin
  namespace: edge
  annotations:
    nginx.ingress.kubernetes.io/upstream-vhost: shop.localtest.me
    nginx.ingress.kubernetes.io/whitelist-source-range: "$1"
spec:
  ingressClassName: nginx
  tls: [{ hosts: [shop.localtest.me], secretName: edge-tls }]
  rules:
    - host: shop.localtest.me
      http:
        paths:
          - { path: /admin, pathType: Prefix, backend: { service: { name: cluster-a, port: { name: http } } } }
YAML
  done
}
on_exit 'for c in dmz-a dmz-b; do kubectl --context kind-$c -n edge delete ingress shop-admin --ignore-not-found; done'
ext() { curl -sk -o /dev/null -w '%{http_code}' --max-time 5 --resolve shop.localtest.me:443:127.0.0.1 "$@"; }
# her iki DMZ'ye de düşmesi için 6 deneme; hepsi aynı sonucu vermeli
all_codes() { local i out=""; for i in 1 2 3 4 5 6; do out+="$(ext "$@") "; done; echo "$out" | tr ' ' '\n' | grep . | sort -u | paste -sd,; }
# DMZ'nin gördüğü istemci IP'si (PROXY protocol ile edge LB'den gelir): işaretli istekle loglardan bulunur
client_ip() {
  local mark="meval-s05-$RANDOM" c ip
  for c in 1 2 3 4; do ext "https://shop.localtest.me/$mark" >/dev/null; done
  sleep 2
  for c in dmz-a dmz-b; do
    ip=$(kubectl --context "kind-$c" -n ingress-nginx logs deploy/ingress-nginx-controller --tail=200 2>/dev/null \
      | grep "$mark" | grep -o '"remote_addr":"[^"]*"' | head -1 | cut -d'"' -f4)
    [ -n "$ip" ] && { echo "$ip"; return; }
  done
}
admin_ingress 10.255.255.0/24
sleep 8
check "izinsiz kaynak: /admin" 403 "$(all_codes https://shop.localtest.me/admin)"
check "izinsiz kaynak: / (kısıtsız)" 200 "$(all_codes https://shop.localtest.me/)"
check "sahte X-Forwarded-For (izinli IP taklidi): /admin" 403 "$(all_codes -H 'X-Forwarded-For: 10.255.255.7' https://shop.localtest.me/admin)"
CIP=$(client_ip); [ -n "$CIP" ] || die "DMZ loglarında istemci IP'si bulunamadı"
metric client_ip 0 - "DMZ'nin gördüğü istemci IP'si: $CIP"
admin_ingress "$CIP/32"
sleep 8
check "izinli kaynak ($CIP): /admin" 200 "$(all_codes https://shop.localtest.me/admin)"
