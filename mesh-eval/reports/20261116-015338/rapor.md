# Service Mesh Değerlendirme Raporu

Oluşturma: 16.11.2026 01:53 · Oturum: adhoc-20261116 · Profil: quick

> Grafikli tam sürüm: `rapor.html`

## 1. Yönetici özeti

- Puan kartı sıralaması (eşit ağırlık): Linkerd 92.
- Linkerd: başarısız/kısmi P02, S03, S05, S08; yetenek yok S07.
- Toplam 3 bulgu kaydedildi (bölüm 6).

## 2. Puan kartı

| Kategori | Linkerd |
|---|---:|
| Performans | 91.7 |
| Kaynak maliyeti | 100 |
| Güvenlik | 77.8 |
| Dayanıklılık | — |
| Trafik yönetimi | 100 |
| Gözlemlenebilirlik | — |
| Operasyon | — |
| **Toplam** | **92.4** |

## 4. Prod projeksiyonu (3.000 servis)

| Varsayım | Değer |
|---|---|
| Servis | 3000 |
| Servis başına replika | 3.0 |
| Pod | 9000 |
| Node başına pod | 30.0 |
| Node | 300 |
| Node boyutu | 16 vCPU / 64 GB |
| Toplam servisler arası istek hızı | 30000 RPS |
| Waypoint başına servis (ambient L7) | 10 |
| Waypoint | 300 |

| Kalem | Linkerd |
|---|---:|
| Veri düzlemi belleği | 51.2 GiB |
| Veri düzlemi CPU | 14.5 çekirdek |
| Ayrılan CPU | 0 çekirdek |
| Ayrılan bellek | 0 GiB |
| Node eşdeğeri (kullanılan) | 0.906 node |
| Node eşdeğeri (ayrılan) | 0 node |

## 5. Test sonuç matrisi

| Test | Linkerd |
|---|---|
| P01 Kademeli yük — gecikme ve kırılma noktası | ✅ Geçti |
| P02 Sabit uzun yük (soak) — kararlılık ve sızıntı | ⚠️ Kısmen / başarısız |
| P03 Ani yük (spike) — dayanım ve toparlanma | ✅ Geçti |
| P04 Uçtan uca yol — edge -> DMZ -> ingress -> zincir | ✅ Geçti |
| P05 Kaynak tüketimi — kalem kalem maliyet | ✅ Geçti |
| P06 Pod başlangıç süresi ve ölçeklenme hızı | ✅ Geçti |
| P07 Politika yayılma süresi ve kontrol düzlemi ölçeği | ✅ Geçti |
| S01 mTLS zorunluluğu ve hat üzerinde şifreleme | ✅ Geçti |
| S02 Servisler arası whitelisting — NetworkPolicy (L3/L4) | ✅ Geçti |
| S03 Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası) | ⚠️ Kısmen / başarısız |
| S04 Endpoint bazlı erişim kısıtı (L7 — path / method) | ✅ Geçti |
| S05 Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress) | ⚠️ Kısmen / başarısız |
| S06 Politika atlatma denemeleri | ✅ Geçti |
| S07 Dış çıkış (egress) whitelisting | ➖ Uygulanamaz |
| S08 Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu | ❌ Hata |
| R01 Timeout, retry ve outlier detection (circuit breaking) | · |
| R02 Hata enjeksiyonu (fault injection) | · |
| R03 Yük altında pod kaybı (failover) | · |
| R04 Mesh'in kendi arızası — kontrol düzlemi kaybı ve node proxy'si yeniden başlaması | · |
| R05 Yük altında kesintisiz mesh güncellemesi | · |
| T01 Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma | ✅ Geçti |
| T02 Protokol desteği — gRPC yük dağılımı, server-first TCP, veri tabanı trafiği | · |
| T03 Gateway API ile giriş (ingress-nginx'in yerine geçme) | · |
| O01 Gözlemlenebilirlik — hazır metrikler, doğruluk, dağıtık izleme, erişim logu | · |
| O02 Metrik maliyeti — seri sayısı ve alım hızı | · |
| O03 Operasyon envanteri — karmaşıklık ve ayrıcalık | · |

## 6. Bulgular


### Linkerd

- **S02** — NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP 200). Kimlik bazlı kural için mesh yetki politikası gerekir (S03).
- **S04** — linkerd: endpoint kuralı tek başına kubelet sağlık kontrollerini (/ready) engelledi; order pod'ları NotReady oldu. Probe yolları için ek kural gerekiyor (policies/linkerd-probes.yaml).
- **T01** — linkerd: trafik yansıtma (RequestMirror) çalışmadı: v2'ye 0 istek ulaştı (beklenen ~400). Route durumu: Accepted=True:Accepted ResolvedRefs=True:ResolvedRefs

