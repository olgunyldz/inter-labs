# Service mesh değerlendirmesi (mesh-eval)

inter-labs topolojisi üzerinde üç service mesh'in (Istio ambient, Istio sidecar, Linkerd) aynı servis
zinciri ve aynı yükle, mesh'siz referansa karşı kıyaslanması. Sonuçlar üst yönetime sunulacak rapora
dönüştürülür.

| Doküman | İçerik |
|---|---|
| [kullanim-kilavuzu.md](kullanim-kilavuzu.md) | Kurulum, mesh seçme, test çalıştırma, sonuçlar, rapor, ayarlar, yeni test ekleme |
| [kurulum.md](kurulum.md) | Mimari, kurulum adımları, doğrulama kontrolleri, kurulum sırasında tespit edilenler |
| [envanter.md](envanter.md) | Tüm bileşenler, sürümler, node yerleşimi, rol bazında ölçüm tanımları |
| [test-senaryolari.md](test-senaryolari.md) | 26 testin amacı, yöntemi, bileşenleri, başarı ölçütü; test x bileşen matrisi |

## Kapsam

| Alan | Testler |
|---|---|
| Performans ve maliyet | P01 kademeli yük, P02 uzun yük, P03 ani yük, P04 uçtan uca, P05 kaynak (kalem kalem), P06 pod başlangıcı, P07 politika yayılma / ölçek |
| Güvenlik / whitelisting | S01 mTLS, S02 NetworkPolicy, S03 kimlik bazlı, S04 endpoint (L7), S05 DMZ endpoint, S06 atlatma, S07 egress, S08 sertifika / CA rotasyonu |
| Trafik yönetimi | T01 kademeli yayın, T02 protokoller (gRPC, server-first TCP, DB), T03 Gateway API ingress |
| Gözlem / operasyon | O01 metrik, trace, log; O02 metrik maliyeti; O03 operasyon envanteri |
| Dayanıklılık | R01 timeout/retry/outlier, R02 hata enjeksiyonu, R03 pod kaybı, R04 kontrol düzlemi kaybı, R05 kesintisiz güncelleme |

Kapsam dışı (sonraya bırakıldı): çok cluster'lı mesh (cluster-a ↔ cluster-b failover).

## Hızlı başlangıç

```bash
cd mesh-eval
bin/meval tools && bin/meval setup
SESSION=degerlendirme-1 bin/meval suite --profile full
bin/meval report --session degerlendirme-1
```
