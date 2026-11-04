"""Prod hedef mimarisi ayrıntılı seti: iki DC (DC1: cluster-a + cluster-b, DC2: DR tek cluster), .NET mikroservisler,
legacy monolith (VM + taşınan modüller cluster'da), Kafka · RabbitMQ · Couchbase (data cluster), Oracle · MSSQL (VM).
Çıktı: docs/images/prod-detay/NN-*.svg (PNG: bash docs/images/src/render.sh docs/images/prod-detay)
Çalıştırma: python docs/images/src/prod_detay.py [resim numaraları...]   (boş: hepsi)

Kurumun verdiği bilgiler (teyitli): Kubernetes · girişler ingress-nginx · DMZ cluster'ı (A/B) · uygulama cluster'ları A/B (DC1) ve DR (DC2)
· data cluster'ı · mgmt cluster'ı · .NET · legacy monolith · Kafka · RabbitMQ · Couchbase (data cluster'ında) · MSSQL · Oracle (VM)
· kanallar: mobil, web, partner, ATM, POS. Bunların dışındaki ürün adları (Strimzi, Keycloak, Vault, Harbor …) öneridir; resimlerde "öneri" yazar."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detay_style import D
from lab_detay import bh, ns_objs, ns_pods
from topo_style import PALETTE

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prod-detay")
os.makedirs(OUT, exist_ok=True)

NET = ".NET 8 · ASP.NET Core"
CONFIRMED = "teyitli: Kubernetes, ingress-nginx, .NET, monolith, Kafka, RabbitMQ, Couchbase, MSSQL, Oracle · diğer ürün adları öneri"


def out(name):
    return os.path.join(OUT, name)


def channels(d, y):
    d.boundary([(20, y), (860, y), (860, y + 116), (20, y + 116)], "İNTERNET · GÜVENİLMEYEN AĞ", "public", fill_opacity=0.55)
    d.boundary([(880, y), (1560, y), (1560, y + 116), (880, y + 116)], "KURUM WAN · ŞUBE AĞI · ÖZEL HAT", "wan", fill_opacity=0.7)
    d.boundary([(1580, y), (2180, y), (2180, y + 116), (1580, y + 116)], "KURUM AĞI · VPN", "wan", fill_opacity=0.7)
    for x, t, s in [(40, "Mobil Bankacılık", "iOS · Android · api.banka"), (320, "İnternet Şubesi", "web · www / ib.banka"),
                    (600, "Partner API", "açık bankacılık · mTLS"), (900, "Şube kullanıcıları", "gişe · operasyon · SD-WAN"),
                    (1120, "ATM", "ATM ağı · ISO 8583"), (1340, "POS", "üye işyeri · acquirer")]:
        d.channel(x, y + 22, 240 if x < 880 else 200, t, s)
    d.channel(1600, y + 22, 560, "Operasyon · yazılım ekipleri", "VPN → PAM / bastion → mgmt · CI/CD")


def merge_lines(d, segs, color="#2f7bd8", w=3):
    d.e.append('<path d="' + " ".join("M " + " L ".join(f"{a},{b}" for a, b in seg) for seg in segs)
               + f'" fill="none" stroke="{color}" stroke-width="{w}"/>')


def table(d, x, y, w, cols, rows, head_fill="#f1f3f6", stripe="#f7f9fc", size=12):
    """Basit tablo: cols = [(başlık, genişlik oranı)], rows = [[hücreler]]; döndürür: alt kenar"""
    xs = [x]
    for _, r in cols[:-1]:
        xs.append(xs[-1] + w * r)
    d.n.append(f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="4" fill="{head_fill}" stroke="#c4c4bf" stroke-width="0.8"/>')
    for (h, _), cx in zip(cols, xs):
        d.text(cx + 8, y + 18, h, size, 700)
    for i, row in enumerate(rows):
        yy = y + 28 + i * 26
        d.n.append(f'<rect x="{x}" y="{yy}" width="{w}" height="24" rx="3" fill="{stripe if i % 2 else "#ffffff"}" stroke="#d8d8d3" stroke-width="0.7"/>')
        for j, (cell, cx) in enumerate(zip(row, xs)):
            d.text(cx + 8, yy + 17, cell, size, 700 if j == 0 else 400, "#1f1f1f" if j == 0 else "#2b2b2b")
    return y + 28 + len(rows) * 26


LEG = [("public", "internet"), ("wan", "kurum WAN / VPN"), ("edge", "edge"), ("dmz", "DMZ"), ("internal", "uygulama (.NET)"),
       ("core", "legacy / core"), ("data", "veri"), ("identity", "kimlik"), ("pci", "kart / PCI"), ("mgmt", "yönetim / platform")]


# =====================================================================================================================
def cluster_box(d, x, y, w, title, ns_lines, in_txt, out_txt, color):
    """Cluster kutusu: başlık, namespace satırları, giriş (ingress) ve çıkış (egress) rozetleri; döndürür: alt kenar"""
    h = bh(len(ns_lines)) + 56
    d.box(x, y, w, h, title, ns_lines, color=color, size=13)
    d.badge(x + 10, y + bh(len(ns_lines)) + 12, in_txt, "in")
    d.badge(x + 10, y + bh(len(ns_lines)) + 38, out_txt, "out")
    return y + h


EG = "#c2410c"


def egress_flow(d, pts, label=None, lx=None, ly=None, anchor="start"):
    """Dışarı çıkış (egress) akışı: turuncu, kesikli"""
    path = "M " + " L ".join(f"{a},{b}" for a, b in pts)
    d.e.append(f'<path d="{path}" fill="none" stroke="{EG}" stroke-width="2.2" stroke-dasharray="8 4" marker-end="url(#ao)"/>')
    if label:
        d.t(lx, ly, label, 12, 600, EG, anchor, d.l)


DMZ_NS = [("ingress-mobile", ["ingress-nginx (nginx-mobile) ×3", "api.banka · rate limit"]),
          ("ingress-web", ["ingress-nginx (nginx-web) ×3", "www / ib · CSP · CSRF"]),
          ("ingress-partner", ["ingress-nginx (nginx-partner) ×3", "mTLS istemci sert. · kota"]),
          ("auth", ["auth-proxy ×3 → iç JWT", "token-handler ×2 (web)"]),
          ("ratelimit", ["ratelimit ×2", "sayaç: Couchbase"]),
          ("egress", ["egress-gateway ×2", "→ app · IdP · dış çıkış"]),
          ("platform", ["cert-manager · otel", "external-secrets · kyverno"])]

APP_NS = [("ingress-nginx", ["ingress-nginx (iç) ×3", "mTLS · iç JWT · strangler"]),
          ("channel-bff", ["mobile-bff ×3 · web-bff ×3", "partner-bff ×2", "branch-bff ×2 (şube)"]),
          ("account", ["account-api ×3 → MSSQL"]),
          ("customer", ["customer-api ×3 → MSSQL"]),
          ("card", ["card-api ×3 → PCI (mTLS)"]),
          ("transfer", ["transfer-api ×3 → MSSQL", "outbox-relay ×2 → Kafka"]),
          ("payment", ["payment-api ×3 → MSSQL"]),
          ("loan", ["loan-api ×2 → MSSQL"]),
          ("notification", ["notification-worker (KEDA)", "Kafka → RabbitMQ → SMS"]),
          ("fraud", ["fraud-scoring ×3", "Kafka · Couchbase profil"]),
          ("integration", ["monolith-adapter (ACL)", "core-adapter → Oracle", "cdc-consumers (KEDA)"]),
          ("legacy-modules", ["taşınan monolith", "modülleri (geçiş)"]),
          ("egress", ["egress-gateway ×2", "→ veri · DB · dış çıkış"]),
          ("platform", ["cert-manager · keda", "external-secrets · otel", "kyverno · fluent-bit"])]


EDGE_BOX = [("F5 LTM ×2 (HA)", ["kanal başına VIP", "TLS 1.2+/1.3 · HSTS"]), ("WAF", ["OWASP CRS · bot", "API şema doğrulama"]),
            ("dış NGFW", ["yalnızca :443", "IPS · DoS eşikleri"]), ("DDoS · CDN", ["sağlayıcı (banka dışı)", "scrubbing · statik içerik"])]
PCI_BOX = [("atm-pos-fw", ["ATM ağı · şema hatları", "IP izin listesi · IPsec"]), ("card-switch ×2", ["ISO 8583 · NDC / DDC", "yetkilendirme yönlendirme"]),
           ("HSM (ağ, HA)", ["PIN · EMV ARQC", "anahtar yönetimi"]), ("tokenization ×2", ["PAN ↔ token", "kasa DB (PCI içinde)"])]
SUBE_BOX = [("SD-WAN hub ×2", ["MPLS / SD-WAN", "şube başına tünel"]), ("branch-fw (HA)", ["iç firewall", "yalnızca :443"]),
            ("branch-gateway", ["ingress-nginx ×2 (A/B)", "cihaz sert. (mTLS)"]), ("şube servisleri", ["yazıcı · kuyruk sunucu", "personel SSO → AD"])]
KIMLIK_NS = [("iam", ["idp ×3 (öneri: Keycloak)", "token exchange · JWKS"]), ("mfa", ["otp-service ×2", "cihaz kaydı (mobil)"]),
             ("consent", ["consent-api ×2", "açık bankacılık onayı"]), ("directory", ["AD / LDAP bağlayıcı", "personel SSO"]),
             ("egress", ["egress-gateway ×2", "→ SMS / OTP sağlayıcı"]), ("platform", ["cert-manager · otel", "external-secrets"])]
LEGACY_BOX = [("NLB / iç VIP", ["monolith.banka.local", "yalnızca app ingress'ten"]), ("IIS VM ×N", ["ASP.NET · .NET Fwk 4.8", "taşınmamış modüller"]),
              ("batch / servis VM", ["gün sonu işleri", "Windows servisleri"]), ("bağlantılar", ["Oracle (ODP.NET)", "Kafka / RabbitMQ köprüsü"])]


def zone_behind(d, zi, *args, **kw):
    """Zone'u çiz ve zeminini zi konumuna (içindeki cluster kutularının altına) taşı"""
    zn = len(d.z)
    d.zone(*args, **kw)
    new = d.z[zn:]
    del d.z[zn:]
    d.z[zi:zi] = new


def cluster_ns_box(d, x, y, w, title, nss, in_txt, out_txt, color, cols=2, kind="ns"):
    """Cluster / segment kutusu: içinde namespace (kind=ns) ya da bileşen (kind=box: appliance, VM) kutuları ızgarası
    + giriş / çıkış rozetleri; döndürür: alt kenar"""
    fill, stroke, tcol = PALETTE[color]
    cw = (w - 20 - (cols - 1) * 10) / cols
    rows = [nss[i:i + cols] for i in range(0, len(nss), cols)]
    if kind == "box":
        hs = [bh(max(len(it) for _, it in r)) - 4 for r in rows]
    else:
        hs = [30 + 17 * max(len(it) for _, it in r) + 6 for r in rows]
    h = 34 + sum(hs) + 8 * len(rows) + 62
    d.z.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="{stroke}" stroke-width="1.6"/>')
    d.t(x + 12, y + 22, title, 14, 700, "#1f1f1f", layer=d.z)
    cy = y + 34
    for r, rh in zip(rows, hs):
        for j, (name, items) in enumerate(r):
            nx = x + 10 + j * (cw + 10)
            if kind == "box":
                d.box(nx, cy, cw, rh, name, items, color=color, size=12)
                continue
            d.nsbox(nx, cy, cw, rh, name, color)
            for k, it in enumerate(items):
                d.t(nx + 10, cy + 45 + k * 17, "■ " + it, 11.5, 400, "#2b2b2b", layer=d.z)
        cy += rh + 8
    d.badge(x + 10, cy + 14, in_txt, "in")
    d.badge(x + 10, cy + 40, out_txt, "out")
    return y + h


