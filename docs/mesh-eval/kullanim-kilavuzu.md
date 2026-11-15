# mesh-eval kullanım kılavuzu

Service mesh değerlendirmesinin kurulması, testlerin çalıştırılması (tek tek veya tamamı), sonuçların
incelenmesi ve raporun üretilmesi. Kurulumun ayrıntıları için [kurulum.md](kurulum.md), testlerin ne
ölçtüğü için [test-senaryolari.md](test-senaryolari.md).

Tüm komutlar `mesh-eval/` dizininden çalıştırılır:

```bash
cd ~/Workspace/inter-labs/mesh-eval
bin/meval help
```

## 1. İlk kurulum (bir kez)

```bash
bash ../scripts/up.sh      # lab (yoksa / yeniden başlatma sonrası)
bin/meval tools            # mesh CLI'ları .tools/ altına
bin/meval setup            # gözlem + servis zinciri + doğrulama (~5 dk)
```

`setup` sonunda "Doğrulama tamam (aktif mesh: none)" görülmelidir. Ardından:

- **Grafana:** https://grafana.localtest.me:9443 (admin / mesh-eval) → `mesh-eval — test izleme`
- **Prometheus:** https://prometheus.localtest.me:9443
- **Uygulama:** https://shop.localtest.me (self-signed sertifika, `curl -k`)

## 2. Mesh profili seçmek

```bash
bin/meval mesh list                          # profiller ve aktif olan
bin/meval mesh use istio-sidecar --fresh     # temiz cluster'da kur (önerilen, ~8 dk)
bin/meval mesh use linkerd                   # mevcut cluster'da değiştir (~3 dk, hızlı deneme için)
bin/meval mesh verify                        # aktif mesh'i doğrula
bin/meval mesh status                        # mesh bileşenleri
```

| Profil | Açıklama |
|---|---|
| `none` | Mesh yok. Referans ölçüm |
| `istio-ambient` | Istio ambient, yalnızca L4 (ztunnel) |
| `istio-ambient-l7` | Istio ambient + shop için waypoint (L7) |
| `istio-sidecar` | Istio klasik sidecar |
| `linkerd` | Linkerd (edge) |

`--fresh` bench cluster'ını (cluster-a) silip yeniden kurar. Böylece önceki mesh'ten kalıntı (CRD, iptables
kuralı, webhook) olmaz. Rapora girecek ölçümler için her zaman `--fresh` kullanın.

## 3. Test çalıştırmak

```bash
bin/meval test list                          # 26 test, kategori, desteklenen mesh'ler
bin/meval test run P01                       # tek test, aktif mesh'te, quick profil
bin/meval test run P01 P05 S03               # birkaç test
bin/meval test run all                       # hepsi (sıra: P, S, T, O, R; R05 en sonda)
bin/meval test run P01 --profile full        # uzun profil (daha yüksek yük, daha uzun süre)
bin/meval test run P01 --repeat 3            # 3 tekrar (raporda medyan + min…max)
```

- **quick:** her testin kısa sürümü. Bir mesh için tüm testler ~45 dk.
- **full:** rapor için önerilen profil. Bir mesh için ~2.5 saat.

Testler istenildiği zaman, istenildiği sırayla yeniden çalıştırılabilir. Her koşu ayrı bir dizine yazılır;
eski sonuçların üzerine yazılmaz.

> **Not:** R05 (mesh güncellemesi) mesh'i bir önceki sürümle yeniden kurar ve sonunda hedef sürüme getirir.
> Tek başına çalıştırıldıktan sonra diğer testlere geçmeden önce `bin/meval mesh use <profil> --fresh` önerilir.

## 4. Tam değerlendirme (tüm mesh'ler × tüm testler)

```bash
SESSION=degerlendirme-1 bin/meval suite --profile full --repeat 3
```

Her mesh için sırayla: temiz cluster → mesh kurulumu → doğrulama → tüm testler. Seçenekler:

