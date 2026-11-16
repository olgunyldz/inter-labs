# mesh-eval kurulumu

Bu doküman, service mesh değerlendirme ortamının nasıl kurulduğunu, her adımın nasıl doğrulandığını ve
kurulum sırasında tespit edilen konuları anlatır. Günlük kullanım için: [kullanim-kilavuzu.md](kullanim-kilavuzu.md).

## Genel yapı

```
                       host (127.0.0.1)
                            │  https://shop.localtest.me
                     ┌──────▼──────┐
  lab-edge           │   edge-lb   │  HAProxy, L4 + PROXY protocol
                     └──┬───────┬──┘
  lab-dmz        ┌──────▼──┐ ┌──▼──────┐
                 │  dmz-a  │ │  dmz-b  │  ingress-nginx (S05: /admin whitelisting)
                 └──────┬──┘ └──┬──────┘
  lab-app   ┌───────────▼───────▼──────────────────────────────────────────┐
            │ cluster-a (bench)                                            │
            │  control-plane  CPU 7-8   ingress-nginx, mesh kontrol düzlemi,│
            │                           Prometheus agent, demo-app          │
            │  worker         CPU 0-3   shop servis zinciri (8 servis)      │──► mgmt: Prometheus,
            │  worker2        CPU 4-6   k6 yük üretici                       │    Grafana, Tempo
            └───────────┬──────────────────────────────────────────────────┘
  lab-data              ▼ data cluster: Postgres, Redis
  lab-app (dış)  meval-ext-allowed / meval-ext-denied (S07 egress hedefleri)
```

- Mesh yalnızca **cluster-a**'ya kurulur; cluster-b mevcut lab haliyle (mesh'siz) kalır.
- Lab'ın ana senaryosu (`app.localtest.me`, `scripts/verify.sh`) etkilenmez.
- Tüm çalışma `mesh-eval` branch'indedir.

## Lab'da yapılan değişiklikler

| Dosya | Değişiklik | Neden |
|---|---|---|
| `clusters/cluster-a.yaml` | 2 worker node (app, loadgen) + `maxPods: 250` | Yük üretici ölçülen servislerle CPU paylaşmasın; P07 ölçek testi |
| `scripts/up.sh` | `attach`: cluster'ın **tüm** node'ları zone network'üne bağlanır | Worker'lar da data segmentine erişsin |
| `platform/ingress-nginx/values-mgmt.yaml` | TCP portları 9090 / 9411 / 4317 | Cluster'lardan mgmt'ye metrik (remote-write) ve trace |

## Kurulum adımları

Ön koşul: lab ayakta (`bash scripts/up.sh`), `kind`, `kubectl`, `helm`, `jq`, `python3` (+`pyyaml`), `openssl`.

```bash
cd mesh-eval
bin/meval tools          # istioctl (1.31.4, 1.30.8) ve linkerd CLI (edge-26.11.2, edge-26.10.2) -> .tools/
bin/meval setup          # node yerleşimi + gözlem + servis zinciri + doğrulama
bin/meval mesh use istio-ambient --fresh   # bir mesh profili (bkz. kılavuz)
```

`setup` sırasıyla şunları yapar (her adım idempotenttir):

1. **Node yerleşimi ve CPU sabitleme** (`lib/app.sh: bench_nodes`)
   - `docker update --cpuset-cpus`: servis node'u 0-3, loadgen 4-6, control-plane 7-8, diğer tüm lab node'ları ve edge LB 9-11.
   - Worker'lara taint (`mesh-eval.role=app|loadgen:NoSchedule`). Kontrol düzlemi taint'i kaldırılır; böylece test dışı her şey control-plane'de çalışır.
2. **Gözlem, mgmt** (`lib/observability.sh: obs_install_mgmt`)
   - Prometheus (remote-write alıcısı, 30 gün saklama), Tempo (Zipkin + OTLP), Grafana (pano: `mesh-eval — test izleme`).
   - Erişim: https://grafana.localtest.me:9443 (admin / mesh-eval), https://prometheus.localtest.me:9443