def img00():
    W, H, OY = 2200, 3240, 40
    d = D(W, H)
    d.e.append(f'<defs><marker id="ao" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
               f'<path d="M0,0 L10,5 L0,10 z" fill="{EG}"/></marker></defs>')
    channels(d, 100)
    d.box(40, 236, 820, bh(1), "GSLB (DNS) · iki DC'nin önünde", ["normalde DC1 · DC1 düşerse DC2 (DR) · sağlık kontrollü"], color="edge", size=13)

    LX, LW, RX, RW = 40, 960, 1020, 440      # DC1: sol (müşteri yolu), sağ (PCI, kimlik, legacy, DB)
    BW = 444                                  # cluster kutusu genişliği
    DX, DW = 1520, 642                        # DC2 (DR)

    # ---- Edge + kart (PCI)
    y_e = 360
    zi = len(d.z)
    e_cont = cluster_ns_box(d, LX + 24, y_e + 56, LW - 48, "edge cihazları · appliance (HA çift)", EDGE_BOX, "in ← internet :443 (GSLB → VIP-1/2/3)",
                            "out → DMZ ingress-nginx :443 (TLS yeniden şifreli)", "edge", cols=4, kind="box")
    p_cont = cluster_ns_box(d, RX + 24, y_e + 56, RW - 48, "kart segmenti · ayrı cluster / VM", PCI_BOX, "in ← ATM ağı · kart şemaları (özel hat)",
                            "out → card-api :443 (mTLS · yalnızca token)", "pci", kind="box")
    e_bot = max(e_cont, p_cont) + 20
    zone_behind(d, zi, LX, y_e, LW, e_bot - y_e, "Edge zone · DC1", right="internet tarafı · TLS / WAF", color="edge")
    zone_behind(d, zi, RX, y_e, RW, e_bot - y_e, "Kart zone · PCI DSS", right="ayrı segment", color="pci")
    d.link(870, y_e + 2, "01")
    d.link(1400, y_e + 2, "17")
    d.firewall(LX, e_bot + 10, LW, 22, "FW · edge → DMZ :443", tx=800)

    # ---- DMZ
    y_d = e_bot + 44
    b = 0
    zi = len(d.z)   # zone zemini cluster kutularının altında kalsın
    for x, n in ((LX + 24, "dmz-a"), (LX + 24 + BW + 24, "dmz-b")):
        b = cluster_ns_box(d, x, y_d + 56, BW, f"{n} · Kubernetes · 7 namespace", DMZ_NS, "in ← F5 VIP-1/2/3 → ingress-nginx :443",
                           "out → egress-gateway → app :443 · IdP · dış çıkış", "dmz")
    s_cont = cluster_ns_box(d, RX + 24, y_d + 56, RW - 48, "şube segmenti · appliance + gateway", SUBE_BOX, "in ← şube WAN (MPLS / SD-WAN) :443",
                            "out → app ingress :443 (mTLS + iç JWT)", "wan", kind="box")
    dmz_bot = max(b, s_cont) + 20
    zone_behind(d, zi, LX, y_d, LW, dmz_bot - y_d, "DMZ zone · dmz-a / dmz-b", right="iş mantığı ve veri yok", color="dmz")
    zone_behind(d, zi, RX, y_d, RW, dmz_bot - y_d, "Şube zone", right="internete kapalı", color="wan")
    d.link(870, y_d + 2, "02")
    d.link(1400, y_d + 2, "15")
    d.firewall(LX, dmz_bot + 10, LW, 22, "FW · DMZ → uygulama :443", tx=780)

    # ---- Uygulama
    y_a = dmz_bot + 44
    zi = len(d.z)   # zone zemini cluster kutularının altında kalsın
    for x, n in ((LX + 24, "cluster-a"), (LX + 24 + BW + 24, "cluster-b")):
        b = cluster_ns_box(d, x, y_a + 56, BW, f"{n} · Kubernetes · .NET 8 · 14 namespace", APP_NS, "in ← DMZ egress · şube zone → ingress-nginx :443 (mTLS)",
                           "out → egress-gateway → veri · DB · monolith · dış çıkış", "internal")
    k_cont = cluster_ns_box(d, RX + 24, y_a + 56, RW - 48, "kimlik cluster · Kubernetes · 6 namespace", KIMLIK_NS,
                            "in ← DMZ auth-proxy · şube gw · app (JWKS)", "out → egress → SMS · AD · IdP DB (MSSQL)", "identity")
    k_bot = k_cont + 20
    y_l = k_bot + 20
    l_cont = cluster_ns_box(d, RX + 24, y_l + 56, RW - 48, "monolith · Windows Server VM'leri", LEGACY_BOX,
                            "in ← app ingress (strangler /*) · ACL", "out → Oracle · forward proxy (dış çıkış)", "core", kind="box")
    app_bot = max(b, l_cont) + 20
    zone_behind(d, zi, LX, y_a, LW, app_bot - y_a, "Uygulama zone", right="cluster-a / cluster-b · " + NET, color="internal")
    zone_behind(d, zi, RX, y_a, RW, k_bot - y_a, "Kimlik zone", right="iç JWT üretir", color="identity")
    zone_behind(d, zi, RX, y_l, RW, app_bot - y_l, "Legacy zone · monolith", right="VM", color="core")
    d.link(830, y_a + 2, "03 · 04")
    d.link(1400, y_a + 2, "16")
    d.link(1400, y_l + 2, "05")
    d.firewall(LX, app_bot + 10, LW, 22, "FW · uygulama → veri portları", tx=760)

    # ---- Data
    y_t = app_bot + 44
    for x, w, t, ls in ((LX + 24, 290, "Kafka · ns kafka", ["broker ×3 · KRaft · TLS", "Schema Registry", "Connect · Debezium (CDC)", "MirrorMaker 2 → DR"]),
                        (LX + 330, 290, "RabbitMQ · ns rabbitmq", ["3 node · quorum queue", "komut / iş kuyrukları", "TLS · vhost başına kullanıcı", "shovel / federation → DR"]),
                        (LX + 636, 300, "Couchbase · ns couchbase", ["data · index · query node'ları", "oturum · önbellek · doküman", "bucket başına RBAC · TLS", "XDCR → DR"])):
        d.box(x, y_t + 56, w, bh(4), t, ls, color="data", size=13)
    yy = y_t + 56 + bh(4) + 22
    d.text(LX + 24, yy, "ns ingress-nginx · egress · platform · kube-system", 12.5, 600)
    d.badge(LX + 24, yy + 26, "in ← app / legacy → ingress-nginx (Kafka TLS passthrough · RabbitMQ tcp) · Couchbase: pod başına LB", "in")
    d.badge(LX + 24, yy + 52, "out → egress → DR replikasyonu (MM2 · shovel · XDCR) · yedek → nesne depolama", "out")
    data_bot = yy + 72
    d.zone(LX, y_t, LW, data_bot - y_t, "Data zone · data cluster (Kubernetes)", right="operator ile", color="data")
    d.link(870, y_t + 2, "06")
    d.zone(RX, y_t, RW, data_bot - y_t, "Veritabanı · VM / fiziksel", ["Oracle RAC · core banking + monolith", "   Data Guard → DR (standby)", "MSSQL Always On AG",
                                                                       "   yeni .NET mikroservisler", "   DC1 içi senkron · DR'a asenkron", "servis başına şema / login · TDE",
                                                                       "internete çıkış yok"], color="data")
    d.link(1400, y_t + 2, "06")

    # ---- Mgmt
    y_m = data_bot + 28
    d.zone(LX, y_m, RX + RW - LX, 186, "Yönetim zone · mgmt cluster", color="mgmt")
    d.text(LX + 24, y_m + 66, "ns ci-cd (build, registry, deploy) · security (vault) · observability (prometheus, grafana, loki, tempo) · backup (velero) · egress · platform",
           12.5, 600)
    d.text(LX + 24, y_m + 90, "deploy → cluster-a, cluster-b, cluster-dr, dmz, data (aynı manifest) · tüm zone'lardan tek yönlü log / metrik / iz · PAM / bastion", 12.5)
    d.badge(LX + 24, y_m + 122, "in ← VPN → PAM / bastion · zone'lardan OTLP / log (tek yön)", "in")
    d.badge(LX + 24, y_m + 150, "out → cluster API :6443 (deploy) · egress → paket / image aynaları (dış çıkış)", "out")
    m_bot = y_m + 186
    d.link(1400, y_m + 2, "08")

    # ---- Dış çıkış zone (DC1)
    y_x = m_bot + 28
    d.zone(LX, y_x, RX + RW - LX, 124, "Dış çıkış zone · DC1", [
        "outbound NGFW (farklı üretici) · forward proxy: hedef / FQDN izin listesi · TLS denetimi (isteğe bağlı) · erişim logu → SIEM",
        "kaynaklar: her cluster'ın egress gateway'i + legacy VM'ler · hiçbir pod / VM doğrudan internete çıkmaz · kart şemaları hariç (PCI özel hattı)"],
           color="egress", center=True)
    x_bot = y_x + 124
    P = x_bot + 20
    d.boundary([(14, 320), (1484, 320), (1484, P), (14, P)], "DC1 · ANA VERİ MERKEZİ · cluster-a + cluster-b (active-active)", "internal", fill_opacity=0.04)
    d.boundary([(1496, 320), (2186, 320), (2186, P), (1496, P)], "DC2 · DR · tek cluster (failover'da devreye girer)", "external", fill_opacity=0.25)

    # ---- DC2 (DR): aynı satırlar
    for y, h, t, ls, c in [(y_e, e_bot - y_e, "Edge · DR + kart zone'u (DR)", ["F5 LB + WAF (standby)", "GSLB felakette buraya yönlendirir",
                                                                                "kart segmenti DR kopyası (şema hatları)"], "edge"),
                           (y_d, dmz_bot - y_d, "DMZ · dmz-dr (tek cluster)", ["aynı namespace'ler (dmz-a / b manifesti)", "ingress-nginx · auth · egress-gateway",
                                                                                "şube zone'u (DR kopyası)", "failover'da ölçeklenir"], "dmz"),
                           (y_a, app_bot - y_a, "Uygulama · cluster-dr (tek cluster)", ["aynı namespace'ler, aynı image", "ingress-nginx (iç) · egress-gateway",
                                                                                         "düşük replika · failover'da HPA ile büyür", "kimlik cluster'ı (DR) · legacy VM'leri (DR)",
                                                                                         "deploy: mgmt CI/CD (DC1)"], "internal"),
                           (y_t, data_bot - y_t, "Data · data-dr + DB VM'leri", ["Kafka (MM2 hedefi) · RabbitMQ (shovel)", "Couchbase (XDCR hedefi)",
                                                                                 "Oracle Data Guard standby", "MSSQL AG asenkron replika", "ns'ler DC1 ile aynı · egress"], "data"),
                           (y_m, 186, "Yönetim · DR", ["DC1 mgmt'den yönetilir", "yerel log / metrik toplayıcı + yedek"], "mgmt"),
                           (y_x, 124, "Dış çıkış zone · DR", ["outbound NGFW + forward proxy", "DR egress gateway'lerinin tek çıkışı"], "egress")]:
        d.zone(DX, y, DW, h, t, ls, color=c)
    d.link(2100, y_e + 2, "07")

    # ---- Dış dünya
    y_w = P + 40
    d.boundary([(14, y_w), (2186, y_w), (2186, y_w + 170), (14, y_w + 170)], "DIŞ DÜNYA · BANKA DIŞI SERVİSLER", "external", fill_opacity=0.6)
    for i, (t, ls) in enumerate([("Kurumlar", ["EFT · FAST (TCMB)", "SWIFT · KKB / Findeks", "GİB (e-belge) · MASAK"]),
                                 ("Bildirim sağlayıcıları", ["SMS operatörleri", "push: APNs · FCM", "e-posta (SMTP relay)"]),
                                 ("Dış API / SaaS", ["kur · adres / kimlik doğrulama", "harita · fraud servisleri", "partner bankalar"]),
                                 ("Paket / image aynaları", ["NuGet · container registry", "OS güncellemeleri", "(yalnızca mgmt egress'i)"]),
                                 ("Kart şemaları", ["Visa · MC · TROY · BKM", "PCI zone'unun özel hattı", "(dış çıkış zone'undan değil)"])]):
        d.box(40 + i * 428, y_w + 30, 408, bh(3), t, ls, color="external", fill="#ffffff", size=13)

    # ---- Akışlar: müşteri trafiği
    merge_lines(d, [[(160, 216), (160, 226), (720, 226)], [(440, 216), (440, 226)], [(720, 216), (720, 226)]])
    d.flow([(360, 226), (360, 236)], "main")
    d.flow([(360, 236 + bh(1)), (360, y_e)], "main", "internet · 443", 372, 352)
    d.flow([(860, 262), (1840, 262), (1840, y_e)], "aux", "felakette → DR", 1852, 300)
    merge_lines(d, [[(1220, 216), (1220, 236), (1440, 236), (1440, 216)]])
    d.flow([(1330, 236), (1330, y_e)], "main", "özel hat → PCI", 1342, 300)
    d.flow([(1000, 216), (1000, 226), (1010, 226), (1010, y_d + 90), (RX, y_d + 90)], "main", "şube WAN (MPLS / SD-WAN)", 1018, 300)
    d.flow([(RX, s_cont - 40), (1004, s_cont - 40), (1004, y_a + 100), (976, y_a + 100)], "main")
    d.t(1012, y_a + 92, "şube", 11.5, 600, "#1f1f1f", layer=d.l)
    d.flow([(520, e_cont), (520, y_d - 6), (380, y_d - 6), (380, y_d + 56)], "main")
    d.flow([(520, y_d - 6), (820, y_d - 6), (820, y_d + 56)], "main")
    dmz_box_bot = dmz_bot - 20
    d.flow([(380, dmz_box_bot), (380, y_a + 56)], "main")
    d.flow([(470, dmz_box_bot), (620, y_a + 56)], "main")
    d.flow([(620, dmz_box_bot), (470, y_a + 56)], "main")
    d.flow([(900, dmz_box_bot), (900, y_a + 56)], "main")
    d.flow([(976, y_l + 110), (RX, y_l + 110)], "main")
    d.t(998, y_l + 102, "ACL", 11.5, 600, "#1f1f1f", "middle", d.l)
    app_box_bot = app_bot - 20
    d.flow([(450, app_box_bot), (450, y_t + 56)], "main")
    d.flow([(820, app_box_bot), (820, y_t + 56)], "main")
    d.flow([(1240, app_bot), (1240, y_t)], "main")
    d.flow([(976, y_a + 160), (1000, y_a + 160), (1000, app_bot + 30), (1100, app_bot + 30), (1100, y_t)], "main")
    d.t(1010, app_bot + 24, "MSSQL", 11.5, 600, "#1f1f1f", layer=d.l)
    # replikasyon ve yönetim
    for yy2 in (y_a + 140, y_l + 120, y_t + 100):
        d.flow([(RX + RW, yy2), (DX, yy2)], "aux")
    d.t(1490, y_t + 92, "repl.", 11.5, 600, "#5f5f5a", "middle", d.l)
    d.flow([(1880, 216), (1880, 228), (1490, 228), (1490, y_m - 10), (1300, y_m - 10), (1300, y_m)], "req", "VPN → PAM", 1500, y_m - 14)

    # ---- Akışlar: egress (turuncu) → dış çıkış zone → dış dünya
    BUS_L, BUS_R = 26, 1472
    for yy2 in (y_d + 140, y_a + 160, y_t + 120, y_m + 100):
        d.e.append(f'<path d="M {LX},{yy2} L {BUS_L},{yy2}" fill="none" stroke="{EG}" stroke-width="2.2" stroke-dasharray="8 4"/>')
    egress_flow(d, [(BUS_L, y_d + 140), (BUS_L, y_x + 62), (LX, y_x + 62)])
    for yy2 in (k_cont - 14, l_cont - 14):
        d.e.append(f'<path d="M {RX + RW},{yy2} L {BUS_R},{yy2}" fill="none" stroke="{EG}" stroke-width="2.2" stroke-dasharray="8 4"/>')
    egress_flow(d, [(BUS_R, k_cont - 14), (BUS_R, y_x + 62), (RX + RW, y_x + 62)])
    egress_flow(d, [(700, x_bot), (700, y_w + 30)], "dış çıkış → internet / kurum hatları :443", 712, y_w - 8)
    egress_flow(d, [(1840, x_bot), (1840, y_w + 30)], "DR çıkışı", 1852, y_w - 8)
    d.flow([(RX + RW, y_e + 80), (1494, y_e + 80), (1494, y_w + 10), (1940, y_w + 10), (1940, y_w + 30)], "aux")
    d.t(1950, y_w + 22, "PCI özel hattı", 11.5, 600, "#5f5f5a", layer=d.l)

    NY = y_w + 200
    d.note(40, NY, 1060, "Okuma sırası · siyah etiket = ayrıntı resmi", [
        "00 · genel bakış (bu resim) · 01 · giriş: kanallar, GSLB, edge, ATM / POS → PCI",
        "02 · DMZ cluster'ı: kanal girişleri, auth, egress · 03 · uygulama cluster'ı: .NET servisleri",
        "04 · bir .NET mikroservis pod'unun içi · 05 · legacy monolith ve strangler geçişi",
        "06 · data cluster'ı (Kafka, RabbitMQ, Couchbase) ve Oracle / MSSQL · 07 · DR ve replikasyon",
        "08 · mgmt: CI/CD, gözlem, güvenlik · uçtan uca: 09 mobil · 10 web · 11 şube · 12 partner · 13 POS · 14 ATM",
        "15 · şube zone'u · 16 · kimlik zone'u · 17 · kart (PCI) zone'u"], 12.5)
    lh = d.legend(1120, NY, 1060, LEG + [("egress", "dış çıkış"), ("external", "banka dışı")], extra=False, cols=4)
    ly = NY + lh + 20
    d.n.append(f'<line x1="1134" y1="{ly}" x2="1174" y2="{ly}" stroke="#2f7bd8" stroke-width="3"/>')
    d.t(1184, ly + 5, "müşteri trafiği", 13)
    d.n.append(f'<line x1="1360" y1="{ly}" x2="1400" y2="{ly}" stroke="{EG}" stroke-width="2.2" stroke-dasharray="8 4"/>')
    d.t(1410, ly + 5, "egress: dışarı çıkış", 13)
    d.n.append(f'<line x1="1600" y1="{ly}" x2="1640" y2="{ly}" stroke="#b3b3ad" stroke-width="1.8" stroke-dasharray="6 5"/>')
    d.t(1650, ly + 5, "replikasyon / yönetim", 13)
    d.save(out("00-genel-bakis.svg"), "00 · Prod hedef mimarisi: iki DC, zone'lar, namespace'ler, giriş (ingress) ve çıkış (egress)",
           CONFIRMED + " · mavi = müşteri trafiği · turuncu = egress → dış çıkış zone'u → dış dünya", oy=OY)


