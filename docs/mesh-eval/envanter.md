# mesh-eval envanteri

Değerlendirmede kullanılan tüm bileşenler, sürümleri ve nerede çalıştıkları. Sürümler
[`mesh-eval/config.env`](../../mesh-eval/config.env) dosyasında sabitlenmiştir. Her test koşusu, kullandığı
sürümleri `results/<koşu>/meta.json` dosyasına yazar; rapordaki envanter tablosu buradan gelir.

## Ortam

| Bileşen | Sürüm / değer | Not |
|---|---|---|
| Host | 12 çekirdek, 62 GB RAM, Linux | Tüm cluster'lar tek host'ta |
| kind | v0.33.0 | |
| Kubernetes (node imajı) | v1.37.0 (`kindest/node:v1.37.0`) | |
| kubectl / helm | v1.37.2 / v4.3.2 | `~/.local/bin` |
| CNI / NetworkPolicy | kindnet `v20260820-69b56db7` (kube-network-policies dahili) | S02, P07 (none) |
| CoreDNS | v1.14.6 | `ext.test` ve `local` bölgeleri mesh-eval tarafından eklenir |
| ingress-nginx | chart 4.15.1, controller v1.15.1 | Tüm cluster'lar |
| Edge LB | `haproxy:3.0-alpine` | |

## Bench cluster'ı (cluster-a)

| Node | CPU (cpuset) | Etiket / taint | Çalışan |
|---|---|---|---|
| cluster-a-control-plane | 7-8 | `ingress-ready=true` | ingress-nginx, demo-app, mesh kontrol düzlemi, Prometheus agent, kube-state-metrics |
| cluster-a-worker | 0-3 | `mesh-eval.role=app` (taint) | shop servis zinciri, test istemcileri, waypoint |
| cluster-a-worker2 | 4-6 | `mesh-eval.role=loadgen` (taint) | k6 pod'ları |

Diğer lab node'ları ve edge LB 9-11 numaralı çekirdeklere sabitlenir. DaemonSet'ler (ztunnel, istio-cni, kindnet, kube-proxy) her node'da çalışır.

## Service mesh'ler

| Mesh | Sürüm | Kurulum kaynağı | Bileşenler |
|---|---|---|---|
| Istio | 1.31.4 (R05 başlangıç: 1.30.8) | Release tarball içindeki Helm chart'ları, imajlar `docker.io/istio` | base, istiod, (ambient) istio-cni + ztunnel, waypoint (Envoy) |
| Linkerd | edge-26.11.2 (R05 başlangıç: edge-26.10.2) | `linkerd` CLI (`.tools/`) | CRD'ler, linkerd-destination, -identity, -proxy-injector, linkerd2-proxy |
| Gateway API CRD'leri | v1.6.1 (standard) | kubernetes-sigs/gateway-api | Istio 1.31 (v1.6.0 ile derlenmiş) ve Linkerd'in ortak sürümü |

Kimlik (PKI, `lib/pki.sh`, `.state/pki/`):

| Mesh | Kök | Ara CA |
|---|---|---|
| Istio | RSA 4096, 10 yıl | RSA 2048, `cacerts` secret |
| Linkerd | ECDSA P-256 trust anchor | ECDSA P-256 issuer, 1 yıl |

S08 testi aynı kökle yeni ara CA üretip yük altında rotasyon yapar.

## Gözlem (mgmt cluster'ı, `observability` namespace)

| Bileşen | Chart / imaj | Erişim |
|---|---|---|
| Prometheus | prometheus-community/prometheus 29.47.2, `prometheus:v3.16.0` | https://prometheus.localtest.me:9443, cluster'lardan `<mgmt>:9090` (remote-write) |
| Grafana | grafana/grafana 10.5.15, `grafana:12.3.1` | https://grafana.localtest.me:9443 (admin / mesh-eval) |
| Tempo | grafana/tempo 1.24.4, `tempo:2.9.0` | Zipkin `<mgmt>:9411`, OTLP `<mgmt>:4317`, sorgu Grafana üzerinden |
| Prometheus agent (bench) | aynı chart, `--agent` | 5 sn toplama, dış etiketler `cluster`, `mesh` |
| kube-state-metrics (bench) | 9.0.1, v2.20.0 | requests/limits, pod durumu |

