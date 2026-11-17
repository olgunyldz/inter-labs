# Service Mesh Değerlendirme Raporu

Oluşturma: 16.11.2026 11:07 · Oturum: dogrulama-quick · Profil: quick

> Grafikli tam sürüm: `rapor.html`

## 1. Yönetici özeti

- Puan kartı sıralaması (eşit ağırlık): Linkerd 76, Istio sidecar 75, Istio ambient + waypoint (L7) 71, Istio ambient (L4) 70.
- Istio ambient (L4): SLO (p99 ≤ 100 ms) kapasitesi 900 RPS — mesh'siz referansın (%100'i).
- Istio ambient + waypoint (L7): SLO (p99 ≤ 100 ms) kapasitesi 100 RPS — mesh'siz referansın (%11'i).
- Istio sidecar: SLO (p99 ≤ 100 ms) kapasitesi 300 RPS — mesh'siz referansın (%33'i).
- Linkerd: SLO (p99 ≤ 100 ms) kapasitesi 600 RPS — mesh'siz referansın (%67'i).
- 3.000 servis projeksiyonu: veri düzlemi belleği ambient 11.6 GiB, sidecar 332 GiB; ayrılan (requests) CPU ambient 90.0, sidecar 900 çekirdek.
- Istio ambient (L4): başarısız/kısmi S02, S06; yetenek yok R01, R02, S04, S07, T01.
- Istio ambient + waypoint (L7): başarısız/kısmi R04, S02, S06, S08; yetenek yok S07.
- Linkerd: başarısız/kısmi —; yetenek yok T03.
- Toplam 47 bulgu kaydedildi (bölüm 6).

## 2. Puan kartı

| Kategori | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|
| Performans | 95.0 | 57.8 | 64.1 | 80.1 |
| Kaynak maliyeti | 94.5 | 39.0 | 23.6 | 40.7 |
| Güvenlik | 65.9 | 74.6 | 100 | 100 |
| Dayanıklılık | 50.3 | 51.2 | 70.2 | 83.3 |
| Trafik yönetimi | 56.5 | 97.3 | 100 | 62.1 |
| Gözlemlenebilirlik | 50.0 | 100 | 100 | 100 |
| Operasyon | 79.2 | 79.2 | 66.7 | 62.5 |
| **Toplam** | **70.2** | **71.3** | **74.9** | **75.5** |

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
| Veri düzlemi belleği | 11.6 GiB | 28.7 GiB | 332 GiB | 39.9 GiB |
| Veri düzlemi CPU | 3.46 çekirdek | 13.7 çekirdek | 25.0 çekirdek | 16.3 çekirdek |
| Ayrılan CPU | 90.0 çekirdek | 120 çekirdek | 900 çekirdek | 0 çekirdek |
| Ayrılan bellek | 179 GiB | 217 GiB | 1 125 GiB | 0 GiB |
| Node eşdeğeri (kullanılan) | 0.216 node | 0.858 node | 5.24 node | 1.02 node |
| Node eşdeğeri (ayrılan) | 5.63 node | 7.50 node | 56.2 node | 0 node |

## 5. Test sonuç matrisi