3. **Gözlem, bench** (`obs_install_agent`)
   - Prometheus **agent** modunda; 5 sn aralıkla cAdvisor, kube-state-metrics, mesh proxy'leri ve kontrol düzlemi toplanır ve mgmt'ye yazılır.
   - Her seriye `cluster=cluster-a` ve `mesh=<aktif profil>` etiketleri eklenir.
4. **Servis zinciri** (`lib/app.sh: app_deploy`)
   - shop namespace'i, test istemcileri, data servisleri, DMZ girişi (`shop.localtest.me`), egress hedefleri ve CoreDNS kayıtları.
5. **Doğrulama** (`meval verify`). Ayrıntısı aşağıda.

### Servis zinciri

Tek kaynak: [`mesh-eval/apps/shop/services.tsv`](../../mesh-eval/apps/shop/services.tsv) → `render.sh` manifest üretir.
Test servisi [`mesh-eval/apps/chainsvc`](../../mesh-eval/apps/chainsvc/main.go) `setup` sırasında derlenip kind node'larına yüklenir.

```
gateway ─► order ─┬─► inventory ─► pricing ─► catalog
                  └─► payment ──gRPC──► fraud ─► ledger
```

| Özellik | Değer |
|---|---|
| Uygulama | `chainsvc` (mesh-eval/apps/chainsvc, Go; HTTP + gRPC, gecikme/hata enjeksiyonu, B3/Zipkin) |
| Derinlik / servis sayısı | 5 kademe, 8 servis, order'da paralel dallanma |
| Replika | 2 (`SVC_REPLICAS`) |
| Yapay işlem süresi | p50 1 ms, p90 2 ms, p99 5 ms |
| Bağlantılar | HTTP keep-alive, kalıcı gRPC bağlantısı; SIGTERM'de bağlantılar boşaltılır |
| Kimlik | Her servisin kendi ServiceAccount'u (mesh kimliği) |
| Protokol ipucu | HTTP servislerde `appProtocol: http`, gRPC'de `kubernetes.io/h2c` (bkz. tespitler) |

Test istemcileri:

| İstemci | Namespace / kimlik | Etiket | Rolü |
|---|---|---|---|
| `probe-gateway` | SA gateway | `shop.role=gateway` | İzinli çağıran |
| `probe-rogue` | SA rogue | `shop.role=rogue` | Yetkisiz servis |
| `probe-outside` | outside namespace, mesh dışı | `shop.role=gateway` | Etiket taklidi denemesi |

Diğer bileşenler:
- **banner:** bağlanınca önce sunucunun yazdığı TCP servisi (server-first protokol testi).
- **postgres / redis:** data cluster'ını temsil eden selector'sız servisler.

### Mesh profilleri

`bin/meval mesh use <profil> [--fresh]` (`lib/mesh.sh`):