```bash
bin/meval suite --meshes none,istio-ambient,istio-sidecar --tests P01,P05,S03
bin/meval suite --no-fresh            # cluster'ı sıfırlamadan (hızlı, ama kıyas için önerilmez)
```

Uzun süreceği için oturumu `tmux` / `screen` içinde ya da `nohup ... &` ile başlatın. İlerleme Grafana panosundan izlenebilir.

## 5. Sonuçlar

```bash
bin/meval results              # son 30 koşu: dizin, durum, süre
bin/meval results --last 100
```

Her koşu: `results/<zaman>_<test>_<mesh>_r<tekrar>/`

| Dosya | İçerik |
|---|---|
| `meta.json` | Test tanımı, mesh, profil, oturum, tekrar no, sürümler, git commit, başlangıç/bitiş, durum |
| `result.json` | Durum, kontroller (beklenen/gerçekleşen), metrikler (değer, birim, açıklama), bulgular, uygulanamaz nedeni |
| `log.txt` | Koşunun tam çıktısı |
| `raw/` | k6 özetleri ve logları, Prometheus zaman serileri, uygulanan politikalar (YAML), tcpdump sayıları, sertifikalar |

Durumlar:

| Durum | Anlamı |
|---|---|
| `pass` | Tüm kontroller geçti |
| `fail` | En az bir kontrol başarısız (ayrıntı `result.json` → `checks`) |
| `na` | Uygulanamaz: bu mesh'te yetenek yok (ör. Linkerd'de ingress Gateway API). Neden kaydedilir ve rapora "yetenek yok" olarak girer |
| `error` | Test yarıda kaldı (altyapı sorunu). `log.txt`'ye bakın, testi yeniden çalıştırın |

Sonuçlar git'e girmez (`.gitignore`). Saklamak veya paylaşmak için `results/` dizinini arşivleyin.

## 6. Rapor

```bash
bin/meval report                          # tüm sonuçlardan (her test x mesh için en son oturum)
bin/meval report --session degerlendirme-1  # yalnızca bu oturum
bin/meval report --out /tmp/rapor         # çıktı dizini
```

Çıktı `reports/<zaman>/`:

| Dosya | İçerik |
|---|---|
| `rapor.html` | Tek dosya, grafikler gömülü, açık/koyu tema, yazdırılabilir. Sunum ve paylaşım için |
| `rapor.md` | Grafiksiz Markdown sürüm |
| `veri.json` | Birleştirilmiş sonuçlar, puan kartı, projeksiyon (başka araçlara aktarım için) |

Rapor bölümleri:
1. Yönetici özeti
2. Puan kartı
3. Kalem kalem maliyet (ambient / sidecar / Linkerd)
4. 3.000 servis prod projeksiyonu
5. Test sonuç matrisi
6. Bulgular
7. Test detayları (amaç, yöntem, bileşenler, metrikler, kontroller, koşu kimlikleri)
8. Lisans / destek
9. Yöntem ve sınırlar
10. Envanter

Ayarlanabilir girdiler:

| Ne | Nerede |
|---|---|
| Puan kartı kalemleri ve ağırlıklar | `report/scorecard.yaml` (varsayılan eşit ağırlık) |
| Prod varsayımları | `config.env` içindeki `PROD_*` (servis, replika, node boyutu, toplam RPS…) |
| Lisans / destek metinleri | `report/static.yaml`. Rapordan önce güncelliği doğrulanmalı |

Varsayımlar değiştiğinde testleri yeniden koşmak gerekmez; yalnızca `bin/meval report` çalıştırın.

## 7. Ayarları değiştirmek

Kalıcı değişiklik için `config.env`, makineye özel değişiklik için `config.local.env` (git dışı) kullanın:

```bash
# config.local.env örneği
SVC_REPLICAS=3
P01_STAGES_FULL=200,400,800,1200,1600,2000,2500
P05_RATE=400
```

