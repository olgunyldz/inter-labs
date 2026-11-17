# Service Mesh Değerlendirme Raporu

Oluşturma: 17.11.2026 12:58 · Oturum: degerlendirme-1 · Profil: full

> Grafikli tam sürüm: `rapor.html`

## 1. Yönetici özeti

- Puan kartı sıralaması (eşit ağırlık): Istio ambient + waypoint (L7) 78, Istio sidecar 72, Istio ambient (L4) 71, Linkerd 68.
- Istio ambient (L4): SLO (p99 ≤ 100 ms) kapasitesi yaklaşık 1 028 RPS (mesh'siz referansa göre %65).
- Istio ambient + waypoint (L7): SLO (p99 ≤ 100 ms) kapasitesi yaklaşık 400 RPS (mesh'siz referansa göre %25).
- Istio sidecar: SLO (p99 ≤ 100 ms) kapasitesi yaklaşık 255 RPS (mesh'siz referansa göre %16).
- Linkerd: SLO (p99 ≤ 100 ms) kapasitesi yaklaşık 380 RPS (mesh'siz referansa göre %24).
- 3.000 servis projeksiyonu: veri düzlemi belleği ambient 16.2 GiB, sidecar 823 GiB; ayrılan (requests) CPU ambient 90.0, sidecar 900 çekirdek.
- Istio ambient (L4): başarısız/kısmi R03, S02, S06; yetenek yok R01, R02, S04, S07, T01.
- Istio ambient + waypoint (L7): başarısız/kısmi P03, S02, S06, S08; yetenek yok S07.
- Istio sidecar: başarısız/kısmi S02; yetenek yok —.
- Linkerd: başarısız/kısmi R02, R05; yetenek yok T03.
- Toplam 60 bulgu kaydedildi (bölüm 6).

## 2. Puan kartı

| Kategori | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|
| Performans | 91.7 | 63.4 | 53.2 | 70.9 |
| Kaynak maliyeti | 100 | 61.4 | 22.3 | 27.7 |
| Güvenlik | 65.9 | 74.6 | 98.4 | 100 |
| Dayanıklılık | 66.7 | 66.7 | 66.7 | 61.1 |
| Trafik yönetimi | 45.3 | 99.1 | 100 | 54.5 |
| Gözlemlenebilirlik | 50.0 | 100 | 100 | 100 |
| Operasyon | 79.2 | 79.2 | 66.7 | 62.5 |
| **Toplam** | **71.2** | **77.8** | **72.5** | **68.1** |

## 3. Maliyet: kalem kalem

| Kalem | Kaynak | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---|---:|---:|---:|---:|
| Veri düzlemi CPU, 250 RPS yükte | P05 | 0.272 çekirdek | 0.979 çekirdek | 1.80 çekirdek | 0.962 çekirdek |
| 1000 servis isteği başına veri düzlemi CPU | P05 | 0.136 çekirdek | 0.489 çekirdek | 0.902 çekirdek | 0.481 çekirdek |
| Veri düzlemi belleği, yüksüz an (toplam, önceki yük testlerinden sonra) | P05 | 164 MiB | 226 MiB | 1 799 MiB | 177 MiB |
| Uygulama pod'u başına veri düzlemi belleği | P05 | 8.64 MiB | 11.9 MiB | 94.7 MiB | 9.34 MiB |
| Pod başına ayrılan CPU (requests) | P05 | 0.047 çekirdek | 0.050 çekirdek | 0.100 çekirdek | 0 çekirdek |
| Pod başına ayrılan bellek (requests) | P05 | 96.6 MiB | 98.2 MiB | 128 MiB | 0 MiB |
| Servis node'unda app+proxy dışı CPU (kernel/ağ) | P05 | 0.026 çekirdek | 0.028 çekirdek | 0.137 çekirdek | 0.109 çekirdek |
| Kontrol düzlemi belleği | P05 | 61.7 MiB | 63.2 MiB | 70.2 MiB | 78.8 MiB |
| Kontrol düzlemi büyümesi (N servis eklenince) | P07 | -2.00 MiB | -3.40 MiB | 151 MiB | 5.40 MiB |
| Her proxy'nin büyümesi (N servis eklenince) | P07 | — | — | 2.55 MiB | -0.080 MiB |
| Orta yükte uçtan uca p99 | P01 | 17.8 ms | 24.4 ms | 62.7 ms | 25.9 ms |
| SLO kırılma noktası (aşamalar arası tahmin) | P01 | 1 028 RPS | 400 RPS | 255 RPS | 380 RPS |
| SLO'yu sağlayan en yüksek aşama | P01 | 1 000 RPS | 250 RPS | 250 RPS | 250 RPS |
| Pod hazır olma süresi (medyan) | P06 | 4.00 sn | 3.00 sn | 11.0 sn | 7.00 sn |
| Güncellemede yeniden başlatılan uygulama pod'u | R05 | 0 adet | 1.00 adet | 19.0 adet | 19.0 adet |
| Güncelleme süresi | R05 | 59.0 sn | 78.0 sn | 122 sn | 103 sn |
| Güncelleme sırasında başarısız istek | R05 | 0 istek | 2.00 istek | 81.0 istek | 767 istek |
| Node proxy'si yeniden başlarken başarısız istek | R04 | 0 istek | 2.00 istek | — | — |
| Pod başına metrik serisi | O02 | 30.1 seri | 308 seri | 804 seri | 1 249 seri |
| Pod'a eklenen konteyner | O03 | 0 adet | 0 adet | 2.00 adet | 2.00 adet |
| Ayrıcalıklı (NET_ADMIN/privileged) bileşen türü | O03 | 2.00 adet | 2.00 adet | 1.00 adet | 2.00 adet |
| CRD sayısı | O03 | 15.0 adet | 15.0 adet | 15.0 adet | 10.0 adet |

## 4. Prod projeksiyonu (3.000 servis)

| Varsayım | Değer |
|---|---|
| Servis | 3000 |
| Servis başına replika | 3.00 |
| Pod | 9000 |
| Node başına pod | 30.0 |
| Node | 300 |
| Node boyutu | 16 vCPU / 64 GB |
| Toplam servisler arası istek hızı | 30000 RPS |
| Waypoint başına servis (ambient L7) | 10 |
| Waypoint | 300 |

| Kalem | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|
| Veri düzlemi belleği | 16.2 GiB | 35.8 GiB | 823 GiB | 83.1 GiB |
| Veri düzlemi CPU | 4.08 çekirdek | 14.7 çekirdek | 27.0 çekirdek | 14.4 çekirdek |
| Ayrılan CPU | 90.0 çekirdek | 120 çekirdek | 900 çekirdek | 0 çekirdek |
| Ayrılan bellek | 179 GiB | 217 GiB | 1 125 GiB | 0 GiB |
| Node eşdeğeri (kullanılan) | 0.255 node | 0.918 node | 21.7 node | 1.30 node |
| Node eşdeğeri (ayrılan) | 5.63 node | 7.50 node | 56.2 node | 0 node |

## 5. Test sonuç matrisi

| Test | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---|---|---|---|---|
| P01 Kademeli yük — gecikme ve kırılma noktası | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P02 Sabit uzun yük (soak) — kararlılık ve sızıntı | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P03 Ani yük (spike) — dayanım ve toparlanma | ✅ Geçti | ✅ Geçti | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| P04 Uçtan uca yol — edge -> DMZ -> ingress -> zincir | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P05 Kaynak tüketimi — kalem kalem maliyet | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P06 Pod başlangıç süresi ve ölçeklenme hızı | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P07 Politika yayılma süresi ve kontrol düzlemi ölçeği | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S01 mTLS zorunluluğu ve hat üzerinde şifreleme | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S02 Servisler arası whitelisting — NetworkPolicy (L3/L4) | ✅ Geçti | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ✅ Geçti |
| S03 Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası) | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S04 Endpoint bazlı erişim kısıtı (L7 — path / method) | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S05 Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress) | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S06 Politika atlatma denemeleri | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| S07 Dış çıkış (egress) whitelisting | ✅ Geçti | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti |
| S08 Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu | ➖ Uygulanamaz | ✅ Geçti | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| R01 Timeout, retry ve outlier detection (circuit breaking) | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| R02 Hata enjeksiyonu (fault injection) | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ⚠️ Kısmen / başarısız |
| R03 Yük altında pod kaybı (failover) | ✅ Geçti | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| R04 Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| R05 Yük altında kesintisiz mesh güncellemesi | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ⚠️ Kısmen / başarısız |
| T01 Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| T02 Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| T03 Gateway API ile giriş (ingress-nginx'in yerine geçme) | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ➖ Uygulanamaz |
| O01 Gözlemlenebilirlik — hazır metrikler, doğruluk, dağıtık izleme, erişim logu | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| O02 Metrik maliyeti — seri sayısı ve alım hızı | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| O03 Operasyon envanteri — karmaşıklık ve ayrıcalık | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |

## 6. Bulgular


### Mesh yok (referans)

- **P01** — Doyma noktasına ulaşılmadı: en yüksek aşama (2000 RPS) hatasız karşılandı; profil 'full' ile daha yüksek hızlar denenebilir.
- **R01** — none: 3 replikadan 1'i sürekli hata verirken uçtan uca hata oranı %100 (replika oranına göre beklenen ~%33). Hızlı hata dönen replika yük dengeleyici tarafından tercih ediliyor; outlier detection / failure accrual olmadan hatalı pod trafiği çeker.
- **S01** — Servisler arası trafik ağda düz metin: başlıklar ve gövde node üzerinde okunabiliyor (40 paket).
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S07** — Mesh'siz egress kısıtı yalnızca IP bazlı yapılabilir: hedefin IP'si değiştiğinde (CDN, bulut servisleri) kural bozulur ve aynı IP'yi paylaşan başka adresler de açılır.
- **T02** — none: gRPC (HTTP/2 kalıcı bağlantı) trafiği istek bazlı dağıtılmıyor: 3 pod'dan 1 tanesi trafik aldı, en yüklü pod payı 1.000. Bağlantı bazlı (L4) dengeleme.

### Istio ambient (L4)

- **O01** — istio-ambient: 0/8 servis için L7 (istek, başarı oranı, gecikme) metriği var; diğerleri için yalnızca TCP metrikleri. Altın metrikler için L7 proxy (waypoint) gerekir.
- **O01** — istio-ambient: trace yalnızca uygulamanın ürettiği span'lardan oluştu; mesh proxy'leri span üretmedi (servisler: catalog,fraud,gateway,inventory,ledger,order,payment,pricing).
- **R01** — istio-ambient: 3 replikadan 1'i sürekli hata verirken uçtan uca hata oranı %100 (replika oranına göre beklenen ~%33). Hızlı hata dönen replika yük dengeleyici tarafından tercih ediliyor; outlier detection / failure accrual olmadan hatalı pod trafiği çeker.
- **R04** — istio-ambient: kontrol düzlemi yokken yeni pod mesh'e girdi ama trafik alamadı (kimlik/yapılandırma dağıtılamadı).
- **S02** — istio-ambient: NetworkPolicy order'a yalnızca gateway rolüne izin verdiği halde yetkisiz pod (rogue) order'a erişebildi (HTTP 200). Mesh proxy'si başka iş yüklerinin açtığı bağlantıları paylaştığında NetworkPolicy bağlantının gerçek kaynağını göremiyor; davranış aralıklı.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S02** — istio-ambient: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 20 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S04** — Ambient L4 (waypoint'siz): path/method içeren kural ztunnel'de uygulanamaz. Gözlenen: GET/=000 GET/api/orders=000 GET/admin=000 POST/=000 (zincir: çalışıyor). L7 kural için waypoint gerekir.
- **S06** — istio-ambient: aynı node'un host ağından pod IP'sine düz (mTLS'siz) istek, zorunlu mTLS ve yetki politikasına rağmen kabul edildi (HTTP 200). Mesh, node'dan gelen trafiği (kubelet sağlık kontrolleri için) muaf tutuyor; hostNetwork pod'ları ve node üzerindeki ajanlar politikayı atlayabilir. Prod'da hostNetwork kullanımı Pod Security ile kısıtlanmalı.
- **S07** — Istio ambient: ztunnel'de REGISTRY_ONLY (kayıtsız dış adreslere ret) yok; ServiceEntry tanımlı olsa da izinsiz hedefe (denied.ext.test) erişim açık. Ambient'te egress kısıtı için egress gateway veya NetworkPolicy ile birleşik tasarım gerekir.
- **S08** — istio-ambient: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **S08** — istio-ambient: CA rotasyonunda yeni pod bile eski ara CA'nın sertifikasını kullandı (ztunnel kimlik başına önbellekte tutuyor). Yeni CA'nın devreye girmesi için ztunnel DaemonSet'inin yeniden başlatılması gerekti; bu sırada node'daki tüm pod'ların trafiği etkilenir.
- **T02** — istio-ambient: gRPC (HTTP/2 kalıcı bağlantı) trafiği istek bazlı dağıtılmıyor: 3 pod'dan 1 tanesi trafik aldı, en yüklü pod payı 1.000. Bağlantı bazlı (L4) dengeleme.

### Istio ambient + waypoint (L7)

- **P01** — istio-ambient-l7: en yüksek aşamadan sonra servis zinciri kendiliğinden toparlanmadı (30 sn sonra hâlâ 5xx); yeniden başlatma gerekti. Mesh'siz referansla kıyaslanmalı.
- **R04** — istio-ambient-l7: kontrol düzlemi yokken yeni pod mesh'e girdi ama trafik alamadı (kimlik/yapılandırma dağıtılamadı).
- **S02** — Standart NetworkPolicy seti istio-ambient-l7 ile uyumsuz (zincir=ok, uçtan uca=bozuk, pod sağlığı=ok). Mesh'e özel ek kural gerekiyor: Ambient'e özel ek: kubelet sağlık kontrolleri ambient'te 169.254.7.127 kaynak adresinden gelir (SNAT).
- **S02** — istio-ambient-l7: servisler arası tüm trafik waypoint üzerinden geldiği için hedef pod'daki NetworkPolicy yalnızca waypoint'i kaynak olarak görür; waypoint'e izin vermek zorunlu olduğundan çağıran bazlı NetworkPolicy kuralları (ör. yalnızca gateway -> order) etkisiz kalır. Bu profilde servisler arası erişim kontrolü yalnızca mesh yetki politikasıyla (S03) yapılabilir.
- **S02** — istio-ambient-l7: NetworkPolicy order'a yalnızca gateway rolüne izin verdiği halde yetkisiz pod (rogue) order'a erişebildi (HTTP 200). Mesh proxy'si başka iş yüklerinin açtığı bağlantıları paylaştığında NetworkPolicy bağlantının gerçek kaynağını göremiyor; davranış aralıklı.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S02** — istio-ambient-l7: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 20 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S06** — istio-ambient-l7: aynı node'un host ağından pod IP'sine düz (mTLS'siz) istek, zorunlu mTLS ve yetki politikasına rağmen kabul edildi (HTTP 200). Mesh, node'dan gelen trafiği (kubelet sağlık kontrolleri için) muaf tutuyor; hostNetwork pod'ları ve node üzerindeki ajanlar politikayı atlayabilir. Prod'da hostNetwork kullanımı Pod Security ile kısıtlanmalı.
- **S07** — Istio ambient: ztunnel'de REGISTRY_ONLY (kayıtsız dış adreslere ret) yok; ServiceEntry tanımlı olsa da izinsiz hedefe (denied.ext.test) erişim açık. Ambient'te egress kısıtı için egress gateway veya NetworkPolicy ile birleşik tasarım gerekir.
- **S08** — istio-ambient-l7: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **S08** — istio-ambient-l7: CA rotasyonunda yeni pod bile eski ara CA'nın sertifikasını kullandı (ztunnel kimlik başına önbellekte tutuyor). Yeni CA'nın devreye girmesi için ztunnel DaemonSet'inin yeniden başlatılması gerekti; bu sırada node'daki tüm pod'ların trafiği etkilenir.
- **S08** — istio-ambient-l7: CA rotasyonu için gereken ztunnel yeniden başlatması yük altında kesinti yarattı: hata oranı %8.5, 2599 başarısız istek, p99 10000 ms. Waypoint üzerinden geçen tüneller node proxy'si yeniden başlarken kopuyor.
- **T01** — istio-ambient-l7: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs
- **T02** — istio-ambient-l7: protokol ipucu (appProtocol) olmayan server-first TCP portunda sunucunun ilk baytı 20 sn içinde hiç gelmedi (bağlantı kullanılamaz) — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla 2 ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.).

### Istio sidecar

- **P07** — istio-sidecar: varsayılan proxy CPU isteğiyle (100m) 120 ek servis lab'daki app node'una (12 çekirdek ayrılabilir) sığmadı; pod'lar Pending kaldı. Ölçek testi için ek pod'larda proxy isteği 5m'ye indirildi. Prod'da bu ayrılan kapasite, kullanılmasa da node sayısını belirler (projeksiyondaki ayrılan çekirdek kalemi).
- **R04** — istio-sidecar: kontrol düzlemi yokken yeni pod oluşturulamadı (enjeksiyon webhook'u hata veriyor: Error creating: Internal error occurred: failed calling webhook "namespace.sidecar-injector.istio.io": failed to call webhook: Post "https://istiod.istio-system.svc:443/inject?timeout=10s": dial tcp 1). Ölçeklenme ve yeniden başlatmalar durur.
- **S02** — istio-sidecar: NetworkPolicy order'a yalnızca gateway rolüne izin verdiği halde yetkisiz pod (rogue) order'a erişebildi (HTTP 200). Mesh proxy'si başka iş yüklerinin açtığı bağlantıları paylaştığında NetworkPolicy bağlantının gerçek kaynağını göremiyor; davranış aralıklı.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S02** — istio-sidecar: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 7 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S02** — istio-sidecar: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 4 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S02** — istio-sidecar: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 9 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S06** — istio-sidecar: proxy metrik ucu (http://10.20.1.40:15020/stats/prometheus) yetkisiz bir pod'dan okunabiliyor (servis adları, istek sayıları sızar). Prod'da NetworkPolicy ile yalnızca izleme sistemine açılmalı.
- **S08** — istio-sidecar: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **T01** — istio-sidecar: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs
- **T02** — istio-sidecar: protokol ipucu (appProtocol) olmayan server-first TCP portunda sunucunun ilk baytı 20 sn içinde hiç gelmedi (bağlantı kullanılamaz) — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla 2 ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.).

### Linkerd

- **O01** — linkerd-jaeger eklentisi kurulamadı: Cannot accept flags before Linkerd extension name
error: no objects passed to apply
- **O01** — linkerd: trace yalnızca uygulamanın ürettiği span'lardan oluştu; mesh proxy'leri span üretmedi (servisler: catalog,fraud,gateway,inventory,ledger,order,payment,pricing).
- **R01** — linkerd: 3 replikadan 1'i sürekli hata verirken uçtan uca hata oranı %63 (replika oranına göre beklenen ~%33). Hızlı hata dönen replika yük dengeleyici tarafından tercih ediliyor; outlier detection / failure accrual olmadan hatalı pod trafiği çeker.
- **R01** — linkerd: 3 replikadan 1'i sürekli hata verirken uçtan uca hata oranı %61 (replika oranına göre beklenen ~%33). Hızlı hata dönen replika yük dengeleyici tarafından tercih ediliyor; outlier detection / failure accrual olmadan hatalı pod trafiği çeker.
- **R02** — Linkerd'de yerleşik hata enjeksiyonu yok; hatalı/yavaş backend'ler kurulup HTTPRoute ağırlığıyla yönlendirilerek yapıldı (ek dağıtım ve bakım gerektirir, gecikme/hata ayrı ayrı oranlanamaz).
- **R04** — linkerd: kontrol düzlemi yokken yeni pod mesh'e GİRMEDEN açıldı (proxy'siz). Zorunlu mTLS altında bu pod diğer servislerle konuşamaz / güvenlik açığı oluşturur.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S04** — linkerd: endpoint kuralı tek başına kubelet sağlık kontrollerini (/ready) engelledi; order pod'ları NotReady oldu. Probe yolları için ek kural gerekiyor (policies/linkerd-probes.yaml).
- **S06** — linkerd: proxy metrik ucu (http://10.20.1.39:4191/metrics) yetkisiz bir pod'dan okunabiliyor (servis adları, istek sayıları sızar). Prod'da NetworkPolicy ile yalnızca izleme sistemine açılmalı.
- **S08** — linkerd: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **T01** — linkerd: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs
- **T02** — linkerd: protokol ipucu (appProtocol) olmayan server-first TCP portunda ilk bayt 10005 ms sonra geldi — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla 4 ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.).
- **T02** — linkerd: gRPC (HTTP/2 kalıcı bağlantı) trafiği istek bazlı dağıtılmıyor: 3 pod'dan 2 tanesi trafik aldı, en yüklü pod payı 0.567. Bağlantı bazlı (L4) dengeleme.
- **T02** — linkerd: protokol ipucu (appProtocol) olmayan server-first TCP portunda ilk bayt 10006 ms sonra geldi — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla 4 ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.).
- **T02** — linkerd: protokol ipucu (appProtocol) olmayan server-first TCP portunda ilk bayt 10004 ms sonra geldi — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla 4 ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.).
- **T03** — Linkerd küme girişi (north-south) için Gateway API uygulaması sunmuyor; ingress-nginx'in yerine ayrı bir ürün (ör. Envoy Gateway, Contour) seçilip mesh'e dahil edilmesi gerekir. Kayıtlı GatewayClass: 

