# Kimlik bazlı yetki politikaları: tek kenar listesinden her mesh'in kendi diline üretilir.
# Kenar: <hedef servis>:<izinli kimlik (ns/sa)>[,<kimlik>...]
AUTHZ_EDGES=(
  "gateway:loadgen/k6,ingress-nginx/ingress-nginx,shop/gateway"
  "order:shop/gateway"
  "inventory:shop/order"
  "payment:shop/order"
  "pricing:shop/inventory"
  "catalog:shop/pricing"
  "fraud:shop/payment"
  "ledger:shop/fraud"
  "banner:shop/gateway"
)
svc_port_proto() { # Linkerd Server için port adı ve protokol
  case $1 in fraud) echo "grpc gRPC" ;; banner) echo "tcp-banner opaque" ;; *) echo "http HTTP/1" ;; esac
}
istio_principals() { local i out=""; IFS=, read -r -a ids <<<"$1"; for i in "${ids[@]}"; do out+="\"cluster.local/ns/${i%%/*}/sa/${i#*/}\","; done; echo "[${out%,}]"; }
linkerd_ids() { local i out=""; IFS=, read -r -a ids <<<"$1"; for i in "${ids[@]}"; do out+="\"${i#*/}.${i%%/*}.serviceaccount.identity.linkerd.cluster.local\","; done; echo "[${out%,}]"; }

# authz_render <profil>: kimlik bazlı izin listesi (varsayılan ret)
authz_render() {
  local p=$1 e t ids
  case $p in
    istio-sidecar|istio-ambient)
      printf 'apiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: { name: allow-nothing, namespace: %s }\nspec: {}\n' "$SHOP_NS"
      for e in "${AUTHZ_EDGES[@]}"; do t=${e%%:*} ids=${e#*:}
        printf -- '---\napiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: { name: allow-%s, namespace: %s }\nspec:\n  selector: { matchLabels: { app: %s } }\n  action: ALLOW\n  rules: [{ from: [{ source: { principals: %s } }] }]\n' "$t" "$SHOP_NS" "$t" "$(istio_principals "$ids")"
      done ;;
    istio-ambient-l7)
      # ztunnel: yalnızca waypoint'ten gelen trafiğe izin; waypoint: servis bazlı izin listesi
      printf 'apiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: { name: allow-nothing, namespace: %s }\nspec: {}\n' "$SHOP_NS"
      printf -- '---\napiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: { name: allow-from-waypoint, namespace: %s }\nspec:\n  action: ALLOW\n  rules: [{ from: [{ source: { principals: ["cluster.local/ns/%s/sa/waypoint"] } }] }]\n' "$SHOP_NS" "$SHOP_NS"
      for e in "${AUTHZ_EDGES[@]}"; do t=${e%%:*} ids=${e#*:}
        printf -- '---\napiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: { name: allow-%s, namespace: %s }\nspec:\n  targetRefs: [{ kind: Service, group: "", name: %s }]\n  action: ALLOW\n  rules: [{ from: [{ source: { principals: %s } }] }]\n' "$t" "$SHOP_NS" "$t" "$(istio_principals "$ids")"
      done ;;
    linkerd)
      for e in "${AUTHZ_EDGES[@]}"; do t=${e%%:*} ids=${e#*:}
        read -r port proto <<<"$(svc_port_proto "$t")"
        printf -- '---\napiVersion: policy.linkerd.io/v1beta3\nkind: Server\nmetadata: { name: %s, namespace: %s }\nspec:\n  podSelector: { matchLabels: { app: %s } }\n  port: %s\n  proxyProtocol: %s\n' "$t" "$SHOP_NS" "$t" "$port" "$proto"
        printf -- '---\napiVersion: policy.linkerd.io/v1alpha1\nkind: MeshTLSAuthentication\nmetadata: { name: %s-clients, namespace: %s }\nspec: { identities: %s }\n' "$t" "$SHOP_NS" "$(linkerd_ids "$ids")"
        printf -- '---\napiVersion: policy.linkerd.io/v1alpha1\nkind: AuthorizationPolicy\nmetadata: { name: %s-authz, namespace: %s }\nspec:\n  targetRef: { group: policy.linkerd.io, kind: Server, name: %s }\n  requiredAuthenticationRefs: [{ group: policy.linkerd.io, kind: MeshTLSAuthentication, name: %s-clients }]\n' "$t" "$SHOP_NS" "$t" "$t"
      done ;;
    *) return 1 ;;
  esac
}

authz_clear() {
  kb -n "$SHOP_NS" delete authorizationpolicies.security.istio.io --all --ignore-not-found >/dev/null 2>&1 || true
  kb -n "$SHOP_NS" delete servers.policy.linkerd.io,meshtlsauthentications.policy.linkerd.io,authorizationpolicies.policy.linkerd.io,httproutes.policy.linkerd.io,networkauthentications.policy.linkerd.io \
    --all --ignore-not-found >/dev/null 2>&1 || true
  return 0
}