# =====================================================================================================================
def img01():
    W, H, OY = 2200, 1170, 40
    d = D(W, H)
    channels(d, 100)
    d.zone(40, 260, 1340, 100, "Sağlayıcı katmanı (banka dışı)", ["DDoS scrubbing · CDN (statik içerik) · bot yönetimi"], color="external", center=True)
    d.box(40, 390, 1340, bh(2), "GSLB (DNS) · api.banka · www.banka · ib.banka · openapi.banka", [
        "sağlık kontrolüne göre DC1 VIP'leri · DC1 düşerse DR VIP'leri (TTL kısa: 30-60 sn)",
        "aktif-pasif: DC2 yalnızca felakette · iki DC arasında oturum taşınmaz (Couchbase XDCR ile oturum DR'da da var)"], color="edge", size=13)
    d.boundary([(20, 500), (1400, 500), (1400, 900), (20, 900)], "DC1 · EDGE ZONE", "edge", fill_opacity=0.25)
    d.box(40, 530, 420, bh(5), "F5 LTM çifti (HA)", ["aktif / standby · bağlantı senkronu", "kanal başına VIP + sertifika", "TLS 1.2+/1.3 · HSTS",
                                                      "X-Forwarded-For / PROXY ekler", "→ DMZ ingress (TLS yeniden şifreli)"], color="edge", size=13)
    d.box(480, 530, 420, bh(5), "WAF (F5 ASM / AWAF ya da ayrı)", ["OWASP CRS · pozitif güvenlik", "API şema (OpenAPI) doğrulama", "bot · credential stuffing koruması",
                                                                    "IP itibar · coğrafi kural", "blok logu → SIEM"], color="edge", size=13)
    d.box(920, 530, 460, bh(5), "Dış firewall (NGFW)", ["yalnızca :443 → VIP'ler", "IPS · DoS eşikleri", "yönetim ağı ayrı (OOB)", "edge'den DMZ'ye yalnızca :443",
                                                        "farklı üretici: iç firewall"], color="edge", size=13)
    table(d, 40, 690, 1300, [("kanal", 0.14), ("host", 0.2), ("VIP", 0.14), ("DMZ girişi", 0.28), ("not", 0.24)], [
        ["Mobil", "api.banka", "VIP-1 :443", "ingress-mobile (IngressClass nginx-mobile)", "rate limit · cihaz bağlama"],
        ["Web", "www / ib.banka", "VIP-2 :443", "ingress-web (nginx-web)", "cookie oturum · CSRF · CSP"],
        ["Partner", "openapi.banka", "VIP-3 :443", "ingress-partner (nginx-partner)", "mTLS istemci sertifikası · kota"],
        ["Şube", "sube.banka.local", "şube zone VIP", "— (DMZ'ye girmez)", "şube zone: branch-fw → branch-gateway → app"],
        ["Operasyon", "—", "VPN", "PAM / bastion → mgmt", "kayıtlı oturum · MFA"]], size=12)
    d.boundary([(1420, 260), (2180, 260), (2180, 900), (1420, 900)], "KART ZONE · PCI DSS · internete kapalı", "pci", fill_opacity=0.35)
    d.box(1440, 300, 720, bh(3), "ATM / POS firewall", ["yalnızca ATM / POS ağı ve acquirer hatları", "ISO 8583 / NDC-DDC portları · IP izin listesi", "TLS / IPsec tünel"], color="pci", size=13)
    d.box(1440, 430, 720, bh(4), "ATM / POS switch (kart yetkilendirme)", ["ISO 8583 mesaj işleme · limit / bakiye sorgusu", "kart şemaları: Visa · MC · TROY · BKM (özel hat)",
                                                                           "uygulama zone'una yalnızca card-api üzerinden (mTLS)", "ayrı cluster ya da ayrı VM segmenti"], color="pci", size=13)
    d.box(1440, 580, 350, bh(3), "HSM", ["PIN doğrulama · anahtar", "yönetimi · ağ HSM'i (HA)", "PCI PIN"], color="pci", size=13)
    d.box(1810, 580, 350, bh(3), "Tokenization", ["PAN → token", "uygulama zone'u PAN görmez", "kasaya yalnızca PCI erişir"], color="pci", size=13)
    d.note(1440, 720, 720, "Neden ayrı?", ["PCI kapsamını daraltmak: kart verisi yalnızca bu zone'da.", "ATM / POS internetten gelmez; edge'den geçmez.",
                                            "DR'da aynı yapı (DC2 kart zone'u)."], 12.5)
    merge_lines(d, [[(160, 216), (160, 236), (720, 236)], [(440, 216), (440, 236)], [(720, 216), (720, 236)]])
    d.flow([(440, 236), (440, 260)], "main")
    d.flow([(440, 360), (440, 390)], "main")
    d.flow([(250, 390 + bh(2)), (250, 530)], "main")
    d.flow([(460, 600), (480, 600)], "main")
    d.flow([(900, 600), (920, 600)], "main")
    d.flow([(1365, 530 + bh(5)), (1365, 920)], "main", "→ DMZ ingress'leri :443 (02)", 1353, 916, "end")
    merge_lines(d, [[(1220, 216), (1220, 232), (1440, 232), (1440, 216)]])
    d.flow([(1330, 232), (1330, 254), (1700, 254), (1700, 300)], "main", "özel hat", 1712, 290)
    d.flow([(1000, 216), (1000, 244), (1392, 244), (1392, 920)], "main", "şube WAN → şube zone → uygulama ingress (00)", 1380, 946, "end")
    d.flow([(1800, 300 + bh(3)), (1800, 430)], "main")
    d.flow([(1800, 430 + bh(4)), (1800, 580)], "req")
    d.flow([(2100, 216), (2100, 250), (2170, 250), (2170, 940)], "req", "VPN → PAM → mgmt (08)", 2158, 936, "end")
    d.note(40, 950, 1060, "Bu resimde", ["İnternet kanalları (mobil, web, partner) GSLB → F5 + WAF → DMZ ingress yolunu izler.",
                                         "ATM ve POS ayrı: özel hat → PCI zone'u; kart verisi uygulama zone'una tokenize gelir.",
                                         "Şube kullanıcıları internetten değil kurum WAN'ından: şube zone'u (branch-fw → branch-gateway) → uygulama.",
                                         "Ürün adları (F5, NGFW) yaygın tercihlerdir; mevcut cihazlarınızla değiştirilebilir."], 12.5)
    d.legend(1120, 950, 1060, [("public", "internet"), ("wan", "kurum WAN"), ("edge", "edge"), ("pci", "kart / PCI"), ("external", "banka dışı")], extra=False, cols=3)
    d.save(out("01-giris-edge-pci.svg"), "01 · Giriş: kanallar, GSLB, edge (F5 + WAF), ATM / POS → kart zone'u",
           "her kanalın girdiği yol · VIP ve DMZ ingress eşlemesi · " + CONFIRMED, oy=OY)


# =====================================================================================================================
PLATFORM = [("cert-manager", "Deployment", "iç CA'dan sertifika (mTLS, ingress TLS)"),
            ("external-secrets", "Deployment", "Vault → Kubernetes Secret"),
            ("otel-collector", "DaemonSet", "iz · metrik · log → mgmt"),
            ("kyverno", "Deployment", "imzalı image · ayrıcalıksız pod · etiket")]