## 7. Test detayları (metrikler)


### P01 — Kademeli yük — gecikme ve kırılma noktası

Artan istek hızında (RPS) servis zincirinin gecikmesini (p50/p95/p99) ve hata oranını ölçmek; sistemin bozulmaya başladığı noktayı (kırılma noktası) bulmak. Mesh'siz referansla kıyaslanınca mesh'in gecikme ve kapasite maliyetini verir.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `stages` | 8.00 adet | 8.00 adet | 8.00 adet | 8.00 adet | 8.00 adet |
| `stage_duration_s` | 60.0 sn | 60.0 sn | 60.0 sn | 60.0 sn | 60.0 sn |
| `stage0.target_rps` | 100 RPS | 100 RPS | 100 RPS | 100 RPS | 100 RPS |
| `stage0.rps` | 100 RPS | 100 RPS | 100 RPS | 100 RPS | 100 RPS |
| `stage0.p50_ms` | 10.4 ms | 10.9 ms | 12.6 ms | 14.3 ms | 12.5 ms |
| `stage0.p95_ms` | 14.8 ms | 15.5 ms | 17.3 ms | 19.1 ms | 17.1 ms |
| `stage0.p99_ms` | 16.8 ms | 17.8 ms | 19.9 ms | 21.5 ms | 19.3 ms |
| `stage0.p999_ms` | 19.8 ms | 21.3 ms | 71.1 ms | 25.2 ms | 22.0 ms |
| `stage0.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage0.dropped` | 0 istek | 0 istek | 0 istek | 0 istek | 0 istek |
| `stage1.target_rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `stage1.rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `stage1.p50_ms` | 10.3 ms | 11.0 ms | 14.5 ms | 17.6 ms | 14.1 ms |
| `stage1.p95_ms` | 14.8 ms | 15.6 ms | 20.3 ms | 34.1 ms | 20.1 ms |
| `stage1.p99_ms` | 17.0 ms | 17.8 ms | 24.4 ms | 62.7 ms | 25.9 ms |
| `stage1.p999_ms` | 19.5 ms | 20.6 ms | 52.1 ms | 101 ms | 46.1 ms |
| `stage1.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage1.dropped` | 0 istek | 0 istek | 0 istek | 2.00 istek | 0 istek |
| `stage2.target_rps` | 500 RPS | 500 RPS | 500 RPS | 500 RPS | 500 RPS |
| `stage2.rps` | 500 RPS | 500 RPS | 499 RPS | 486 RPS | 499 RPS |
| `stage2.p50_ms` | 10.3 ms | 11.8 ms | 49.8 ms | 867 ms | 60.5 ms |
| `stage2.p95_ms` | 14.9 ms | 17.1 ms | 108 ms | 1 503 ms | 128 ms |
| `stage2.p99_ms` | 17.2 ms | 20.6 ms | 150 ms | 1 917 ms | 168 ms |
| `stage2.p999_ms` | 19.8 ms | 34.7 ms | 202 ms | 2 420 ms | 215 ms |
| `stage2.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage2.dropped` | 0 istek | 0 istek | 49.0 istek | 809 istek | 52.0 istek |
| `stage3.target_rps` | 750 RPS | 750 RPS | 750 RPS | 750 RPS | 750 RPS |
| `stage3.rps` | 750 RPS | 750 RPS | 741 RPS | 523 RPS | 740 RPS |
| `stage3.p50_ms` | 10.6 ms | 13.1 ms | 392 ms | 4 301 ms | 314 ms |
| `stage3.p95_ms` | 15.4 ms | 23.8 ms | 568 ms | 10 000 ms | 569 ms |
| `stage3.p99_ms` | 17.9 ms | 37.2 ms | 670 ms | 10 001 ms | 718 ms |
| `stage3.p999_ms` | 23.3 ms | 64.5 ms | 780 ms | 10 004 ms | 871 ms |
| `stage3.error_rate` | 0 oran | 0 oran | 0 oran | 0.115 oran | 0 oran |
| `stage3.dropped` | 0 istek | 0 istek | 560 istek | 13 045 istek | 570 istek |
| `stage4.target_rps` | 1 000 RPS | 1 000 RPS | 1 000 RPS | 1 000 RPS | 1 000 RPS |
| `stage4.rps` | 1 000 RPS | 999 RPS | 926 RPS | 522 RPS | 847 RPS |
| `stage4.p50_ms` | 11.2 ms | 27.0 ms | 0.112 ms | 5 116 ms | 2 023 ms |
| `stage4.p95_ms` | 17.5 ms | 57.3 ms | 2 620 ms | 10 001 ms | 6 448 ms |
| `stage4.p99_ms` | 23.5 ms | 88.6 ms | 3 078 ms | 10 001 ms | 8 412 ms |
| `stage4.p999_ms` | 39.3 ms | 143 ms | 3 436 ms | 10 004 ms | 10 000 ms |