| Test | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---|---|---|---|---|
| P01 Kademeli yük — gecikme ve kırılma noktası | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P02 Sabit uzun yük (soak) — kararlılık ve sızıntı | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P03 Ani yük (spike) — dayanım ve toparlanma | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P04 Uçtan uca yol — edge -> DMZ -> ingress -> zincir | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P05 Kaynak tüketimi — kalem kalem maliyet | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P06 Pod başlangıç süresi ve ölçeklenme hızı | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| P07 Politika yayılma süresi ve kontrol düzlemi ölçeği | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S01 mTLS zorunluluğu ve hat üzerinde şifreleme | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S02 Servisler arası whitelisting — NetworkPolicy (L3/L4) | ✅ Geçti | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| S03 Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası) | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S04 Endpoint bazlı erişim kısıtı (L7 — path / method) | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S05 Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress) | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| S06 Politika atlatma denemeleri | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| S07 Dış çıkış (egress) whitelisting | ✅ Geçti | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti |
| S08 Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu | ➖ Uygulanamaz | ✅ Geçti | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| R01 Timeout, retry ve outlier detection (circuit breaking) | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| R02 Hata enjeksiyonu (fault injection) | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| R03 Yük altında pod kaybı (failover) | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| R04 Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması | ➖ Uygulanamaz | ✅ Geçti | ⚠️ Kısmen / başarısız | ✅ Geçti | ✅ Geçti |
| R05 Yük altında kesintisiz mesh güncellemesi | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| T01 Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma | ➖ Uygulanamaz | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| T02 Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| T03 Gateway API ile giriş (ingress-nginx'in yerine geçme) | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ➖ Uygulanamaz |
| O01 Gözlemlenebilirlik — hazır metrikler, doğruluk, dağıtık izleme, erişim logu | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| O02 Metrik maliyeti — seri sayısı ve alım hızı | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |
| O03 Operasyon envanteri — karmaşıklık ve ayrıcalık | ➖ Uygulanamaz | ✅ Geçti | ✅ Geçti | ✅ Geçti | ✅ Geçti |

## 6. Bulgular


### Mesh yok (referans)

- **P01** — Doyma noktasına ulaşılmadı: en yüksek aşama (900 RPS) hatasız karşılandı; profil 'full' ile daha yüksek hızlar denenebilir.
- **S01** — Servisler arası trafik ağda düz metin: başlıklar ve gövde node üzerinde okunabiliyor (40 paket).
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S07** — Mesh'siz egress kısıtı yalnızca IP bazlı yapılabilir: hedefin IP'si değiştiğinde (CDN, bulut servisleri) kural bozulur ve aynı IP'yi paylaşan başka adresler de açılır.
- **T02** — none: gRPC (HTTP/2 kalıcı bağlantı) trafiği istek bazlı dağıtılmıyor: 3 pod'dan 2 tanesi trafik aldı, en yüklü pod payı 0.503. Bağlantı bazlı (L4) dengeleme.

### Istio ambient (L4)

- **O01** — istio-ambient: 0/8 servis için L7 (istek, başarı oranı, gecikme) metriği var; diğerleri için yalnızca TCP metrikleri. Altın metrikler için L7 proxy (waypoint) gerekir.
- **O01** — istio-ambient: trace yalnızca uygulamanın ürettiği span'lardan oluştu; mesh proxy'leri span üretmedi (servisler: catalog,fraud,gateway,inventory,ledger,order,payment,pricing).
- **P01** — Doyma noktasına ulaşılmadı: en yüksek aşama (900 RPS) hatasız karşılandı; profil 'full' ile daha yüksek hızlar denenebilir.
- **R04** — istio-ambient: kontrol düzlemi yokken yeni pod mesh'e girdi ama trafik alamadı (kimlik/yapılandırma dağıtılamadı).
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S02** — istio-ambient: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 20 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S04** — Ambient L4 (waypoint'siz): path/method içeren kural ztunnel'de uygulanamaz. Gözlenen: GET/=000 GET/api/orders=000 GET/admin=000 POST/=000 (zincir: çalışıyor). L7 kural için waypoint gerekir.
- **S06** — istio-ambient: aynı node'un host ağından pod IP'sine düz (mTLS'siz) istek, zorunlu mTLS ve yetki politikasına rağmen kabul edildi (HTTP 200). Mesh, node'dan gelen trafiği (kubelet sağlık kontrolleri için) muaf tutuyor; hostNetwork pod'ları ve node üzerindeki ajanlar politikayı atlayabilir. Prod'da hostNetwork kullanımı Pod Security ile kısıtlanmalı.
- **S07** — Istio ambient: ztunnel'de REGISTRY_ONLY (kayıtsız dış adreslere ret) yok; ServiceEntry tanımlı olsa da izinsiz hedefe (denied.ext.test) erişim açık. Ambient'te egress kısıtı için egress gateway veya NetworkPolicy ile birleşik tasarım gerekir.
- **S08** — istio-ambient: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **S08** — istio-ambient: CA rotasyonunda yeni pod bile eski ara CA'nın sertifikasını kullandı (ztunnel kimlik başına önbellekte tutuyor). Yeni CA'nın devreye girmesi için ztunnel DaemonSet'inin yeniden başlatılması gerekti; bu sırada node'daki tüm pod'ların trafiği etkilenir.
- **T02** — istio-ambient: gRPC (HTTP/2 kalıcı bağlantı) trafiği istek bazlı dağıtılmıyor: 3 pod'dan 2 tanesi trafik aldı, en yüklü pod payı 0.543. Bağlantı bazlı (L4) dengeleme.

### Istio ambient + waypoint (L7)

- **R04** — istio-ambient-l7: kontrol düzlemi yokken yeni pod mesh'e girdi ama trafik alamadı (kimlik/yapılandırma dağıtılamadı).
- **S02** — Standart NetworkPolicy seti istio-ambient-l7 ile uyumsuz (zincir=ok, uçtan uca=bozuk, pod sağlığı=ok). Mesh'e özel ek kural gerekiyor: Ambient'e özel ek: kubelet sağlık kontrolleri ambient'te 169.254.7.127 kaynak adresinden gelir (SNAT).
- **S02** — istio-ambient-l7: NetworkPolicy order'a yalnızca gateway rolüne izin verdiği halde yetkisiz pod (rogue) order'a erişebildi (HTTP 200). Mesh proxy'si başka iş yüklerinin açtığı bağlantıları paylaştığında NetworkPolicy bağlantının gerçek kaynağını göremiyor; davranış aralıklı.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S02** — istio-ambient-l7: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin 20 tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir.
- **S06** — istio-ambient-l7: aynı node'un host ağından pod IP'sine düz (mTLS'siz) istek, zorunlu mTLS ve yetki politikasına rağmen kabul edildi (HTTP 200). Mesh, node'dan gelen trafiği (kubelet sağlık kontrolleri için) muaf tutuyor; hostNetwork pod'ları ve node üzerindeki ajanlar politikayı atlayabilir. Prod'da hostNetwork kullanımı Pod Security ile kısıtlanmalı.
- **S07** — Istio ambient: ztunnel'de REGISTRY_ONLY (kayıtsız dış adreslere ret) yok; ServiceEntry tanımlı olsa da izinsiz hedefe (denied.ext.test) erişim açık. Ambient'te egress kısıtı için egress gateway veya NetworkPolicy ile birleşik tasarım gerekir.
- **S08** — istio-ambient-l7: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **S08** — istio-ambient-l7: CA rotasyonunda yeni pod bile eski ara CA'nın sertifikasını kullandı (ztunnel kimlik başına önbellekte tutuyor). Yeni CA'nın devreye girmesi için ztunnel DaemonSet'inin yeniden başlatılması gerekti; bu sırada node'daki tüm pod'ların trafiği etkilenir.
- **T01** — istio-ambient-l7: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs
- **T02** — istio-ambient-l7: protokol ipucu (appProtocol) olmayan server-first TCP portunda sunucunun ilk baytı 20 sn içinde hiç gelmedi (bağlantı kullanılamaz) — mesh istemcinin önce veri göndermesini bekliyor (protokol algılama). İpucuyla 2 ms. Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı (Oracle, MSSQL, SMTP vb.).

### Istio sidecar

- **R04** — istio-sidecar: kontrol düzlemi yokken yeni pod oluşturulamadı (enjeksiyon webhook'u hata veriyor: Error creating: Internal error occurred: failed calling webhook "namespace.sidecar-injector.istio.io": failed to call webhook: Post "https://istiod.istio-system.svc:443/inject?timeout=10s": context de). Ölçeklenme ve yeniden başlatmalar durur.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S06** — istio-sidecar: proxy metrik ucu (http://10.20.1.29:15020/stats/prometheus) yetkisiz bir pod'dan okunabiliyor (servis adları, istek sayıları sızar). Prod'da NetworkPolicy ile yalnızca izleme sistemine açılmalı.
- **S08** — istio-sidecar: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **T01** — istio-sidecar: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs
- **T02** — istio-sidecar: protokol ipucu olmayan server-first TCP bağlantısında ilk bayt gelmedi ms (protokol algılama beklemesi). Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı.

### Linkerd

- **O01** — linkerd-jaeger eklentisi kurulamadı: Cannot accept flags before Linkerd extension name
error: no objects passed to apply
- **O01** — linkerd: trace yalnızca uygulamanın ürettiği span'lardan oluştu; mesh proxy'leri span üretmedi (servisler: catalog,fraud,gateway,inventory,ledger,order,payment,pricing).
- **P01** — Doyma noktasına ulaşılmadı: en yüksek aşama (900 RPS) hatasız karşılandı; profil 'full' ile daha yüksek hızlar denenebilir.
- **R01** — linkerd: 3 replikadan 1'i sürekli hata verirken uçtan uca hata oranı %58 (replika oranına göre beklenen ~%33). Hızlı hata dönen replika yük dengeleyici tarafından tercih ediliyor; outlier detection / failure accrual olmadan hatalı pod trafiği çeker.
- **R02** — Linkerd'de yerleşik hata enjeksiyonu yok; hatalı/yavaş backend'ler kurulup HTTPRoute ağırlığıyla yönlendirilerek yapıldı (ek dağıtım ve bakım gerektirir, gecikme/hata ayrı ayrı oranlanamaz).
- **R04** — linkerd: kontrol düzlemi yokken yeni pod mesh'e GİRMEDEN açıldı (proxy'siz). Zorunlu mTLS altında bu pod diğer servislerle konuşamaz / güvenlik açığı oluşturur.
- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S04** — linkerd: endpoint kuralı tek başına kubelet sağlık kontrollerini (/ready) engelledi; order pod'ları NotReady oldu. Probe yolları için ek kural gerekiyor (policies/linkerd-probes.yaml).
- **S06** — linkerd: proxy metrik ucu (http://10.20.1.29:4191/metrics) yetkisiz bir pod'dan okunabiliyor (servis adları, istek sayıları sızar). Prod'da NetworkPolicy ile yalnızca izleme sistemine açılmalı.
- **S08** — linkerd: yeni ara CA otomatik yüklenmedi; kontrol düzleminin yeniden başlatılması gerekti.
- **T01** — linkerd: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs
- **T02** — linkerd: protokol ipucu olmayan server-first TCP bağlantısında ilk bayt 10006 ms (protokol algılama beklemesi). Prod'da tüm TCP portlarına appProtocol / opaque port tanımı zorunlu olmalı.
- **T03** — Linkerd küme girişi (north-south) için Gateway API uygulaması sunmuyor; ingress-nginx'in yerine ayrı bir ürün (ör. Envoy Gateway, Contour) seçilip mesh'e dahil edilmesi gerekir. Kayıtlı GatewayClass: 

## 7. Test detayları (metrikler)


### P01 — Kademeli yük — gecikme ve kırılma noktası

Artan istek hızında (RPS) servis zincirinin gecikmesini (p50/p95/p99) ve hata oranını ölçmek; sistemin bozulmaya başladığı noktayı (kırılma noktası) bulmak. Mesh'siz referansla kıyaslanınca mesh'in gecikme ve kapasite maliyetini verir.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `stages` | 4.00 adet | 4.00 adet | 4.00 adet | 4.00 adet | 4.00 adet |
| `stage_duration_s` | 30.0 sn | 30.0 sn | 30.0 sn | 30.0 sn | 30.0 sn |
| `stage0.target_rps` | 100 RPS | 100 RPS | 100 RPS | 100 RPS | 100 RPS |
| `stage0.rps` | 100 RPS | 100 RPS | 100 RPS | 100 RPS | 100 RPS |
| `stage0.p50_ms` | 10.4 ms | 10.9 ms | 13.8 ms | 13.7 ms | 12.5 ms |
| `stage0.p95_ms` | 14.8 ms | 15.3 ms | 19.0 ms | 18.4 ms | 16.8 ms |
| `stage0.p99_ms` | 16.7 ms | 18.1 ms | 23.4 ms | 21.0 ms | 19.0 ms |
| `stage0.p999_ms` | 19.6 ms | 33.2 ms | 87.2 ms | 24.4 ms | 21.5 ms |
| `stage0.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage0.dropped` | 0 istek | 0 istek | 0 istek | 0 istek | 0 istek |
| `stage1.target_rps` | 300 RPS | 300 RPS | 300 RPS | 300 RPS | 300 RPS |
| `stage1.rps` | 300 RPS | 300 RPS | 300 RPS | 300 RPS | 300 RPS |
| `stage1.p50_ms` | 10.2 ms | 10.7 ms | 28.0 ms | 15.0 ms | 12.7 ms |
| `stage1.p95_ms` | 14.9 ms | 15.1 ms | 72.4 ms | 21.6 ms | 17.5 ms |
| `stage1.p99_ms` | 17.0 ms | 17.3 ms | 100 ms | 28.9 ms | 20.5 ms |
| `stage1.p999_ms` | 19.4 ms | 20.0 ms | 138 ms | 44.8 ms | 23.3 ms |
| `stage1.error_rate` | 0 oran | 0 oran | 0.000 oran | 0 oran | 0 oran |
| `stage1.dropped` | 0 istek | 0 istek | 9.00 istek | 0 istek | 0 istek |
| `stage2.target_rps` | 600 RPS | 600 RPS | 600 RPS | 600 RPS | 600 RPS |
| `stage2.rps` | 600 RPS | 600 RPS | 564 RPS | 581 RPS | 600 RPS |
| `stage2.p50_ms` | 10.4 ms | 10.9 ms | 935 ms | 316 ms | 24.2 ms |
| `stage2.p95_ms` | 15.0 ms | 15.6 ms | 1 275 ms | 884 ms | 64.0 ms |
| `stage2.p99_ms` | 17.2 ms | 17.7 ms | 1 408 ms | 1 124 ms | 96.6 ms |
| `stage2.p999_ms` | 19.7 ms | 21.0 ms | 1 519 ms | 1 402 ms | 136 ms |
| `stage2.error_rate` | 0 oran | 0 oran | 0.000 oran | 0 oran | 0 oran |
| `stage2.dropped` | 0 istek | 0 istek | 1 090 istek | 568 istek | 11.0 istek |
| `stage3.target_rps` | 900 RPS | 900 RPS | 900 RPS | 900 RPS | 900 RPS |
| `stage3.rps` | 900 RPS | 900 RPS | 700 RPS | 649 RPS | 892 RPS |
| `stage3.p50_ms` | 10.8 ms | 11.7 ms | 708 ms | 3 017 ms | 132 ms |
| `stage3.p95_ms` | 16.3 ms | 17.6 ms | 4 109 ms | 7 775 ms | 251 ms |
| `stage3.p99_ms` | 20.6 ms | 23.7 ms | 4 551 ms | 10 000 ms | 317 ms |
| `stage3.p999_ms` | 28.5 ms | 55.2 ms | 5 020 ms | 10 001 ms | 392 ms |
| `stage3.error_rate` | 0 oran | 0 oran | 0.597 oran | 0.018 oran | 0 oran |
| `stage3.dropped` | 0 istek | 0 istek | 6 004 istek | 7 540 istek | 239 istek |
| `knee_slo_rps` | 900 RPS | 900 RPS | 100 RPS | 300 RPS | 600 RPS |
| `knee_sat_rps` | 900 RPS | 900 RPS | 300 RPS | 600 RPS | 900 RPS |
| `slo_p99_ms` | 100 ms | 100 ms | 100 ms | 100 ms | 100 ms |
| `post_overload_healthy` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `hop.order.p50_ms` | — | — | 22.0 ms | 12.5 ms | 8.66 ms |
| `hop.gateway.p50_ms` | — | — | 28.8 ms | 17.2 ms | 12.8 ms |

### P02 — Sabit uzun yük (soak) — kararlılık ve sızıntı

Uzun süre sabit yük altında gecikmenin kayıp kaymadığını (drift) ve proxy'lerin bellek kullanımının büyümediğini (sızıntı) göstermek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `rate_rps` | 200 RPS | 200 RPS | 200 RPS | 200 RPS | 200 RPS |
| `duration_s` | 120 sn | 120 sn | 120 sn | 120 sn | 120 sn |
| `q0.p99_ms` | 16.9 ms | 18.0 ms | 23.7 ms | 22.5 ms | 19.8 ms |
| `q0.p50_ms` | 10.2 ms | 10.8 ms | 13.9 ms | 14.2 ms | 12.5 ms |
| `q1.p99_ms` | 16.9 ms | 17.5 ms | 23.2 ms | 22.1 ms | 19.4 ms |
| `q1.p50_ms` | 10.3 ms | 10.8 ms | 13.9 ms | 14.5 ms | 12.6 ms |
| `q2.p99_ms` | 17.0 ms | 17.2 ms | 21.5 ms | 23.3 ms | 19.8 ms |
| `q2.p50_ms` | 10.3 ms | 10.8 ms | 13.7 ms | 14.6 ms | 12.7 ms |
| `q3.p99_ms` | 16.8 ms | 17.7 ms | 22.5 ms | 27.5 ms | 19.8 ms |
| `q3.p50_ms` | 10.3 ms | 10.7 ms | 13.7 ms | 15.2 ms | 12.7 ms |
| `p50_ms` | 10.3 ms | 10.8 ms | 13.8 ms | 14.6 ms | 12.6 ms |
| `p99_ms` | 16.9 ms | 17.6 ms | 22.8 ms | 24.1 ms | 19.7 ms |
| `error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `p99_drift` | 0.992 kat | 0.979 kat | 0.951 kat | 1.22 kat | 0.998 kat |
| `app.mem_first_mib` | 128 MiB | 131 MiB | 121 MiB | 329 MiB | 133 MiB |
| `app.mem_last_mib` | 126 MiB | 127 MiB | 125 MiB | 157 MiB | 128 MiB |
| `app.mem_growth_mib` | -2.10 MiB | -3.50 MiB | 3.60 MiB | -172 MiB | -4.50 MiB |
| `p99_drift_limit_ms` | 26.9 ms | 28.0 ms | 35.5 ms | 33.7 ms | 29.9 ms |
| `ztunnel.mem_first_mib` | — | 29.2 MiB | 26.8 MiB | — | — |
| `ztunnel.mem_last_mib` | — | 28.0 MiB | 26.3 MiB | — | — |
| `ztunnel.mem_growth_mib` | — | -1.20 MiB | -0.500 MiB | — | — |
| `control.mem_first_mib` | — | 59.0 MiB | 61.3 MiB | 73.8 MiB | 80.5 MiB |
| `control.mem_last_mib` | — | 58.1 MiB | 63.9 MiB | 74.2 MiB | 80.6 MiB |
| `control.mem_growth_mib` | — | -0.900 MiB | 2.60 MiB | 0.400 MiB | 0.100 MiB |
| `waypoint.mem_first_mib` | — | — | 49.4 MiB | — | — |
| `waypoint.mem_last_mib` | — | — | 53.2 MiB | — | — |
| `waypoint.mem_growth_mib` | — | — | 3.80 MiB | — | — |
| `sidecar.mem_first_mib` | — | — | — | 1 629 MiB | 101 MiB |
| `sidecar.mem_last_mib` | — | — | — | 1 626 MiB | 97.9 MiB |
| `sidecar.mem_growth_mib` | — | — | — | -3.90 MiB | -3.50 MiB |

### P03 — Ani yük (spike) — dayanım ve toparlanma

Ani trafik sıçramasında hata oranını ve sistemin normale dönme süresini ölçmek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `spike_rps` | 700 RPS | 700 RPS | 700 RPS | 700 RPS | 700 RPS |
| `spike_duration_s` | 20.0 sn | 20.0 sn | 20.0 sn | 20.0 sn | 20.0 sn |
| `before.p50_ms` | 10.4 ms | 11.0 ms | 13.8 ms | 13.8 ms | 12.5 ms |
| `before.p99_ms` | 16.8 ms | 18.0 ms | 22.2 ms | 21.0 ms | 18.9 ms |
| `before.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `before.dropped` | 0 istek | 0 istek | 0 istek | 0 istek | 0 istek |
| `spike.p50_ms` | 10.6 ms | 10.9 ms | 2 139 ms | 904 ms | 45.5 ms |
| `spike.p99_ms` | 17.8 ms | 18.1 ms | 3 593 ms | 2 079 ms | 149 ms |
| `spike.error_rate` | 0 oran | 0 oran | 0.000 oran | 0 oran | 0 oran |
| `spike.dropped` | 0 istek | 0 istek | 2 794 istek | 1 207 istek | 45.0 istek |
| `after.p50_ms` | 10.4 ms | 10.9 ms | 14.2 ms | 14.2 ms | 12.5 ms |
| `after.p99_ms` | 16.7 ms | 17.6 ms | 1 152 ms | 24.0 ms | 19.2 ms |
| `after.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `after.dropped` | 0 istek | 0 istek | 89.0 istek | 27.0 istek | 0 istek |
| `recovery_s` | 5.00 sn | 5.00 sn | 5.00 sn | 5.00 sn | 5.00 sn |

### P04 — Uçtan uca yol — edge -> DMZ -> ingress -> zincir

Gerçek kullanıcı yolundaki toplam gecikmeyi ölçmek (edge LB, DMZ ingress A/B, cluster-a ingress, mesh'li ingress -> gateway kenarı dahil) ve küme içi ölçümle (P01) kıyaslamak.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `stage0.target_rps` | 100 RPS | 100 RPS | 100 RPS | 100 RPS | 100 RPS |
| `stage0.p50_ms` | 11.1 ms | 11.9 ms | 15.5 ms | 15.0 ms | 13.7 ms |
| `stage0.p95_ms` | 15.7 ms | 16.8 ms | 21.3 ms | 19.7 ms | 18.6 ms |
| `stage0.p99_ms` | 17.8 ms | 18.6 ms | 26.0 ms | 22.3 ms | 20.6 ms |
| `stage0.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `stage1.target_rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `stage1.p50_ms` | 11.1 ms | 11.7 ms | 28.8 ms | 16.0 ms | 14.1 ms |
| `stage1.p95_ms` | 15.5 ms | 16.3 ms | 74.1 ms | 22.2 ms | 19.2 ms |
| `stage1.p99_ms` | 17.7 ms | 18.6 ms | 116 ms | 27.4 ms | 21.9 ms |
| `stage1.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `tls_handshake_p50_ms` | 0 ms | 0 ms | 0 ms | 0 ms | 0 ms |

### P05 — Kaynak tüketimi — kalem kalem maliyet

Mesh'in her bileşeninin boşta ve sabit yük altında harcadığı CPU/belleği ve kapasite planlamasında "ayrılan" kaynak isteklerini (requests) ölçmek. Ambient / sidecar / Linkerd maliyet tablosunun ve prod projeksiyonunun ana girdisi.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `rate_rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `load.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `load.p50_ms` | 10.3 ms | 10.8 ms | 14.3 ms | 17.3 ms | 14.8 ms |
| `load.p99_ms` | 16.9 ms | 17.5 ms | 25.7 ms | 57.2 ms | 31.6 ms |
| `load.rps` | 250 RPS | 250 RPS | 250 RPS | 250 RPS | 250 RPS |
| `shop_pods` | 19.0 adet | 19.0 adet | 19.0 adet | 19.0 adet | 19.0 adet |
| `shop_pods_running` | 19.0 adet | 19.0 adet | 20.0 adet | 38.0 adet | 19.0 adet |
| `dataplane.cpu_cores` | 0 çekirdek | 0.230 çekirdek | 0.915 çekirdek | 1.67 çekirdek | 1.09 çekirdek |
| `dataplane.cpu_per_1k_rps` | 0 çekirdek | 0.922 çekirdek | 3.66 çekirdek | 6.67 çekirdek | 4.36 çekirdek |
| `dataplane.mem_idle_mib` | 0 MiB | 115 MiB | 163 MiB | 643 MiB | 83.4 MiB |
| `dataplane.mem_per_pod_mib` | 0 MiB | 6.05 MiB | 8.56 MiB | 33.8 MiB | 4.39 MiB |
| `node_overhead_cores` | 0.048 çekirdek | 0.015 çekirdek | 0.100 çekirdek | 0.188 çekirdek | 0.143 çekirdek |
| `derived.req_cpu_per_pod` | 0 çekirdek | 0.047 çekirdek | 0.050 çekirdek | 0.050 çekirdek | 0 çekirdek |
| `derived.req_mem_per_pod` | 0 MiB | 96.6 MiB | 98.2 MiB | 64.0 MiB | 0 MiB |
| `derived.cpu_per_1k_hops` | 0 çekirdek | 0.115 çekirdek | 0.458 çekirdek | 0.834 çekirdek | 0.544 çekirdek |

### P06 — Pod başlangıç süresi ve ölçeklenme hızı

Mesh'in yeni pod'ların hazır olma süresine etkisini ölçmek (sidecar enjeksiyonu, proxy başlatma, sertifika alma). Ani ölçeklenmede (HPA) ne kadar gecikme eklediğini gösterir.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `replicas` | 10.0 adet | 10.0 adet | 10.0 adet | 10.0 adet | 10.0 adet |
| `rounds` | 1.00 tur | 1.00 tur | 1.00 tur | 1.00 tur | 1.00 tur |
| `round1.all_ready_s` | 1.03 sn | 1.10 sn | 1.57 sn | 5.36 sn | 3.85 sn |
| `ready_p50_s` | 1.00 sn | 1.00 sn | 1.00 sn | 4.00 sn | 4.00 sn |
| `ready_p95_s` | 1.00 sn | 1.00 sn | 1.00 sn | 5.00 sn | 4.00 sn |
| `ready_max_s` | 1.00 sn | 1.00 sn | 1.00 sn | 5.00 sn | 4.00 sn |
| `all_ready_s` | 1.03 sn | 1.10 sn | 1.57 sn | 5.36 sn | 3.85 sn |

### P07 — Politika yayılma süresi ve kontrol düzlemi ölçeği

Bir erişim kuralı değiştiğinde ne kadar sürede yürürlüğe girdiğini ölçmek; cluster'daki servis sayısı arttığında kontrol düzleminin ve proxy'lerin kaynak tüketiminin nasıl büyüdüğünü göstermek (3.000 servislik prod için ölçeklenme göstergesi).

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `base.deny_s` | 1.10 sn | 0.230 sn | 0.250 sn | 0.240 sn | 0.150 sn |
| `base.allow_s` | 0.110 sn | 0.220 sn | 0.230 sn | 0.270 sn | 0.140 sn |
| `scale_services` | 30.0 adet | 30.0 adet | 30.0 adet | 30.0 adet | 30.0 adet |
| `control.mem_before_mib` | 0 MiB | 60.4 MiB | 65.8 MiB | 69.5 MiB | 78.7 MiB |
| `control.mem_after_mib` | 0 MiB | 60.8 MiB | 70.4 MiB | 104 MiB | 92.9 MiB |
| `control.mem_growth_mib` | 0 MiB | 0.400 MiB | 4.60 MiB | 34.5 MiB | 14.2 MiB |
| `scaled.deny_s` | 1.12 sn | 0.240 sn | 0.240 sn | 0.350 sn | 0.150 sn |
| `scaled.allow_s` | 0.120 sn | 0.220 sn | 0.220 sn | 0.240 sn | 0.140 sn |
| `ztunnel.mem_growth_mib` | — | 2.80 MiB | 3.20 MiB | — | — |
| `sidecar.mem_per_container_before_mib` | — | — | — | 60.4 MiB | 4.94 MiB |
| `sidecar.mem_per_container_after_mib` | — | — | — | 57.0 MiB | 4.87 MiB |
| `sidecar.mem_per_container_growth_mib` | — | — | — | -3.33 MiB | -0.070 MiB |

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
| durum | Geçti | Kısmen / başarısız | Kısmen / başarısız | Geçti | Geçti |
| `naive.chain_ok` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `naive.e2e_ok` | 1.00 | 1.00 | 0 | 1.00 | 1.00 |
| `naive.pods_ready` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `mesh_specific_rules` | 0 adet | 1.00 adet | 3.00 adet | 0 adet | 0 adet |
| `impostor_access` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `shared_identity_bypass` | 0 /20 | 20.0 /20 | 20.0 /20 | — | — |

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
| `rotation.ztunnel_restart` | — | 1.00 | 1.00 | — | — |
| `rotation.error_rate` | — | 0.001 oran | 0.089 oran | 0.003 oran | 0.000 oran |
| `rotation.p99_ms` | — | 19.8 ms | 10 000 ms | 5 452 ms | 22.5 ms |

### R01 — Timeout, retry ve outlier detection (circuit breaking)

(A) Bir alt servis yavaşladığında mesh'in timeout + retry politikasının uçtan uca gecikmeyi sınırladığını ve retry'ların yükü ne kadar artırdığını (amplifikasyon) ölçmek. (B) Hatalı bir replika (sürekli 503) devredeyken outlier detection'ın onu devreden çıkardığını göstermek.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Geçti |
| `A.none.p50_ms` | 11.2 ms | 12.4 ms | 14.1 ms | 14.6 ms | 13.4 ms |
| `A.none.p99_ms` | 1 014 ms | 1 015 ms | 1 018 ms | 1 018 ms | 1 016 ms |
| `A.none.error_rate` | 0 oran | 0 oran | 0 oran | 0 oran | 0 oran |
| `B.none.p50_ms` | 10.4 ms | 11.6 ms | 12.9 ms | 13.4 ms | 12.1 ms |
| `B.none.p99_ms` | 17.4 ms | 18.5 ms | 21.3 ms | 20.5 ms | 18.9 ms |
| `B.none.error_rate` | 0 oran | 0.002 oran | 0.326 oran | 0.334 oran | 0.579 oran |
| `A.none.amplification` | — | — | 1.00 kat | 0.978 kat | 0.992 kat |
| `A.policy.p50_ms` | — | — | 14.1 ms | 14.6 ms | 13.4 ms |
| `A.policy.p99_ms` | — | — | 383 ms | 366 ms | 457 ms |
| `A.policy.error_rate` | — | — | 0.007 oran | 0.003 oran | 0.009 oran |
| `A.policy.amplification` | — | — | 0.999 kat | 1.21 kat | 1.25 kat |
| `B.none.amplification` | — | — | 0.675 kat | 0.665 kat | 1.01 kat |
| `B.policy.p50_ms` | — | — | 13.1 ms | 13.7 ms | 12.5 ms |
| `B.policy.p99_ms` | — | — | 20.6 ms | 20.6 ms | 19.5 ms |
| `B.policy.error_rate` | — | — | 0.008 oran | 0.011 oran | 0.004 oran |
| `B.policy.amplification` | — | — | 0.991 kat | 0.993 kat | 1.03 kat |

### R02 — Hata enjeksiyonu (fault injection)

Uygulama koduna dokunmadan, mesh üzerinden kontrollü hata ve gecikme enjekte edebilmek (kaos testi, dayanıklılık tatbikatı). Mesh'lerin bu yeteneğini ve doğruluğunu kıyaslamak.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Geçti |
| `method` | — | — | 0 | 0 | 1.00 |
| `observed_error_rate` | — | — | 0.097 oran | 0.102 oran | 0.102 oran |
| `p50_ms` | — | — | 13.6 ms | 14.1 ms | 12.9 ms |
| `p90_ms` | — | — | 208 ms | 21.9 ms | 54.7 ms |
| `p95_ms` | — | — | 212 ms | 214 ms | 208 ms |

### R03 — Yük altında pod kaybı (failover)

Yük altındayken servis replikaları kaybedildiğinde (deploy, node bakımı, çökme) kullanıcıya yansıyan hata sayısını ölçmek. Mesh'in bağlantı yönetimi / yeniden deneme davranışının etkisi.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `failed_requests` | 0 istek | 180 istek | 42.0 istek | 14.0 istek | 3.00 istek |
| `error_rate` | 0 oran | 0.009 oran | 0.002 oran | 0.001 oran | 0.000 oran |
| `p99_ms` | 16.9 ms | 17.7 ms | 26.8 ms | 27.1 ms | 19.8 ms |
| `max_ms` | 23.2 ms | 51.5 ms | 10 001 ms | 117 ms | 1 010 ms |

### R04 — Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması

"Mesh tek hata noktası mı?" sorusunu cevaplamak. (A) Kontrol düzlemi tamamen düştüğünde mevcut trafik akıyor mu, yeni pod'lar açılabiliyor ve trafik alabiliyor mu? (B) Ambient'te node başına paylaşılan ztunnel yeniden başlarsa o node'daki tüm pod'lar ne kadar etkilenir (arıza etki alanı)?

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Kısmen / başarısız | Geçti | Geçti |
| `A.new_pod_created` | — | 1.00 | 1.00 | 0 | 1.00 |
| `A.new_pod_ready` | — | 1.00 | 1.00 | 0 | 1.00 |
| `A.new_pod_meshed` | — | 1.00 | 1.00 | 0 | 0 |
| `A.new_pod_serving` | — | 0 | 0 | 0 | 0 |
| `A.error_rate` | — | 0 oran | 0.012 oran | 0 oran | 0 oran |
| `A.failed_requests` | — | 0 istek | 172 istek | 0 istek | 0 istek |
| `A.p99_ms` | — | 17.5 ms | 1 600 ms | 22.3 ms | 19.4 ms |
| `B.ztunnel_restart_s` | — | 27.0 sn | 26.0 sn | — | — |
| `B.failed_requests` | — | 0 istek | 2.00 istek | — | — |
| `B.error_rate` | — | 0 oran | 0.000 oran | — | — |
| `B.pods_on_node` | — | 19.0 adet | 20.0 adet | — | — |

### R05 — Yük altında kesintisiz mesh güncellemesi

Mesh sürüm güncellemesinin (yılda birkaç kez zorunlu) iş trafiğini kesip kesmediğini, ne kadar sürdüğünü ve hangi adımları gerektirdiğini ölçmek. Sidecar ile ambient arasındaki en büyük operasyonel fark beklenen kalem.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Geçti |
| `from_version` | — | 0 | 0 | 0 | 0 |
| `to_version` | — | 0 | 0 | 0 | 0 |
| `upgrade_duration_s` | — | 58.0 sn | 86.0 sn | 108 sn | 113 sn |
| `steps` | — | 4.00 adım | 5.00 adım | 6.00 adım | 4.00 adım |
| `restarted_pods` | — | 0 adet | 1.00 adet | 19.0 adet | 19.0 adet |
| `failed_requests` | — | 0 istek | 2.00 istek | 79.0 istek | 27.0 istek |
| `error_rate` | — | 0 oran | 0.000 oran | 0.001 oran | 0.000 oran |
| `p99_ms` | — | 17.6 ms | 21.0 ms | 34.5 ms | 20.2 ms |
| `max_ms` | — | 55.4 ms | 105 ms | 244 ms | 3 013 ms |

### T01 — Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma

Yeni sürümü (canary) kullanıcıların küçük bir kısmına açabilmek, belirli istekleri (başlık) yeni sürüme yönlendirebilmek ve gerçek trafiği yeni sürüme kopyalayıp (mirroring) cevabı kullanmadan deneyebilmek. Tüm mesh'lerde aynı standart (Gateway API HTTPRoute, GAMMA) kullanılır.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Uygulanamaz | Geçti | Geçti | Geçti |
| `baseline.v2_share` | 0.190 oran | 0.338 oran | 0.343 oran | 0.335 oran | 0.328 oran |
| `weighted.v2_share` | — | — | 0.092 oran | 0.105 oran | 0.085 oran |
| `header.v2_share` | — | — | 1.00 oran | 1.00 oran | 1.00 oran |
| `mirror.v2_share_in_responses` | — | — | 0 oran | 0 oran | 0.115 oran |
| `mirror.v2_received` | — | — | 0 istek | 0 istek | 0 istek |
| `mirror.supported` | — | — | 0 | 0 | 0 |

### T02 — Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği

Prod'daki protokollerin mesh'ten sorunsuz geçtiğini göstermek: (1) gRPC / HTTP2'de istek bazlı yük dağılımı (kube-proxy bağlantı bazlı dağıtır, uzun ömürlü bağlantı tek pod'a yapışır); (2) bağlantıyı önce sunucunun konuştuğu protokoller (SMTP, MySQL benzeri; Oracle/MSSQL/Kafka gibi TCP protokolleri için gösterge) — protokol algılama gecikmesi; (3) Redis / Postgres TCP trafiği.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `grpc.pods_used` | 2.00 adet | 2.00 adet | 3.00 adet | 3.00 adet | 3.00 adet |
| `grpc.max_share` | 0.503 oran | 0.543 oran | 0.410 oran | 0.377 oran | 0.437 oran |
| `banner.hint_ms` | 1.00 ms | 1.00 ms | 2.00 ms | 3.00 ms | 4.00 ms |
| `banner.nohint_ms` | 1.00 ms | 1.00 ms | — | — | 10 006 ms |

### T03 — Gateway API ile giriş (ingress-nginx'in yerine geçme)

ingress-nginx Mart 2026'da emekliye ayrıldı. Mesh'in kendi Gateway API uygulamasının küme girişini (north-south) üstlenip üstlenemeyeceğini göstermek: ayrı bir ingress ürününe gerek kalır mı?

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Uygulanamaz | Geçti | Geçti | Geçti | Uygulanamaz |
| `p50_ms` | — | 12.4 ms | 13.8 ms | 15.1 ms | — |

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
| `mesh_p99_ms` | — | — | 24.9 ms | 24.8 ms | 19.9 ms |
| `k6_p99_ms` | — | — | 20.9 ms | 21.1 ms | 19.3 ms |
| `latency_accuracy_ratio` | — | — | 1.19 kat | 1.18 kat | 1.03 kat |

### O02 — Metrik maliyeti — seri sayısı ve alım hızı

Mesh metriklerinin izleme altyapısına (Prometheus) getirdiği gizli maliyeti ölçmek: aktif zaman serisi sayısı ve saniyede alınan örnek sayısı. Prod'da 3.000 servise projeksiyonun girdisi.

| Metrik | Mesh yok (referans) | Istio ambient (L4) | Istio ambient + waypoint (L7) | Istio sidecar | Linkerd |
|---|---:|---:|---:|---:|---:|
| durum | Geçti | Geçti | Geçti | Geçti | Geçti |
| `series_total` | 62 458 seri | 80 279 seri | 84 801 seri | 97 467 seri | 106 648 seri |
| `series_mesh` | 0 seri | 732 seri | 4 782 seri | 14 538 seri | 21 957 seri |
| `shop_pods` | 19.0 adet | 19.0 adet | 20.0 adet | 19.0 adet | 19.0 adet |
| `series_mesh_per_pod` | 0 seri | 38.5 seri | 239 seri | 765 seri | 1 156 seri |
| `samples_per_s` | 10 599 örnek/sn | 13 866 örnek/sn | 14 792 örnek/sn | 16 913 örnek/sn | 18 696 örnek/sn |

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
| `install_s` | — | 35.0 sn | 37.0 sn | 17.0 sn | 66.0 sn |
| `helm_releases` | — | 4.00 adet | 4.00 adet | 2.00 adet | 0 adet |
| `diag_issues` | — | 0 adet | 0 adet | 0 adet | 0 adet |

## 10. Envanter

- istio: `1.31.4`
- linkerd: `edge-26.11.2`
- k6: `grafana/k6:2.4.0`
- app: `mesh-eval/chainsvc:0.1.0`
- gateway_api: `v1.6.1`
- kubernetes: `v1.37.0`
- kind: `v0.33.0`
- ingress_nginx_chart: `4.15.1`