def img02():
    W, H, OY = 2200, 940, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 640), (14, 640)], "DMZ CLUSTER'LARI · dmz-a + dmz-b (DC1, active-active) · dmz-dr (DC2) · iş mantığı ve veri yok", "dmz")
    d.badge(40, 146, "in ← F5 VIP-1/2/3 → ingress :443 (TLS yeniden şifreli · XFF / PROXY) · şube trafiği DMZ'ye girmez (şube zone'u)", "in")
    d.badge(2160, 146, "out → uygulama ingress :443 (mTLS + iç JWT) · IdP · log / metrik → mgmt", "out", anchor="end")
    c, cw = [40, 760, 1480], 680
    y = ns_pods(d, c[0], 180, cw, "ingress-mobile", [("ingress-nginx (nginx-mobile)", "Deployment ×3", "api.banka · rate limit · cihaz başlığı")], "dmz") + 12
    y = ns_pods(d, c[0], y, cw, "ingress-web", [("ingress-nginx (nginx-web)", "Deployment ×3", "www / ib · CSP · statik → CDN")], "dmz") + 12
    y = ns_pods(d, c[0], y, cw, "ingress-partner", [("ingress-nginx (nginx-partner)", "Deployment ×3", "mTLS (auth-tls-verify-client) · kota")], "dmz") + 12
    y = ns_pods(d, c[0], y, cw, "egress", [("egress-gateway", "Deployment ×2", "TEK çıkış · hedef izin listesi")], "dmz") + 12
    d.text(c[0] + 12, y + 18, "Her kanal ayrı IngressClass + ayrı namespace: biri düşse / açık verse diğerleri etkilenmez.", 12, 400, "#3a3a3a")
    y2 = ns_pods(d, c[1], 180, cw, "auth", [("auth-proxy (.NET · YARP)", "Deployment ×3", "token introspection → iç JWT (öneri)"),
                                            ("token-handler (web)", "Deployment ×2", "cookie ↔ token · CSRF · oturum: Couchbase")], "dmz") + 12
    y2 = ns_pods(d, c[1], y2, cw, "ratelimit", [("ratelimit", "Deployment ×2", "kanal / partner kotası · sayaç: Redis/Couchbase")], "dmz") + 12
    d.text(c[1] + 12, y2 + 18, "ingress-nginx kural örnekleri (kanal başına)", 13, 700)
    table(d, c[1] + 12, y2 + 30, cw - 24, [("anotasyon", 0.52), ("amaç", 0.48)], [
        ["auth-url: http://auth-proxy.auth/check", "her istek önce auth-proxy"],
        ["auth-response-headers: X-User-Jwt", "iç JWT uygulamaya taşınır"],
        ["limit-rps / limit-connections", "kanal başına hız sınırı"],
        ["auth-tls-verify-client: on (partner)", "partner istemci sertifikası"],
        ["enable-modsecurity (isteğe bağlı)", "WAF'a ek ikinci katman"],
        ["proxy-ssl-secret / backend-protocol HTTPS", "uygulama zone'una mTLS"]], size=11.5)
    y3 = ns_pods(d, c[2], 180, cw, "platform", PLATFORM, "mgmt") + 12
    ns_pods(d, c[2], y3, cw, "kube-system", [("coredns · kube-proxy · CNI", "DS / Deploy", "CNI NetworkPolicy destekli (öneri: Cilium / Calico)")], "mgmt")
    d.note(40, 670, 1060, "Bu resimde", ["DMZ'de iş mantığı ve veri yok: yalnızca giriş, kimlik doğrulama, hız sınırı ve tek çıkış.",
                                         "dmz-a ve dmz-b aynı manifest; dmz-dr DC2'de aynı yapı, daha az replika.",
                                         "Çıkış: uygulama ingress'ine mTLS + iç JWT; dış token DMZ'de kalır.",
                                         "auth-proxy / token-handler önerisi; mevcut API gateway'iniz varsa onun yerini tutar."], 12.5)
    d.legend(1120, 670, 1060, [("dmz", "DMZ"), ("mgmt", "platform")], extra=True, cols=3)
    d.save(out("02-dmz-cluster.svg"), "02 · DMZ cluster'ı: kanal başına ingress-nginx, auth-proxy, rate limit, tek çıkış",
           "her kutu bir namespace · satırlar pod'lar (ad · iş yükü · görev) · replika sayıları önerilir · " + CONFIRMED, oy=OY)


# =====================================================================================================================
def img03():
    W, H, OY = 2200, 1130, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 790), (14, 790)], "UYGULAMA CLUSTER'LARI · cluster-a + cluster-b (DC1) · cluster-dr (DC2) · aynı manifest · .NET 8", "internal")
    d.badge(40, 146, "in ← DMZ :443 · şube zone (branch-gateway) :443 (mTLS + iç JWT)", "in")
    d.badge(2160, 146, "out → Kafka · RabbitMQ · Couchbase (data cluster) · MSSQL · Oracle (VM) · monolith (VM) · PCI card switch", "out", anchor="end")
    c, cw = [40, 760, 1480], 680
    y = ns_pods(d, c[0], 180, cw, "ingress-nginx", [("ingress-nginx (iç)", "Deployment ×3", "mTLS · iç JWT · strangler rotaları (05)")], "internal") + 12
    y = ns_pods(d, c[0], y, cw, "channel-bff", [("mobile-bff", "Deployment ×3 · HPA", "mobil ekranlara özel birleştirme"),
                                                ("web-bff", "Deployment ×3 · HPA", "internet şubesi"),
                                                ("partner-bff", "Deployment ×2 · HPA", "açık bankacılık API'leri"),
                                                ("branch-bff", "Deployment ×2 · HPA", "şube ekranları · personel yetkisi")], "internal") + 12
    y = ns_pods(d, c[0], y, cw, "account · customer", [("account-api", "Deployment ×3 · HPA", "hesap, bakiye, hareket → MSSQL"),
                                                       ("customer-api", "Deployment ×3", "müşteri, KYC → MSSQL")], "internal") + 12
    ns_pods(d, c[0], y, cw, "card", [("card-api", "Deployment ×3", "token'lı kart · PCI switch'e mTLS")], "internal")
    y = ns_pods(d, c[1], 180, cw, "transfer · payment", [("transfer-api", "Deployment ×3 · HPA", "havale / EFT / FAST · MSSQL + outbox"),
                                                         ("payment-api", "Deployment ×3", "fatura, vergi, ödeme"),
                                                         ("outbox-relay", "Deployment ×2", "outbox tablosu → Kafka (CDC / polling)")], "internal") + 12
    y = ns_pods(d, c[1], y, cw, "loan · notification · fraud", [("loan-api", "Deployment ×2", "kredi başvurusu"),
                                                                ("notification-worker", "Deployment · KEDA", "Kafka tüketir → SMS / push / e-posta"),
                                                                ("fraud-scoring", "Deployment ×3", "Kafka akışı → risk skoru")], "internal") + 12
    y = ns_pods(d, c[1], y, cw, "integration", [("monolith-adapter (ACL)", "Deployment ×3", "monolith ↔ yeni model çevirisi"),
                                                ("core-adapter", "Deployment ×3", "core posting → Oracle / core API"),
                                                ("cdc-consumers", "Deployment · KEDA", "Oracle CDC olayları → okuma modelleri")], "core") + 12
    ns_pods(d, c[1], y, cw, "legacy-modules", [("taşınan monolith modülleri", "Deployment", "container'a alınmış parçalar (05)")], "core")
    y = ns_pods(d, c[2], 180, cw, "platform", PLATFORM + [("keda", "Deployment", "Kafka lag / RabbitMQ kuyruk → ölçek")], "mgmt") + 12
    d.text(c[2] + 12, y + 18, "Servis → veri bağımlılıkları (öneri dağılım)", 13, 700)
    table(d, c[2] + 12, y + 30, cw - 24, [("servis", 0.3), ("yazar / okur", 0.7)], [
        ["account / customer", "MSSQL (servis başına DB) · Couchbase önbellek"],
        ["transfer / payment", "MSSQL + outbox → Kafka · RabbitMQ komut"],
        ["notification", "Kafka tüketir · RabbitMQ (SMS sağlayıcı kuyruğu)"],
        ["fraud-scoring", "Kafka akışı · Couchbase (profil)"],
        ["core-adapter", "Oracle (core) · RabbitMQ (posting kuyruğu)"],
        ["monolith-adapter", "monolith API (VM) · Kafka (olay köprüsü)"],
        ["BFF'ler", "Couchbase (oturum / önbellek) · iç servisler"]], size=11.5)
    d.note(40, 820, 1060, "Bu resimde", ["Tüm yeni servisler .NET 8 (ASP.NET Core), aynı image üç cluster'a gider.",
                                         "Veri: işlem verisi MSSQL'de, servis başına ayrı DB; olaylar outbox ile Kafka'ya.",
                                         "Monolith ile konuşma yalnızca integration namespace'inden (ACL); doğrudan Oracle yok.",
                                         "Servis adları ve dağılım önerilir; mevcut domain'lerinize göre uyarlanır. Pod içi: 04."], 12.5)
    d.legend(1120, 820, 1060, [("internal", "uygulama (.NET)"), ("core", "legacy / entegrasyon"), ("mgmt", "platform")], extra=True, cols=3)
    d.save(out("03-uygulama-cluster.svg"), "03 · Uygulama cluster'ı: .NET mikroservisler, entegrasyon, platform, veri bağımlılıkları",
           "her kutu bir namespace · cluster-a, cluster-b ve cluster-dr aynı · " + CONFIRMED, oy=OY)


# =====================================================================================================================
def img04():
    W, H, OY = 2200, 920, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 670), (14, 670)], "cluster-a · ns transfer · bir worker node'unda", "internal")
    d.node(36, 140, 2128, 510, "worker-…", "uygulama havuzu · DC1 · topologySpread: zone / node")
    pb = d.pod(56, 184, 1060, None, "transfer-api-…", "Deployment ×3 · HPA 3-12 · PDB minAvailable 2 · SA transfer-api", "internal", [
        ("app · " + NET + " (Kestrel :8080)", "app", [
            "non-root · read-only root FS · capabilities drop ALL · seccomp RuntimeDefault",
            "probe: /health/live · /health/ready (DB, Kafka bağımlılık kontrolü) · startup probe",
            "EF Core → MSSQL AG listener (MultiSubnetFailover=True, Encrypt=True) · tek transaction: transfer + outbox",
            "RabbitMQ: MassTransit (öneri) · publisher confirm · quorum queue · core.posting komutu",
            "Couchbase SDK: idempotency anahtarı (X-Idempotency-Key, 24 sa) · oturum okumaz",
            "Polly: timeout · retry (yalnızca okuma) · circuit breaker · bulkhead",
            "iç JWT doğrulama (JwtBearer, IdP JWKS) · yetki: policy + scope",
            "OpenTelemetry: iz + metrik → otel-collector · Serilog JSON → stdout"]),
        ("secret'lar (volume)", "data", ["ExternalSecret → Vault: MSSQL login (dinamik), RabbitMQ kullanıcı, Couchbase RBAC kullanıcı",
                                         "mTLS sertifikası: cert-manager (iç CA) · otomatik yenileme"]),
        ("config", "init", ["ConfigMap: appsettings.Production.json · ortam: DC1 / DR", "migration: ayrı Job (deploy öncesi) · pod içinde migration yok"])])
    d.badge(56, pb + 24, "in ← ingress-nginx (iç) :8080 · mTLS + iç JWT", "in")
    d.badge(1116, pb + 24, "out → MSSQL :1433 · RabbitMQ :5671 · Couchbase :11207 · otel :4317", "out", anchor="end")
    nb = d.pod(1140, 184, 1004, None, "outbox-relay-…", "Deployment ×2 · tek aktif (lease)", "internal", [
        ("app · .NET 8 worker (BackgroundService)", "app", ["outbox tablosunu okur (ya da Debezium CDC)", "Confluent.Kafka producer: acks=all · idempotent",
                                                           "konu: banka.transfer.created.v1 · anahtar: hesap no", "Schema Registry (Avro / JSON Schema)",
                                                           "gönderilen satır işaretlenir · en az bir kez"])])
    nb2 = d.pod(1140, nb + 16, 1004, None, "notification-worker-…", "Deployment · KEDA 1-20 (Kafka lag)", "internal", [
        ("app · .NET 8 worker", "app", ["consumer group: notification · manuel commit", "işlenen olay id'si Couchbase'te (tekrar koruması)",
                                       "→ RabbitMQ sms.send kuyruğu → SMS sağlayıcı (egress)", "zehirli mesaj → DLQ konusu"])])
    d.badge(1140, nb2 + 24, "in ← Kafka :9093 (mTLS / SASL) · out → Kafka · RabbitMQ", "in")
    nh = d.note(56, max(pb, nb2) + 50, 2088, "İstek yolu (numaralar)", [
        "1 ingress → transfer-api :8080 · iç JWT doğrulanır  ·  2 MSSQL'de tek transaction: transfer kaydı + outbox satırı  ·  3 RabbitMQ'ya core.posting komutu (core-adapter tüketir)",
        "4 outbox-relay outbox'ı okur → Kafka banka.transfer.created.v1  ·  5 notification-worker olayı tüketir → SMS / push  ·  6 202 Accepted + işlem no (sonuç olayla gelir)"], 12.5)
    for x, y, n, col in [(48, 230, 1, "#2f7bd8"), (48, 300, 2, "#2f7bd8"), (48, 320, 3, "#c2410c"), (1132, 230, 4, "#c2410c"), (1132, nb + 50, 5, "#c2410c")]:
        d.marker(x, y, n, col)
    d.flow([(400, 124), (400, 184)], "main")
    d.flow([(1116, 260), (1140, 260)], "aux")
    d.legend(40, 700, 2140, [("internal", "uygulama (.NET)"), ("data", "veri"), ("mgmt", "platform")], extra=True, cols=6)
    d.save(out("04-dotnet-pod-detay.svg"), "04 · .NET mikroservis pod içi: transfer-api, outbox-relay, notification-worker",
           "pod → container → port, probe, güvenlik, bağlantılar · numaralar: bir transferin servis içindeki yolu · kütüphane adları öneri", oy=OY)