### P02 — Sabit uzun yük (soak) — kararlılık ve sızıntı

Uzun süre sabit yük altında gecikmenin kayıp kaymadığını (drift) ve proxy'lerin bellek kullanımının büyümediğini (sızıntı) göstermek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `rate_rps` | 300 RPS | 300 RPS | 300 RPS | 300 RPS | 300 RPS |
| `duration_s` | 1 200 sn | 1 200 sn | 1 200 sn | 1 200 sn | 1 200 sn |
| `q0.p99_ms` | 16.9 ms | 18.1 ms | 33.7 ms | 137 ms | 39.6 ms |
| `q0.p50_ms` | 10.2 ms | 11.1 ms | 15.6 ms | 27.4 ms | 14.9 ms |
| `q1.p99_ms` | 16.9 ms | 18.1 ms | 34.5 ms | 129 ms | 39.2 ms |
| `q1.p50_ms` | 10.2 ms | 11.1 ms | 15.7 ms | 27.5 ms | 14.9 ms |
| `q2.p99_ms` | 16.9 ms | 18.1 ms | 33.4 ms | 127 ms | 39.7 ms |
| `q2.p50_ms` | 10.2 ms | 11.2 ms | 15.7 ms | 27.6 ms | 14.9 ms |
| `q3.p99_ms` | 16.8 ms | 18.1 ms | 33.1 ms | 129 ms | 40.1 ms |
| `q3.p50_ms` | 10.2 ms | 11.1 ms | 15.7 ms | 27.3 ms | 14.9 ms |
| `p50_ms` | 10.2 ms | 11.1 ms | 15.7 ms | 27.5 ms | 14.9 ms |
| `p99_ms` | 16.9 ms | 18.1 ms | 33.7 ms | 131 ms | 39.6 ms |
| `error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `p99_drift` | 0.997 kat | 0.998 kat | 0.956 kat | 0.942 kat | 1.01 kat |
| `app.mem_first_mib` | 139 MiB | 220 MiB | 128 MiB | 184 MiB | 228 MiB |
| `app.mem_last_mib` | 138 MiB | 218 MiB | 127 MiB | 182 MiB | 228 MiB |
| `app.mem_growth_mib` | -1.60 MiB | -1.50 MiB | -1.00 MiB | -1.40 MiB | 0 MiB |
| `p99_drift_limit_ms` | 26.9 ms | 28.1 ms | 50.6 ms | 205 ms | 59.4 ms |
| `ztunnel.mem_first_mib` | — | 85.3 MiB | 64.4 MiB | — | — |
| `ztunnel.mem_last_mib` | — | 79.5 MiB | 64.7 MiB | — | — |
| `ztunnel.mem_growth_mib` | — | -5.80 MiB | 0.300 MiB | — | — |
| `control.mem_first_mib` | — | 60.4 MiB | 64.5 MiB | 67.9 MiB | 78.5 MiB |
| `control.mem_last_mib` | — | 61.4 MiB | 64.3 MiB | 68.4 MiB | 77.9 MiB |
| `control.mem_growth_mib` | — | 0.600 MiB | 0.400 MiB | 0.500 MiB | -0.600 MiB |
| `waypoint.mem_first_mib` | — | — | 72.5 MiB | — | — |
| `waypoint.mem_last_mib` | — | — | 73.2 MiB | — | — |
| `waypoint.mem_growth_mib` | — | — | 0.700 MiB | — | — |
| `sidecar.mem_first_mib` | — | — | — | 1 791 MiB | 192 MiB |
| `sidecar.mem_last_mib` | — | — | — | 1 673 MiB | 193 MiB |
| `sidecar.mem_growth_mib` | — | — | — | -30.5 MiB | 0.600 MiB |

### P03 — Ani yük (spike) — dayanım ve toparlanma

Ani trafik sıçramasında hata oranını ve sistemin normale dönme süresini ölçmek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Kısmen / başarısız | Geçti | Geçti |
| `spike_rps` | 1 200 RPS | 1 200 RPS | 1 200 RPS | 1 200 RPS | 1 200 RPS |
| `spike_duration_s` | 30.0 sn | 30.0 sn | 30.0 sn | 30.0 sn | 30.0 sn |
| `before.p50_ms` | 10.4 ms | 10.9 ms | 12.8 ms | 14.6 ms | 12.6 ms |
| `before.p99_ms` | 16.7 ms | 18.0 ms | 20.2 ms | 22.6 ms | 19.5 ms |
| `before.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `before.dropped` | 0 istek | 0 istek | 0 istek | 0 istek | 0 istek |
| `spike.p50_ms` | 10.3 ms | 19.5 ms | 1 468 ms | 4 244 ms | 645 ms |
| `spike.p99_ms` | 18.1 ms | 99.0 ms | 2 840 ms | 10 001 ms | 3 171 ms |
| `spike.error_rate` | 0 oran | 0 oran | 0.281 oran | 0.078 oran | 0 oran |
| `spike.dropped` | 0 istek | 23.0 istek | 4 444 istek | 18 337 istek | 3 766 istek |
| `after.p50_ms` | 10.4 ms | 11.0 ms | 12.3 ms | 14.9 ms | 13.0 ms |
| `after.p99_ms` | 16.6 ms | 17.7 ms | 404 ms | 2 456 ms | 617 ms |
| `after.error_rate` | 0 oran | 0 oran | 0.121 oran | 0 oran | 0 oran |
| `after.dropped` | 0 istek | 0 istek | 61.0 istek | 141 istek | 60.0 istek |
| `recovery_s` | 5.00 sn | 5.00 sn | 5.00 sn | 5.00 sn | 5.00 sn |

