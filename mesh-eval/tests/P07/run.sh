# P07 — Politika yayılma süresi ve ölçek
N=$(profile_val 30 120)
POL="policies/$MESH.yaml"
URL="http://order.$SHOP_NS.svc:9090/"
on_exit kb delete -f "$POL" --ignore-not-found
on_exit kb delete namespace shop-scale --wait=false

# poll_until <deny|allow>: probe-rogue içinden 100 ms aralıkla yoklar; koşul sağlandığı anı (unix) yazar
poll_until() {
  kb -n "$SHOP_NS" exec deploy/probe-rogue -c probe -- bash -c "
    end=\$((SECONDS + 60))
    while [ \$SECONDS -lt \$end ]; do
      c=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 1 $URL)
      if [ '$1' = deny ] && [ \"\$c\" != 200 ]; then echo \$EPOCHREALTIME; exit 0; fi
      if [ '$1' = allow ] && [ \"\$c\" = 200 ]; then echo \$EPOCHREALTIME; exit 0; fi
      sleep 0.1
    done; echo timeout"
}
measure() { # measure <önek> -> 3 tekrar, medyan
  local p=$1 i t0 t1 d=() a=()
  for i in 1 2 3; do
    [ "$(http_code probe-rogue "$SHOP_NS" "$URL")" = 200 ] || { check "$p: başlangıçta erişim açık" 200 "$(http_code probe-rogue "$SHOP_NS" "$URL")"; return; }
    t0=$(date +%s.%N); kb apply -f "$POL" >/dev/null; t1=$(poll_until deny)
    [ "$t1" = timeout ] && { check "$p: kural 60 sn içinde yürürlüğe girdi" ok zaman_aşımı; kb delete -f "$POL" >/dev/null; return; }
    d+=("$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')")
    t0=$(date +%s.%N); kb delete -f "$POL" >/dev/null; t1=$(poll_until allow)
    [ "$t1" = timeout ] && { check "$p: kural kaldırılınca erişim geri geldi" ok zaman_aşımı; return; }
    a+=("$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')")
    sleep 2
  done
  med() { printf '%s\n' "$@" | sort -n | sed -n 2p; }
  metric "$p.deny_s" "$(med "${d[@]}")" sn "kural uygulandı -> erişim kesildi (medyan)"
  metric "$p.allow_s" "$(med "${a[@]}")" sn "kural kaldırıldı -> erişim açıldı (medyan)"
  check_le "$p: yürürlüğe girme süresi" "$(med "${d[@]}")" 30
}

log "Yayılma süresi (mevcut ölçek)"
measure base

log "Ölçek: $N ek servis"
t=$(date +%s)
before_ctl=$(role_mem control $((t - 30)) "$t"); before_sc=$(role_mem sidecar $((t - 30)) "$t"); before_zt=$(role_mem ztunnel $((t - 30)) "$t")
sc_n=$(role_count sidecar "$t")
kb create namespace shop-scale --dry-run=client -o yaml | kb apply -f - >/dev/null
ns_mesh_labels "$SHOP_NS" shop-scale
for ((i = 1; i <= N; i++)); do
  cat <<YAML
---
apiVersion: v1
kind: Service
metadata: { name: svc-$i, namespace: shop-scale }
spec: { selector: { app: svc-$i }, ports: [{ name: http, port: 9090, appProtocol: http }] }
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: svc-$i, namespace: shop-scale }
spec:
  replicas: 1
  selector: { matchLabels: { app: svc-$i } }
  template:
    metadata: { labels: { app: svc-$i } }
    spec:
      nodeSelector: { mesh-eval.role: app }
      tolerations: [{ key: mesh-eval.role, operator: Equal, value: app, effect: NoSchedule }]
      terminationGracePeriodSeconds: 1
      containers:
        - name: app
          image: $FAKE_SERVICE_IMAGE
          env: [{ name: NAME, value: svc-$i }]
          resources: { requests: { cpu: 5m, memory: 16Mi } }
YAML
done | kb apply -f - >/dev/null
for d in $(kb -n shop-scale get deploy -o name); do kb -n shop-scale rollout status "$d" --timeout=300s >/dev/null; done
ok "$N servis hazır"
sleep 60   # yapılandırmanın proxy'lere yayılması
t=$(date +%s)
after_ctl=$(role_mem control $((t - 30)) "$t"); after_sc=$(role_mem sidecar $((t - 30)) "$t"); after_zt=$(role_mem ztunnel $((t - 30)) "$t")
metric scale_services "$N" adet
metric control.mem_before_mib "$before_ctl" MiB; metric control.mem_after_mib "$after_ctl" MiB
metric control.mem_growth_mib "$(awk -v a="$after_ctl" -v b="$before_ctl" 'BEGIN{printf "%.1f", a-b}')" MiB "N servis eklenince kontrol düzlemi bellek artışı"
if [ "$sc_n" != 0 ]; then
  metric sidecar.mem_per_container_before_mib "$(awk -v m="$before_sc" -v n="$sc_n" 'BEGIN{printf "%.2f", m/n}')" MiB
  metric sidecar.mem_per_container_after_mib "$(awk -v m="$after_sc" -v n="$sc_n" 'BEGIN{printf "%.2f", m/n}')" MiB
  metric sidecar.mem_per_container_growth_mib "$(awk -v a="$after_sc" -v b="$before_sc" -v n="$sc_n" 'BEGIN{printf "%.2f", (a-b)/n}')" MiB "shop'taki her proxy'nin, N servis eklenince bellek artışı"
fi
[ "$(role_count ztunnel "$t")" != 0 ] && metric ztunnel.mem_growth_mib "$(awk -v a="$after_zt" -v b="$before_zt" 'BEGIN{printf "%.1f", a-b}')" MiB

log "Yayılma süresi ($N ek servisle)"
measure scaled