# =====================================================================================================================
def img05():
    W, H, OY = 2200, 1170, 40
    d = D(W, H)
    d.boundary([(14, 108), (1100, 108), (1100, 820), (14, 820)], "LEGACY ZONE · Windows VM'ler · DC1 (DR'da kopyası)", "core", fill_opacity=0.25)
    d.box(40, 146, 1036, bh(3), "NLB / F5 iç VIP · monolith.banka.local :443", ["yalnızca uygulama cluster'larının ingress'inden ve monolith-adapter'dan",
                                                                               "sticky session yok (oturum dışarıda) · TLS", "sağlık: /health (IIS)"], color="core", size=13)
    for i in range(3):
        x = 40 + i * 350
        d.pod(x, 250, 336, None, f"monolith-vm-0{i + 1}", "Windows Server · IIS", "core", [
            ("ASP.NET · .NET Framework 4.8", "app", ["app pool (ayrı kimlik)", "hesap işlemleri · kredi", "raporlama · backoffice", "taşınmamış modüller"]),
            ("bağlantılar", "init", ["Oracle (ODP.NET) :1521", "MSMQ / RabbitMQ · Kafka köprüsü"])])
    d.box(40, 530, 1036, bh(4), "Oracle RAC · core banking + monolith şeması", ["monolith doğrudan yazar · core-adapter core API / paket üzerinden",
                                                                               "Debezium (LogMiner) CDC → Kafka: oracle.core.* konuları", "Data Guard → DR standby",
                                                                               "yeni servisler Oracle'a doğrudan bağlanmaz (yalnızca core-adapter)"], color="data", size=13)
    d.text(40, 700, "Monolith'in mikroservislere taşınması (strangler fig)", 14, 700)
    table(d, 40, 712, 1036, [("adım", 0.07), ("ne yapılır", 0.63), ("araç", 0.3)], [
        ["1", "taşınacak modül seçilir (sınırları belli, az bağımlı)", "domain analizi"],
        ["2", ".NET 8 servis yazılır · kendi MSSQL DB'si", "transfer-api vb."],
        ["3", "veri senkronu: Oracle CDC → Kafka → servisin okuma modeli", "Debezium · cdc-consumers"]], size=11.5)
    d.boundary([(1120, 108), (2186, 108), (2186, 820), (1120, 820)], "UYGULAMA CLUSTER'I · strangler cephesi", "internal", fill_opacity=0.15)
    d.pod(1140, 146, 1026, None, "ingress-nginx (iç) · strangler yönlendirme", "Ingress kuralları", "internal", [
        ("yol bazlı yönlendirme", "proxy", ["/api/transfers/*  → transfer-api (yeni)", "/api/payments/*   → payment-api (yeni)",
                                            "/api/loans/*      → %10 loan-api (canary: canary-weight) · %90 monolith",
                                            "/*                → monolith (ExternalName / selector'sız Service → NLB VIP)"])])
    d.pod(1140, 330, 500, None, "monolith-adapter (ACL)", "Deployment ×3", "core", [
        ("app · .NET 8", "app", ["yeni servis → monolith çağrıları", "eski model ↔ yeni model çevirisi", "monolith olaylarını Kafka'ya köprüler"])])
    d.pod(1666, 330, 500, None, "cdc-consumers", "Deployment · KEDA", "core", [
        ("app · .NET 8 worker", "app", ["oracle.core.* konularını tüketir", "MSSQL okuma modellerini günceller", "sıra: anahtar bazlı (hesap no)"])])
    d.pod(1140, 500, 1026, None, "taşınan monolith modülleri", "Deployment (geçiş dönemi)", "core", [
        ("container · .NET 8'e taşınmış parça", "app", ["monolith kodundan ayrılıp container'a alınan modüller", "kalıcı hedef değil: ayrı servis olarak yeniden yazılana kadar"])])
    table(d, 1140, 640, 1026, [("adım", 0.07), ("ne yapılır", 0.63), ("araç", 0.3)], [
        ["4", "trafik kademeli yeni servise (canary %10 → %100)", "ingress-nginx canary"],
        ["5", "yazma yönü yeni servise geçer · monolith okur (geri CDC)", "Kafka · ACL"],
        ["6", "modül monolith'ten silinir · Oracle tablosu emekli", "—"]], size=11.5)
    d.flow([(1140, 220), (1100, 220), (1100, 180), (1076, 180)], "main")
    d.flow([(1140, 400), (1076, 400)], "req")
    d.flow([(1076, 570), (1110, 570), (1110, 482), (1800, 482), (1800, 446)], "aux")
    d.t(1200, 476, "Oracle CDC (Debezium) → Kafka → cdc-consumers", 12, 600, "#5f5f5a", layer=d.l)
    d.note(40, 850, 1060, "Bu resimde", ["Monolith .NET Framework / IIS üzerinde VM'lerde; taşınan modüller cluster'da.",
                                         "Giriş tek: uygulama ingress'i. Yol bazlı kural yeni servise ya da monolith'e yönlendirir.",
                                         "Veri iki yönde senkron: Oracle CDC → yeni servisler; yeni servis olayları → ACL → monolith.",
                                         "Yeni servisler Oracle'a doğrudan bağlanmaz; core-adapter ve CDC tek geçit."], 12.5)
    d.legend(1120, 850, 1060, [("core", "legacy / entegrasyon"), ("internal", "uygulama"), ("data", "veri")], extra=False, cols=3)
    d.save(out("05-legacy-monolith-strangler.svg"), "05 · Legacy monolith ve strangler geçişi: VM'ler, yönlendirme, CDC, ACL",
           "monolith VM'de (.NET Framework / IIS) · taşınan modüller cluster'da · " + CONFIRMED, oy=OY)


# =====================================================================================================================
def img06():
    W, H, OY = 2200, 1160, 40
    d = D(W, H)
    d.boundary([(14, 108), (1460, 108), (1460, 800), (14, 800)], "DATA CLUSTER · Kubernetes · DC1 (DR: data-dr) · operator'lar", "data")
    d.badge(40, 146, "in ← uygulama cluster'ları + monolith VM'leri → Kafka :9093 · RabbitMQ :5671 · Couchbase :11207 (TLS)", "in")
    c, cw = [40, 760], 680
    y = ns_pods(d, c[0], 180, cw, "kafka", [("strimzi-cluster-operator", "Deployment", "Kafka CR'larını yönetir (öneri)"),
                                            ("kafka-broker ×3", "StatefulSet / NodePool", "TLS · mTLS / SCRAM · rack: node"),
                                            ("kafka-controller ×3", "StatefulSet / NodePool", "KRaft (ZooKeeper yok)"),
                                            ("schema-registry ×2", "Deployment", "Avro / JSON Schema · uyumluluk"),
                                            ("kafka-connect ×3", "Deployment", "Debezium: Oracle (LogMiner), MSSQL CDC"),
                                            ("mirrormaker2 ×2", "Deployment", "→ data-dr · offset senkronu"),
                                            ("cruise-control", "Deployment", "partition dengeleme")], "data") + 12
    ns_objs(d, c[0], y, cw, "kafka (giriş)", [("Listener", "tls :9093", "type: ingress → ingress-nginx TLS passthrough"),
                                             ("", "", "broker başına host: b0 / b1 / b2.kafka.data.banka"),
                                             ("KafkaUser", "servis başına", "ACL: konu bazlı okuma / yazma"),
                                             ("KafkaTopic", "banka.*.v1", "RF 3 · min.insync 2 · retention")], "data")
    y = ns_pods(d, c[1], 180, cw, "rabbitmq", [("rabbitmq-cluster-operator", "Deployment", "RabbitmqCluster CR (öneri)"),
                                               ("rabbitmq-server ×3", "StatefulSet", "quorum queue · TLS :5671 · yönetim :15671"),
                                               ("messaging-topology-operator", "Deployment", "vhost · kullanıcı · izin · shovel CR")], "data") + 12
    y = ns_pods(d, c[1], y, cw, "couchbase", [("couchbase-operator", "Deployment", "CouchbaseCluster CR"),
                                              ("couchbase data ×3", "pod (operator)", "oturum · önbellek · idempotency"),
                                              ("couchbase index / query ×2", "pod (operator)", "N1QL · GSI"),
                                              ("couchbase-backup", "CronJob", "→ nesne depolama")], "data") + 12
    y = ns_pods(d, c[1], y, cw, "ingress-nginx", [("ingress-nginx", "Deployment ×3", "Kafka TLS passthrough · RabbitMQ tcp-services")], "data") + 12
    d.text(c[1] + 12, y + 18, "Couchbase SDK tüm node'lara bağlanır → ingress uygun değil:", 12, 700)
    d.text(c[1] + 12, y + 38, "pod başına LoadBalancer + DNS (ya da istemci ağına yönlendirilmiş pod ağı).", 12)
    d.boundary([(1480, 108), (2186, 108), (2186, 800), (1480, 800)], "VERİTABANI · VM / fiziksel · DC1", "data", fill_opacity=0.35)
    d.box(1500, 146, 666, bh(7), "Oracle RAC (2+ node) · ASM", ["kim: core banking · legacy monolith", "erişim: monolith (ODP.NET) · core-adapter · Debezium",
                                                                  "port :1521 / TCPS :2484 · servis adı başına", "Data Guard → DR standby (Max Availability / async)",
                                                                  "TDE · Unified Audit → SIEM", "yedek: RMAN · DR'da test", "yeni servisler doğrudan bağlanmaz"], color="data", size=13)
    d.box(1500, 330, 666, bh(7), "MSSQL Always On AG", ["kim: yeni .NET mikroservisler (servis başına DB)", "primary + senkron secondary (DC1, otomatik failover)",
                                                         "asenkron secondary (DR) · listener :1433", "MultiSubnetFailover=True · Encrypt=True",
                                                         "login: Vault dinamik (öneri) · least privilege", "CDC açık (outbox / okuma modelleri)", "TDE · Audit → SIEM"], color="data", size=13)
    table(d, 1500, 520, 666, [("kim", 0.36), ("nereye", 0.64)], [
        ["account · customer · transfer", "MSSQL (kendi DB'si)"], ["core-adapter · monolith", "Oracle"], ["outbox-relay · fraud", "Kafka"],
        ["core-adapter · notification", "RabbitMQ"], ["BFF · transfer · fraud", "Couchbase"], ["Debezium", "Oracle + MSSQL → Kafka"]], size=11.5)
    d.note(1500, 720, 666, "Ağ kuralı (DATA FW)", ["kaynak: yalnızca uygulama cluster'ları, legacy VM'ler,", "data cluster'ın kendisi (Connect, MM2) ve mgmt (yedek / izleme)",
                                                     "DMZ ve edge'den yol yok"], 12.5)
    d.note(40, 830, 1060, "Bu resimde", ["Kafka, RabbitMQ ve Couchbase data cluster'ında operator ile; Oracle ve MSSQL VM'de.",
                                         "Kafka dışarı ingress-nginx TLS passthrough ile (broker başına host) açılır; RabbitMQ tcp-services ile.",
                                         "Operator adları (Strimzi, RabbitMQ Cluster Operator, Couchbase Operator) öneri.",
                                         "DR tarafı ve replikasyon: 07."], 12.5)
    d.legend(1120, 830, 1060, [("data", "veri"), ("mgmt", "platform")], extra=True, cols=3)
    d.save(out("06-veri-katmani.svg"), "06 · Veri katmanı: data cluster (Kafka, RabbitMQ, Couchbase) ve VM'deki Oracle, MSSQL",
           "her kutu bir namespace ya da sunucu grubu · kim nereye bağlanır · " + CONFIRMED, oy=OY)