Bench → mgmt erişimi lab'daki data servisleriyle aynı yöntemle kurulur: selector'sız Service + EndpointSlice → mgmt node'unun lab-app IP'si → mgmt ingress-nginx TCP portu.

## Test bileşenleri

| Bileşen | İmaj | Görev | Kullanan testler |
|---|---|---|---|
| chainsvc | `mesh-eval/chainsvc:0.1.0` (apps/chainsvc, Go 1.26, grpc-go 1.75, scratch imaj) | 8 servislik zincir (HTTP/gRPC), gecikme ve hata enjeksiyonu, v2 sürümü, B3/Zipkin | Tümü |
| k6 | `grafana/k6:2.4.0` | Yük üretici. Bench'te pod (loadgen node'u, mesh içinde); P04'te host'ta container (lab-edge) | P01–P05, S08, R01–R05, O01, O02 |
| netshoot | `nicolaka/netshoot:v0.14` | Test istemcileri (curl, openssl, tcpdump, socat, dig) | S01–S08, T01–T03, P07 |
| banner (socat) | netshoot | Server-first TCP sunucusu | T02 |
| Egress hedefleri | `nginx:1.27-alpine` (docker, lab-app, 172.28.20.250/251) | `allowed.ext.test` / `denied.ext.test` HTTPS | S07 |
| Data servisleri | lab'daki Postgres / Redis | TCP trafiği | T02 |

## Rol bazında kaynak ölçümü

[`lib/resources.sh`](../../mesh-eval/lib/resources.sh), cAdvisor serilerini maliyet kalemlerine ayırır:

| Rol | Seçici | Anlamı |
|---|---|---|
| app | `namespace=shop, container=app` | Uygulama |
| sidecar | `namespace=shop, container=~istio-proxy\|linkerd-proxy` | Pod içi proxy |
| ztunnel | `istio-system, pod=~ztunnel-.*` | Ambient node proxy'si |
| waypoint | `shop, pod=~waypoint-.*` | Ambient L7 proxy'si |
| cni | `istio-system, pod=~istio-cni-node-.*` | Ambient yönlendirme ajanı |
| control | `istio-system` / `linkerd` (yukarıdakiler hariç) | Kontrol düzlemi |
| ingress | `ingress-nginx` | Bench girişi (+ proxy'si) |
| loadgen | `loadgen` pod cgroup'u | k6 (+ proxy'si) |
| node_app / node_loadgen / node_control | `id="/"` | Node toplamı. app + proxy dışında kalan kernel ağ işleme yükü buradan görünür |

## Dosya yapısı

```
mesh-eval/
  bin/meval                 tek giriş noktası (CLI)
  config.env                sürümler, CPU yerleşimi, servis zinciri, prod varsayımları
  lib/                      common, app, observability, mesh, pki, policy, k6, resources, test, tools
  apps/shop/                services.tsv (zincir tanımı) + render.sh
  apps/chainsvc/            test servisi (Go) + Dockerfile
  meshes/istio|linkerd/     mesh'e özel helm değerleri ve ek politikalar
  observability/            Prometheus/Grafana/Tempo değerleri + Grafana panosu
  tests/<ID>/               test.yaml (tanım) + run.sh (çalıştırıcı) + policies/
  tests/k6/load.js          ortak yük script'i
  report/                   generate.py (rapor), docs.py (test dokümanı), scorecard.yaml, static.yaml
  results/                  test koşuları (git dışı)
  reports/                  üretilen raporlar (git dışı)
  .tools/ .state/           indirilen CLI'lar, PKI, aktif profil (git dışı)
docs/mesh-eval/             kurulum, envanter, test senaryoları, kullanım kılavuzu
```
