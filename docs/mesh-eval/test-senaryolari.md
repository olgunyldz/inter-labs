# Test senaryoları

> Bu dosya `tests/*/test.yaml` dosyalarından üretilir (`meval docs`). Elle düzenlemeyin.

Toplam **26 test**. Her test her mesh profilinde ayrı koşulur; sonuçlar `mesh-eval/results/` altına kaydedilir.

## Özet

| ID | Kategori | Test | Mesh profilleri | Başarı ölçütü |
|---|---|---|---|---|
| [P01](#p01) | performans | Kademeli yük — gecikme ve kırılma noktası | hepsi | İlk aşamada hata oranı < %1 (sistem düşük yükte sağlıklı) |
| [P02](#p02) | performans | Sabit uzun yük (soak) — kararlılık ve sızıntı | hepsi | Hata oranı < %1 ve son çeyrek p99 <= max(1.5 x ilk çeyrek, ilk çeyrek + 10 ms) |
| [P03](#p03) | performans | Ani yük (spike) — dayanım ve toparlanma | hepsi | Sıçrama sonrası aşamada hata oranı < %1 |
| [P04](#p04) | performans | Uçtan uca yol — edge -> DMZ -> ingress -> zincir | hepsi | İlk aşamada hata oranı < %1 |
| [P05](#p05) | performans | Kaynak tüketimi — kalem kalem maliyet | hepsi | Yük penceresinde hata oranı < %1 |
| [P06](#p06) | performans | Pod başlangıç süresi ve ölçeklenme hızı | hepsi | Tüm pod'lar 120 sn içinde hazır |
| [P07](#p07) | performans | Politika yayılma süresi ve kontrol düzlemi ölçeği | hepsi | Kural 30 sn içinde yürürlüğe girer ve kaldırıldığında erişim geri gelir |
| [S01](#s01) | güvenlik | mTLS zorunluluğu ve hat üzerinde şifreleme | hepsi | Mesh dışı düz erişim reddedilir ve işaret metni ağda görünmez |
| [S02](#s02) | güvenlik | Servisler arası whitelisting — NetworkPolicy (L3/L4) | hepsi | Uyarlanmış kurallarla izin/ret matrisinin tamamı beklendiği gibi |
| [S03](#s03) | güvenlik | Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası) | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | İzin/ret matrisinin tamamı beklendiği gibi, kimlik taklidi reddedilir, pod'lar sağlıklı |
| [S04](#s04) | güvenlik | Endpoint bazlı erişim kısıtı (L7 — path / method) | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | İzinli endpoint'ler açık, diğerleri reddedilir, zincir çalışır |
| [S05](#s05) | güvenlik | Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress) | hepsi | Tüm kontroller beklendiği gibi |
| [S06](#s06) | güvenlik | Politika atlatma denemeleri | hepsi | Tüm denemeler reddedilir |
| [S07](#s07) | güvenlik | Dış çıkış (egress) whitelisting | hepsi | İzinli hedef açık, izinsiz hedef kapalı |
| [S08](#s08) | güvenlik | Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Sertifika kurumsal ara CA'dan, ömür <= 24 sa, rotasyonda hata oranı < %1 ve yeni issuer |
| [T01](#t01) | trafik | Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma | hepsi | Ağırlıklı yönlendirmede v2 payı %10 ± 5 puan, başlıklı isteklerin tamamı v2 |
| [T02](#t02) | trafik | Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği | hepsi | Redis/Postgres erişimi çalışır, protokol ipuçlu server-first bağlantı < 1 sn |
| [T03](#t03) | trafik | Gateway API ile giriş (ingress-nginx'in yerine geçme) | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Gateway hazır, route kabul edildi, zincir mesh dışından erişilebilir |
| [O01](#o01) | gözlem | Gözlemlenebilirlik — hazır metrikler, doğruluk, dağıtık izleme, erişim logu | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Tüm servisler için en az L4 metrik var ve trace Tempo'da bulunur |
| [O02](#o02) | gözlem | Metrik maliyeti — seri sayısı ve alım hızı | hepsi | Ölçüm tamamlanır (bilgi amaçlı) |
| [O03](#o03) | operasyon | Operasyon envanteri — karmaşıklık ve ayrıcalık | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Tanılama aracında hata yok |
| [R01](#r01) | dayanıklılık | Timeout, retry ve outlier detection (circuit breaking) | hepsi | Politikayla p99 < 1000 ms ve outlier detection ile hata oranı yarıdan fazla düşer |
| [R02](#r02) | dayanıklılık | Hata enjeksiyonu (fault injection) | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Gözlenen hata oranı %10 ± 3 puan ve p95 >= 200 ms |
| [R03](#r03) | dayanıklılık | Yük altında pod kaybı (failover) | hepsi | Hata oranı < %1 |
| [R04](#r04) | dayanıklılık | Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Kontrol düzlemi kaybında mevcut trafikte hata oranı < %1 |
| [R05](#r05) | dayanıklılık | Yük altında kesintisiz mesh güncellemesi | istio-sidecar, istio-ambient, istio-ambient-l7, linkerd | Güncelleme sırasında hata oranı < %1 ve sonunda tüm proxy'ler yeni sürümde |

## Hangi test hangi bileşenle yapılıyor

| Test | k6 | Servis zinciri | Prometheus/Grafana | Tempo | Edge LB / DMZ | NetworkPolicy | Mesh yetki politikası | Mesh trafik kuralları | Mesh kontrol düzlemi | Gateway API | netshoot / tcpdump | Data cluster | Egress hedefleri | CLI araçları |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01 | ● | ● | ● |  |  |  |  |  | ● |  |  |  |  |  |
| P02 | ● | ● | ● |  |  |  |  |  | ● |  |  |  |  |  |
| P03 | ● | ● | ● |  |  |  |  |  |  |  |  |  |  |  |
| P04 | ● | ● |  |  | ● |  |  |  |  |  |  |  |  |  |
| P05 | ● |  | ● |  |  |  |  |  | ● |  |  |  |  |  |
| P06 |  | ● |  |  |  |  |  |  |  |  |  |  |  |  |
| P07 |  |  |  |  |  | ● |  |  | ● |  |  |  |  |  |
| S01 |  |  |  |  |  |  |  |  | ● |  | ● |  |  |  |
| S02 |  |  |  |  |  | ● |  |  |  |  | ● |  |  |  |
| S03 |  |  |  |  |  |  | ● |  |  |  | ● |  |  |  |
| S04 |  |  |  |  |  |  | ● | ● | ● |  |  |  |  |  |
| S05 |  |  |  |  | ● |  |  |  |  |  |  |  |  |  |
| S06 |  |  |  |  |  |  | ● |  |  |  | ● |  |  |  |
| S07 |  |  |  |  |  | ● |  |  | ● |  |  |  | ● |  |
| S08 | ● |  |  |  |  |  |  |  | ● |  |  |  |  |  |
| T01 |  | ● |  |  |  |  |  | ● | ● | ● |  |  |  |  |
| T02 |  | ● |  |  |  |  |  |  | ● |  | ● | ● |  |  |
| T03 |  |  |  |  |  |  |  | ● |  | ● |  |  |  |  |
| O01 |  |  | ● | ● |  |  |  |  |  |  |  |  |  |  |
| O02 |  |  | ● |  |  |  |  |  |  |  |  |  |  |  |
| O03 |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |
| R01 |  | ● |  |  |  |  |  | ● | ● |  |  |  |  |  |
| R02 | ● |  |  |  |  |  |  | ● | ● |  |  |  |  |  |
| R03 | ● | ● |  |  |  |  |  |  |  |  |  |  |  |  |
| R04 | ● |  |  |  |  |  |  |  | ● |  |  |  |  |  |
| R05 | ● |  |  |  |  |  |  |  |  |  |  |  |  | ● |

Bileşenlerin ayrıntısı ve sürümleri: [envanter.md](envanter.md).

## Mesh profili desteği

| Test | none | istio-ambient | istio-ambient-l7 | istio-sidecar | linkerd |
|---|---|---|---|---|---|
| P01 | ● | ● | ● | ● | ● |
| P02 | ● | ● | ● | ● | ● |
| P03 | ● | ● | ● | ● | ● |
| P04 | ● | ● | ● | ● | ● |
| P05 | ● | ● | ● | ● | ● |
| P06 | ● | ● | ● | ● | ● |
| P07 | ● | ● | ● | ● | ● |
| S01 | ● | ● | ● | ● | ● |
| S02 | ● | ● | ● | ● | ● |
| S03 | — | ● | ● | ● | ● |
| S04 | — | ● | ● | ● | ● |
| S05 | ● | ● | ● | ● | ● |
| S06 | ● | ● | ● | ● | ● |
| S07 | ● | ● | ● | ● | ● |
| S08 | — | ● | ● | ● | ● |
| T01 | ● | ● | ● | ● | ● |
| T02 | ● | ● | ● | ● | ● |
| T03 | — | ● | ● | ● | ● |
| O01 | — | ● | ● | ● | ● |
| O02 | ● | ● | ● | ● | ● |
| O03 | — | ● | ● | ● | ● |
| R01 | ● | ● | ● | ● | ● |
| R02 | — | ● | ● | ● | ● |
| R03 | ● | ● | ● | ● | ● |
| R04 | — | ● | ● | ● | ● |
| R05 | — | ● | ● | ● | ● |

— : test o profilde tanımlı değil (ör. mesh yokken kimlik bazlı yetki). Test tanımlı olduğu halde mesh'in yeteneği yoksa sonuç **uygulanamaz** olarak kaydedilir ve nedeni rapora yazılır.

## Performans

### P01

**Kademeli yük — gecikme ve kırılma noktası**

**Amaç.** Artan istek hızında (RPS) servis zincirinin gecikmesini (p50/p95/p99) ve hata oranını ölçmek; sistemin bozulmaya başladığı noktayı (kırılma noktası) bulmak. Mesh'siz referansla kıyaslanınca mesh'in gecikme ve kapasite maliyetini verir.

**Yöntem.** k6 (loadgen node'u, mesh içinde) gateway'e sabit hızlı (constant-arrival-rate) aşamalarla yük verir. Her aşama ayrı ölçülür. Her aşamada rol bazında CPU/bellek (cAdvisor; node toplamı dahil) ve mesh'in servis başına gecikmesi kaydedilir. İki kırılma noktası raporlanır: SLO noktası (p99 <= 100 ms, hata < %1, hedef hızın >= %95'i) ve doyma noktası (hata < %1, hız >= %95).

**Bileşenler.** k6, chainsvc zinciri (8 servis), Prometheus (mgmt), cAdvisor, mesh metrikleri

**Süre profilleri.** `quick`: 100,300,600,900 RPS x 30 sn; `full`: 100,250,500,750,1000,1250,1500,2000 RPS x 60 sn

**Çıktılar.** `stage<i>.p50_ms/p95_ms/p99_ms, stage<i>.rps, stage<i>.error_rate`; `stage<i>.<rol>.cpu_cores / mem_mib`; `knee_slo_rps, knee_sat_rps (kırılma noktaları), hop.<servis>.p50_ms`; `post_overload_healthy (aşırı yükten 30 sn sonra kendiliğinden toparlandı mı)`

**Başarı ölçütü.** İlk aşamada hata oranı < %1 (sistem düşük yükte sağlıklı)

Tanım: [`mesh-eval/tests/P01/`](../../mesh-eval/tests/P01/) · Çalıştırma: `meval test run P01`

### P02

**Sabit uzun yük (soak) — kararlılık ve sızıntı**

**Amaç.** Uzun süre sabit yük altında gecikmenin kayıp kaymadığını (drift) ve proxy'lerin bellek kullanımının büyümediğini (sızıntı) göstermek.

**Yöntem.** k6 sabit hızla yük verir; süre dört eşit çeyreğe bölünür. İlk ve son çeyreğin p99'u ile rol bazında bellek kullanımı kıyaslanır.

**Bileşenler.** k6, chainsvc zinciri, cAdvisor, Prometheus

**Süre profilleri.** `quick`: 200 RPS x 2 dk; `full`: 300 RPS x 20 dk

**Çıktılar.** `p50_ms`; `p99_ms`; `error_rate`; `p99_drift (son/ilk çeyrek)`; `<rol>.mem_growth_mib`

**Başarı ölçütü.** Hata oranı < %1 ve son çeyrek p99 <= max(1.5 x ilk çeyrek, ilk çeyrek + 10 ms)

Tanım: [`mesh-eval/tests/P02/`](../../mesh-eval/tests/P02/) · Çalıştırma: `meval test run P02`

### P03

**Ani yük (spike) — dayanım ve toparlanma**

**Amaç.** Ani trafik sıçramasında hata oranını ve sistemin normale dönme süresini ölçmek.

**Yöntem.** Üç aşama: düşük yük (100 RPS) -> ani sıçrama -> tekrar düşük yük. Sıçrama ve sonrası p99/hata ölçülür; toparlanma süresi, sıçrama bittikten sonra p99'un tekrar ilk aşamanın 2 katının altına indiği ana kadar geçen süredir (k6 canlı metrikleri, 5 sn çözünürlük).

**Bileşenler.** k6, chainsvc zinciri, Prometheus

**Süre profilleri.** `quick`: 100 -> 700 (20 sn) -> 100 RPS; `full`: 100 -> 1200 (30 sn) -> 100 RPS

**Çıktılar.** `before.p99_ms`; `spike.p99_ms`; `spike.error_rate`; `after.p99_ms`; `recovery_s`

**Başarı ölçütü.** Sıçrama sonrası aşamada hata oranı < %1

Tanım: [`mesh-eval/tests/P03/`](../../mesh-eval/tests/P03/) · Çalıştırma: `meval test run P03`

### P04

**Uçtan uca yol — edge -> DMZ -> ingress -> zincir**

**Amaç.** Gerçek kullanıcı yolundaki toplam gecikmeyi ölçmek (edge LB, DMZ ingress A/B, cluster-a ingress, mesh'li ingress -> gateway kenarı dahil) ve küme içi ölçümle (P01) kıyaslamak.

**Yöntem.** k6 host'ta, "internet" segmentinde (lab-edge network'ü) bir container olarak çalışır ve https://shop.localtest.me adresine edge LB üzerinden sabit hızlı aşamalarla yük verir.

**Bileşenler.** k6 (docker, lab-edge), HAProxy edge LB, DMZ ingress-nginx x2, cluster-a ingress-nginx, chainsvc zinciri

**Süre profilleri.** `quick`: 100, 250 RPS x 30 sn; `full`: 100, 250, 400 RPS x 60 sn

**Çıktılar.** `stage<i>.p50_ms/p95_ms/p99_ms/error_rate`

**Başarı ölçütü.** İlk aşamada hata oranı < %1

Tanım: [`mesh-eval/tests/P04/`](../../mesh-eval/tests/P04/) · Çalıştırma: `meval test run P04`

### P05

**Kaynak tüketimi — kalem kalem maliyet**

**Amaç.** Mesh'in her bileşeninin boşta ve sabit yük altında harcadığı CPU/belleği ve kapasite planlamasında "ayrılan" kaynak isteklerini (requests) ölçmek. Ambient / sidecar / Linkerd maliyet tablosunun ve prod projeksiyonunun ana girdisi.

**Yöntem.** Önce boşta (yük yok) bir pencere, sonra tüm mesh'lerde aynı sabit hızda (250 RPS) yük penceresi ölçülür. Roller: app, sidecar, ztunnel, waypoint, cni, control, node toplamı. Ayrıca kaynak istekleri (kube-state-metrics) ve konteyner sayıları kaydedilir.

**Bileşenler.** k6, cAdvisor, kube-state-metrics, Prometheus

**Süre profilleri.** `quick`: boşta 45 sn, 250 RPS x 90 sn; `full`: boşta 120 sn, 250 RPS x 300 sn

**Çıktılar.** `idle.<rol>.cpu_cores/mem_mib, load.<rol>.cpu_cores/mem_mib`; `req.<rol>.cpu_cores/mem_mib (ayrılan)`; `dataplane.cpu_per_1k_rps, dataplane.mem_per_pod_mib, node_overhead_cores`

**Başarı ölçütü.** Yük penceresinde hata oranı < %1

Tanım: [`mesh-eval/tests/P05/`](../../mesh-eval/tests/P05/) · Çalıştırma: `meval test run P05`

### P06

**Pod başlangıç süresi ve ölçeklenme hızı**

**Amaç.** Mesh'in yeni pod'ların hazır olma süresine etkisini ölçmek (sidecar enjeksiyonu, proxy başlatma, sertifika alma). Ani ölçeklenmede (HPA) ne kadar gecikme eklediğini gösterir.

**Yöntem.** shop namespace'inde (mesh'li) bağımsız bir test deployment'ı 0'dan N replikaya ölçeklenir. Her pod için oluşturulma -> Ready süresi ve tüm pod'ların hazır olma süresi ölçülür. İmajlar node'da önceden bulunur (indirme süresi ölçüme girmez).

**Bileşenler.** kube-apiserver, kubelet, mesh enjektörü / CNI, chainsvc

**Süre profilleri.** `quick`: 10 replika x 1 tur; `full`: 30 replika x 3 tur

**Çıktılar.** `ready_p50_s`; `ready_p95_s`; `ready_max_s`; `all_ready_s`

**Başarı ölçütü.** Tüm pod'lar 120 sn içinde hazır

Tanım: [`mesh-eval/tests/P06/`](../../mesh-eval/tests/P06/) · Çalıştırma: `meval test run P06`

### P07

**Politika yayılma süresi ve kontrol düzlemi ölçeği**

**Amaç.** Bir erişim kuralı değiştiğinde ne kadar sürede yürürlüğe girdiğini ölçmek; cluster'daki servis sayısı arttığında kontrol düzleminin ve proxy'lerin kaynak tüketiminin nasıl büyüdüğünü göstermek (3.000 servislik prod için ölçeklenme göstergesi).

**Yöntem.** (1) probe-rogue -> order erişimini kesen kural uygulanır; erişimin kesildiği an (pod içinden 100 ms aralıkla yoklama) ölçülür; kural kaldırılır, erişimin geri geldiği an ölçülür (3 tekrar, medyan). Mesh yoksa NetworkPolicy, mesh'lerde mesh'in yetki politikası kullanılır. (2) Ayrı bir mesh'li namespace'e N servis (1 replika) eklenir; kontrol düzlemi ve shop proxy'lerinin belleği öncesi/sonrası kıyaslanır. (3) Ölçüm (1) N servis varken tekrarlanır.

**Bileşenler.** mesh kontrol düzlemi (istiod / linkerd-destination), proxy'ler, kube-network-policies (none)

**Süre profilleri.** `quick`: N = 30 servis; `full`: N = 120 servis

**Çıktılar.** `deny_s`; `allow_s`; `scaled.deny_s`; `scaled.allow_s`; `control.mem_growth_mib`; `sidecar.mem_per_container_growth_mib`

**Başarı ölçütü.** Kural 30 sn içinde yürürlüğe girer ve kaldırıldığında erişim geri gelir

Tanım: [`mesh-eval/tests/P07/`](../../mesh-eval/tests/P07/) · Çalıştırma: `meval test run P07`

## Güvenlik

### S01

**mTLS zorunluluğu ve hat üzerinde şifreleme**

**Amaç.** Servisler arası trafiğin (1) mesh dışından şifresiz erişime kapalı olduğunu ve (2) ağ üzerinde gerçekten şifreli aktığını kanıtlamak. PCI DSS segmentasyon ve "iletimde şifreleme" kanıtı.

**Yöntem.** (1) Mesh dışı bir namespace'teki pod order servisine düz HTTP ile bağlanmayı dener. (2) Servis node'unda host ağında çalışan tcpdump, probe-gateway -> order isteklerine eklenen benzersiz bir işaret metnini (X-Meval-Marker başlığı) ağ paketlerinde arar. İşaret görünüyorsa trafik şifresizdir.

**Bileşenler.** tcpdump (netshoot, hostNetwork), mesh proxy'leri, PeerAuthentication / default-inbound-policy

**Çıktılar.** `plaintext_from_outside`; `marker_packets`

**Başarı ölçütü.** Mesh dışı düz erişim reddedilir ve işaret metni ağda görünmez

Tanım: [`mesh-eval/tests/S01/`](../../mesh-eval/tests/S01/) · Çalıştırma: `meval test run S01`

### S02

**Servisler arası whitelisting — NetworkPolicy (L3/L4)**

**Amaç.** Kubernetes NetworkPolicy ile servisler arası izin listesinin (varsayılan ret + zincir kuralları) her mesh ile birlikte doğru çalıştığını ve mesh'e özel ek kural gerekip gerekmediğini göstermek. Etiket bazlı kuralların "kimlik taklidi"ne açık olduğunu kanıtlamak.

**Yöntem.** (1) Standart kural seti (mesh'ten habersiz) uygulanır; zincir, uçtan uca erişim ve pod sağlığı kontrol edilir (mesh ile uyumsuzluk bulgusu). (2) Gerekiyorsa mesh'e uyarlanmış ek kurallar uygulanır. (3) İzin/ret matrisi: izinli kenarlar açık, yetkisiz pod, başka namespace ve yatay geçiş kapalı olmalı. (4) Etiketi "gateway" olan ama kimliği farklı bir pod (impostor) order'a erişmeye çalışır.

**Bileşenler.** kindnet / kube-network-policies (NetworkPolicy motoru), netshoot istemcileri

**Çıktılar.** `naive.chain`; `naive.e2e`; `naive.ready`; `matris kontrolleri`; `impostor_access`

**Başarı ölçütü.** Uyarlanmış kurallarla izin/ret matrisinin tamamı beklendiği gibi

Tanım: [`mesh-eval/tests/S02/`](../../mesh-eval/tests/S02/) · Çalıştırma: `meval test run S02`

### S03

**Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası)**

**Amaç.** Servisler arası erişimi IP/etiket yerine kriptografik kimlikle (ServiceAccount, mTLS sertifikası) kısıtlamak: varsayılan ret + her servis için izinli çağıranlar listesi. NetworkPolicy'den (S02) farkı: etiket taklidi işe yaramaz.

**Yöntem.** Kenar listesi (lib/policy.sh, AUTHZ_EDGES) mesh'in politika diline çevrilip uygulanır: Istio AuthorizationPolicy (sidecar/ambient: pod seçici; ambient+waypoint: Service hedefli), Linkerd Server + MeshTLSAuthentication + AuthorizationPolicy. İzin/ret matrisi ve kimlik taklidi (impostor: etiket gateway, kimlik rogue) denenir.

**Bileşenler.** mesh yetki politikası, mTLS kimlikleri, netshoot istemcileri

**Çıktılar.** `policy_objects`; `matris kontrolleri`; `impostor_access`

**Başarı ölçütü.** İzin/ret matrisinin tamamı beklendiği gibi, kimlik taklidi reddedilir, pod'lar sağlıklı

Tanım: [`mesh-eval/tests/S03/`](../../mesh-eval/tests/S03/) · Çalıştırma: `meval test run S03`

### S04

**Endpoint bazlı erişim kısıtı (L7 — path / method)**

**Amaç.** Bir servisin yalnızca belirli endpoint'lerinin, belirli kimliklere ve HTTP metotlarına açık olmasını sağlamak (ör. /admin kapalı, yalnızca GET). Mesh içinde endpoint bazlı whitelisting.

**Yöntem.** order servisi için kural: yalnızca gateway kimliği, yalnızca GET, yalnızca "/" ve "/api/*". /admin, POST, DELETE ve başka kimlik reddedilmeli. Önce kural tek başına uygulanır; kubelet sağlık kontrollerini bozuyorsa (bulgu) gerekli ek kural eklenir. Ambient L4 (waypoint'siz) profilde L7 kural uygulanamaz; gözlenen davranış kaydedilir.

**Bileşenler.** Istio AuthorizationPolicy (sidecar / waypoint), Linkerd HTTPRoute + AuthorizationPolicy

**Çıktılar.** `matris kontrolleri`; `probe_fix_needed`

**Başarı ölçütü.** İzinli endpoint'ler açık, diğerleri reddedilir, zincir çalışır

Tanım: [`mesh-eval/tests/S04/`](../../mesh-eval/tests/S04/) · Çalıştırma: `meval test run S04`

### S05

**Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress)**

**Amaç.** Dışarıya açık bir endpoint'in (ör. /admin) yalnızca izinli kaynak IP'lerinden erişilebilir olmasını DMZ katmanında sağlamak; istemci IP'sinin sahte X-Forwarded-For başlığıyla taklit edilemediğini kanıtlamak. Mesh'ten bağımsızdır (DMZ cluster'larında mesh yok); her profilde aynı sonuç beklenir.

**Yöntem.** dmz-a ve dmz-b'de shop.localtest.me/admin için whitelist-source-range kuralı tanımlanır. (1) İzinsiz aralık: /admin 403, / 200. (2) Sahte X-Forwarded-For ile /admin hâlâ 403. (3) Edge segmenti (lab-edge) izinli yapılınca /admin 200. İstemci IP'si edge LB'den PROXY protocol ile gelir.

**Bileşenler.** HAProxy edge LB (PROXY protocol), DMZ ingress-nginx x2

**Çıktılar.** `matris kontrolleri`

**Başarı ölçütü.** Tüm kontroller beklendiği gibi

Tanım: [`mesh-eval/tests/S05/`](../../mesh-eval/tests/S05/) · Çalıştırma: `meval test run S05`

### S06

**Politika atlatma denemeleri**

**Amaç.** Yetki kurallarının (S03) yalnızca "doğru yoldan" gelen trafikte değil, kötü niyetli denemelerde de geçerli olduğunu kanıtlamak: mesh dışı pod, mesh'ten çıkarılmış pod (aynı kimlikle), host ağı, doğrudan pod IP'si, sahte kimlik başlıkları, proxy yönetim portları.

**Yöntem.** S03'ün kimlik politikası uygulanır; ardından her deneme order servisine/pod'una yapılır. Mesh yoksa (none) aynı denemeler politikasız ortamda yapılır (risk görünürlüğü).

**Bileşenler.** mesh yetki politikası, mTLS, netshoot (hostNetwork dahil)

**Çıktılar.** `her deneme için izin/ret`; `admin_ports`

**Başarı ölçütü.** Tüm denemeler reddedilir

Tanım: [`mesh-eval/tests/S06/`](../../mesh-eval/tests/S06/) · Çalıştırma: `meval test run S06`

### S07

**Dış çıkış (egress) whitelisting**

**Amaç.** Servislerin yalnızca izinli dış adreslere (FQDN) çıkabilmesini sağlamak; prod'daki ayrı dış çıkış zone'unun cluster içi karşılığı. Hangi mesh'in FQDN bazlı egress kısıtı yapabildiğini göstermek.

**Yöntem.** Cluster dışında (lab-app segmenti) iki HTTPS sunucusu: izinli allowed.ext.test, izinsiz denied.ext.test (adlar cluster DNS'inde; internet bağımlılığı yok). Mesh'e göre yöntem: none: NetworkPolicy (yalnızca IP bazlı, DNS'ten çözülen IP'ler); istio-sidecar: Sidecar kaynağı REGISTRY_ONLY + ServiceEntry; istio-ambient(-l7): ServiceEntry (ztunnel'de REGISTRY_ONLY yok — gözlenen davranış kaydedilir); linkerd: EgressNetwork (trafficPolicy: Deny) + TLSRoute.

**Bileşenler.** NetworkPolicy, Istio Sidecar/ServiceEntry, Linkerd EgressNetwork, CoreDNS hosts, nginx dış hedefleri

**Çıktılar.** `allowed_ok`; `denied_blocked`; `method`

**Başarı ölçütü.** İzinli hedef açık, izinsiz hedef kapalı

Tanım: [`mesh-eval/tests/S07/`](../../mesh-eval/tests/S07/) · Çalıştırma: `meval test run S07`

### S08

**Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu**

**Amaç.** İş yükü sertifikalarının bizim (kurumsal) CA'mızdan imzalandığını, kısa ömürlü olduğunu ve otomatik yenilendiğini; ara CA (issuer) yük altında değiştirildiğinde trafik kesilmediğini göstermek. Prod'da Vault gibi kurumsal CA ile entegrasyonun lab karşılığı.

**Yöntem.** (1) order pod'unun iş yükü sertifikası mesh aracıyla alınır (istioctl / linkerd identity): veren CA, geçerlilik süresi, SPIFFE kimliği. (2) 200 RPS sabit yük altında, aynı kök CA ile yeni bir ara CA üretilip mesh'e verilir; order yeniden başlatılır. Yeni pod'un sertifikası yeni ara CA'dan gelmeli, eski ve yeni sertifikalı pod'lar konuşabilmeli, yükte hata oluşmamalı.

**Bileşenler.** mesh CA (istiod / linkerd-identity), plug-in CA (lib/pki.sh), k6

**Çıktılar.** `cert_ttl_h`; `issuer_cn`; `rotation.error_rate`; `rotation.new_issuer_ok`; `rotation.needed_restart`

**Başarı ölçütü.** Sertifika kurumsal ara CA'dan, ömür <= 24 sa, rotasyonda hata oranı < %1 ve yeni issuer

Tanım: [`mesh-eval/tests/S08/`](../../mesh-eval/tests/S08/) · Çalıştırma: `meval test run S08`

## Trafik yönetimi

### T01

**Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma**

**Amaç.** Yeni sürümü (canary) kullanıcıların küçük bir kısmına açabilmek, belirli istekleri (başlık) yeni sürüme yönlendirebilmek ve gerçek trafiği yeni sürüme kopyalayıp (mirroring) cevabı kullanmadan deneyebilmek. Tüm mesh'lerde aynı standart (Gateway API HTTPRoute, GAMMA) kullanılır.

**Yöntem.** catalog'un v2 sürümü ayrı deployment olarak açılır (catalog-v1 / catalog-v2 servisleri). (1) %90/%10 ağırlık: 400 istekte v2 oranı ölçülür. (2) "x-canary: true" başlıklı istekler %100 v2. (3) Tüm trafik v1'e giderken v2'ye yansıtılır: cevaplar v1, v2'ye gelen istek sayısı ölçülür. Mesh yoksa yalnızca replika sayısıyla orantılı dağılım mümkündür (referans).

**Bileşenler.** Gateway API HTTPRoute (GAMMA), Istio (sidecar / waypoint), Linkerd, chainsvc v1/v2

**Çıktılar.** `weighted.v2_share`; `header.v2_share`; `mirror.supported`; `mirror.v2_received`

**Başarı ölçütü.** Ağırlıklı yönlendirmede v2 payı %10 ± 5 puan, başlıklı isteklerin tamamı v2

Tanım: [`mesh-eval/tests/T01/`](../../mesh-eval/tests/T01/) · Çalıştırma: `meval test run T01`

### T02

**Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği**

**Amaç.** Prod'daki protokollerin mesh'ten sorunsuz geçtiğini göstermek: (1) gRPC / HTTP2'de istek bazlı yük dağılımı (kube-proxy bağlantı bazlı dağıtır, uzun ömürlü bağlantı tek pod'a yapışır); (2) bağlantıyı önce sunucunun konuştuğu protokoller (SMTP, MySQL benzeri; Oracle/MSSQL/Kafka gibi TCP protokolleri için gösterge) — protokol algılama gecikmesi; (3) Redis / Postgres TCP trafiği.

**Yöntem.** (1) fraud 3 replikaya çıkarılır; payment'a 300 istek atılır (payment -> fraud gRPC, kalıcı bağlantı); cevaplardaki fraud pod IP'lerinin dağılımı ölçülür. (2) banner servisine (bağlanınca sunucu yazar) protokol ipucu olan (appProtocol: tcp) ve olmayan port üzerinden bağlanılıp ilk baytın gelme süresi ölçülür. (3) data cluster'ındaki Redis'e PING, Postgres'e TCP bağlantısı.

**Bileşenler.** chainsvc gRPC, socat (banner), data cluster Redis/Postgres, mesh protokol algılama

**Çıktılar.** `grpc.pods_used`; `grpc.max_share`; `banner.hint_ms`; `banner.nohint_ms`; `redis_ok`; `postgres_ok`

**Başarı ölçütü.** Redis/Postgres erişimi çalışır, protokol ipuçlu server-first bağlantı < 1 sn

Tanım: [`mesh-eval/tests/T02/`](../../mesh-eval/tests/T02/) · Çalıştırma: `meval test run T02`

### T03

**Gateway API ile giriş (ingress-nginx'in yerine geçme)**

**Amaç.** ingress-nginx Mart 2026'da emekliye ayrıldı. Mesh'in kendi Gateway API uygulamasının küme girişini (north-south) üstlenip üstlenemeyeceğini göstermek: ayrı bir ingress ürününe gerek kalır mı?

**Yöntem.** shop namespace'inde Gateway (gatewayClassName: istio) + HTTPRoute ile gateway servisi yayınlanır; mesh dışı bir pod'dan erişilir ve zincirin tamamının çalıştığı doğrulanır. Linkerd'de giriş için Gateway API uygulaması yoktur (yalnızca mesh içi GAMMA); ayrı bir ürün gerekir.

**Bileşenler.** Gateway API v1.6, Istio gateway (Envoy), HTTPRoute

**Çıktılar.** `gateway_programmed`; `route_accepted`; `chain_ok`; `p50_ms`

**Başarı ölçütü.** Gateway hazır, route kabul edildi, zincir mesh dışından erişilebilir

Tanım: [`mesh-eval/tests/T03/`](../../mesh-eval/tests/T03/) · Çalıştırma: `meval test run T03`

## Gözlemlenebilirlik

### O01

**Gözlemlenebilirlik — hazır metrikler, doğruluk, dağıtık izleme, erişim logu**

**Amaç.** Mesh'in uygulama koduna dokunmadan ne kadar görünürlük sağladığını ölçmek: her servis için "altın metrikler" (istek hızı, başarı oranı, gecikme), mesh'in ölçtüğü gecikmenin doğruluğu (k6'ya göre), uçtan uca trace (Tempo) ve erişim logu.

**Yöntem.** 100 RPS yük altında: (1) 8 servisin kaçı için mesh L7 metrikleri (istek/başarı/gecikme histogramı) veya yalnızca L4 (TCP) metrikleri var; (2) gateway'de mesh'in p99'u / k6 p99 oranı; (3) tracing geçici olarak açılır (Istio Telemetry API %100 örnekleme -> Tempo; Linkerd linkerd-jaeger eklentisi -> Tempo; uygulama B3 başlıklarını taşır) ve bir trace'teki span / servis sayısı ölçülür; (4) erişim logu açılıp proxy logunda istek satırı aranır.

**Bileşenler.** mesh metrikleri, Prometheus, Tempo (mgmt), Grafana datasource proxy, Istio Telemetry API, linkerd-jaeger

**Çıktılar.** `services_l7_metrics`; `services_l4_metrics`; `latency_accuracy_ratio`; `trace.spans`; `trace.services`; `trace.mesh_spans`; `access_log`

**Başarı ölçütü.** Tüm servisler için en az L4 metrik var ve trace Tempo'da bulunur

Tanım: [`mesh-eval/tests/O01/`](../../mesh-eval/tests/O01/) · Çalıştırma: `meval test run O01`

### O02

**Metrik maliyeti — seri sayısı ve alım hızı**

**Amaç.** Mesh metriklerinin izleme altyapısına (Prometheus) getirdiği gizli maliyeti ölçmek: aktif zaman serisi sayısı ve saniyede alınan örnek sayısı. Prod'da 3.000 servise projeksiyonun girdisi.

**Yöntem.** 60 sn 100 RPS yükten sonra bench cluster'ından (bu mesh profili etiketiyle) gelen aktif seri sayısı toplam ve mesh'e ait metrik aileleri (istio_*, envoy_*, linkerd proxy işleri) olarak ayrılır; agent'ın remote-write örnek hızı ölçülür. Mesh'siz profil referanstır.

**Bileşenler.** Prometheus agent (bench), Prometheus (mgmt), mesh metrik uçları

**Çıktılar.** `series_total`; `series_mesh`; `series_mesh_per_pod`; `samples_per_s`

**Başarı ölçütü.** Ölçüm tamamlanır (bilgi amaçlı)

Tanım: [`mesh-eval/tests/O02/`](../../mesh-eval/tests/O02/) · Çalıştırma: `meval test run O02`

## Operasyon

### O03

**Operasyon envanteri — karmaşıklık ve ayrıcalık**

**Amaç.** Mesh'in işletme yükünü nesnel göstergelerle kaydetmek: CRD sayısı, kontrol düzlemi ve node ajanı bileşenleri, kullanılan imajlar, webhook'lar, uygulama pod'una eklenen konteynerler, ayrıcalıklı (NET_ADMIN / privileged) gereksinimler, kurulum süresi ve tanılama aracının sonucu.

**Yöntem.** Kurulu mesh'in Kubernetes nesneleri sayılır; istioctl analyze / linkerd check çalıştırılır.

**Bileşenler.** kubectl, istioctl, linkerd CLI

**Çıktılar.** `crds`; `control_plane_pods`; `node_agents`; `images`; `webhooks`; `added_containers_per_pod`; `privileged_components`; `install_s`; `diag_issues`

**Başarı ölçütü.** Tanılama aracında hata yok

Tanım: [`mesh-eval/tests/O03/`](../../mesh-eval/tests/O03/) · Çalıştırma: `meval test run O03`

## Dayanıklılık

### R01

**Timeout, retry ve outlier detection (circuit breaking)**

**Amaç.** (A) Bir alt servis yavaşladığında mesh'in timeout + retry politikasının uçtan uca gecikmeyi sınırladığını ve retry'ların yükü ne kadar artırdığını (amplifikasyon) ölçmek. (B) Hatalı bir replika (sürekli 503) devredeyken outlier detection'ın onu devreden çıkardığını göstermek.

**Yöntem.** 100 RPS sabit yük. (A) pricing isteklerinin %20'si 1 sn gecikir; önce politikasız, sonra inventory -> pricing için timeout 500 ms / deneme başına 150 ms / 2 retry. pricing'e gelen istek sayısı / gateway istek sayısı = amplifikasyon. (B) pricing'e sürekli 503 dönen 1 replika eklenir (2 sağlam + 1 hatalı); önce politikasız, sonra outlier detection (Istio DestinationRule / Linkerd failure accrual) ile hata oranı ölçülür.

**Bileşenler.** Istio VirtualService + DestinationRule (sidecar / waypoint), Linkerd HTTPRoute retry/timeout + failure accrual, chainsvc hata enjeksiyonu

**Çıktılar.** `A.none.p99_ms`; `A.policy.p99_ms`; `A.amplification`; `B.none.error_rate`; `B.policy.error_rate`

**Başarı ölçütü.** Politikayla p99 < 1000 ms ve outlier detection ile hata oranı yarıdan fazla düşer

Tanım: [`mesh-eval/tests/R01/`](../../mesh-eval/tests/R01/) · Çalıştırma: `meval test run R01`

### R02

**Hata enjeksiyonu (fault injection)**

**Amaç.** Uygulama koduna dokunmadan, mesh üzerinden kontrollü hata ve gecikme enjekte edebilmek (kaos testi, dayanıklılık tatbikatı). Mesh'lerin bu yeteneğini ve doğruluğunu kıyaslamak.

**Yöntem.** catalog'a giden isteklerin %10'una 503, %10'una 200 ms gecikme enjekte edilir; 100 RPS yükte gateway'de gözlenen hata oranı ve gecikme dağılımı ölçülür. Istio: VirtualService fault. Linkerd'de yerleşik hata enjeksiyonu yoktur; önerilen yöntemle (HTTPRoute ağırlıklı yönlendirme ile hatalı / yavaş backend) yapılır.

**Bileşenler.** Istio VirtualService (sidecar / waypoint), Linkerd HTTPRoute + hatalı backend'ler, k6

**Çıktılar.** `observed_error_rate`; `p50_ms`; `p95_ms`; `method`

**Başarı ölçütü.** Gözlenen hata oranı %10 ± 3 puan ve p95 >= 200 ms

Tanım: [`mesh-eval/tests/R02/`](../../mesh-eval/tests/R02/) · Çalıştırma: `meval test run R02`

### R03

**Yük altında pod kaybı (failover)**

**Amaç.** Yük altındayken servis replikaları kaybedildiğinde (deploy, node bakımı, çökme) kullanıcıya yansıyan hata sayısını ölçmek. Mesh'in bağlantı yönetimi / yeniden deneme davranışının etkisi.

**Yöntem.** 200 RPS sabit yük sürerken sırayla order (HTTP), catalog (zincirin sonu) ve fraud (gRPC) servislerinin birer pod'u silinir. Toplam başarısız istek, hata oranı ve p99 ölçülür.

**Bileşenler.** k6, kube-proxy / mesh uç nokta yönetimi, chainsvc

**Çıktılar.** `failed_requests`; `error_rate`; `p99_ms`

**Başarı ölçütü.** Hata oranı < %1

Tanım: [`mesh-eval/tests/R03/`](../../mesh-eval/tests/R03/) · Çalıştırma: `meval test run R03`

### R04

**Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması**

**Amaç.** "Mesh tek hata noktası mı?" sorusunu cevaplamak. (A) Kontrol düzlemi tamamen düştüğünde mevcut trafik akıyor mu, yeni pod'lar açılabiliyor ve trafik alabiliyor mu? (B) Ambient'te node başına paylaşılan ztunnel yeniden başlarsa o node'daki tüm pod'lar ne kadar etkilenir (arıza etki alanı)?

**Yöntem.** 150 RPS sabit yük. (A) Kontrol düzlemi deployment'ları 0'a indirilir (istiod / linkerd-destination, -identity, -proxy-injector); 20 sn sonra catalog bir replika ölçeklenir; yeni pod'un oluşturulup oluşturulmadığı, mesh'e girip girmediği ve trafik alıp alamadığı kontrol edilir; 45 sn sonra kontrol düzlemi geri getirilir. (B, yalnızca ambient) app node'undaki ztunnel pod'u silinir; hata sayısı ölçülür.

**Bileşenler.** istiod / linkerd kontrol düzlemi, ztunnel, mutating webhook'lar, k6

**Çıktılar.** `A.error_rate`; `A.new_pod_created`; `A.new_pod_meshed`; `A.new_pod_serving`; `B.failed_requests`; `B.error_rate`

**Başarı ölçütü.** Kontrol düzlemi kaybında mevcut trafikte hata oranı < %1

Tanım: [`mesh-eval/tests/R04/`](../../mesh-eval/tests/R04/) · Çalıştırma: `meval test run R04`

### R05

**Yük altında kesintisiz mesh güncellemesi**

**Amaç.** Mesh sürüm güncellemesinin (yılda birkaç kez zorunlu) iş trafiğini kesip kesmediğini, ne kadar sürdüğünü ve hangi adımları gerektirdiğini ölçmek. Sidecar ile ambient arasındaki en büyük operasyonel fark beklenen kalem.

**Yöntem.** Mesh bir önceki sürümle (Istio 1.30.x / Linkerd bir önceki edge) yeniden kurulur, uygulama mesh'e alınır. 150 RPS sabit yük sürerken hedef sürüme güncellenir: sidecar: revizyonlu (canary) kontrol düzlemi + varsayılan etiketin taşınması + tüm deployment'ların sırayla yeniden başlatılması; ambient: helm ile yerinde güncelleme (base, istiod, istio-cni, ztunnel); linkerd: linkerd upgrade + deployment'ların yeniden başlatılması. Güncelleme süresi, adım sayısı, yeniden başlatılan pod sayısı ve başarısız istekler ölçülür.

**Bileşenler.** helm / istioctl / linkerd CLI, k6, tüm veri düzlemi

**Çıktılar.** `upgrade_duration_s`; `steps`; `restarted_pods`; `failed_requests`; `error_rate`

**Başarı ölçütü.** Güncelleme sırasında hata oranı < %1 ve sonunda tüm proxy'ler yeni sürümde

Tanım: [`mesh-eval/tests/R05/`](../../mesh-eval/tests/R05/) · Çalıştırma: `meval test run R05`