# =====================================================================================================================
def img07():
    W, H, OY = 2200, 1110, 40
    d = D(W, H)
    d.boundary([(14, 108), (760, 108), (760, 830), (14, 830)], "DC1 · ANA", "internal", fill_opacity=0.08)
    d.boundary([(1440, 108), (2186, 108), (2186, 830), (1440, 830)], "DC2 · DR", "external", fill_opacity=0.25)
    rows = [("GSLB / F5", "VIP'ler aktif", "standby VIP'ler", "DNS sağlık kontrolü · elle ya da otomatik", "TTL 30-60 sn"),
            ("Kubernetes iş yükleri", "cluster-a + cluster-b", "cluster-dr (düşük replika)", "aynı image + manifest (CI/CD her üçüne)", "dk · HPA büyütür"),
            ("Kafka", "data cluster", "data-dr", "MirrorMaker 2 · asenkron · offset senkronu", "RPO sn"),
            ("RabbitMQ", "data cluster", "data-dr", "shovel / federation · kuyruk tanımları CR ile", "RPO: yolda mesaj"),
            ("Couchbase", "data cluster", "data-dr", "XDCR · asenkron · çift yönlü değil", "RPO sn"),
            ("Oracle", "RAC (primary)", "Data Guard standby", "redo taşıma · switchover / failover", "RPO ~0-sn"),
            ("MSSQL", "AG primary + sync", "AG async secondary", "asenkron commit · forced failover", "RPO sn"),
            ("Legacy monolith", "IIS VM'leri", "DR VM'leri (kapalı / ılık)", "VM replikasyonu ya da aynı paket deploy", "dk"),
            ("Secret / sertifika", "Vault (DC1)", "Vault (DR)", "performans / DR replikasyonu", "—"),
            ("Image", "registry (DC1)", "registry (DR)", "registry replikasyonu", "—")]
    y = 160
    for i, (n, a, b, how, rpo) in enumerate(rows):
        yy = y + i * 62
        fill = PALETTE["data"][0] if i in (2, 3, 4, 5, 6) else PALETTE["internal"][0]
        stroke = PALETTE["data"][1] if i in (2, 3, 4, 5, 6) else PALETTE["internal"][1]
        d.n.append(f'<rect x="40" y="{yy}" width="700" height="50" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
        d.text(56, yy + 21, n, 13.5, 700)
        d.text(56, yy + 40, a, 12.5)
        d.n.append(f'<rect x="1460" y="{yy}" width="700" height="50" rx="7" fill="#f4f4f2" stroke="#a3a3a3" stroke-width="1.4"/>')
        d.text(1476, yy + 21, n, 13.5, 700)
        d.text(1476, yy + 40, b, 12.5)
        d.flow([(740, yy + 25), (1460, yy + 25)], "aux")
        d.text(1100, yy + 18, how, 12, 600, "#1f1f1f", "middle")
        d.text(1100, yy + 42, rpo, 11.5, 400, "#5f5f5a", "middle")
    d.note(40, 860, 1060, "Failover sırası (DC1 tamamen kaybedilirse)", [
        "1 olay ilanı · 2 Oracle Data Guard failover · MSSQL AG forced failover (DR primary olur)",
        "3 Kafka: tüketiciler DR'da çevrilmiş offset'lerden başlar · RabbitMQ / Couchbase DR kopyası aktif",
        "4 cluster-dr ölçeklenir · DR monolith VM'leri açılır · 5 GSLB DR VIP'lerine çevrilir · 6 doğrulama testleri"], 12.5)
    d.note(1120, 860, 1060, "Dikkat", ["RPO / RTO değerleri örnektir; kurumun iş etki analizine göre belirlenir.",
                                       "Asenkron replikasyonda DR'a geçişte son birkaç saniyelik veri kaybolabilir.",
                                       "Geri dönüş (failback) ayrı bir prosedürdür ve düzenli tatbikat gerekir."], 12.5)
    d.save(out("07-dr-replikasyon.svg"), "07 · DR ve replikasyon: DC1 → DC2, bileşen başına yöntem, RPO / RTO ve failover sırası",
           "DC1'de cluster-a + cluster-b · DC2'de tek cluster · gri kesikli = replikasyon yönü · değerler örnek", oy=OY)


# =====================================================================================================================
def img08():
    W, H, OY = 2200, 860, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 570), (14, 570)], "MGMT CLUSTER · DC1 (DR'da yerel toplayıcı + yedek) · tüm cluster'ları yönetir", "mgmt")
    d.badge(40, 146, "in ← yalnızca VPN → PAM / bastion · tüm zone'lardan tek yönlü telemetri (OTLP, log)", "in")
    d.badge(2160, 146, "out → cluster API'leri :6443 (deploy) · registry pull", "out", anchor="end")
    c, cw = [40, 760, 1480], 680
    y = ns_pods(d, c[0], 180, cw, "ci-cd", [("build runner'lar", "Deployment", "dotnet build · test · SAST · SBOM"),
                                            ("registry (öneri: Harbor)", "Deployment", "imzalı image · zafiyet tarama · DR replikası"),
                                            ("deploy (öneri: Argo CD)", "Deployment", "cluster-a · cluster-b · cluster-dr · dmz · data")], "mgmt") + 12
    ns_pods(d, c[0], y, cw, "security", [("vault", "StatefulSet ×3", "secret · PKI · MSSQL dinamik login"),
                                         ("kyverno policy reporter", "Deployment", "politika ihlali raporu")], "mgmt")
    y = ns_pods(d, c[1], 180, cw, "observability", [("prometheus + thanos", "StatefulSet", "metrik · uzun süreli saklama"),
                                                     ("grafana", "Deployment", "panolar · alarm"),
                                                     ("loki / ELK", "StatefulSet", "uygulama ve erişim logu"),
                                                     ("tempo", "StatefulSet", "iz (OpenTelemetry)"),
                                                     ("alertmanager", "StatefulSet", "→ nöbet / ITSM")], "mgmt") + 12
    ns_pods(d, c[1], y, cw, "backup", [("velero", "Deployment", "cluster nesneleri + PV yedeği")], "mgmt")
    d.text(c[2] + 12, 196, "Kim, neyi, nereye (tek yön)", 13, 700)
    table(d, c[2] + 12, 208, cw - 24, [("kaynak", 0.4), ("hedef", 0.6)], [
        ["tüm cluster'lar", "otel-collector → mgmt (OTLP :4317)"], ["tüm cluster'lar", "log → Loki / ELK → SIEM"],
        ["legacy VM'ler", "Windows olay logu → SIEM"], ["Oracle · MSSQL", "audit → SIEM"], ["mgmt", "deploy → cluster API :6443"],
        ["operasyon", "VPN → PAM → kubectl / UI"]], size=11.5)
    d.note(c[2] + 12, 420, cw - 24, "İlke", ["Zone'lar mgmt'ye yazar, mgmt zone'lara yalnızca", "deploy ve yönetim için gider.",
                                             "Prod'a elle kubectl yok: değişiklik CI/CD'den.", "Ürün adları öneri; mevcut araçlarınızla eşlenir."], 12.5)
    d.note(40, 600, 1060, "Bu resimde", ["mgmt cluster'ı yazılım teslimatı, gözlem ve güvenlik servislerini toplar.",
                                         "Aynı image ve manifest DC1 ve DR cluster'larına gider; DR her zaman güncel kalır.",
                                         "Telemetri tek yönlüdür: zone'lar gönderir, mgmt içeri bağlanmaz."], 12.5)
    d.legend(1120, 600, 1060, [("mgmt", "yönetim / platform")], extra=True, cols=3)
    d.save(out("08-mgmt.svg"), "08 · Mgmt: CI/CD (.NET), registry, deploy, gözlem, Vault, yedekleme",
           "her kutu bir namespace · tek yönlü telemetri · " + CONFIRMED, oy=OY)


