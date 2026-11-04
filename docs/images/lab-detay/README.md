# Lab (demo) ortamı ayrıntılı topolojisi: genelden pod içine

Bu klasör, inter-labs ortamının ayrıntılı topolojisini gösterir: Docker ağları, kind cluster'ları, gerçek namespace, pod, container, port ve IP adları. Resimler büyük resimden başlar; her adımda bir katman içeri girer: zone → cluster → namespace → pod → container → node.

Her resimde **kırmızı kesikli kutular**, bir bankacılık platformunda o zone'da olması gereken ama lab'da bulunmayan servisleri gösterir. Kırmızı yazı, lab'ın bilinçli açık noktasıdır (ör. düz metin parola).

## Okuma sırası

| # | Resim | Ne gösterir | Seviye |
|---|-------|-------------|--------|
| 00 | [Genel bakış](00-genel-bakis.png) | Beş kanal, her zone'da lab'da çalışan ve olması gereken servisler, hedefteki Kimlik ve Kart (PCI) zone'ları, firewall geçişleri | Büyük resim |
| 01 | [Edge zone](01-edge-zone.png) | edge-lb (HAProxy): frontend / backend, sağlık kontrolü, PROXY protocol, istatistik; lab-edge ve lab-dmz ağları | Docker |
| 02 | [DMZ cluster'ları](02-dmz-cluster.png) | dmz-a / dmz-b namespace'leri, edge nesneleri (Ingress, selector'sız Service, EndpointSlice), ingress kuralları tablosu | Cluster |
| 03 | [DMZ pod içi](03-dmz-pod-detay.png) | ingress-nginx controller ayarları (PROXY, TLS, X-Dmz, upstream seçimi), node agent'ları, isteğin DMZ içindeki yolu | Pod |
| 04 | [Uygulama cluster'ları](04-app-cluster.png) | cluster-a / cluster-b namespace'leri, demo-app, veri servis nesneleri; hedefteki bankacılık servisleri | Cluster |
| 05 | [Uygulama pod içi](05-app-pod-detay.png) | demo-app pod'u (nginx, ConfigMap şablonu, probe, kaynak), ingress ayarları, veri servis yönlendirmesi | Pod |
| 06 | [Data cluster'ı](06-data-cluster.png) | tcp-services girişi, PostgreSQL StatefulSet + PVC, Redis; açık noktalar | Cluster / pod |
| 07 | [Mgmt cluster'ı](07-mgmt-cluster.png) | dört ağ bacağı, API erişim tablosu, olması gereken yönetim servisleri | Cluster |
| 08 | [Node anatomisi](08-node-anatomisi.png) | Bir kind node'u: kontrol düzlemi, pod'lar, DaemonSet'ler, paket yolu, port ve CIDR tabloları | Node |
| 09 | [Uçtan uca istek](09-uctan-uca-istek.png) | Müşteriden demo-app'e ve veri katmanına 11 adım: kimden → kime, port / protokol, yapılan iş | Akış |

## draw.io

Bu klasördeki resimler, diğer setlerle birlikte tek dosyada ve her biri ayrı sayfa (sekme) olarak: [`../inter-labs.drawio`](../inter-labs.drawio). draw.io / diagrams.net'te **Dosya → Aç** ile açılır. Resim değil, draw.io bileşenleri: zone, namespace, node ve pod'lar container (içindekiler birlikte taşınır), kutuların yazısı kendi içinde, oklar bağlandığı şekle bağlı. Aynı üreteçten çıkar: `python docs/images/src/drawio.py`.

## Yeniden üretme

```bash
python docs/images/src/lab_detay.py            # hepsi; ya da: python docs/images/src/lab_detay.py 03 05
bash docs/images/src/render.sh docs/images/lab-detay
```

Kaynak: [`src/lab_detay.py`](../src/lab_detay.py) (resimler), [`src/detay_style.py`](../src/detay_style.py) ve [`src/topo_style.py`](../src/topo_style.py) (service-mesh-labs'tan kopya ortak yardımcılar). IP'ler `lab_detay.py` başındaki `IP` tablosunda; Docker yeniden başlayıp IP'ler değişirse oradan güncellenir. İçerik `clusters/`, `platform/`, `workloads/`, `edge/` ve `scripts/` ile tutarlı tutulmalı: bir bileşen, port ya da kural değişirse ilgili resim de güncellenir.
