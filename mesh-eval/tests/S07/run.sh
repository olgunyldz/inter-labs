# S07 — Egress whitelisting
# Hedefler cluster dışında (lab-app segmenti, bkz. lib/app.sh egress_targets); adlar cluster DNS'inde
ALLOW=allowed.ext.test; DENY=denied.ext.test
code() { kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- curl -sk -o /dev/null -w '%{http_code}' --max-time 8 "https://$1/" 2>/dev/null || true; }
reach() { local c; c=$(code "$1"); [[ "$c" =~ ^[23] ]]; }
reach "$ALLOW" || die "izinli dış hedefe kural öncesinde erişilemiyor ($ALLOW) — egress_targets kurulumu"
reach "$DENY" || die "izinsiz dış hedefe kural öncesinde erişilemiyor ($DENY)"
on_exit kb -n "$SHOP_NS" delete networkpolicy s07-egress --ignore-not-found
on_exit kb delete -f "policies/$MESH.yaml" --ignore-not-found
case $MESH in
  none)
    ips=$(kb -n "$SHOP_NS" exec deploy/probe-gateway -c probe -- dig +short "$ALLOW" A | grep -E '^[0-9.]+$' | sed 's|.*|        - ipBlock: { cidr: &/32 }|')
    [ -n "$ips" ] || die "$ALLOW çözümlenemedi"
    kb apply -f - >/dev/null <<YAML
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: s07-egress, namespace: $SHOP_NS }
spec:
  podSelector: { matchLabels: { app: probe-gateway } }
  policyTypes: [Egress]
  egress:
    - to: [{ namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } } }]
      ports: [{ port: 53, protocol: UDP }, { port: 53, protocol: TCP }]
    - to:
$ips
      ports: [{ port: 443, protocol: TCP }]
YAML
    metric method 0 - "NetworkPolicy (IP bazlı)"
    finding "Mesh'siz egress kısıtı yalnızca IP bazlı yapılabilir: hedefin IP'si değiştiğinde (CDN, bulut servisleri) kural bozulur ve aynı IP'yi paylaşan başka adresler de açılır." ;;
  *) kb apply -f "policies/$MESH.yaml" >/dev/null ;;
esac
sleep 15
a=$(code "$ALLOW"); d=$(code "$DENY")
metric allowed_http_code "$a" kod; metric denied_http_code "$d" kod
if [[ "$MESH" == istio-ambient* ]] && [[ "$d" =~ ^[23] ]]; then
  finding "Istio ambient: ztunnel'de REGISTRY_ONLY (kayıtsız dış adreslere ret) yok; ServiceEntry tanımlı olsa da izinsiz hedefe ($DENY) erişim açık. Ambient'te egress kısıtı için egress gateway veya NetworkPolicy ile birleşik tasarım gerekir."
  na "ambient: FQDN bazlı egress reddi mesh tarafından yapılamıyor (izinsiz hedef HTTP $d)"
fi
check "izinli dış hedef ($ALLOW)" açık "$([[ "$a" =~ ^[23] ]] && echo açık || echo kapalı)"
check "izinsiz dış hedef ($DENY)" kapalı "$([[ "$d" =~ ^[23] ]] && echo açık || echo kapalı)"