# =====================================================================================================================
def seq_image(fname, title, subtitle, parts, steps, note_lines, sections=None):
    """Uçtan uca akış: sütunlar = bileşenler (renk = zone), satırlar = adımlar.
    steps: (kimden, kime, tür, etiket, alt satır) · tür: main (müşteri isteği), req (kontrol / komut), ret (yanıt), aux (olay)
    sections: {adım indeksi: başlık} — o adımdan önce ara başlık"""
    W = 2200
    n = len(parts)
    x0 = 100
    dx = min(200, (W - 2 * x0) / (n - 1))
    bw = min(170, dx - 12)
    xs = [x0 + i * dx for i in range(n)]
    top = 120
    sections = sections or {}
    bot = top + 82 + len(steps) * 62 + len(sections) * 30
    H = bot + 220
    d = D(W, H)
    for x, (nm, c) in zip(xs, parts):
        fill, stroke, tcol = PALETTE[c]
        d.n.append(f'<rect x="{x - bw / 2}" y="{top}" width="{bw}" height="44" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        d.text(x, top + 28, nm, 13, 700, tcol, "middle")
        d.e.append(f'<line x1="{x}" y1="{top + 44}" x2="{x}" y2="{bot}" stroke="{stroke}" stroke-width="1.4" stroke-dasharray="5 5"/>')
    y = top + 82
    for i, (a, b, kind, lab, sub) in enumerate(steps):
        if i in sections:
            d.text(40, y - 20, sections[i], 13, 700, "#c2410c")
            y += 30
        xa, xb = xs[a], xs[b]
        d.flow([(xa, y), (xb, y)], "aux" if kind in ("ret", "aux") else kind)
        mx = min(xa, xb)
        d.marker(mx + 2, y - 18, i + 1, "#2f7bd8" if kind == "main" else ("#5f5f5a" if kind in ("ret", "aux") else "#c2410c"))
        longest = max(len(lab) * 7.2, len(sub) * 6.4)
        if mx + 22 + longest > W - 20:   # sağ kenara taşmasın
            d.text(W - 20, y - 12, lab, 12.5, 600, anchor="end")
            if sub:
                d.text(W - 20, y + 14, sub, 11.5, 400, "#5f5f5a", "end")
        else:
            d.text(mx + 22, y - 12, lab, 12.5, 600)
            if sub:
                d.text(mx + 22, y + 14, sub, 11.5, 400, "#5f5f5a")
        y += 62
    zones = []
    for _, c in parts:
        if c not in [z for z, _ in zones]:
            zones.append((c, {"public": "istemci", "wan": "kurum WAN / şube", "edge": "edge", "dmz": "DMZ", "identity": "kimlik",
                              "internal": "uygulama", "core": "legacy / core", "data": "veri", "pci": "kart / PCI", "external": "banka dışı"}[c]))
    d.note(40, bot + 30, 1050, "Nasıl okunur", ["Sütunlar istekten geçen bileşenler (renk = zone), yukarıdan aşağı zaman."] + note_lines, 12.5)
    d.legend(1110, bot + 30, 1070, zones, extra=False, cols=4)
    d.save(out(fname), title, subtitle, oy=40)


SEQ_NOTE = ["Mavi: müşteri isteği · turuncu: kontrol / komut · gri: yanıt ya da olay.", "Servis, konu ve kuyruk adları önerilir; ayrıntılar: 01-06."]


def img09():
    seq_image("09-uctan-uca-mobil-transfer.svg", "09 · Uçtan uca · mobil: uygulamadan para transferi, adım adım",
              "her adım: kimden → kime · port / protokol · yapılan kontrol · servis ve konu adları öneri",
              [("Mobil", "public"), ("F5 + WAF", "edge"), ("ingress-mobile", "dmz"), ("auth-proxy", "dmz"), ("IdP", "identity"), ("app ingress", "internal"),
               ("mobile-bff", "internal"), ("transfer-api", "internal"), ("MSSQL", "data"), ("Kafka", "data"), ("RabbitMQ", "data"), ("core-adapter", "core"),
               ("Oracle", "data")],
              [(0, 1, "main", "POST api.banka/mobile/v1/transfers · TLS :443", "GSLB → DC1 VIP-1 · WAF: OWASP, şema, bot"),
               (1, 2, "main", "VIP-1 → ingress-mobile :443 (TLS yeniden şifreli)", "XFF · rate limit (kanal) · header temizliği"),
               (2, 3, "req", "auth-url: auth-proxy /check", "dış access token · cihaz bağlama"),
               (3, 4, "req", "introspection + token exchange", "aktif mi · kapsam · cihaz bağlı mı"),
               (4, 3, "ret", "iç JWT (≤ 2 dk, channel=mobile)", ""),
               (3, 2, "ret", "200 + X-User-Jwt", "ret olsaydı 401 / 403 burada"),
               (2, 5, "main", "egress → cluster-a ingress :443 (mTLS + iç JWT)", "dış token DMZ'de kalır"),
               (5, 6, "main", "/transfers → mobile-bff :8080", "JWT doğrulama · scope"),
               (6, 7, "main", "POST /transfers (X-Idempotency-Key)", "Couchbase: aynı anahtar → aynı cevap"),
               (7, 8, "main", "tek transaction: transfer + outbox satırı", "EF Core · AG listener · Encrypt"),
               (7, 10, "req", "komut core.posting (publisher confirm)", "quorum queue · TLS :5671"),
               (10, 11, "req", "core-adapter tüketir", "tekrar korumalı (mesaj id)"),
               (11, 12, "req", "muhasebe kaydı (core paket / API)", "Oracle RAC · sonuç → Kafka olayı"),
               (8, 9, "aux", "outbox-relay → banka.transfer.created.v1", "notification · fraud tüketir (04)"),
               (7, 0, "ret", "202 Accepted + işlem no", "sonuç push bildirimi ile gelir")], SEQ_NOTE)


def img10():
    seq_image("10-uctan-uca-web-fatura.svg", "10 · Uçtan uca · web (İnternet Şubesi): fatura ödeme, adım adım",
              "tarayıcıda token yok: oturum cookie'si DMZ'deki token-handler'da token'a çevrilir · servis adları öneri",
              [("Tarayıcı", "public"), ("F5 + WAF", "edge"), ("ingress-web", "dmz"), ("token-handler", "dmz"), ("IdP", "identity"), ("app ingress", "internal"),
               ("web-bff", "internal"), ("payment-api", "internal"), ("MSSQL", "data"), ("RabbitMQ", "data"), ("core-adapter", "core"), ("Oracle", "data")],
              [(0, 1, "main", "POST ib.banka/api/bills/pay · cookie __Host-sid · TLS :443", "GSLB → DC1 VIP-2 · WAF: OWASP, bot · CSP / HSTS"),
               (1, 2, "main", "VIP-2 → ingress-web :443", "rate limit · header temizliği"),
               (2, 3, "req", "auth-url: token-handler /check", "cookie → oturum (Couchbase) · CSRF token kontrolü"),
               (3, 4, "req", "token exchange (oturumdaki access token)", "oturum süresi · adım-yukarı (OTP) gerekiyor mu"),
               (4, 3, "ret", "iç JWT (≤ 2 dk, channel=web)", ""),
               (3, 2, "ret", "200 + X-User-Jwt", "oturum yoksa 401 → giriş sayfası"),
               (2, 5, "main", "egress → cluster-a ingress :443 (mTLS + iç JWT)", "cookie DMZ'de kalır"),
               (5, 6, "main", "/bills/pay → web-bff :8080", "JWT doğrulama · scope payments:write"),
               (6, 7, "main", "POST /bills/pay (X-Idempotency-Key)", "fatura tutarı kurum API'sinden (egress → dış çıkış)"),
               (7, 8, "main", "ödeme kaydı + outbox (tek transaction)", "EF Core · servis başına DB"),
               (7, 9, "req", "komut core.posting", "quorum queue · publisher confirm"),
               (9, 10, "req", "core-adapter tüketir", "tekrar korumalı"),
               (10, 11, "req", "hesaptan borç kaydı", "Oracle RAC · sonuç olayı → Kafka"),
               (7, 0, "ret", "200 + dekont no", "kuruma bildirim: Kafka olayı → payment-notifier → egress → kurum API")], SEQ_NOTE)


def img11():
    seq_image("11-uctan-uca-sube-havale.svg", "11 · Uçtan uca · şube: gişeden havale, adım adım",
              "şube trafiği internete ve DMZ'ye uğramaz: kurum WAN → şube zone'u → uygulama · servis adları öneri",
              [("Şube terminali", "wan"), ("branch-fw", "wan"), ("branch-gateway", "wan"), ("IdP (AD)", "identity"), ("app ingress", "internal"),
               ("branch-bff", "internal"), ("transfer-api", "internal"), ("MSSQL", "data"), ("Kafka", "data"), ("fraud-scoring", "internal"),
               ("RabbitMQ", "data"), ("core-adapter", "core"), ("Oracle", "data")],
              [(0, 1, "main", "POST sube.banka.local/branch/v1/transfers", "SD-WAN / MPLS · TLS + şube cihaz sertifikası"),
               (1, 2, "main", "yalnızca :443 → branch-gateway", "iç firewall · TLS'e dokunmaz"),
               (2, 3, "req", "personel token'ı doğrulama (AD SSO)", "cihaz sertifikası CN = şube kodu · rol: gişe"),
               (3, 2, "ret", "iç JWT (channel=branch, rol=gişe, şube=0001)", ""),
               (2, 4, "main", "→ app ingress :443 (mTLS + iç JWT)", "XFCC: cihaz sertifikası bilgisi"),
               (4, 5, "main", "/branch/v1/transfers → branch-bff :8080", "rol ve şube yetkisi"),
               (5, 6, "main", "POST /transfers (personel + müşteri no)", "limit üstü → yetkili onayı (4 göz)"),
               (6, 7, "main", "transfer + outbox (tek transaction)", "EF Core · AG listener"),
               (7, 8, "aux", "outbox-relay → banka.transfer.created.v1", ""),
               (8, 9, "aux", "fraud-scoring tüketir", "şüpheli → işlem bekletilir, uyarı"),
               (6, 10, "req", "komut core.posting", "quorum queue"),
               (10, 11, "req", "core-adapter tüketir", "tekrar korumalı"),
               (11, 12, "req", "muhasebe kaydı", "Oracle RAC"),
               (6, 0, "ret", "200 + dekont no", "şube yazıcısı · personel işlem logu → SIEM")], SEQ_NOTE)


def img12():
    seq_image("12-uctan-uca-partner-hesap.svg", "12 · Uçtan uca · partner (açık bankacılık): hesap bilgisi sorgusu, adım adım",
              "TPP mTLS + OAuth2 · müşteri onayı (consent) kapsamı dışına çıkılmaz · servis adları öneri",
              [("Partner (TPP)", "public"), ("F5 + WAF", "edge"), ("ingress-partner", "dmz"), ("ratelimit", "dmz"), ("auth-proxy", "dmz"), ("IdP · consent", "identity"),
               ("app ingress", "internal"), ("partner-bff", "internal"), ("account-api", "internal"), ("Couchbase", "data"), ("MSSQL", "data")],
              [(0, 1, "main", "GET openapi.banka/v1/accounts · mTLS (TPP sertifikası)", "GSLB → DC1 VIP-3 · WAF: API şema doğrulama"),
               (1, 2, "main", "VIP-3 → ingress-partner :443", "auth-tls-verify-client · sertifika → partner id"),
               (2, 3, "req", "kota kontrolü (partner başına)", "aşılırsa 429"),
               (2, 4, "req", "auth-url: auth-proxy /check", "OAuth2 access token"),
               (4, 5, "req", "introspection: consent geçerli mi", "kapsam accounts:read · süre · iptal edilmiş mi"),
               (5, 4, "ret", "iç JWT (channel=partner, consent id)", ""),
               (4, 2, "ret", "200 + X-User-Jwt", "consent yoksa 403"),
               (2, 6, "main", "egress → app ingress :443 (mTLS + iç JWT)", ""),
               (6, 7, "main", "/v1/accounts → partner-bff :8080", "partner id ↔ token eşleşmesi"),
               (7, 8, "main", "GET /accounts?consent=…", "yalnızca consent kapsamındaki hesaplar"),
               (8, 9, "req", "bakiye önbelleği (30 sn)", "Couchbase · bucket RBAC"),
               (8, 10, "req", "hesap / bakiye okuma (önbellekte yoksa)", "servis başına DB · salt okunur login"),
               (7, 0, "ret", "200 JSON (açık bankacılık şeması)", "erişim kaydı → SIEM · consent denetim izi")], SEQ_NOTE)


def img13():
    seq_image("13-uctan-uca-pos-yetkilendirme.svg", "13 · Uçtan uca · POS: kartlı alışveriş yetkilendirmesi (banka kartı veren), adım adım",
              "POS internetten gelmez: acquirer → kart şeması → özel hat → kart (PCI) zone'u · uygulama zone'u PAN görmez · adlar öneri",
              [("POS", "wan"), ("acquirer", "external"), ("kart şeması / BKM", "external"), ("PCI firewall", "pci"), ("ATM/POS switch", "pci"), ("HSM", "pci"),
               ("tokenization", "pci"), ("card-api", "internal"), ("fraud-scoring", "internal"), ("Oracle (core)", "data"), ("Kafka", "data")],
              [(0, 1, "main", "kart okutma · ISO 8583 0100 (yetkilendirme)", "PIN bloğu PIN pad'de şifreli · EMV kriptogramı"),
               (1, 2, "main", "0100 → kart şeması / BKM (TROY)", "işyeri ve acquirer bilgisi"),
               (2, 3, "main", "özel hat → bankanın kart zone'u", "IPsec / TLS · IP izin listesi"),
               (3, 4, "main", "ISO 8583 → switch", "yalnızca şema bağlantıları"),
               (4, 5, "req", "PIN doğrulama · EMV ARQC kontrolü", "anahtarlar HSM dışına çıkmaz"),
               (4, 6, "req", "PAN → token", "bundan sonra yalnızca token"),
               (4, 7, "main", "yetkilendirme isteği (token, tutar, işyeri) · mTLS", "uygulama zone'u PAN görmez"),
               (7, 8, "req", "gerçek zamanlı risk skoru (≤ 50 ms)", "konum · tutar · sıklık"),
               (7, 9, "req", "provizyon: limitten düş (blokaj)", "kart limiti · hesap bakiyesi"),
               (7, 4, "ret", "onay / ret kodu (00 / 51 / 05)", ""),
               (4, 2, "ret", "0110 yanıt", "zaman aşımı → şema stand-in kuralları"),
               (2, 0, "ret", "onay · slip (acquirer üzerinden)", ""),
               (7, 10, "aux", "banka.card.authorized.v1", "SMS bildirimi · fraud modeli · gün sonu takas")], SEQ_NOTE)


def img14():
    seq_image("14-uctan-uca-atm-para-cekme.svg", "14 · Uçtan uca · ATM: bankanın kendi ATM'sinden para çekme, adım adım",
              "ATM özel ağdan kart (PCI) zone'una gelir · para verilemezse otomatik ters kayıt · adlar öneri",
              [("ATM", "wan"), ("ATM firewall", "pci"), ("ATM switch", "pci"), ("HSM", "pci"), ("tokenization", "pci"), ("card-api", "internal"),
               ("fraud-scoring", "internal"), ("Oracle (core)", "data"), ("Kafka", "data"), ("notification", "internal")],
              [(0, 1, "main", "kart + PIN · NDC / DDC mesajı", "özel ATM ağı (TLS / IPsec) · cihaz sertifikası"),
               (1, 2, "main", "yalnızca kayıtlı ATM IP'leri → switch", ""),
               (2, 3, "req", "PIN doğrulama · EMV ARQC", "anahtarlar HSM'de"),
               (2, 4, "req", "PAN → token", ""),
               (2, 5, "main", "nakit çekme yetkilendirmesi (token, tutar, ATM id) · mTLS", ""),
               (5, 6, "req", "risk skoru", "konum · sıklık · olağan dışı tutar"),
               (5, 7, "req", "hesaptan borç · günlük limit kontrolü", "Oracle RAC · tek transaction"),
               (5, 2, "ret", "onay", ""),
               (2, 0, "ret", "para ver komutu (NDC)", ""),
               (0, 2, "req", "işlem tamamlandı / para verilemedi", "verilemezse switch → card-api: ters kayıt (reversal)"),
               (5, 8, "aux", "banka.card.cash-withdrawn.v1", ""),
               (8, 9, "aux", "notification tüketir → SMS", "\"hesabınızdan … TL çekildi\"")], SEQ_NOTE)


# =====================================================================================================================
def img15():
    W, H, OY = 2200, 860, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 560), (14, 560)], "ŞUBE ZONE · DC1 (DR'da kopyası) · internete ve DMZ'ye kapalı", "wan", fill_opacity=0.3)
    d.badge(40, 146, "in ← şubeler: SD-WAN / MPLS tünelleri · yalnızca :443 (+ yazıcı / kuyruk sunucu portları)", "in")
    d.badge(2160, 146, "out → uygulama ingress :443 (mTLS + iç JWT) · kimlik zone'u (AD SSO) · mgmt (log)", "out", anchor="end")
    d.box(40, 180, 520, bh(5), "SD-WAN hub ×2 (HA)", ["şube başına IPsec tüneli · MPLS yedek hat", "şube başına VLAN / VRF ayrımı",
                                                      "QoS: gişe uygulaması öncelikli", "şube cihaz envanteri (NAC)", "yönetim: ayrı OOB ağı"], color="wan", size=13)
    d.box(580, 180, 520, bh(5), "branch-fw (iç firewall, HA çift)", ["kaynak: şube VLAN'ları · hedef: branch-gateway :443",
                                                                    "şubeden başka hedefe yol yok (internet, DMZ, veri)", "IPS · uygulama tanıma",
                                                                    "TLS'e dokunmaz (uçtan uca mTLS)", "log → SIEM"], color="wan", size=13)
    gb = d.pod(1120, 180, 1046, None, "branch-gateway (ingress-nginx · A/B)", "Deployment ×2 · ayrı küçük cluster ya da VM (öneri)", "wan", [
        ("ingress-nginx (nginx-branch)", "proxy", ["auth-tls-verify-client: on · auth-tls-secret: şube CA (cihaz sertifikası)",
                                                  "sertifika CN → şube kodu (ör. 0001) · XFCC başlığı → uygulama", "auth-url: kimlik zone'u (personel token doğrulama → iç JWT)",
                                                  "limit-rps (şube başına) · yalnızca /branch/v1/* yolları", "upstream: uygulama ingress :443 (proxy-ssl, mTLS)"]),
        ("platform", "agent", ["cert-manager (şube CA) · otel-collector · fluent-bit → mgmt"])])
    d.text(40, 420, "Şube başına bilgiler (örnek)", 14, 700)
    table(d, 40, 432, 1060, [("şube", 0.12), ("cihaz sertifikası", 0.3), ("VLAN / VRF", 0.2), ("izinli kullanıcılar", 0.38)], [
        ["0001", "CN=sube-0001 · Branch CA", "VLAN 101 / VRF şube", "gişe · operasyon · şube müdürü (AD grupları)"],
        ["0002", "CN=sube-0002 · Branch CA", "VLAN 102 / VRF şube", "gişe · operasyon"],
        ["genel müdürlük", "CN=gm-ops · Branch CA", "VLAN 900", "merkez operasyon · denetim (salt okunur)"]], size=11.5)
    d.note(1120, gb + 20, 1046, "Kurallar", ["Şube personeli kimliği AD'den gelir; iç JWT'de rol (gişe, müdür) ve şube kodu taşınır.",
                                              "Limit üstü işlemler 4 göz: ikinci onay branch-bff'te zorunlu.",
                                              "Kayıp / çalınan cihaz: sertifika iptal (CRL / OCSP) → gateway bağlantıyı keser."], 12.5)
    d.flow([(300, 124), (300, 180)], "main")
    d.flow([(560, 260), (580, 260)], "main")
    d.flow([(1100, 260), (1120, 260)], "main")
    d.flow([(1640, gb), (1640, 580)], "main", "→ uygulama ingress :443 (03, 11)", 1652, 576)
    d.note(40, 600, 1060, "Bu resimde", ["Şube trafiği internete ve DMZ'ye uğramaz: kurum WAN → şube zone'u → uygulama.",
                                         "branch-gateway şube cihaz sertifikasını ve personel kimliğini doğrular, iç JWT üretir.",
                                         "Ürün adları ve şube bilgileri örnek; uçtan uca akış: 11."], 12.5)
    d.legend(1120, 600, 1060, [("wan", "şube / kurum WAN"), ("internal", "uygulama")], extra=False, cols=3)
    d.save(out("15-sube-zone.svg"), "15 · Şube zone'u: SD-WAN hub, branch-fw, branch-gateway (ingress-nginx), şube bazlı kurallar",
           "kurum WAN'dan gelen şube trafiği · cihaz sertifikası + personel kimliği · " + CONFIRMED, oy=OY)


