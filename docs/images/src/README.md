# Topoloji diyagramları

Üreteçler yalnızca Python standart kütüphanesini kullanır. Stil service-mesh-labs ile aynıdır.

| Üreteç | Çıktı |
|---|---|
| `mimari.py` | `../mimari/00-hedef-mimari.svg`: **katmanlar ve teknolojiler** (logolu, faz rozetli); `--faz N`: o fazın sonunu gösteren yeni resim `faz-NN-*.svg` (üzerine yazmaz); bkz. [mimari/README.md](../mimari/README.md) |
| `prod_detay.py` | `../prod-detay/NN-*.svg`: **prod hedef mimarisi** (iki DC, .NET, monolith, Kafka, RabbitMQ, Couchbase, Oracle, MSSQL); bkz. [prod-detay/README.md](../prod-detay/README.md) |
| `lab_detay.py` | `../lab-detay/NN-*.svg`: bu makinedeki lab (demo) ortamı; bkz. [lab-detay/README.md](../lab-detay/README.md) |
| `topo_inter_labs.py` | `../topology.svg`: lab ortamının tek sayfalık özeti, 1400 px |
| `topo_style.py`, `detay_style.py` | ortak stil ve çizim yardımcıları (service-mesh-labs'tan kopya) |
| `drawio.py` | `../inter-labs.drawio`: yukarıdaki tüm resimler tek draw.io dosyasında, her biri ayrı sayfa (sekme) |
| `render.sh` | SVG → PNG (headless Edge; boyut SVG'den okunur, Edge boş dönerse yeniden dener) |

```bash
python docs/images/src/mimari.py                 # hedef; faz sonu: python docs/images/src/mimari.py --faz N
python docs/images/src/prod_detay.py
python docs/images/src/lab_detay.py
python docs/images/src/topo_inter_labs.py
bash docs/images/src/render.sh docs/images/prod-detay docs/images/lab-detay docs/images/topology.svg
python docs/images/src/drawio.py      # draw.io dosyası
```
