#!/usr/bin/env bash
# services.tsv -> Kubernetes manifest'leri (stdout)
# Kullanım: render.sh [replika]   (varsayılan: config.env SVC_REPLICAS)
source "$(dirname "$0")/../../lib/common.sh"
REPLICAS=${1:-$SVC_REPLICAS}
NS=$SHOP_NS

cat <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $NS
  labels: { mesh-eval/part-of: shop }
EOF

grep -v '^#' "$MEVAL_ROOT/apps/shop/services.tsv" | while IFS=$'\t' read -r name proto workers upstreams; do
  [ -z "$name" ] && continue
  [ "$upstreams" = "-" ] && upstreams=""
  if [ "$proto" = grpc ]; then
    probe='tcpSocket: { port: 9090 }'
  else
    probe='httpGet: { path: /ready, port: 9090 }'
  fi
  cat <<EOF
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: $name, namespace: $NS }
---
apiVersion: v1
kind: Service
metadata:
  name: $name
  namespace: $NS
  labels: { app: $name }
spec:
  selector: { app: $name }
  ports:
    - { name: $proto, port: 9090, targetPort: 9090, appProtocol: $([ "$proto" = grpc ] && echo kubernetes.io/h2c || echo http) }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $name
  namespace: $NS
  labels: { app: $name, mesh-eval/part-of: shop }
spec:
  replicas: $REPLICAS
  selector:
    matchLabels: { app: $name, version: v1 }
  template:
    metadata:
      labels: { app: $name, version: v1, shop.role: $name, mesh-eval/part-of: shop }
    spec:
      serviceAccountName: $name
      nodeSelector: { mesh-eval.role: app }
      tolerations: [{ key: mesh-eval.role, operator: Equal, value: app, effect: NoSchedule }]
      terminationGracePeriodSeconds: 10
      containers:
        - name: app
          image: $FAKE_SERVICE_IMAGE
          ports: [{ name: $proto, containerPort: 9090 }]
          env:
            - { name: NAME, value: "$name" }
            - { name: MESSAGE, value: "$name v1" }
            - { name: SERVER_TYPE, value: "$proto" }
            - { name: UPSTREAM_URIS, value: "$upstreams" }
            - { name: UPSTREAM_WORKERS, value: "$workers" }
            - { name: TIMING_50_PERCENTILE, value: "$SVC_TIMING_P50" }
            - { name: TIMING_90_PERCENTILE, value: "$SVC_TIMING_P90" }
            - { name: TIMING_99_PERCENTILE, value: "$SVC_TIMING_P99" }
            - { name: HTTP_CLIENT_KEEP_ALIVES, value: "true" }
            - { name: HTTP_SERVER_KEEP_ALIVES, value: "true" }
            - { name: HTTP_CLIENT_REQUEST_TIMEOUT, value: "10s" }
            - { name: TRACING_ZIPKIN, value: "${SVC_TRACING_ZIPKIN:-}" }
            - { name: LOG_LEVEL, value: "error" }
          readinessProbe:
            $probe
            periodSeconds: 2
          resources:
            requests: { cpu: 50m, memory: 32Mi }
            limits: { memory: 256Mi }
EOF
done

# Test istemcileri (uzun ömürlü, kubectl exec ile kullanılır)
#   probe-gateway : SA=gateway, shop.role=gateway  -> gateway kimliğini/etiketini taşır (izinli)
#   probe-rogue   : SA=rogue,   shop.role=rogue    -> yetkisiz servis (engellenmeli)
cat <<EOF
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: rogue, namespace: $NS }
EOF
for p in gateway:gateway rogue:rogue; do
  pname=probe-${p%%:*} sa=${p#*:}
  cat <<EOF
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $pname
  namespace: $NS
  labels: { app: $pname, mesh-eval/part-of: shop }
spec:
  replicas: 1
  selector: { matchLabels: { app: $pname } }
  template:
    metadata:
      labels: { app: $pname, shop.role: $sa, mesh-eval/part-of: shop }
    spec:
      serviceAccountName: $sa
      nodeSelector: { mesh-eval.role: app }
      tolerations: [{ key: mesh-eval.role, operator: Equal, value: app, effect: NoSchedule }]
      terminationGracePeriodSeconds: 1
      containers:
        - name: probe
          image: $NETSHOOT_IMAGE
          command: ["sleep", "infinity"]
          resources: { requests: { cpu: 10m, memory: 16Mi } }
EOF
done

# Server-first TCP servisi (bağlanınca önce sunucu "BANNER" yazar; SMTP/MySQL benzeri).
# Mesh'lerin protokol algılamasını zorlar (T02).
cat <<EOF
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: banner, namespace: $NS }
---
apiVersion: v1
kind: Service
metadata: { name: banner, namespace: $NS, labels: { app: banner } }
spec:
  selector: { app: banner }
  ports: [{ name: tcp-banner, port: 7000, targetPort: 7000, appProtocol: tcp }]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: banner
  namespace: $NS
  labels: { app: banner, mesh-eval/part-of: shop }