def img16():
    W, H, OY = 2200, 900, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 580), (14, 580)], "KİMLİK ZONE · kimlik cluster'ı (Kubernetes) · DC1 (DR'da kopyası)", "identity", fill_opacity=0.2)
    d.badge(40, 146, "in ← DMZ auth-proxy / token-handler · şube gateway · uygulama (JWKS) :443 (mTLS)", "in")
    d.badge(2160, 146, "out → AD / LDAP · IdP DB (MSSQL) · egress → SMS / OTP sağlayıcı · log → mgmt", "out", anchor="end")
    c, cw = [40, 760, 1480], 680
    y = ns_pods(d, c[0], 180, cw, "iam", [("idp (öneri: Keycloak / Duende)", "Deployment ×3", "müşteri · personel · partner realm'leri"),
                                          ("idp-cache", "StatefulSet ×3", "oturum / token önbelleği (Infinispan)")], "identity") + 12
    y = ns_pods(d, c[0], y, cw, "mfa", [("otp-service", "Deployment ×2", "SMS / push OTP · TOTP"),
                                        ("device-registry", "Deployment ×2", "mobil cihaz anahtarları · bağlama")], "identity") + 12
    ns_pods(d, c[0], y, cw, "consent", [("consent-api", "Deployment ×2", "açık bankacılık onayları · iptal")], "identity")
    y2 = ns_pods(d, c[1], 180, cw, "directory", [("ldap-connector", "Deployment ×2", "AD / LDAP → personel kullanıcıları"),
                                                 ("group-sync", "CronJob", "AD grupları → roller (gişe, müdür)")], "identity") + 12
    y2 = ns_pods(d, c[1], y2, cw, "egress", [("egress-gateway", "Deployment ×2", "→ SMS / push sağlayıcı · AD")], "identity") + 12
    ns_pods(d, c[1], y2, cw, "platform", PLATFORM[:3], "mgmt")
    d.text(c[2] + 12, 196, "Token türleri", 13, 700)
    yt = table(d, c[2] + 12, 208, cw - 24, [("token", 0.3), ("kim alır", 0.36), ("ömür", 0.34)], [
        ["dış access token", "mobil · web (handler) · partner", "5-15 dk · DPoP / mTLS bağlı"],
        ["refresh token", "mobil · web oturumu", "saatler · tek kullanımlık"],
        ["iç JWT", "uygulama servisleri", "≤ 2 dk · RFC 8693 exchange"],
        ["personel token", "şube (AD SSO)", "mesai süresi · cihaz bağlı"]], size=11.5)
    d.note(c[2] + 12, yt + 20, cw - 24, "Veri ve DR", ["IdP DB: MSSQL AG (kendi DB'si) · imza anahtarları Vault / HSM'de",
                                                      "JWKS uygulama ingress'leri ve servislerce önbelleğe alınır",
                                                      "DR: kimlik cluster'ı DC2'de · DB AG asenkron replika"], 12.5)
    d.note(40, 610, 1060, "Bu resimde", ["Kimlik zone'u dış token'ı doğrular ve uygulamaya giden iç JWT'yi üretir.",
                                         "Müşteri, personel (AD) ve partner (consent) kimlikleri ayrı realm'lerde.",
                                         "Ürün adları öneri; mevcut IdP'niz (ör. Duende, Keycloak, ADFS) ile eşlenir."], 12.5)
    d.legend(1120, 610, 1060, [("identity", "kimlik"), ("mgmt", "platform")], extra=True, cols=3)
    d.save(out("16-kimlik-zone.svg"), "16 · Kimlik zone'u: IdP, MFA / OTP, cihaz kaydı, consent, AD bağlantısı, token türleri",
           "her kutu bir namespace · iç JWT bu zone'da üretilir · " + CONFIRMED, oy=OY)


def img17():
    W, H, OY = 2200, 920, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 610), (14, 610)], "KART ZONE · PCI DSS · ayrı segment (DC1, DR'da kopyası) · internete kapalı", "pci", fill_opacity=0.3)
    d.badge(40, 146, "in ← ATM ağı (NDC / DDC) · kart şemaları / BKM (ISO 8583, özel hat)", "in")
    d.badge(2160, 146, "out → uygulama zone'u card-api :443 (mTLS · yalnızca token) · log → SIEM", "out", anchor="end")
    d.box(40, 180, 520, bh(5), "atm-pos-fw (HA çift)", ["kaynak: kayıtlı ATM IP'leri · şema hatları", "IPsec / TLS tünel sonlandırma",
                                                         "yalnızca switch portları", "her bağlantı loglanır (PCI 10)", "yönetim: ayrı OOB ağı"], color="pci", size=13)
    sb = d.pod(580, 180, 760, None, "card-switch", "×2 · aktif / aktif · ayrı cluster ya da VM", "pci", [
        ("switch uygulaması", "app", ["ISO 8583 (şemalar) · NDC / DDC (ATM) mesaj işleme", "yönlendirme: kendi kartımız → card-api · diğerleri → şema",
                                      "stand-in: card-api'ye ulaşılamazsa limitli onay kuralları", "reversal (ters kayıt) ve zaman aşımı yönetimi"]),
        ("HSM istemcisi", "agent", ["PIN çevirme / doğrulama · EMV ARQC / ARPC · anahtar türetme"])])
    d.box(1360, 180, 380, bh(4), "HSM (ağ HSM'i, HA)", ["PIN doğrulama (PVV / offset)", "EMV kriptogram · MAC", "anahtar yönetimi (ZMK, ZPK)",
                                                         "FIPS 140-2 L3 · PCI PIN"], color="pci", size=13)
    d.box(1760, 180, 406, bh(4), "tokenization ×2", ["PAN ↔ token (format korumalı)", "kasa DB: PCI içinde, şifreli",
                                                     "detokenize: yalnızca switch", "uygulama zone'u PAN görmez"], color="pci", size=13)
    d.text(40, 400, "PCI DSS kontrolleri (özet)", 14, 700)
    table(d, 40, 412, 1300, [("gereksinim", 0.22), ("bu zone'da", 0.78)], [
        ["1 · ağ ayrımı", "ayrı segment · yalnızca atm-pos-fw ve card-api bağlantısı · DMZ / internet yolu yok"],
        ["3 · kart verisi", "PAN yalnızca tokenization kasasında, şifreli · uygulama zone'u token görür"],
        ["4 · iletim", "tüm bağlantılar TLS / IPsec · şema hatları özel"],
        ["7-8 · erişim", "PAM üzerinden, MFA · kişi başına hesap · en az yetki"],
        ["10 · log", "tüm erişim ve işlem logları → SIEM · 1 yıl saklama"],
        ["11 · test", "çeyreklik zafiyet taraması · yıllık sızma testi"]], size=11.5)
    d.note(1360, sb + 120, 806, "Neden ayrı?", ["PCI kapsamını daraltmak: kart verisi yalnızca bu zone'da.",
                                                 "ATM / POS internetten ve edge'den gelmez.",
                                                 "Uygulama zone'u PCI kapsamı dışında kalır (yalnızca token)."], 12.5)
    d.flow([(300, 124), (300, 180)], "main")
    d.flow([(560, 260), (580, 260)], "main")
    d.flow([(1340, 240), (1360, 240)], "req")
    d.flow([(1740, 240), (1760, 240)], "req")
    d.flow([(960, sb), (960, 390), (1350, 390), (1350, 630)], "main", "→ card-api :443 (mTLS, token) · 13, 14", 1362, 626)
    d.note(40, 650, 1060, "Bu resimde", ["Kart (PCI) zone'u ATM ve POS trafiğini karşılar; kart verisi bu zone'dan çıkmaz.",
                                         "card-switch PIN ve EMV'yi HSM'de doğrular, PAN'ı token'a çevirip card-api'ye gönderir.",
                                         "Ürün adları ve kontroller özet / öneri; uçtan uca akışlar: 13 (POS), 14 (ATM)."], 12.5)
    d.legend(1120, 650, 1060, [("pci", "kart / PCI"), ("internal", "uygulama")], extra=False, cols=3)
    d.save(out("17-kart-pci-zone.svg"), "17 · Kart (PCI) zone'u: atm-pos-fw, card-switch, HSM, tokenization, PCI kontrolleri",
           "ATM / POS ve kart şemalarının girdiği ayrı segment · " + CONFIRMED, oy=OY)


IMAGES = {"00": img00, "01": img01, "02": img02, "03": img03, "04": img04, "05": img05, "06": img06, "07": img07, "08": img08, "09": img09, "10": img10, "11": img11, "12": img12, "13": img13, "14": img14, "15": img15, "16": img16, "17": img17}

if __name__ == "__main__":
    for k in (sys.argv[1:] or IMAGES):
        IMAGES[k]()
        print("ok", k)
