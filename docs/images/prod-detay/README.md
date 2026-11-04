# Prod hedef mimarisi: genelden pod içine

Bu klasör, bankanın prod ortamında olması gereken mimariyi gösterir: iki veri merkezi, zone'lar, .NET mikroservisler, legacy monolith ve veri katmanı. Resimler büyük resimden başlar; her adımda bir katman içeri girer. Lab (demo) ortamının karşılığı: [lab-detay](../lab-detay/README.md).

## Kurumun verdiği bilgiler (teyitli)

- **İki DC:** DC1'de cluster-a ve cluster-b (active-active), DC2 (DR) tek cluster.
- **Cluster'lar:** DMZ (dmz-a / dmz-b), uygulama, data ve mgmt. Girişler ingress-nginx.
- **Uygulamalar:** .NET mikroservisler. Legacy monolith'in bir kısmı VM'de (.NET Framework / IIS), taşınan modüller cluster'da.
- **Veri:** Kafka, RabbitMQ ve Couchbase data cluster'ında. Oracle (core banking + monolith) ve MSSQL (yeni mikroservisler) VM'de.
- **Kanallar:** mobil, web, partner (internet) · şube kullanıcıları (kurum WAN → şube zone: branch-fw → branch-gateway → uygulama; DMZ'ye girmez) · ATM, POS (özel hat → PCI).

Bunların dışındaki ürün ve servis adları (F5, Strimzi, Keycloak, Vault, Harbor, Argo CD, MassTransit, servis adları, replika sayıları, RPO değerleri) **öneridir**; resimlerde "öneri" olarak geçer ve kurumun mevcut araçlarıyla eşlenmelidir.

## Okuma sırası

| # | Resim | Ne gösterir |
|---|-------|-------------|
| 00 | [Genel bakış](00-genel-bakis.png) | İki DC, kanallar, GSLB, tüm zone'lar (edge, kart, şube, kimlik, legacy dahil hepsi kutularla); her cluster'ın namespace'leri (uygulama zone'unda servisleriyle ayrı kutular), girişi (ingress-nginx) ve çıkışı (egress gateway); dış çıkış zone'u ve dış dünya (EFT/FAST, SWIFT, SMS, kart şemaları …); replikasyon yönleri |
| 01 | [Giriş](01-giris-edge-pci.png) | Kanallar, DDoS, GSLB, F5 + WAF + NGFW, kanal → VIP → DMZ ingress eşlemesi, ATM / POS → kart (PCI) zone'u |
| 02 | [DMZ cluster'ı](02-dmz-cluster.png) | Kanal başına ingress-nginx, auth-proxy, token handler, rate limit, egress; ingress anotasyon örnekleri |
| 03 | [Uygulama cluster'ı](03-uygulama-cluster.png) | .NET mikroservis namespace'leri, entegrasyon (ACL, core-adapter, CDC), platform, servis → veri bağımlılıkları |
| 04 | [.NET pod içi](04-dotnet-pod-detay.png) | transfer-api, outbox-relay, notification-worker: probe, güvenlik, secret, MSSQL / Kafka / RabbitMQ / Couchbase bağlantıları |
| 05 | [Legacy monolith](05-legacy-monolith-strangler.png) | IIS VM'leri, strangler yönlendirme (ingress-nginx), Oracle CDC, ACL, 6 adımlık taşıma süreci |
| 06 | [Veri katmanı](06-veri-katmani.png) | Kafka, RabbitMQ, Couchbase (operator) ve Oracle RAC, MSSQL AG; kim nereye bağlanır |
| 07 | [DR ve replikasyon](07-dr-replikasyon.png) | Bileşen başına replikasyon yöntemi, örnek RPO / RTO, failover sırası |
| 08 | [Mgmt](08-mgmt.png) | CI/CD (.NET), registry, deploy, gözlem, Vault, yedekleme; tek yönlü telemetri |
| 09 | [Uçtan uca · mobil](09-uctan-uca-mobil-transfer.png) | Mobil para transferi: giriş, kimlik, BFF, MSSQL + outbox, RabbitMQ, core, Kafka |
| 10 | [Uçtan uca · web](10-uctan-uca-web-fatura.png) | İnternet şubesinden fatura ödeme: cookie → token-handler → iç JWT, payment-api, core |
| 11 | [Uçtan uca · şube](11-uctan-uca-sube-havale.png) | Gişeden havale: kurum WAN → şube zone'u (branch-fw, branch-gateway) → branch-bff, 4 göz, fraud |
| 12 | [Uçtan uca · partner](12-uctan-uca-partner-hesap.png) | Açık bankacılık hesap bilgisi: TPP mTLS, kota, consent kontrolü, Couchbase önbellek |
| 13 | [Uçtan uca · POS](13-uctan-uca-pos-yetkilendirme.png) | Kartlı alışveriş yetkilendirmesi: acquirer → kart şeması → PCI switch, HSM, tokenization, card-api |
| 14 | [Uçtan uca · ATM](14-uctan-uca-atm-para-cekme.png) | Kendi ATM'sinden para çekme: ATM ağı → PCI switch → card-api → core, ters kayıt, SMS |
| 15 | [Şube zone'u](15-sube-zone.png) | SD-WAN hub, branch-fw, branch-gateway (ingress-nginx, cihaz sertifikası), şube bazlı kurallar |
| 16 | [Kimlik zone'u](16-kimlik-zone.png) | IdP, MFA / OTP, cihaz kaydı, consent, AD bağlantısı (namespace'ler); token türleri ve ömürleri |
| 17 | [Kart (PCI) zone'u](17-kart-pci-zone.png) | atm-pos-fw, card-switch, HSM, tokenization; PCI DSS kontrolleri özeti |

## draw.io

Bu klasördeki resimler, diğer setlerle birlikte tek dosyada ve her biri ayrı sayfa (sekme) olarak: [`../inter-labs.drawio`](../inter-labs.drawio). draw.io / diagrams.net'te **Dosya → Aç** ile açılır. Resim değil, draw.io bileşenleri: zone, namespace, node ve pod'lar container (içindekiler birlikte taşınır), kutuların yazısı kendi içinde, oklar bağlandığı şekle bağlı. Aynı üreteçten çıkar: `python docs/images/src/drawio.py`.

## Yeniden üretme

```bash
python docs/images/src/prod_detay.py            # hepsi; ya da: python docs/images/src/prod_detay.py 03 05
bash docs/images/src/render.sh docs/images/prod-detay
```

Kaynak: [`src/prod_detay.py`](../src/prod_detay.py). Prod bilgisi değiştikçe (yeni servis, farklı DB dağılımı, ürün kararı) ilgili resim güncellenir.
