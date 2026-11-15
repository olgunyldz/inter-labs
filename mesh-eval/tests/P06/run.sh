# P06 — Pod başlangıç süresi
N=$(profile_val 10 30); ROUNDS=$(profile_val 1 3)
metric replicas "$N" adet; metric rounds "$ROUNDS" tur
kb -n "$SHOP_NS" apply -f - >/dev/null <<YAML
apiVersion: apps/v1
kind: Deployment
metadata: { name: scaler, namespace: $SHOP_NS, labels: { app: scaler } }
spec:
  replicas: 0
  selector: { matchLabels: { app: scaler } }
  template:
    metadata: { labels: { app: scaler } }
    spec:
      serviceAccountName: catalog
      nodeSelector: { mesh-eval.role: app }
      tolerations: [{ key: mesh-eval.role, operator: Equal, value: app, effect: NoSchedule }]
      terminationGracePeriodSeconds: 1
      containers:
        - name: app
          image: $FAKE_SERVICE_IMAGE
          env: [{ name: NAME, value: scaler }]
          readinessProbe: { httpGet: { path: /ready, port: 9090 }, periodSeconds: 1 }
          resources: { requests: { cpu: 10m, memory: 16Mi } }
YAML
on_exit kb -n "$SHOP_NS" delete deploy scaler --wait=false
all=()
for ((r = 1; r <= ROUNDS; r++)); do
  kb -n "$SHOP_NS" scale deploy scaler --replicas=0 >/dev/null
  wait_for 120 "scaler pod'ları silindi" bash -c "[ -z \"\$(kubectl --context kind-$BENCH_CLUSTER -n $SHOP_NS get pods -l app=scaler -o name)\" ]"
  t0=$(date +%s.%N)
  kb -n "$SHOP_NS" scale deploy scaler --replicas="$N" >/dev/null
  if kb -n "$SHOP_NS" rollout status deploy/scaler --timeout=120s >/dev/null; then
    t1=$(date +%s.%N)
    allr=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')
    metric "round$r.all_ready_s" "$allr" sn; all+=("$allr")
    kb -n "$SHOP_NS" get pods -l app=scaler -o json > "$(raw "pods-round$r.json")"
  else
    check "tur $r: tüm pod'lar 120 sn içinde hazır" ok zaman_aşımı
  fi
done
# Pod başına: creationTimestamp -> Ready (tüm turlar)
durs=$(jq -s '[.[].items[] | ((.status.conditions[] | select(.type=="Ready") | .lastTransitionTime | fromdate) - (.metadata.creationTimestamp | fromdate))] | sort' "$RUN_DIR"/raw/pods-round*.json)
q() { jq -r --argjson p "$1" 'if length == 0 then "null" else .[((length - 1) * $p | floor)] end' <<<"$durs"; }
metric ready_p50_s "$(q 0.5)" sn "pod oluşturma -> Ready (medyan)"
metric ready_p95_s "$(q 0.95)" sn
metric ready_max_s "$(q 1)" sn
metric all_ready_s "$(printf '%s\n' "${all[@]}" | sort -n | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}')" sn "N pod'un tamamı hazır (medyan tur)"
check "tüm turlar tamamlandı" "$ROUNDS" "${#all[@]}"