### P04 — Uçtan uca yol — edge -> DMZ -> ingress -> zincir

Gerçek kullanıcı yolundaki toplam gecikmeyi ölçmek (edge LB, DMZ ingress A/B, cluster-a ingress, mesh'li ingress -> gateway kenarı dahil) ve küme içi ölçümle (P01) kıyaslamak.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `stage0.target_rps` | 100 RPS | 100 RPS | 100 RPS | 100 RPS | 100 RPS |
| `stage0.p50_ms` | 11.0 ms | 12.0 ms | 14.1 ms | 15.6 ms | 14.2 ms |
| `stage0.p95_ms` | 15.5 ms | 16.7 ms | 19.0 ms | 20.6 ms | 19.3 ms |
| `stage0.p99_ms` | 17.5 ms | 18.9 ms | 22.0 ms | 23.4 ms | 22.0 ms |
| `stage0.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage1.target_rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `stage1.p50_ms` | 10.9 ms | 12.1 ms | 16.7 ms | 21.3 ms | 16.5 ms |
| `stage1.p95_ms` | 15.4 ms | 16.9 ms | 24.3 ms | 49.4 ms | 25.7 ms |
| `stage1.p99_ms` | 17.5 ms | 19.3 ms | 31.1 ms | 77.1 ms | 40.4 ms |
| `stage1.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage2.target_rps` | 400 RPS | 400 RPS | 400 RPS | 400 RPS | 400 RPS |
| `stage2.p50_ms` | 11.2 ms | 13.3 ms | 35.8 ms | 289 ms | 42.0 ms |
| `stage2.p95_ms` | 16.0 ms | 19.0 ms | 72.9 ms | 516 ms | 101 ms |
| `stage2.p99_ms` | 18.4 ms | 23.1 ms | 104 ms | 655 ms | 142 ms |
| `stage2.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `tls_handshake_p50_ms` | 0 ms | 0 ms | 0 ms | 0 ms | 0 ms |

### P05 — Kaynak tüketimi — kalem kalem maliyet

Mesh'in her bileşeninin boşta ve sabit yük altında harcadığı CPU/belleği ve kapasite planlamasında "ayrılan" kaynak isteklerini (requests) ölçmek. Ambient / sidecar / Linkerd maliyet tablosunun ve prod projeksiyonunun ana girdisi.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `rate_rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `load.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `load.p50_ms` | 10.2 ms | 11.0 ms | 14.4 ms | 17.7 ms | 13.8 ms |
| `load.p99_ms` | 16.8 ms | 17.9 ms | 25.0 ms | 59.2 ms | 24.9 ms |
| `load.rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `shop_pods` | 19.0 adet | 19.0 adet | 19.0 adet | 19.0 adet | 19.0 adet |
| `shop_pods_running` | 19.0 adet | 19.0 adet | 20.0 adet | 19.0 adet | 19.0 adet |
| `dataplane.cpu_cores` | 0 çekirdek | 0.272 çekirdek | 0.979 çekirdek | 1.80 çekirdek | 0.962 çekirdek |
| `dataplane.cpu_per_1k_rps` | 0 çekirdek | 1.09 çekirdek | 3.92 çekirdek | 7.21 çekirdek | 3.85 çekirdek |
| `dataplane.mem_idle_mib` | 0 MiB | 164 MiB | 226 MiB | 1 799 MiB | 177 MiB |
| `dataplane.mem_per_pod_mib` | 0 MiB | 8.64 MiB | 11.9 MiB | 94.7 MiB | 9.34 MiB |
| `node_overhead_cores` | 0.049 çekirdek | 0.026 çekirdek | 0.028 çekirdek | 0.137 çekirdek | 0.109 çekirdek |
| `derived.req_cpu_per_pod` | 0 çekirdek | 0.047 çekirdek | 0.050 çekirdek | 0.100 çekirdek | 0 çekirdek |
| `derived.req_mem_per_pod` | 0 MiB | 96.6 MiB | 98.2 MiB | 128 MiB | 0 MiB |
| `derived.cpu_per_1k_hops` | 0 çekirdek | 0.136 çekirdek | 0.489 çekirdek | 0.902 çekirdek | 0.481 çekirdek |

### P06 — Pod başlangıç süresi ve ölçeklenme hızı

Mesh'in yeni pod'ların hazır olma süresine etkisini ölçmek (sidecar enjeksiyonu, proxy başlatma, sertifika alma). Ani ölçeklenmede (HPA) ne kadar gecikme eklediğini gösterir.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `replicas` | 30.0 adet | 30.0 adet | 30.0 adet | 30.0 adet | 30.0 adet |
| `rounds` | 3.00 tur | 3.00 tur | 3.00 tur | 3.00 tur | 3.00 tur |
| `round1.all_ready_s` | 3.65 sn | 4.43 sn | 4.29 sn | 12.6 sn | 9.52 sn |
| `round2.all_ready_s` | 3.40 sn | 4.49 sn | 4.39 sn | 12.5 sn | 10.0 sn |
| `round3.all_ready_s` | 3.65 sn | 4.49 sn | 4.06 sn | 12.3 sn | 10.2 sn |
| `ready_p50_s` | 2.00 sn | 4.00 sn | 3.00 sn | 11.0 sn | 7.00 sn |
| `ready_p95_s` | 3.00 sn | 4.00 sn | 4.00 sn | 12.0 sn | 8.00 sn |
| `ready_max_s` | 3.00 sn | 4.00 sn | 4.00 sn | 13.0 sn | 9.00 sn |
| `all_ready_s` | 3.65 sn | 4.49 sn | 4.29 sn | 12.3 sn | 10.0 sn |

### P07 — Politika yayılma süresi ve kontrol düzlemi ölçeği

Bir erişim kuralı değiştiğinde ne kadar sürede yürürlüğe girdiğini ölçmek; cluster'daki servis sayısı arttığında kontrol düzleminin ve proxy'lerin kaynak tüketiminin nasıl büyüdüğünü göstermek (3.000 servislik prod için ölçeklenme göstergesi).

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `base.deny_s` | 1.15 sn | 0.240 sn | 0.230 sn | 0.240 sn | 0.160 sn |
| `base.allow_s` | 0.145 sn | 0.240 sn | 0.240 sn | 0.250 sn | 0.170 sn |
| `scale_services` | 120 adet | 120 adet | 120 adet | 120 adet | 120 adet |
| `control.mem_before_mib` | 0 MiB | 76.0 MiB | 77.8 MiB | 101 MiB | 112 MiB |
| `control.mem_after_mib` | 0 MiB | 71.2 MiB | 74.4 MiB | 241 MiB | 117 MiB |
| `control.mem_growth_mib` | 0 MiB | -2.00 MiB | -3.40 MiB | 151 MiB | 5.40 MiB |
| `scaled.deny_s` | 1.12 sn | 0.240 sn | 0.260 sn | 0.365 sn | 0.240 sn |
| `scaled.allow_s` | 0.130 sn | 0.240 sn | 0.240 sn | 0.290 sn | 0.200 sn |
| `ztunnel.mem_growth_mib` | — | 4.00 MiB | 5.70 MiB | — | — |
| `sidecar.mem_per_container_before_mib` | — | — | — | 53.6 MiB | 8.71 MiB |
| `sidecar.mem_per_container_after_mib` | — | — | — | 56.2 MiB | 8.63 MiB |
| `sidecar.mem_per_container_growth_mib` | — | — | — | 2.55 MiB | -0.080 MiB |

### S01 — mTLS zorunluluğu ve hat üzerinde şifreleme

Servisler arası trafiğin (1) mesh dışından şifresiz erişime kapalı olduğunu ve (2) ağ üzerinde gerçekten şifreli aktığını kanıtlamak. PCI DSS segmentasyon ve "iletimde şifreleme" kanıtı.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Kısmen / başarısız | Geçti | Geçti | Geçti | Geçti |
| `marker_packets` | 40.0 paket | 0 paket | 0 paket | 0 paket | 0 paket |
| `control_packets` | 6.00 paket | 9.00 paket | 9.00 paket | 9.00 paket | 6.00 paket |

### S02 — Servisler arası whitelisting — NetworkPolicy (L3/L4)

Kubernetes NetworkPolicy ile servisler arası izin listesinin (varsayılan ret + zincir kuralları) her mesh ile birlikte doğru çalıştığını ve mesh'e özel ek kural gerekip gerekmediğini göstermek. Etiket bazlı kuralların "kimlik taklidi"ne açık olduğunu kanıtlamak.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Kısmen / başarısız | Kısmen / başarısız | Kısmen / başarısız | Geçti |
| `naive.chain_ok` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `naive.e2e_ok` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `naive.pods_ready` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `mesh_specific_rules` | 0 adet | 1.00 adet | 3.00 adet | 0 adet | 0 adet |
| `impostor_access` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `shared_identity_bypass` | 0 /20 | 20.0 /20 | 20.0 /20 | 7.00 /20 | 0 /20 |

### S03 — Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası)

Servisler arası erişimi IP/etiket yerine kriptografik kimlikle (ServiceAccount, mTLS sertifikası) kısıtlamak: varsayılan ret + her servis için izinli çağıranlar listesi. NetworkPolicy'den (S02) farkı: etiket taklidi işe yaramaz.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Geçti |
| `policy_objects` | — | 10.0 adet | 11.0 adet | 10.0 adet | 27.0 adet |
| `deny_http_code` | — | 0 kod | 403 kod | 403 kod | 403 kod |

### S04 — Endpoint bazlı erişim kısıtı (L7 — path / method)

Bir servisin yalnızca belirli endpoint'lerinin, belirli kimliklere ve HTTP metotlarına açık olmasını sağlamak (ör. /admin kapalı, yalnızca GET). Mesh içinde endpoint bazlı whitelisting.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Geçti |
| `probes_ok_without_fix` | — | 1.00 | 1.00 | 1.00 | 0 |
| `converge_s` | — | — | 21.0 sn | 20.0 sn | 20.0 sn |
| `deny_http_code` | — | — | 403 kod | 403 kod | 404 kod |

### S05 — Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress)

Dışarıya açık bir endpoint'in (ör. /admin) yalnızca izinli kaynak IP'lerinden erişilebilir olmasını DMZ katmanında sağlamak; istemci IP'sinin sahte X-Forwarded-For başlığıyla taklit edilemediğini kanıtlamak. Mesh'ten bağımsızdır (DMZ cluster'larında mesh yok); her profilde aynı sonuç beklenir.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `client_ip` | 0 | 0 | 0 | 0 | 0 |

### S06 — Politika atlatma denemeleri

Yetki kurallarının (S03) yalnızca "doğru yoldan" gelen trafikte değil, kötü niyetli denemelerde de geçerli olduğunu kanıtlamak: mesh dışı pod, mesh'ten çıkarılmış pod (aynı kimlikle), host ağı, doğrudan pod IP'si, sahte kimlik başlıkları, proxy yönetim portları.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Kısmen / başarısız | Kısmen / başarısız | Kısmen / başarısız | Geçti | Geçti |
| `proxy_metrics_exposed` | — | 0 | 0 | 1.00 | 1.00 |

### S07 — Dış çıkış (egress) whitelisting

Servislerin yalnızca izinli dış adreslere (FQDN) çıkabilmesini sağlamak; prod'daki ayrı dış çıkış zone'unun cluster içi karşılığı. Hangi mesh'in FQDN bazlı egress kısıtı yapabildiğini göstermek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Uygulanamaz | Uygulanamaz | Geçti | Geçti |
| `method` | 0 | — | — | — | — |
| `allowed_http_code` | 200 kod | 200 kod | 200 kod | 200 kod | 200 kod |
| `denied_http_code` | 0 kod | 200 kod | 200 kod | 0 kod | 0 kod |

### S08 — Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu

İş yükü sertifikalarının bizim (kurumsal) CA'mızdan imzalandığını, kısa ömürlü olduğunu ve otomatik yenilendiğini; ara CA (issuer) yük altında değiştirildiğinde trafik kesilmediğini göstermek. Prod'da Vault gibi kurumsal CA ile entegrasyonun lab karşılığı.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Kısmen / başarısız | Geçti | Geçti |
| `cert_ttl_h` | — | 24.0 saat | 24.0 saat | 24.0 saat | 24.0 saat |
| `rotation.needed_restart` | — | 1.00 | 1.00 | 1.00 | 1.00 |
| `rotation.ztunnel_restart` | — | 1.00 | 1.00 | 0 | 0 |
| `rotation.error_rate` | — | 0.000 oran | 0.002 oran | 0.002 oran | 0.000 oran |
| `rotation.p99_ms` | — | 18.0 ms | 26.0 ms | 74.8 ms | 26.3 ms |

### R01 — Timeout, retry ve outlier detection (circuit breaking)

(A) Bir alt servis yavaşladığında mesh'in timeout + retry politikasının uçtan uca gecikmeyi sınırladığını ve retry'ların yükü ne kadar artırdığını (amplifikasyon) ölçmek. (B) Hatalı bir replika (sürekli 503) devredeyken outlier detection'ın onu devreden çıkardığını göstermek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Geçti |
| `A.none.p50_ms` | 11.2 ms | 11.8 ms | 13.9 ms | 15.1 ms | 13.6 ms |
| `A.none.p99_ms` | 1 014 ms | 1 015 ms | 1 017 ms | 1 018 ms | 1 017 ms |
| `A.none.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `B.none.p50_ms` | 10.3 ms | 10.9 ms | 12.8 ms | 13.8 ms | 12.2 ms |
| `B.none.p99_ms` | 16.8 ms | 17.6 ms | 20.8 ms | 21.3 ms | 19.3 ms |
| `B.none.error_rate` | 0.172 oran | 0.001 oran | 0.332 oran | 0.330 oran | 0.626 oran |
| `A.none.amplification` | — | — | 1.00 kat | 0.991 kat | 1.01 kat |
| `A.policy.p50_ms` | — | — | 13.9 ms | 15.7 ms | 13.5 ms |
| `A.policy.p99_ms` | — | — | 381 ms | 379 ms | 456 ms |
| `A.policy.error_rate` | — | — | 0.008 oran | 0.008 oran | 0.009 oran |
| `A.policy.amplification` | — | — | 1.00 kat | 1.24 kat | 1.26 kat |
| `B.none.amplification` | — | — | 0.667 kat | 0.663 kat | 1.02 kat |
| `B.policy.p50_ms` | — | — | 12.9 ms | 14.1 ms | 12.7 ms |
| `B.policy.p99_ms` | — | — | 20.7 ms | 21.6 ms | 19.5 ms |
| `B.policy.error_rate` | — | — | 0.005 oran | 0.005 oran | 0.002 oran |
| `B.policy.amplification` | — | — | 0.996 kat | 0.992 kat | 1.03 kat |

### R02 — Hata enjeksiyonu (fault injection)

Uygulama koduna dokunmadan, mesh üzerinden kontrollü hata ve gecikme enjekte edebilmek (kaos testi, dayanıklılık tatbikatı). Mesh'lerin bu yeteneğini ve doğruluğunu kıyaslamak.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Kısmen / başarısız |
| `method` | — | — | 0 | 0 | 1.00 |
| `observed_error_rate` | — | — | 0.098 oran | 0.098 oran | 0.099 oran |
| `p50_ms` | — | — | 13.4 ms | 14.5 ms | 13.2 ms |
| `p90_ms` | — | — | 209 ms | 210 ms | 21.3 ms |
| `p95_ms` | — | — | 213 ms | 214 ms | 208 ms |

### R03 — Yük altında pod kaybı (failover)

Yük altındayken servis replikaları kaybedildiğinde (deploy, node bakımı, çökme) kullanıcıya yansıyan hata sayısını ölçmek. Mesh'in bağlantı yönetimi / yeniden deneme davranışının etkisi.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Kısmen / başarısız | Geçti | Geçti | Geçti |
| `failed_requests` | 0 istek | 0 istek | 39.0 istek | 21.0 istek | 5.00 istek |
| `error_rate` | 0 oran | 0 oran | 0.002 oran | 0.001 oran | 0.000 oran |
| `p99_ms` | 16.8 ms | 18.1 ms | 27.4 ms | 54.7 ms | 23.2 ms |
| `max_ms` | 22.6 ms | 42.5 ms | 10 001 ms | 222 ms | 1 013 ms |

### R04 — Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması

"Mesh tek hata noktası mı?" sorusunu cevaplamak. (A) Kontrol düzlemi tamamen düştüğünde mevcut trafik akıyor mu, yeni pod'lar açılabiliyor ve trafik alabiliyor mu? (B) Ambient'te node başına paylaşılan ztunnel yeniden başlarsa o node'daki tüm pod'lar ne kadar etkilenir (arıza etki alanı)?

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Geçti |
| `A.new_pod_created` | — | 1.00 | 1.00 | 0 | 1.00 |
| `A.new_pod_ready` | — | 1.00 | 1.00 | 0 | 1.00 |
| `A.new_pod_meshed` | — | 1.00 | 1.00 | 0 | 0 |
| `A.new_pod_serving` | — | 0 | 0 | 0 | 0 |
| `A.error_rate` | — | 0 oran | 0 oran | 0 oran | 0 oran |
| `A.failed_requests` | — | 0 istek | 0 istek | 0 istek | 0 istek |
| `A.p99_ms` | — | 17.9 ms | 23.7 ms | 23.9 ms | 20.6 ms |
| `B.ztunnel_restart_s` | — | 26.0 sn | 26.0 sn | — | — |
| `B.failed_requests` | — | 0 istek | 2.00 istek | — | — |
| `B.error_rate` | — | 0 oran | 0.000 oran | — | — |
| `B.pods_on_node` | — | 19.0 adet | 20.0 adet | — | — |

### R05 — Yük altında kesintisiz mesh güncellemesi

Mesh sürüm güncellemesinin (yılda birkaç kez zorunlu) iş trafiğini kesip kesmediğini, ne kadar sürdüğünü ve hangi adımları gerektirdiğini ölçmek. Sidecar ile ambient arasındaki en büyük operasyonel fark beklenen kalem.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Kısmen / başarısız |
| `from_version` | — | 0 | 0 | 0 | 0 |
| `to_version` | — | 0 | 0 | 0 | 0 |
| `upgrade_duration_s` | — | 59.0 sn | 78.0 sn | 122 sn | 103 sn |
| `steps` | — | 4.00 adım | 5.00 adım | 6.00 adım | 4.00 adım |
| `restarted_pods` | — | 0 adet | 1.00 adet | 19.0 adet | 19.0 adet |
| `failed_requests` | — | 0 istek | 2.00 istek | 81.0 istek | 767 istek |
| `error_rate` | — | 0 oran | 0.000 oran | 0.001 oran | 0.009 oran |
| `p99_ms` | — | 17.8 ms | 21.3 ms | 34.5 ms | 23.1 ms |
| `max_ms` | — | 57.8 ms | 137 ms | 258 ms | 3 052 ms |

### T01 — Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma

Yeni sürümü (canary) kullanıcıların küçük bir kısmına açabilmek, belirli istekleri (başlık) yeni sürüme yönlendirebilmek ve gerçek trafiği yeni sürüme kopyalayıp (mirroring) cevabı kullanmadan deneyebilmek. Tüm mesh'lerde aynı standart (Gateway API HTTPRoute, GAMMA) kullanılır.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Geçti |
| `baseline.v2_share` | 0.300 oran | 0.325 oran | 0.335 oran | 0.335 oran | 0.333 oran |
| `weighted.v2_share` | — | — | 0.110 oran | 0.098 oran | 0.102 oran |
| `header.v2_share` | — | — | 1.00 oran | 1.00 oran | 1.00 oran |
| `mirror.v2_share_in_responses` | — | — | 0 oran | 0 oran | 0.098 oran |
| `mirror.v2_received` | — | — | 0 istek | 0 istek | 0 istek |
| `mirror.supported` | — | — | 0 | 0 | 0 |

### T02 — Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği

Prod'daki protokollerin mesh'ten sorunsuz geçtiğini göstermek: (1) gRPC / HTTP2'de istek bazlı yük dağılımı (kube-proxy bağlantı bazlı dağıtır, uzun ömürlü bağlantı tek pod'a yapışır); (2) bağlantıyı önce sunucunun konuştuğu protokoller (SMTP, MySQL benzeri; Oracle/MSSQL/Kafka gibi TCP protokolleri için gösterge) — protokol algılama gecikmesi; (3) Redis / Postgres TCP trafiği.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `grpc.pods_used` | 1.00 adet | 1.00 adet | 3.00 adet | 3.00 adet | 2.00 adet |
| `grpc.max_share` | 1.00 oran | 1.00 oran | 0.370 oran | 0.360 oran | 0.567 oran |
| `banner.hint_ms` | 1.00 ms | 1.00 ms | 2.00 ms | 2.00 ms | 4.00 ms |
| `banner.nohint_ms` | 1.00 ms | 1.00 ms | — | — | 10 005 ms |