## 7. Test detayları (metrikler)


### P01 — Kademeli yük — gecikme ve kırılma noktası

Artan istek hızında (RPS) servis zincirinin gecikmesini (p50/p95/p99) ve hata oranını ölçmek; sistemin bozulmaya başladığı noktayı (kırılma noktası) bulmak. Mesh'siz referansla kıyaslanınca mesh'in gecikme ve kapasite maliyetini verir.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `stages` | 4.00 adet |
| `stage_duration_s` | 30.0 sn |
| `stage0.target_rps` | 100 RPS |
| `stage0.rps` | 100 RPS |
| `stage0.p50_ms` | 4.80 ms |
| `stage0.p95_ms` | 7.81 ms |
| `stage0.p99_ms` | 8.82 ms |
| `stage0.p999_ms` | 10.7 ms |
| `stage0.error_rate` | 0 oran |
| `stage0.dropped` | 0 istek |
| `stage1.target_rps` | 300 RPS |
| `stage1.rps` | 300 RPS |
| `stage1.p50_ms` | 5.90 ms |
| `stage1.p95_ms` | 14.7 ms |
| `stage1.p99_ms` | 48.9 ms |
| `stage1.p999_ms` | 103 ms |
| `stage1.error_rate` | 0 oran |
| `stage1.dropped` | 0 istek |
| `hop.pricing.p50_ms` | 1.38 ms |
| `hop.gateway.p50_ms` | 4.29 ms |
| `hop.banner.p50_ms` | 0.500 ms |
| `hop.catalog.p50_ms` | 0.568 ms |
| `hop.ledger.p50_ms` | 0.575 ms |
| `hop.payment.p50_ms` | 1.88 ms |
| `hop.order.p50_ms` | 3.29 ms |
| `hop.inventory.p50_ms` | 1.99 ms |
| `hop.fraud.p50_ms` | 0.800 ms |
| `stage2.target_rps` | 600 RPS |
| `stage2.rps` | 447 RPS |
| `stage2.p50_ms` | 4.225 ms |
| `stage2.p95_ms` | 8.185 ms |
| `stage2.p99_ms` | 9.347 ms |
| `stage2.p999_ms` | 9.998 ms |
| `stage2.error_rate` | 0.001 oran |
| `stage2.dropped` | 4.583 istek |
| `stage3.target_rps` | 900 RPS |
| `stage3.rps` | 464 RPS |
| `stage3.p50_ms` | 6.696 ms |
| `stage3.p95_ms` | 9.877 ms |
| `stage3.p99_ms` | 10.001 ms |

### P02 — Sabit uzun yük (soak) — kararlılık ve sızıntı

Uzun süre sabit yük altında gecikmenin kayıp kaymadığını (drift) ve proxy'lerin bellek kullanımının büyümediğini (sızıntı) göstermek.

| Metrik | Linkerd |
|---|---:|
| durum | Kısmen / başarısız |
| `rate_rps` | 200 RPS |
| `duration_s` | 120 sn |
| `q0.p99_ms` | 9.94 ms |
| `q0.p50_ms` | 4.86 ms |
| `q1.p99_ms` | 9.98 ms |
| `q1.p50_ms` | 4.91 ms |
| `q2.p99_ms` | 18.8 ms |
| `q2.p50_ms` | 5.89 ms |
| `q3.p99_ms` | 15.7 ms |
| `q3.p50_ms` | 6.04 ms |
| `p50_ms` | 5.42 ms |
| `p99_ms` | 13.7 ms |
| `error_rate` | 0 oran |
| `p99_drift` | 1.58 kat |
| `app.mem_first_mib` | 226 MiB |
| `app.mem_last_mib` | 224 MiB |
| `app.mem_growth_mib` | -1.90 MiB |
| `sidecar.mem_first_mib` | 169 MiB |
| `sidecar.mem_last_mib` | 168 MiB |
| `sidecar.mem_growth_mib` | -0.500 MiB |
| `control.mem_first_mib` | 82.6 MiB |
| `control.mem_last_mib` | 82.6 MiB |
| `control.mem_growth_mib` | 0 MiB |

### P03 — Ani yük (spike) — dayanım ve toparlanma

Ani trafik sıçramasında hata oranını ve sistemin normale dönme süresini ölçmek.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `spike_rps` | 700 RPS |
| `spike_duration_s` | 20.0 sn |
| `before.p50_ms` | 4.84 ms |
| `before.p99_ms` | 9.04 ms |
| `before.error_rate` | 0 oran |
| `before.dropped` | 0 istek |
| `spike.p50_ms` | 1.547 ms |
| `spike.p99_ms` | 3.349 ms |
| `spike.error_rate` | 0 oran |
| `spike.dropped` | 2.098 istek |
| `after.p50_ms` | 5.42 ms |
| `after.p99_ms` | 818 ms |
| `after.error_rate` | 0 oran |
| `after.dropped` | 66.0 istek |
| `recovery_s` | 5.00 sn |

