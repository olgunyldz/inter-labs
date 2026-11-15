# O03 — Operasyon envanteri
case $(mesh_family "$MESH") in istio) NS=istio-system; G='istio\.io' ;; linkerd) NS=linkerd; G='linkerd\.io' ;; esac
metric crds "$(kb get crd -o name | grep -cE "$G")" adet "mesh'e ait CRD"
metric gateway_api_crds "$(kb get crd -o name | grep -c 'gateway.networking.k8s.io')" adet
metric control_plane_pods "$(kb -n "$NS" get pods --no-headers | grep -vE 'ztunnel|cni-node' | wc -l)" adet
metric node_agents "$(kb -n "$NS" get ds --no-headers 2>/dev/null | wc -l)" adet "DaemonSet (node başına ajan)"
imgs=$( { kb -n "$NS" get pods -o json; kb -n "$SHOP_NS" get pods -o json; } | jq -r '.items[].spec | (.containers + (.initContainers // []))[] | .image' \
  | grep -E 'istio|linkerd|l5d' | sort -u)
echo "$imgs" > "$(raw images.txt)"
metric images "$(grep -c . <<<"$imgs")" adet "kullanılan farklı mesh imajı"
metric webhooks "$(kb get mutatingwebhookconfiguration,validatingwebhookconfiguration -o name | grep -cE 'istio|linkerd')" adet
pj=$(kb -n "$SHOP_NS" get pod -l app=order -o json | jq '.items[0]')
added=$(jq '[(.spec.containers + (.spec.initContainers // []))[].name | select(test("istio|linkerd"))] | length' <<<"$pj")
metric added_containers_per_pod "$added" adet "uygulama pod'una mesh'in eklediği konteyner (init dahil)"
priv=$( { kb -n "$NS" get pods -o json; kb -n "$SHOP_NS" get pods -o json; } | jq -r '
  [.items[] | .metadata.name as $p | (.spec.containers + (.spec.initContainers // []))[]
   | select(.securityContext.privileged == true or ((.securityContext.capabilities.add // []) | index("NET_ADMIN")))
   | "\(.name)"] | unique | join(",")')
echo "$priv" > "$(raw privileged.txt)"
metric privileged_components "$(tr ',' '\n' <<<"$priv" | grep -c . || true)" adet "privileged veya NET_ADMIN isteyen konteyner türü ($priv)"
metric install_s "$(jq -r --arg p "$MESH" '.[$p] // "null"' "$INSTALL_TIMES" 2>/dev/null)" sn "kurulum süresi (meval mesh use)"
metric helm_releases "$(hb list -n "$NS" -q 2>/dev/null | wc -l)" adet
case $(mesh_family "$MESH") in
  istio)
    istioctl_v "$ISTIO_VERSION" --context "kind-$BENCH_CLUSTER" analyze -n "$SHOP_NS" > "$(raw diag.txt)" 2>&1 || true
    issues=$(grep -cE '^(Error|Warning)' "$(raw diag.txt)" || true)
    errs=$(grep -c '^Error' "$(raw diag.txt)" || true) ;;
  linkerd)
    lk check > "$(raw diag.txt)" 2>&1 || true
    issues=$(grep -cE '^\s*(×|‼)' "$(raw diag.txt)" || true)
    errs=$(grep -cE '^\s*×' "$(raw diag.txt)" || true) ;;
esac
metric diag_issues "$issues" adet "tanılama aracının uyarı + hata sayısı"
check "tanılama aracında hata yok" 0 "$errs"