| Değişken | Etkisi |
|---|---|
| `ISTIO_VERSION`, `LINKERD_VERSION` (+ `_PREV_`) | Mesh sürümleri (R05: önceki sürümden yükseltme) |
| `CPUSET_*` | Node CPU yerleşimi (`bin/meval setup` ile uygulanır) |
| `SVC_TIMING_*`, `SVC_REPLICAS` | Servis zincirinin yapay işlem süresi / replika (sonrasında `bin/meval setup`) |
| `P01_STAGES_QUICK/FULL`, `P01_SLO_P99_MS` | P01 aşamaları ve SLO eşiği |
| `P02_RATE_*`, `P03_SPIKE_*`, `P05_RATE` | P02, P03 ve P05 yük seviyeleri |
| `PROD_*` | Rapordaki prod projeksiyonu |

Test tanımları değişirse dokümanı güncelleyin:

```bash
bin/meval docs     # docs/mesh-eval/test-senaryolari.md yeniden üretilir
```

## 8. Yeni test eklemek

1. `tests/<ID>/test.yaml` oluşturun. Alanlar: `id`, `name`, `category`, `purpose`, `method`, `components`, `meshes`, `profiles`, `outputs`, `pass_criteria`.
2. `tests/<ID>/run.sh` yazın. Bu dosya test çerçevesi içinde `source` edilir ve şu yardımcılar kullanılabilir:

   | Yardımcı | İşlev |
   |---|---|
   | `check <ad> <beklenen> <gerçekleşen>` | Eşitlik kontrolü |
   | `check_le` / `check_ge` | Sayısal sınır kontrolü |
   | `check_true` | Komut başarılıysa geçer |
   | `metric <anahtar> <değer> [birim] [açıklama]` | Metrik kaydı |
   | `finding <metin>` | Rapora girecek bulgu |
   | `na <neden>` | Bu mesh'te uygulanamaz |
   | `on_exit <komut>` | Test bitince (hata olsa da) çalışacak temizlik |
   | `profile_val <quick> <full>` | Profile göre değer |
   | `k6_run` / `k6_start` / `k6_wait`, `k6_val` | Yük çalıştırma ve özet okuma |
   | `resources_snapshot`, `role_cpu`, `role_mem`, `role_requests` | Kaynak ölçümü |
   | `prom_query`, `prom_scalar`, `prom_save` | Prometheus sorguları |
   | `http_code`, `expect_access`, `chain_ok`, `probe_pod`, `authz_render` | İstemci ve politika yardımcıları |

3. Gerekirse `report/scorecard.yaml`'a puan kalemi ekleyin; `bin/meval docs` çalıştırın.

## 9. Temizlik

```bash
bin/meval mesh use none          # mesh'i kaldır (servis zinciri kalır)
kind delete cluster --name cluster-a && bash ../scripts/up.sh   # bench'i lab'ın ilk haline döndür
docker rm -f meval-ext-allowed meval-ext-denied                 # egress hedefleri
bash ../scripts/down.sh          # tüm lab
```

## 10. Sık karşılaşılanlar

| Durum | Çözüm |
|---|---|
| Test `error` ile bitti | `results/<koşu>/log.txt` son satırlar; çoğu zaman geçici: aynı testi yeniden çalıştırın |
| `k6 zaman aşımı` | loadgen node'unda pod durumu: `kubectl --context kind-cluster-a -n loadgen get pods` |
| Mesh değiştirdikten sonra garip sonuçlar | `--fresh` ile yeniden kurun |
| Host yeniden başladı | `bash ../scripts/up.sh && bin/meval setup` (CPU sabitleme ve CoreDNS ayarları yeniden uygulanır), sonra `mesh use` |
| Rapor bir mesh'i göstermiyor | O mesh için koşu yok ya da `--session` filtresi dışında: `bin/meval results` |