| Profil | Kurulum | Uygulamayı mesh'e alma |
|---|---|---|
| `none` | — | — |
| `istio-ambient` | Helm: base, istiod (`profile=ambient`), istio-cni, ztunnel | `istio.io/dataplane-mode=ambient` (shop, loadgen, ingress-nginx), PeerAuthentication STRICT |
| `istio-ambient-l7` | ambient ile aynı | + `istioctl waypoint apply -n shop --enroll-namespace` |
| `istio-sidecar` | Helm: base, istiod | `istio-injection=enabled`, ingress-nginx pod'una sidecar (yalnız giden trafik), STRICT |
| `linkerd` | `linkerd install --crds` + `linkerd install` (kendi CA'mızla) | `linkerd.io/inject=enabled`, `default-inbound-policy=all-authenticated`, ingress-nginx `inject: ingress` |

Ortak ayarlar:
- **Gateway API CRD'leri:** v1.6.1, standard kanal.
- **Kimlik:** mesh'ler kendi CA'sını üretmez; `lib/pki.sh` kök + ara CA verir. Istio: RSA, `cacerts` secret. Linkerd: ECDSA P-256 trust anchor + issuer. Bu, prod'da kurumsal CA (Vault) kullanımının lab karşılığıdır.
- **Varsayılandan sapmalar:** tek replika, autoscale kapalı, erişim logu ve tracing kapalı. Gerekçeleri [`meshes/istio/istiod-values.yaml`](../../mesh-eval/meshes/istio/istiod-values.yaml) ve [`meshes/linkerd/values.yaml`](../../mesh-eval/meshes/linkerd/values.yaml) içinde.
- **Kaynak istekleri** (proxy requests) mesh varsayılanında bırakıldı; raporda "ayrılan kapasite" olarak ayrıca gösterilir.
- **`--fresh`:** bench cluster'ını silip yeniden kurar (~5 dk). Adil kıyas için `suite` bunu varsayılan olarak kullanır.

## Doğrulama: neyi, nasıl kontrol ediyoruz

`bin/meval verify` her kurulumdan sonra otomatik çalışır.

| Kontrol | Yöntem |
|---|---|
| Prometheus hazır | `/-/ready` |
| Remote-write çalışıyor | mgmt'de `count(up{cluster="cluster-a"}) > 0` |
| cAdvisor / kube-state-metrics | ilgili seriler mevcut |
| Grafana + Tempo datasource | `/api/health`, datasource health |
| Zincir tam | probe-gateway → gateway: 8 servisin hepsi cevap veriyor (HTTP 200 / gRPC OK) |
| Uçtan uca | `https://shop.localtest.me` → edge → DMZ → cluster-a → gateway |
| Server-first TCP | banner:7000 |
| Data erişimi | shop → postgres (data cluster) |
| Proxy'ler | sidecar/linkerd: her shop pod'unda proxy; ambient: `ambient.istio.io/redirection=enabled` + ztunnel'de HBONE |
| Waypoint | ambient-l7: waypoint var, trafik `reporter="waypoint"` ile görünüyor |
| mTLS zorunlu | mesh dışı namespace'ten düz HTTP **reddedilmeli** |
| Mesh metrikleri | `istio_requests_total` / `istio_tcp_connections_opened_total` / Linkerd `request_total` mgmt'de mevcut |

Kurulum sırasında elle yapılan ek doğrulamalar: her profilde kenar bazında mTLS. Istio'da her kenar
`connection_security_policy="mutual_tls"`, ambient'te 19/19 iş yükü HBONE, Linkerd'de tüm servisler arası kenarlar
`tls=true` ve kimlikli.

## Kurulum sırasında tespit edilenler

Bu tespitler rapora da girecek niteliktedir.

1. **Istio 1.31 sidecar'ı native sidecar olarak ekliyor.** `istio-proxy` init container olarak, `restartPolicy: Always` ile geliyor. Pod yaşam döngüsü (Job'lar, başlatma sırası) klasik sidecar'dan farklıdır.
2. **Linkerd'de `all-authenticated` politikası proxy'nin admin portunu da (4191) kapsıyor.** Mesh dışındaki
   Prometheus metrik toplayamıyor (`up=0`). Admin portu için bir `Server` tanımlamak ise Linkerd'ün kubelet
   probe'larına verdiği otomatik izni kaldırıyor: native sidecar olarak çalışan proxy'nin kendi startup probe'u
   (`/ready`) 403 alıyor ve **yeni pod'lar hiç hazır olmuyor**. Yol bazında (HTTPRoute) izin de admin sunucusunda
   uygulanmıyor. Çözüm Linkerd'ün kendi önerisi: Prometheus'u da mesh'e almak (`observability` namespace'i
   inject). Metrikler mTLS ile kimlikli toplanır ve admin portuna politika gerekmez.