### T03 — Gateway API ile giriş (ingress-nginx'in yerine geçme)

ingress-nginx Mart 2026'da emekliye ayrıldı. Mesh'in kendi Gateway API uygulamasının küme girişini (north-south) üstlenip üstlenemeyeceğini göstermek: ayrı bir ingress ürününe gerek kalır mı?

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Uygulanamaz |
| `p50_ms` | — | 12.6 ms | 13.9 ms | 14.6 ms | — |

### O01 — Gözlemlenebilirlik — hazır metrikler, doğruluk, dağıtık izleme, erişim logu

Mesh'in uygulama koduna dokunmadan ne kadar görünürlük sağladığını ölçmek: her servis için "altın metrikler" (istek hızı, başarı oranı, gecikme), mesh'in ölçtüğü gecikmenin doğruluğu (k6'ya göre), uçtan uca trace (Tempo) ve erişim logu.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Geçti |
| `services_l7_metrics` | — | 0 /8 | 8.00 /8 | 8.00 /8 | 8.00 /8 |
| `services_l4_metrics` | — | 8.00 /8 | 8.00 /8 | 0 /8 | 8.00 /8 |
| `trace.spans` | — | 15.0 span | 23.0 span | 31.0 span | 15.0 span |
| `trace.services` | — | 8.00 adet | 9.00 adet | 17.0 adet | 8.00 adet |
| `trace.mesh_spans` | — | 0 adet | 1.00 adet | 9.00 adet | 0 adet |
| `access_log` | — | 0 | 0 | 0 | 0 |
| `mesh_p99_ms` | — | — | 92.9 ms | 974 ms | 26.2 ms |
| `k6_p99_ms` | — | — | 123 ms | 1 851 ms | 49.3 ms |
| `latency_accuracy_ratio` | — | — | 0.760 kat | 0.860 kat | 0.670 kat |

### O02 — Metrik maliyeti — seri sayısı ve alım hızı

Mesh metriklerinin izleme altyapısına (Prometheus) getirdiği gizli maliyeti ölçmek: aktif zaman serisi sayısı ve saniyede alınan örnek sayısı. Prod'da 3.000 servise projeksiyonun girdisi.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `series_total` | 58 417 seri | 79 592 seri | 86 238 seri | 97 514 seri | 107 799 seri |
| `series_mesh` | 0 seri | 571 seri | 6 152 seri | 15 281 seri | 23 736 seri |
| `shop_pods` | 19.0 adet | 19.0 adet | 20.0 adet | 19.0 adet | 19.0 adet |
| `series_mesh_per_pod` | 0 seri | 30.1 seri | 308 seri | 804 seri | 1 249 seri |
| `samples_per_s` | 10 348 örnek/sn | 13 927 örnek/sn | 15 227 örnek/sn | 17 130 örnek/sn | 18 826 örnek/sn |

### O03 — Operasyon envanteri — karmaşıklık ve ayrıcalık

Mesh'in işletme yükünü nesnel göstergelerle kaydetmek: CRD sayısı, kontrol düzlemi ve node ajanı bileşenleri, kullanılan imajlar, webhook'lar, uygulama pod'una eklenen konteynerler, ayrıcalıklı (NET_ADMIN / privileged) gereksinimler, kurulum süresi ve tanılama aracının sonucu.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Geçti |
| `crds` | — | 15.0 adet | 15.0 adet | 15.0 adet | 10.0 adet |
| `gateway_api_crds` | — | 10.0 adet | 10.0 adet | 10.0 adet | 10.0 adet |
| `control_plane_pods` | — | 1.00 adet | 1.00 adet | 1.00 adet | 3.00 adet |
| `node_agents` | — | 2.00 adet | 2.00 adet | 0 adet | 0 adet |
| `images` | — | 3.00 adet | 4.00 adet | 2.00 adet | 2.00 adet |
| `webhooks` | — | 3.00 adet | 3.00 adet | 3.00 adet | 3.00 adet |
| `added_containers_per_pod` | — | 0 adet | 0 adet | 2.00 adet | 2.00 adet |
| `privileged_components` | — | 2.00 adet | 2.00 adet | 1.00 adet | 2.00 adet |
| `install_s` | — | 44.0 sn | 45.0 sn | 18.0 sn | 60.0 sn |
| `helm_releases` | — | 4.00 adet | 4.00 adet | 2.00 adet | 0 adet |
| `diag_issues` | — | 0 adet | 0 adet | 0 adet | 0 adet |

## 8. Lisans, destek, olgunluk

Test edilmez; kaynaklardan derlenmiştir (doğrulama: 2026-11-16).

| | Istio | Linkerd |
|---|---|---|
| **Lisans** | Apache 2.0 (kaynak kod ve tüm sürümler) | Kaynak kod Apache 2.0. Açık kaynak proje 2024'ten beri yalnızca 'edge' sürümleri yayınlıyor; 'stable' sürümler Buoyant Enterprise for Linkerd (BEL) dağıtımında. |
| **CNCF** | CNCF graduated (Temmuz 2023) | CNCF graduated (Temmuz 2021) |
| **Sürüm modeli** | Yaklaşık 3 ayda bir minor sürüm; her minor sürüm yaklaşık 6 ay yama alır. Ambient modu 1.24 (Kasım 2024) ile GA. | Edge sürümleri haftalık / iki haftalık; sürüm başına uzun destek yok (bu değerlendirmede edge kullanıldı). |
| **Destek** | Topluluk + çok sayıda ticari destek sağlayıcısı (ör. Solo.io, Tetrate, Red Hat OpenShift Service Mesh, Google Cloud Service Mesh). | Ticari destek ve stable sürüm: Buoyant (BEL). BEL'in üretim kullanımı için belirli kurum büyüklüğünün üzerinde ücretli lisans gerekir. |
| **Değerlendirme** | Düşük lisans riski. Ambient modu sidecar'a göre daha yeni; bazı özellikler waypoint gerektirir. | Orta-yüksek lisans/destek riski: üretimde stable sürüm için tek tedarikçiye (Buoyant) bağımlılık ve lisans maliyeti; edge sürümlerle üretim, sık güncelleme yükü getirir. |
- Lisans ve destek bilgileri test edilmez; karar öncesi tedarikçilerden güncel teklif ve koşullar alınmalıdır.

## 9. Yöntem ve sınırlar

- Ortam: tek host üzerinde kind cluster'ları (prod topolojisinin kopyası: edge LB, DMZ A/B, cluster A/B, data, mgmt). Mesh yalnızca cluster-a'da.
- CPU ayrımı: servis node'u 0-3, yük üretici node'u 4-6, kontrol düzlemi 7-8 numaralı çekirdeklere sabitlendi (docker cpuset); yük üretici ölçülen servislerle CPU paylaşmaz.
- Adil kıyas: her mesh, sıfırdan kurulmuş bench cluster'ında (`meval mesh use <profil> --fresh`) aynı servis zinciri, aynı test sırası ve aynı yükle ölçülür. Tüm mesh'lerde zorunlu mTLS açık, erişim logu ve tracing (O01 hariç) kapalı, kaynak istekleri mesh varsayılanında.
- Servis zinciri: 8 servis (HTTP + bir gRPC kademesi), derinlik 5, paralel dallanma; her servis yapay 1–5 ms işlem süresi (chainsvc, `mesh-eval/apps/chainsvc`).
- Bağlantılar: servisler HTTP keep-alive ve kalıcı gRPC bağlantısı kullanır (gerçek servislerdeki gibi bağlantı havuzu).
- Bellek ölçümü (P05): proxy belleği, P01–P04 yük testlerinden sonra ölçülür; proxy'lerin yoğun yükte büyüyüp geri vermediği bellek dahildir. Bu, yeni kurulmuş bir pod'dan yüksek ama uzun süre çalışan prod pod'larına daha yakın bir değerdir. Sıra tüm mesh'lerde aynıdır; değer, önceki yükün yoğunluğuna bağlıdır (quick profilde daha düşük çıkar).
- SLO kırılma noktası: P01 aşamalı yükte p99 ≤ SLO, hata < %1 ve hedef hızın %95'i koşullarını sağlayan son aşama ölçülür. Aşamalar kaba olduğundan (full profilde 250 RPS adım) özet ve puan kartında, son geçen ve ilk kalan aşama arasında p99'a göre doğrusal tahmin kullanılır; aşama bazlı değer test detaylarında yer alır.
- Mutlak değerler (RPS, ms) prod donanımına aktarılamaz; mesh'ler arası göreli fark ve kırılma davranışı değerlendirilmelidir. Bulguların prod benzeri donanımda doğrulanması önerilir.
- Ambient + waypoint profilinde lab'da tek waypoint replikası vardır ve shop namespace'inin tüm servisler arası trafiği bu tek Envoy'dan geçer; bu profildeki L7 kapasite sonucu (P01) waypoint ölçeklenmesine bağlıdır. Prod'da waypoint'ler namespace / servis bazında ve HPA ile ölçeklenir.
- P07 (ölçek): Istio sidecar'da varsayılan proxy CPU isteği (100m) 120 ek servisle lab node'unun ayrılabilir CPU'sunu doldurduğu için ek pod'larda proxy isteği 5m'ye indirildi (bulgu olarak kayıtlı); diğer mesh'lerde değişiklik yok.
- Tekrarlanan koşularda metriklerin medyanı alınır, durum en kötü sonuçtur; yayılım (min…max) tablolarda gösterilir. Altyapı veya test hatasıyla yarıda kalan bir tekrar (ölçüm sonucu değil), başarılı tekrar varsa ölçümden çıkarılır ve ilgili testte belirtilir. Test hatası düzeltilen testler aynı oturumda yeniden koşulmuştur; rapor her test için en son koşuyu kullanır.

## 10. Envanter

- istio: `1.31.4`
- linkerd: `edge-26.11.2`
- k6: `grafana/k6:2.4.0`
- app: `mesh-eval/chainsvc:0.1.0`
- gateway_api: `v1.6.1`
- kubernetes: `v1.37.0`
- kind: `v0.33.0`
- ingress_nginx_chart: `4.15.1`
