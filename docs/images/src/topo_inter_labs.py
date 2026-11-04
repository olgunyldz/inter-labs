"""inter-labs topolojisi: edge LB → DMZ A/B → uygulama A/B → data, yan tarafta yönetim zone'u.
Çalıştırma: python docs/images/src/topo_inter_labs.py  (SVG üretir; PNG için README.md'deki komut)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from topo_style import Diagram, PALETTE

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "topology.svg")
OY = 50
W, H = 1400, 1490
d = Diagram(W, H)

# Sütunlar: sol (müşteri trafiği), sağ (yönetim)
LX0, LX1 = 40, 990
RX0, RX1 = 1040, 1370
AX0, AX1 = 65, 495     # A kutuları
BX0, BX1 = 535, 965    # B kutuları

# ---------------- Güven sınırları
d.boundary([(20, 88), (690, 88), (690, 204), (20, 204)], "İNTERNET · GÜVENİLMEYEN AĞ", "public", fill_opacity=0.55)
d.boundary([(700, 88), (1012, 88), (1012, 204), (700, 204)], "KURUM WAN · ÖZEL HAT", "wan", fill_opacity=0.7)
d.boundary([(1026, 88), (1384, 88), (1384, 204), (1026, 204)], "KURUM AĞI · VPN", "wan", fill_opacity=0.7)
d.boundary([(14, 236), (1390, 236), (1390, 1150), (14, 1150)], "LAB PERİMETRESİ · DOCKER DESKTOP", "external")
d.boundary([(28, 676), (1004, 676), (1004, 1124), (28, 1124)], "PRIVATE · İNTERNETE KAPALI", "internal", label_at=(44, 1120))

# ---------------- Kanallar
d.channel(40, 110, 200, "Mobil Bankacılık", "iOS · Android")
d.channel(255, 110, 200, "İnternet Şubesi", "web · tarayıcı")
d.channel(470, 110, 200, "Partner API", "açık bankacılık · 3. taraf")
d.channel(715, 110, 135, "ATM", "ATM ağı")
d.channel(862, 110, 135, "POS", "üye işyeri")
d.channel(RX0 + 10, 110, RX1 - RX0 - 20, "Operasyon ekibi", "VPN · 127.0.0.1:9080 / 9443")

# ---------------- Edge
d.zone(LX0, 260, LX1 - LX0, 150, "Edge zone", right="lab-edge · 172.28.5.0/24", color="edge")
d.ns(280, 310, 470, 84, "edge-lb · HAProxy 3.0 (container)",
     ["L4 round-robin · /healthz her 3 sn, 2 hata → DOWN", "PROXY protocol ile istemci IP'si · istatistik :9404"], color="edge")
d.firewall(LX0, 424, LX1 - LX0, 22, "DMZ FW · yalnızca edge-lb → :80 / :443", tx=60)

# ---------------- DMZ
d.zone(LX0, 460, LX1 - LX0, 180, "DMZ zone · active-active", right="lab-dmz · 172.28.10.0/24", color="dmz")
for x0, x1, name in ((AX0, AX1, "dmz-a"), (BX0, BX1, "dmz-b")):
    d.ns(x0, 522, x1 - x0, 96, f"{name} · kind · ingress-nginx",
         ["TLS sonlandırma · X-Dmz başlığı", "app-pool → cluster-a + cluster-b"], color="dmz")
d.firewall(LX0, 654, LX1 - LX0, 22, "APP FW · DMZ → :80", tx=60)

# ---------------- Uygulama
d.zone(LX0, 690, LX1 - LX0, 200, "Uygulama zone · active-active", right="lab-app · 172.28.20.0/24", color="internal")
for x0, x1, name in ((AX0, AX1, "cluster-a"), (BX0, BX1, "cluster-b")):
    d.ns(x0, 752, x1 - x0, 118, f"{name} · kind · ingress-nginx",
         ["ns demo · demo-app ×2 (nginx)", "postgres.demo.svc → data :5432", "redis.demo.svc → data :6379"], color="internal")
d.firewall(LX0, 904, LX1 - LX0, 22, "DATA FW · uygulama → :5432 / :6379", tx=300)

# ---------------- Data
d.zone(LX0, 940, LX1 - LX0, 170, "Data zone", right="lab-data · 172.28.30.0/24", color="data")
d.ns(AX0, 1002, AX1 - AX0, 86, "PostgreSQL 16 · StatefulSet + PVC", ["ingress-nginx L4 (tcp-services) :5432 → postgres"], color="data")
d.ns(BX0, 1002, BX1 - BX0, 86, "Redis 7 · Deployment", ["ingress-nginx L4 (tcp-services) :6379 → redis"], color="data")

# ---------------- Yönetim
d.zone(RX0, 260, RX1 - RX0, 850, "Yönetim zone", ["lab-mgmt · 172.28.40.0/24"], color="mgmt")
d.ns(RX0 + 20, 340, RX1 - RX0 - 40, 110, "mgmt · kind · ingress-nginx",
     ["host :9080 / :9443", "her zone'a bir ağ bacağı", "API erişimi :6443"], color="mgmt")
d.t(RX0 + 24, 506, "ağ bacakları", 14.5, 600, PALETTE["mgmt"][2])
d.ns(RX0 + 20, 540, RX1 - RX0 - 40, 60, "lab-dmz → dmz-a, dmz-b", [], color="mgmt")
d.ns(RX0 + 20, 780, RX1 - RX0 - 40, 60, "lab-app → cluster-a, cluster-b", [], color="mgmt")
d.ns(RX0 + 20, 1015, RX1 - RX0 - 40, 60, "lab-data → data", [], color="mgmt")

# ---------------- Kapalı yollar
d.zone(LX0, 1172, RX1 - LX0, 126, "Kapalı yollar, failover ve kanallar (scripts/verify.sh ile test edildi)",
       ["kapalı: edge-lb → cluster-a/b · dmz → data · data → cluster-a/b",
        "dmz-a durdurulunca edge-lb onu ~10 sn'de DOWN işaretledi; trafiğin tamamı dmz-b'ye geçti",
        "lab'da beş kanal da aynı edge-lb'ye (127.0.0.1:443) ve demo-app'e gider; prod'da ATM/POS internetten değil özel hattan gelir"],
       center=True, color="note")

# ---------------- Oklar
# İnternet kanalları ve ATM/POS ayrı toplanıp edge-lb'ye girer (birleşme çizgileri oksuz)
for pts in ([(140, 188), (140, 214), (570, 214)], [(355, 188), (355, 214)], [(570, 188), (570, 214)],
            [(782, 188), (782, 214), (930, 214), (930, 188)]):
    d.e.append('<path d="M ' + " L ".join(f"{a},{b}" for a, b in pts) + '" fill="none" stroke="#2f7bd8" stroke-width="3"/>')
d.arrow([(515, 214), (515, 310)], blue=True, label="internet · TCP 443", lx=527, ly=254)
d.arrow([(770, 214), (770, 352), (752, 352)], blue=True)
d.t(782, 254, "özel hat · TCP 443", 15.5, 600, "#1f1f1f", layer=d.l)
d.arrow([(470, 394), (470, 456), (360, 456), (360, 522)], blue=True)
d.arrow([(560, 394), (560, 456), (700, 456), (700, 522)], blue=True)

d.arrow([(360, 618), (360, 752)], blue=True)
d.arrow([(460, 618), (600, 752)], blue=True)
d.arrow([(600, 618), (460, 752)], blue=True)
d.arrow([(700, 618), (700, 752)], blue=True)

d.arrow([(280, 870), (280, 1002)], blue=True, label="TCP 5432 / 6379", lx=292, ly=964)
d.arrow([(700, 870), (700, 1002)], blue=True)

d.arrow([(1320, 188), (1320, 340)], label="VPN · TCP 9443", lx=1308, ly=222, lanchor="end")
d.arrow([(RX0 + 20, 570), (BX1, 570)], dashed=True, label=":6443", lx=1015, ly=562, lanchor="middle")
d.arrow([(RX0 + 20, 810), (BX1, 810)], dashed=True, label=":6443", lx=1015, ly=802, lanchor="middle")
d.arrow([(RX0 + 20, 1045), (BX1, 1045)], dashed=True, label=":6443", lx=1015, ly=1037, lanchor="middle")

# ---------------- Lejant
ly = 1326
items = [("public", "internet"), ("wan", "kurum WAN / VPN"), ("edge", "edge"), ("dmz", "DMZ"),
         ("internal", "uygulama"), ("data", "veri"), ("mgmt", "yönetim"), ("external", "lab perimetresi")]
for i, (k, label) in enumerate(items):
    x = 40 + (i % 4) * 330
    y = ly + (i // 4) * 32
    fill, stroke, _ = PALETTE[k]
    d.n.append(f'<rect x="{x}" y="{y}" width="30" height="18" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    d.t(x + 40, y + 14, label, 14.5)
y = ly + 70
d.n.append(f'<line x1="40" y1="{y + 6}" x2="80" y2="{y + 6}" stroke="#2f7bd8" stroke-width="3"/>')
d.t(92, y + 11, "müşteri trafiği (zone geçişi)", 14.5)
d.n.append(f'<line x1="400" y1="{y + 6}" x2="440" y2="{y + 6}" stroke="#b3b3ad" stroke-width="1.8" stroke-dasharray="6 5"/>')
d.t(452, y + 11, "yönetim erişimi (Kubernetes API)", 14.5)
d.n.append(f'<line x1="760" y1="{y + 6}" x2="800" y2="{y + 6}" stroke="#6d9fe4" stroke-width="3" stroke-dasharray="14 8"/>')
d.t(812, y + 11, "güven sınırı", 14.5)

d.save(OUT, "inter-labs topolojisi: internete yalnızca edge-lb bakar; her katman A/B active-active",
       "Aşağı indikçe güven artar · TLS DMZ'de sonlanır · her zone ayrı Docker ağı, geçişler yalnızca gösterilen portlardan · 6 kind cluster + 1 HAProxy · Kubernetes v1.37",
       oy=OY)
print("ok", OUT)