spec:
  replicas: 1
  selector: { matchLabels: { app: banner } }
  template:
    metadata:
      labels: { app: banner, shop.role: banner, mesh-eval/part-of: shop }
    spec:
      serviceAccountName: banner
      nodeSelector: { mesh-eval.role: app }
      tolerations: [{ key: mesh-eval.role, operator: Equal, value: app, effect: NoSchedule }]
      terminationGracePeriodSeconds: 1
      containers:
        - name: banner
          image: $NETSHOOT_IMAGE
          command: ["socat", "TCP-LISTEN:7000,fork,reuseaddr", "SYSTEM:echo BANNER-READY; cat"]
          ports: [{ containerPort: 7000 }]
          readinessProbe: { tcpSocket: { port: 7000 }, periodSeconds: 2 }
          resources: { requests: { cpu: 10m, memory: 16Mi } }
EOF

# Veri servisleri: data cluster'ı (lab'daki demo/postgres ile aynı yöntem, EndpointSlice'ı meval yazar)
cat <<EOF
---
apiVersion: v1
kind: Service
metadata: { name: postgres, namespace: $NS }
spec:
  ports: [{ name: tcp-postgres, port: 5432, targetPort: 5432, appProtocol: tcp }]
---
apiVersion: v1
kind: Service
metadata: { name: redis, namespace: $NS }
spec:
  ports: [{ name: tcp-redis, port: 6379, targetPort: 6379, appProtocol: tcp }]
EOF

# Mesh dışı istemci (atlatma denemeleri)
cat <<EOF
---
apiVersion: v1
kind: Namespace
metadata: { name: $OUTSIDE_NS, labels: { mesh-eval/part-of: outside } }
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: probe-outside, namespace: $OUTSIDE_NS }
spec:
  replicas: 1
  selector: { matchLabels: { app: probe-outside } }
  template:
    metadata: { labels: { app: probe-outside, shop.role: gateway } }
    spec:
      nodeSelector: { mesh-eval.role: app }
      tolerations: [{ key: mesh-eval.role, operator: Equal, value: app, effect: NoSchedule }]
      terminationGracePeriodSeconds: 1
      containers:
        - name: probe
          image: $NETSHOOT_IMAGE
          command: ["sleep", "infinity"]
          resources: { requests: { cpu: 10m, memory: 16Mi } }
EOF

# Yük üretici namespace'i (k6 pod'ları testler tarafından oluşturulur)
cat <<EOF
---
apiVersion: v1
kind: Namespace
metadata: { name: $LOADGEN_NS, labels: { mesh-eval/part-of: loadgen } }
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: k6, namespace: $LOADGEN_NS }
EOF

# Giriş: shop.localtest.me -> (edge -> DMZ) -> cluster-a ingress -> gateway
cat <<EOF
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop
  namespace: $NS
  annotations:
    # Mesh'li ingress'te upstream olarak pod IP'leri değil Service kullanılır (sidecar/linkerd yönlendirmesi için)
    nginx.ingress.kubernetes.io/service-upstream: "true"
    nginx.ingress.kubernetes.io/upstream-vhost: gateway.$NS.svc.cluster.local
spec:
  ingressClassName: nginx
  rules:
    - host: shop.localtest.me
      http:
        paths:
          - { path: /, pathType: Prefix, backend: { service: { name: gateway, port: { number: 9090 } } } }
EOF