### P04 — Uçtan uca yol — edge -> DMZ -> ingress -> zincir

Gerçek kullanıcı yolundaki toplam gecikmeyi ölçmek (edge LB, DMZ ingress A/B, cluster-a ingress, mesh'li ingress -> gateway kenarı dahil) ve küme içi ölçümle (P01) kıyaslamak.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `stage0.target_rps` | 100 RPS |
| `stage0.p50_ms` | 6.15 ms |
| `stage0.p95_ms` | 9.36 ms |
| `stage0.p99_ms` | 11.2 ms |
| `stage0.error_rate` | 0 oran |
| `stage1.target_rps` | 250 RPS |
| `stage1.p50_ms` | 6.86 ms |
| `stage1.p95_ms` | 12.3 ms |
| `stage1.p99_ms` | 22.0 ms |
| `stage1.error_rate` | 0 oran |
| `tls_handshake_p50_ms` | 0 ms |

### P05 — Kaynak tüketimi — kalem kalem maliyet

Mesh'in her bileşeninin boşta ve sabit yük altında harcadığı CPU/belleği ve kapasite planlamasında "ayrılan" kaynak isteklerini (requests) ölçmek. Ambient / sidecar / Linkerd maliyet tablosunun ve prod projeksiyonunun ana girdisi.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `rate_rps` | 250 RPS |
| `load.error_rate` | 0 oran |
| `load.p50_ms` | 6.14 ms |
| `load.p99_ms` | 31.0 ms |
| `load.rps` | 250 RPS |
| `shop_pods` | 19.0 adet |
| `dataplane.cpu_cores` | 0.966 çekirdek |
| `dataplane.cpu_per_1k_rps` | 3.86 çekirdek |
| `dataplane.mem_idle_mib` | 166 MiB |
| `dataplane.mem_per_pod_mib` | 8.75 MiB |
| `node_overhead_cores` | 0.166 çekirdek |
| `derived.req_cpu_per_pod` | 0 çekirdek |
| `derived.req_mem_per_pod` | 0 MiB |
| `derived.cpu_per_1k_hops` | 0.483 çekirdek |

### P06 — Pod başlangıç süresi ve ölçeklenme hızı

Mesh'in yeni pod'ların hazır olma süresine etkisini ölçmek (sidecar enjeksiyonu, proxy başlatma, sertifika alma). Ani ölçeklenmede (HPA) ne kadar gecikme eklediğini gösterir.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `replicas` | 10.0 adet |
| `rounds` | 1.00 tur |
| `round1.all_ready_s` | 4.68 sn |
| `ready_p50_s` | 4.00 sn |
| `ready_p95_s` | 4.00 sn |
| `ready_max_s` | 4.00 sn |
| `all_ready_s` | 4.68 sn |

### P07 — Politika yayılma süresi ve kontrol düzlemi ölçeği

Bir erişim kuralı değiştiğinde ne kadar sürede yürürlüğe girdiğini ölçmek; cluster'daki servis sayısı arttığında kontrol düzleminin ve proxy'lerin kaynak tüketiminin nasıl büyüdüğünü göstermek (3.000 servislik prod için ölçeklenme göstergesi).

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `base.deny_s` | 0.180 sn |
| `base.allow_s` | 0.130 sn |
| `scale_services` | 30.0 adet |
| `control.mem_before_mib` | 77.9 MiB |
| `control.mem_after_mib` | 89.0 MiB |
| `control.mem_growth_mib` | 11.1 MiB |
| `sidecar.mem_per_container_before_mib` | 6.87 MiB |
| `sidecar.mem_per_container_after_mib` | 5.74 MiB |
| `sidecar.mem_per_container_growth_mib` | -1.12 MiB |
| `scaled.deny_s` | 0.160 sn |
| `scaled.allow_s` | 0.130 sn |

### S01 — mTLS zorunluluğu ve hat üzerinde şifreleme

Servisler arası trafiğin (1) mesh dışından şifresiz erişime kapalı olduğunu ve (2) ağ üzerinde gerçekten şifreli aktığını kanıtlamak. PCI DSS segmentasyon ve "iletimde şifreleme" kanıtı.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `marker_packets` | 0 paket |
| `control_packets` | 6.00 paket |

### S02 — Servisler arası whitelisting — NetworkPolicy (L3/L4)

Kubernetes NetworkPolicy ile servisler arası izin listesinin (varsayılan ret + zincir kuralları) her mesh ile birlikte doğru çalıştığını ve mesh'e özel ek kural gerekip gerekmediğini göstermek. Etiket bazlı kuralların "kimlik taklidi"ne açık olduğunu kanıtlamak.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `naive.chain_ok` | 1.00 |
| `naive.e2e_ok` | 1.00 |
| `naive.pods_ready` | 1.00 |
| `mesh_specific_rules` | 0 adet |
| `impostor_access` | 1.00 |

### S03 — Servisler arası whitelisting — kimlik bazlı (mesh yetki politikası)

Servisler arası erişimi IP/etiket yerine kriptografik kimlikle (ServiceAccount, mTLS sertifikası) kısıtlamak: varsayılan ret + her servis için izinli çağıranlar listesi. NetworkPolicy'den (S02) farkı: etiket taklidi işe yaramaz.

| Metrik | Linkerd |
|---|---:|
| durum | Kısmen / başarısız |
| `policy_objects` | 27.0 adet |
| `deny_http_code` | 403 kod |

### S04 — Endpoint bazlı erişim kısıtı (L7 — path / method)

Bir servisin yalnızca belirli endpoint'lerinin, belirli kimliklere ve HTTP metotlarına açık olmasını sağlamak (ör. /admin kapalı, yalnızca GET). Mesh içinde endpoint bazlı whitelisting.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `probes_ok_without_fix` | 0 |
| `deny_http_code` | 404 kod |

### S05 — Giriş noktasında endpoint bazlı erişim kısıtı (DMZ ingress)

Dışarıya açık bir endpoint'in (ör. /admin) yalnızca izinli kaynak IP'lerinden erişilebilir olmasını DMZ katmanında sağlamak; istemci IP'sinin sahte X-Forwarded-For başlığıyla taklit edilemediğini kanıtlamak. Mesh'ten bağımsızdır (DMZ cluster'larında mesh yok); her profilde aynı sonuç beklenir.

| Metrik | Linkerd |
|---|---:|
| durum | Kısmen / başarısız |
| `allowed_cidr` | 0 |

### S06 — Politika atlatma denemeleri

Yetki kurallarının (S03) yalnızca "doğru yoldan" gelen trafikte değil, kötü niyetli denemelerde de geçerli olduğunu kanıtlamak: mesh dışı pod, mesh'ten çıkarılmış pod (aynı kimlikle), host ağı, doğrudan pod IP'si, sahte kimlik başlıkları, proxy yönetim portları.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `admin_port_15000` | 0 |
| `admin_port_4191` | 0 |

### S07 — Dış çıkış (egress) whitelisting

Servislerin yalnızca izinli dış adreslere (FQDN) çıkabilmesini sağlamak; prod'daki ayrı dış çıkış zone'unun cluster içi karşılığı. Hangi mesh'in FQDN bazlı egress kısıtı yapabildiğini göstermek.

| Metrik | Linkerd |
|---|---:|
| durum | Uygulanamaz |

### S08 — Sertifika yönetimi — kurumsal CA, ömür, yük altında CA rotasyonu

İş yükü sertifikalarının bizim (kurumsal) CA'mızdan imzalandığını, kısa ömürlü olduğunu ve otomatik yenilendiğini; ara CA (issuer) yük altında değiştirildiğinde trafik kesilmediğini göstermek. Prod'da Vault gibi kurumsal CA ile entegrasyonun lab karşılığı.

| Metrik | Linkerd |
|---|---:|
| durum | Hata |

### T01 — Kademeli yayın — ağırlıklı yönlendirme, başlık bazlı yönlendirme, trafik yansıtma

Yeni sürümü (canary) kullanıcıların küçük bir kısmına açabilmek, belirli istekleri (başlık) yeni sürüme yönlendirebilmek ve gerçek trafiği yeni sürüme kopyalayıp (mirroring) cevabı kullanmadan deneyebilmek. Tüm mesh'lerde aynı standart (Gateway API HTTPRoute, GAMMA) kullanılır.

| Metrik | Linkerd |
|---|---:|
| durum | Geçti |
| `baseline.v2_share` | 0.325 oran |
| `weighted.v2_share` | 0.085 oran |
| `header.v2_share` | 1.00 oran |
| `mirror.v2_share_in_responses` | 0.098 oran |
| `mirror.v2_received` | 0 istek |
| `mirror.supported` | 0 |

## 10. Envanter

- istio: `1.31.4`
- linkerd: `edge-26.11.2`
- k6: `grafana/k6:2.4.0`
- app: `nicholasjackson/fake-service:v0.26.2`
- gateway_api: `v1.6.1`
- kubernetes: `v1.37.0`
- kind: `v0.33.0`
- ingress_nginx_chart: `4.15.1`