3. **Linkerd, Service'teki `appProtocol: grpc` değerini tanımıyor.** gRPC trafiği opak TCP taşınıyor; L7 metrikler ve gRPC tipinde `Server` yetkisi çalışmıyor (bağlantı reddi). Kubernetes standardı `appProtocol: kubernetes.io/h2c` ile düzeldi. Prod'da protokol ipuçları mesh'e göre standartlaştırılmalı.
4. **Linkerd `RequestMirror` filtresini desteklemiyor.** Politika denetleyicisi logu: `RequestMirror filter is not supported`.
5. **Lab DNS sorunu (mesh'ten bağımsız).** kind node'larının `resolv.conf`'u docker ağ geçidini (172.28.x.1) gösteriyor; orada DNS yok. Cluster içinden internet adları çözülemiyor, `search local` yüzünden her dış sorgu önce zaman aşımına uğruyor. mesh-eval CoreDNS'e `ext.test` bölgesini ve `ext.test.local` için hızlı NXDOMAIN ekler (genel bir `local:53` bloğu `cluster.local`'ı da yakalar ve cluster DNS'ini bozar; geliştirme sırasında yaşandı). S07 internete bağımlı değildir.
6. **Istio Helm chart'ları.** Istio 1.31 chart'ları klasik Helm deposunda ve OCI registry'de yok (en yeni 1.30.8). Kurulum release tarball'ının içindeki chart'larla yapılır; imajlar docker.io'da mevcut.
7. **Grafana / Tempo Helm chart'ları "deprecated" uyarısı veriyor.** Topluluk depolarına taşınıyorlar. Lab için sorun değil; prod'da güncel chart kaynağı seçilmeli.

8. **Hazır test uygulaması (fake-service) kullanılamadı; yerine `chainsvc` yazıldı.** fake-service (v0.26.2, son
   sürüm Ocak 2024) keep-alive açıkken upstream'den hata aldığı bir istekten sonra kalıcı bağlantıya bozuk HTTP
   cevabı yazıyor (proxy logu: `invalid HTTP version parsed`). Servis yeniden başlatılana kadar her istek 500
   dönüyor; aşırı yük ve hata enjeksiyonu testlerini geçersiz kılıyor. Keep-alive kapatılınca da her istek yeni
   bağlantı açtığı için 2 dakikalık sabit yükte gecikme sürekli arttı (p50 11 → 43 ms). İkisi de mesh kıyasını
   bozduğu için aynı ortam değişkenlerini ve aynı JSON cevap biçimini kullanan küçük bir Go servisi yazıldı:
   keep-alive doğru çalışıyor, gRPC kalıcı tek bağlantı kullanıyor (L4 / L7 yük dengeleme farkı gözlenebilir),
   SIGTERM'de istekler boşaltılıyor. Ek önlem: her testten önce zincir sağlık kontrolü yapılır; bozuksa shop
   yeniden başlatılır ve koşu kaydına not düşülür (`meta.json` → `precheck`).

9. **Linkerd'ün varsayılan `clusterNetworks` değeri tüm özel IP bloklarını kapsıyor** (10/8, 172.16/12, 192.168/16).
   Bu yüzden cluster dışındaki ama özel IP'li hedefler (lab'da 172.28.x; prod'da kurum içi veri merkezi ağları)
   "cluster içi" sayılıyor ve `EgressNetwork` reddediliyor ("networks overlap with clusterNetworks"). Kural kabul
   edilmediği halde izinli hedefe giden trafik de kesildi. mesh-eval Linkerd'ü gerçek pod/servis aralıklarıyla
   kurar (`meshes/linkerd/values.yaml`). Prod'da da aralıklar açıkça verilmelidir.

## Sorun giderme

| Belirti | Kontrol |
|---|---|
| `verify` "bench cluster metrikleri mgmt'ye ulaşmıyor" | `kb -n observability logs deploy/prom-agent-server`, mgmt node'unun lab-app IP'si (`obs_bridge_bench`) |
| Mesh değişiminde pod'lar hazır olmuyor | `kb -n shop get pods`, `kb -n shop describe pod ...`; temiz başlangıç için `meval mesh use <p> --fresh` |
| k6 zaman aşımı | `kubectl --context kind-cluster-a -n loadgen get pods`, `results/<koşu>/raw/*-k6.log` |
| Docker yeniden başladı, IP'ler değişti | `bash scripts/up.sh` + `bin/meval setup` |
| Grafana panosu boş | Zaman aralığı; `mesh` etiketi; `k6_*` metrikleri yalnızca test sırasında yazılır |
