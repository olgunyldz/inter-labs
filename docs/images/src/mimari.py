"""Mimari genel bakış (referans mimari stili): istek yolu ortada (edge -> DMZ -> uygulama -> veri, aralarında FW ve portlar),
kimlik ve özel zone'lar yanda, ağ ve güvenlik solda, DC2 (DR) sağda, platform ve mgmt altta. Her kartta logo, ad, kurulacağı faz.
Çıktı: docs/images/mimari/  (PNG: bash docs/images/src/render.sh <svg>)

  python docs/images/src/mimari.py                         -> 00-hedef-mimari.svg  (hedef; teknoloji listesi değişince yeniden üretilir)
  python docs/images/src/mimari.py --faz 3                 -> faz-03-veri.svg      (Faz 3 sonu; YENİ dosya, varsa üzerine yazmaz)
  python docs/images/src/mimari.py --faz 4 --tamam 0,1,2,4                         (paralel fazlar: biten fazlar açıkça; varsayılan 0..N)

Faz resimleri o günün fotoğrafıdır: bir kez üretilir, sonra değiştirilmez (--force yalnızca yanlış üretilmiş bir resmi düzeltmek için).
Bir faz bitince önce ZONES'taki adları kurulan ürünle eşle (öneri -> gerçek ürün), kurulmayanı ERTELENEN'e yaz, sonra --faz N.
Logolar: docs/images/logos/ (Devicon, CNCF artwork, Simple Icons; ti-*: Tabler Icons)."""
import base64
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detay_style import D
from topo_style import BLUE, FONT, GRAY, PALETTE, PLANNED, SUB, TXT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "mimari")
LOGOS = os.path.join(HERE, "..", "logos")
SURUM = "v2"

FAZLAR = [(0, "kararlar", "Kararlar"), (1, "ag-fw", "Ağ ve FW"), (2, "mgmt", "Mgmt"), (3, "veri", "Veri"), (4, "kimlik", "Kimlik"),
          (5, "uygulama", "Uygulama"), (6, "dmz", "DMZ"), (7, "edge", "Edge"), (8, "ozel-zonelar", "Özel zone'lar"),
          (9, "dr", "DR (DC2)"), (10, "canli", "Canlıya geçiş")]

# Zone başlık rengi = güven seviyesi (topo_style.PALETTE anahtarı)
# Bileşen: (logo dosyası, ad, kısa açıklama, faz, teyitli mi)   teyitli = kurumun verdiği bilgi; diğerleri öneri (Faz 0'da eşlenir)
ZONES = {
    "kanal_vpn": ("Kurum ağı · VPN", None, "wan", [
        ("ti-users", "Operasyon", "VPN → PAM → mgmt", 1, True)]),
    "kanal_net": ("İnternet", None, "public", [
        ("android+apple", "Mobil", "iOS · Android", 10, True),
        ("ti-world-www", "İnternet Şubesi", "web · ib.banka", 10, True),
        ("ti-api", "Partner API", "açık bankacılık", 10, True)]),
    "kanal_wan": ("Kurum WAN · özel hat", None, "wan", [
        ("ti-building-bank", "Şube", "gişe · SD-WAN", 10, True),
        ("ti-credit-card", "ATM · POS", "ISO 8583", 10, True)]),
    "edge": ("Edge", "DC1 · appliance (HA)", "edge", [
        ("ti-world", "GSLB", "DC1 aktif · DC2 DR", 7, False),
        ("f5", "F5 LTM ×2", "VIP · TLS 1.2/1.3", 7, False),
        ("ti-shield-check", "WAF", "OWASP CRS · bot", 7, False),
        ("ti-wall", "Dış NGFW", "yalnızca :443 · IPS", 7, False),
        ("ti-cloud", "DDoS · CDN", "scrubbing · statik", 7, False)]),
    "dmz": ("DMZ", "dmz-a · dmz-b · iş mantığı ve veri yok", "dmz", [
        ("nginx", "ingress-nginx", "kanal başına ×3", 6, True),
        ("ti-lock", "auth-proxy", "iç JWT üretimi", 6, False),
        ("ti-key", "token-handler", "web: cookie → JWT", 6, False),
        ("ti-gauge", "rate limit", "sayaç Couchbase'de", 6, False),
        ("ti-logout", "egress-gateway", "→ app · IdP", 6, False)]),
    "uyg": ("Uygulama", "cluster-a · cluster-b · active-active", "internal", [
        ("dotnetcore", ".NET 8", "ASP.NET Core", 5, True),
        ("nginx", "ingress-nginx", "iç · mTLS · JWT", 5, True),
        ("keda", "KEDA", "olay tabanlı ölçek", 5, False),
        ("ti-messages", "MassTransit", "outbox · retry", 5, False),
        ("ti-logout", "egress-gateway", "→ veri · monolith", 5, False)]),
    "kimlik": ("Kimlik", "iç JWT · JWKS → DMZ, app", "identity", [
        ("keycloak", "Keycloak", "IdP · ×3", 4, False),
        ("ti-password-mobile-phone", "MFA · OTP", "cihaz kaydı", 4, False),
        ("ti-checklist", "consent", "açık bankacılık", 4, False),
        ("windows11", "AD / LDAP", "personel SSO", 4, False)]),
    "kart": ("Kart zone'u · PCI DSS", "ayrı segment → card-api :443", "pci", [
        ("ti-arrows-exchange", "card-switch", "ISO 8583 · ×2", 8, False),
        ("ti-shield-lock", "HSM", "PIN · EMV ARQC", 8, False),
        ("ti-hash", "tokenization", "PAN ↔ token", 8, False)]),
    "sube": ("Şube zone'u", "→ app (DMZ'siz)", "wan", [
        ("ti-router", "SD-WAN · FW", "tünel · branch-fw", 8, False),
        ("nginx", "branch-gateway", "ingress · cihaz mTLS", 8, True)]),
    "legacy": ("Legacy", "VM", "core", [
        ("windows11", "Monolith", "IIS · strangler", 8, True)]),
    "veri_k8s": ("data cluster · operator ile", None, "data", [
        ("apachekafka", "Kafka", "KRaft · 3 broker", 3, True),
        ("strimzi", "Strimzi", "Kafka operator", 3, False),
        ("rabbitmq", "RabbitMQ", "quorum · 3 node", 3, True),
        ("ti-transform", "Debezium", "Oracle CDC", 3, False),
        ("ti-schema", "Schema Registry", "Avro / JSON", 3, False),
        ("couchbase", "Couchbase", "önbellek · doküman", 3, True)]),
    "veri_vm": ("VM / fiziksel", None, "data", [
        ("oracle", "Oracle RAC", "core · monolith", 3, True),
        ("microsoftsqlserver", "MSSQL AG", "yeni servisler", 3, True)]),
    "ag": ("Ağ ve güvenlik", "DC1 + DC2", "wan", [
        ("ti-wall", "Zone FW'leri", "port matrisi", 1, False),
        ("ti-world-upload", "Dış çıkış", "NGFW · FQDN proxy", 1, False),
        ("ti-lock-access", "VPN · PAM", "bastion", 1, False),
        ("ti-building", "DC1 ↔ DC2", "replikasyon hattı", 1, False),
        ("ti-file-certificate", "PKI", "kök + ara CA", 1, False)]),
    "dr": ("DC2 · DR", "felakette GSLB → DC2", "external", [
        ("kubernetes", "DR cluster'ları", "dmz · app · data · kimlik", 9, True),
        ("f5", "Edge DR", "F5 + WAF standby", 9, False),
        ("ti-switch-horizontal", "Failover", "runbook · tatbikat", 9, False),
        ("apachekafka", "MirrorMaker 2", "Kafka → DR", 9, False),
        ("rabbitmq", "shovel", "RabbitMQ → DR", 9, False),
        ("couchbase", "XDCR", "Couchbase → DR", 9, False),
        ("oracle", "Data Guard", "Oracle → standby", 9, False),
        ("microsoftsqlserver", "AG async", "MSSQL → DR", 9, False)]),
    "platform": ("Platform", "her cluster'da aynı · DC1 + DC2", "mgmt", [
        ("kubernetes", "Kubernetes", "3 CP · CIS", 2, True),
        ("cert-manager", "cert-manager", "Vault PKI · mTLS", 2, False),
        ("ti-key", "External Secrets", "Vault → Secret", 2, False),
        ("kyverno", "Kyverno", "policy · imaj imzası", 2, False),
        ("fluentbit", "fluent-bit", "log → mgmt", 2, False),
        ("opentelemetry", "OpenTelemetry", "trace · metrik", 2, False)]),
    "mgmt": ("Mgmt", "dağıtım: script + Helm/OCI · telemetri tek yönlü", "mgmt", [
        ("harbor", "Harbor", "imaj · chart (OCI)", 2, False),
        ("helm", "Helm · OCI", "deploy.sh", 2, False),
        ("vault", "Vault", "PKI · KV · DB", 2, False),
        ("prometheus", "Prometheus", "metrik · alarm", 2, False),
        ("grafana", "Grafana", "Loki · Tempo", 2, False),
        ("ti-archive", "Velero", "cluster yedeği", 2, False)]),
}

# Fazı bittiği hâlde kurulmamış (ertelenmiş / kapsamdan çıkmış) bileşenler: ad -> not. Faz resmi üretmeden önce güncellenir.
ERTELENEN = {}

# Yerleşim (px): sol kolon (ağ), omurga (edge/DMZ/uygulama), yan kolon (kimlik, kart, şube, legacy), DR kolonu
W, H = 2190, 1240   # H: draw() içeriğe göre ayarlar
LX, LW = 24, 210
SX, SW = 254, 940
RX, RW = 1214, 616
DRX, DRW = 1870, 296
CW, CH, G = 172, 54, 12
BG, LINE, CARD_LINE = "#f6f6f4", "#d9d9d3", "#d4d4ce"
DONE_C, DONE_F = "#1d7a46", "#e5f4e5"

_cache = {}


def data_uri(name, drawio=False):
    if name not in _cache:
        _cache[name] = base64.b64encode(open(os.path.join(LOGOS, name + ".svg"), "rb").read()).decode()
    return ("data:image/svg+xml," if drawio else "data:image/svg+xml;base64,") + _cache[name]


def rect(layer, x, y, w, h, fill, stroke="none", sw=0, rx=10, dash=False, opacity=None):
    extra = (' stroke-dasharray="5 4"' if dash else "") + (f' opacity="{opacity}"' if opacity else "")
    layer.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>')


def logo(d, x, y, s, key, faded=False):
    names = key.split("+")
    sub = s / len(names)
    for i, n in enumerate(names):
        ix, iy = x + i * sub, y + (s - sub) / 2
        if hasattr(d, "_v"):   # draw.io (drawio.DX): resim şekli
            d._v(ix, iy, sub, sub, "shape=image;html=1;imageAspect=1;aspect=fixed;" + ("opacity=35;" if faded else "")
                 + "image=" + data_uri(n, True) + ";")
        else:
            op = ' opacity="0.35"' if faded else ""
            d.n.append(f'<image x="{ix}" y="{iy}" width="{sub}" height="{sub}" preserveAspectRatio="xMidYMid meet"{op} href="{data_uri(n)}"/>')


def faz_badge(d, cx, cy, n, state):
    """Kartın sağ üst köşesindeki faz numarası. state: hedef | done | planned"""
    fill = {"hedef": "#2b2b28", "done": DONE_C, "planned": "#b5b5af"}[state]
    d.n.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="{fill}" stroke="#ffffff" stroke-width="2"/>')
    if hasattr(d, "_v"):
        d._v(cx - 10, cy - 10, 20, 20, f"ellipse;html=1;fillColor={fill};strokeColor=#ffffff;strokeWidth=2;fontColor=#ffffff;fontSize=10.5;"
             "fontStyle=1;align=center;verticalAlign=middle;", str(n))
    else:
        d.t(cx, cy + 4, str(n), 10.5, 700, "#ffffff", "middle")


def card(d, x, y, item, done_set, w=CW):
    key, name, sub, faz, teyit = item
    done = done_set is not None and faz in done_set and name not in ERTELENEN
    planned = done_set is not None and not done
    if done:
        rect(d.n, x, y, w, CH, "#ffffff", DONE_C, 1.8, 8)
    elif planned:
        rect(d.n, x, y, w, CH, "#fbfbfa", "#cfcfc9", 1.2, 8, dash=True)
    else:
        rect(d.n, x, y, w, CH, "#ffffff", CARD_LINE if teyit else "#a9a9a3", 1.2, 8, dash=not teyit)
    logo(d, x + 11, y + 13, 28, key, faded=planned)
    d.t(x + 48, y + 24, name, 13, 600, PLANNED if planned else TXT)
    d.t(x + 48, y + 41, "ertelendi" if name in ERTELENEN and done_set is not None else sub, 11.5, 400,
        PLANNED if planned else SUB)
    faz_badge(d, x + w - 4, y + 3, faz, "done" if done else ("planned" if planned else "hedef"))
    return done


def zone(d, x, y, w, h, title, right, color, count=None):
    """Beyaz zone, renkli başlık şeridi (renk = güven seviyesi)"""
    fill, stroke, tcol = PALETTE[color]
    rect(d.z, x, y, w, h, "#ffffff", LINE, 1.2, 10)
    rect(d.z, x, y, w, 30, fill, "none", 0, 10)
    rect(d.z, x, y + 20, w, 10, fill, "none", 0, 0)
    d.z.append(f'<line x1="{x}" y1="{y + 30}" x2="{x + w}" y2="{y + 30}" stroke="{stroke}" stroke-width="1.2"/>')
    d.t(x + 14, y + 20, title, 14, 700, tcol, layer=d.l)
    r = " · ".join(s for s in (right, count) if s)
    if r:
        d.t(x + w - 14, y + 20, r, 11.5, 400 if not count else 600, tcol, "end", d.l)


def zone_h(n, ncol):
    rows = (n + ncol - 1) // ncol
    return 30 + 14 + rows * CH + (rows - 1) * G + 14


def cards(d, x, y, items, ncol, done_set, w=CW, gap=G):
    k = 0
    for i, it in enumerate(items):
        k += card(d, x + (i % ncol) * (w + gap), y + (i // ncol) * (CH + G), it, done_set, w)
    return k


def count_txt(items, k, done_set):
    return f"{k}/{len(items)} kuruldu" if done_set is not None else None


def put(d, key, x, y, w, ncol, done_set, cw=CW):
    """Zone'u ve kartlarını çiz; yüksekliği döndür"""
    title, right, color, items = ZONES[key]
    h = zone_h(len(items), ncol)
    k = sum(1 for it in items if done_set is not None and it[3] in done_set and it[1] not in ERTELENEN)
    zone(d, x, y, w, h, title, right, color, count_txt(items, k, done_set))
    used = ncol * cw + (ncol - 1) * G
    cards(d, x + (w - used) / 2, y + 44, items, ncol, done_set, cw)
    return h, k, len(items)


def fw_band(d, y, text):
    rect(d.z, SX, y, SW, 26, "#fbe9e4", "#e3b4a6", 1.2, 6)
    d.t(SX + 14, y + 17, text, 12, 600, "#8a2f1c", layer=d.z)


def phase_strip(d, y, done_set):
    cw = (W - 2 * LX - 10 * 8) / 11
    for i, (n, _, ad) in enumerate(FAZLAR):
        x = LX + i * (cw + 8)
        done = done_set is not None and n in done_set
        state = "done" if done else ("planned" if done_set is not None else "hedef")
        rect(d.n, x, y, cw, 32, DONE_F if done else "#ffffff", DONE_C if done else LINE, 1.2, 16, dash=state == "planned")
        faz_badge(d, x + 18, y + 16, n, state)
        d.t(x + 36, y + 21, ad, 12.5, 600 if done else 400, TXT if state != "planned" else PLANNED)


def draw(done_set=None):
    d = D(W, H)
    phase_strip(d, 102, done_set)
    tot = kur = 0

    def acc(r):
        nonlocal tot, kur
        kur, tot = kur + r[1], tot + r[2]
        return r[0]

    # kanallar
    acc(put(d, "kanal_vpn", LX, 146, LW, 1, done_set, LW - 32))
    acc(put(d, "kanal_net", SX, 146, SW, 3, done_set))
    acc(put(d, "kanal_wan", RX, 146, RW, 2, done_set))
    d.t(DRX + DRW / 2, 206, "DC2: felakette devreye girer", 12.5, 400, SUB, "middle")
    d.arrow([(SX + SW / 2, 258), (SX + SW / 2, 278)], blue=True)
    # omurga: edge -> FW -> DMZ -> FW -> uygulama -> FW -> veri
    y = 278
    for key, fw in (("edge", "FW · edge → DMZ · :443 (TLS yeniden şifreli)"), ("dmz", "FW · DMZ → uygulama · :443 (mTLS)"),
                    ("uyg", "FW · uygulama → veri · Kafka TLS · 5671 · Couchbase · 1433 · 1521")):
        h = acc(put(d, key, SX, y, SW, 5, done_set))
        fw_band(d, y + h + 8, fw)
        d.arrow([(SX + SW / 2, y + h), (SX + SW / 2, y + h + 42)], blue=True)
        y += h + 42
    yv = y
    # yan kolon
    hk = acc(put(d, "kimlik", RX, 278, RW, 2, done_set))
    hc = acc(put(d, "kart", RX, 278 + hk + 14, RW, 3, done_set))
    ys = 278 + hk + 14 + hc + 14
    acc(put(d, "sube", RX, ys, 388, 2, done_set))
    hl = acc(put(d, "legacy", RX + 400, ys, RW - 400, 1, done_set))
    # veri: tek zone, iki alt grup
    title_h = 30 + 14
    sub_h = 26 + CH + 14
    vh = title_h + sub_h + 14
    nv = len(ZONES["veri_k8s"][3]) + len(ZONES["veri_vm"][3])
    kv = sum(1 for z in ("veri_k8s", "veri_vm") for it in ZONES[z][3] if done_set is not None and it[3] in done_set and it[1] not in ERTELENEN)
    zone(d, SX, yv, RX + RW - SX, vh, "Veri ve mesajlaşma", None, "data",
         count_txt(range(nv), kv, done_set))
    gx = SX + 16
    for key, ncol in (("veri_k8s", 6), ("veri_vm", 2)):
        t, _, color, items = ZONES[key]
        gw = ncol * CW + (ncol - 1) * G + 24
        rect(d.z, gx, yv + title_h, gw, sub_h, PALETTE[color][0], PALETTE[color][1], 1, 8, dash=True)
        d.t(gx + 12, yv + title_h + 18, t, 12, 600, PALETTE[color][2], layer=d.l)
        cards(d, gx + 12, yv + title_h + 26, items, ncol, done_set)
        gx += gw + 16
    kur, tot = kur + kv, tot + nv
    # legacy -> Oracle
    lx = RX + 400 + (RW - 400) / 2
    d.arrow([(lx, ys + hl), (lx, yv + title_h)])
    d.t(lx + 8, ys + hl + 22, "ODP.NET", 11.5, 400, SUB, layer=d.l)
    bottom = yv + vh
    # sol kolon: ağ ve güvenlik
    acc(put_col(d, "ag", LX, 278, LW, bottom - 278, done_set,
                ["Zone'lar arası trafik yalnızca", "FW bantlarındaki portlardan.", "Dış dünyaya çıkış yalnızca", "egress → dış çıkış zone'u."]))
    # DR kolonu
    acc(put_col(d, "dr", DRX, 278, DRW, bottom - 278, done_set, [], split=3, split_label="asenkron replikasyon"))
    d.arrow([(RX + RW, yv + vh / 2), (DRX, yv + vh / 2)], dashed=True)
    # platform ve mgmt
    y = bottom + 20
    for key in ("platform", "mgmt"):   # kartlar omurgayla hizalı, açıklama solda
        title, right, color, items = ZONES[key]
        h = zone_h(len(items), 6)
        k = sum(1 for it in items if done_set is not None and it[3] in done_set and it[1] not in ERTELENEN)
        zone(d, LX, y, W - 2 * LX, h, title, None, color, count_txt(items, k, done_set))
        for i, ln in enumerate(right.split(" · ")):
            d.t(LX + 16, y + 56 + i * 18, ln, 12, 400, SUB, layer=d.l)
        cards(d, SX, y + 44, items, 6, done_set)
        kur, tot = kur + k, tot + len(items)
        y += h + 14
    legend(d, y + 6, done_set)
    d.h = y + 6 + 48 + 24
    bg = []
    rect(bg, 0, 92, W, d.h - 92, BG, "none", 0, 0)
    d.z[:0] = bg
    return d, tot, kur


def put_col(d, key, x, y, w, h, done_set, notes, split=None, split_label=None):
    """Dikey kolon zone'u: kartlar alt alta (split: bu kadar karttan sonra ara başlık)"""
    title, right, color, items = ZONES[key]
    k = sum(1 for it in items if done_set is not None and it[3] in done_set and it[1] not in ERTELENEN)
    zone(d, x, y, w, h, title, None, color, None)
    cw = w - 32
    cy = y + 44
    if right:
        d.t(x + 16, cy + 4, right, 11.5, 400, SUB, layer=d.l)
        cy += 18
    if done_set is not None:
        d.t(x + 16, cy + 4, f"{k}/{len(items)} kuruldu", 11.5, 600, DONE_C if k == len(items) else TXT, layer=d.l)
        cy += 18
    for i, it in enumerate(items):
        if split is not None and i == split:
            d.t(x + 16, cy + 14, split_label, 12, 600, PALETTE[color][2], layer=d.l)
            cy += 24
        card(d, x + 16, cy, it, done_set, cw)
        cy += CH + 8
    for i, ln in enumerate(notes):
        d.t(x + 16, cy + 16 + i * 18, ln, 11.5, 400, SUB, layer=d.l)
    return h, k, len(items)


def legend(d, y, done_set):
    rect(d.z, LX, y, W - 2 * LX, 48, "#ffffff", LINE, 1.2, 10)
    x, cy = LX + 16, y + 24
    d.t(x, cy + 5, "Lejant", 13, 700, TXT)
    x += 70
    rect(d.n, x, cy - 10, 34, 20, "#ffffff", CARD_LINE, 1.2, 5)
    d.t(x + 42, cy + 4, "teyitli (kurumun verdiği bilgi)", 12, 400, SUB)
    x += 250
    rect(d.n, x, cy - 10, 34, 20, "#ffffff", "#a9a9a3", 1.2, 5, dash=True)
    d.t(x + 42, cy + 4, "öneri (kurumun araçlarıyla eşlenecek)", 12, 400, SUB)
    x += 300
    faz_badge(d, x + 10, cy, "N", "hedef")
    d.t(x + 28, cy + 4, "kurulacağı faz", 12, 400, SUB)
    x += 140
    d.arrow([(x, cy), (x + 40, cy)], blue=True)
    d.t(x + 50, cy + 4, "müşteri trafiği", 12, 400, SUB)
    x += 160
    rect(d.n, x, cy - 9, 40, 18, "#fbe9e4", "#e3b4a6", 1.2, 4)
    d.t(x + 50, cy + 4, "FW: zone'lar arası açık portlar", 12, 400, SUB)
    x += 270
    d.arrow([(x, cy), (x + 40, cy)], dashed=True)
    d.t(x + 50, cy + 4, "bağlantı / replikasyon", 12, 400, SUB)
    x += 210
    if done_set is not None:
        faz_badge(d, x + 10, cy, "✓", "done")
        d.t(x + 28, cy + 4, "kuruldu", 12, 400, SUB)
        x += 100
        faz_badge(d, x + 10, cy, "N", "planned")
        d.t(x + 28, cy + 4, "planlı (soluk)", 12, 400, SUB)
    d.t(W - LX - 16, cy + 4, f"{SURUM} · logolar: Devicon · CNCF artwork · Simple Icons · Tabler Icons", 11.5, 400, SUB, "end")


def img_hedef():
    d, total, _ = draw(None)
    d.save(os.path.join(OUT, "00-hedef-mimari.svg"), "Hedef mimari: katmanlar ve teknolojiler",
           f"İki veri merkezi · {total} bileşen · köşedeki sayı kurulacağı faz (docs/prod-kurulum-plani.md) · "
           f"kesikli çerçeve = öneri · {datetime.date.today():%Y-%m-%d}")


def img_faz(n, force=False, tamam=None):
    _, slug, ad = FAZLAR[n]
    tamam = set(tamam) if tamam else set(range(n + 1))
    path = os.path.join(OUT, f"faz-{n:02d}-{slug}.svg")
    if os.path.exists(path) and not force:
        sys.exit(f"{os.path.normpath(path)} zaten var: faz resimleri bir kez üretilir (düzeltmek için --force)")
    d, total, kur = draw(tamam)
    d.save(path, f"Faz {n} sonu: gerçekleşen mimari ({ad})",
           f"{datetime.date.today():%Y-%m-%d} · {kur}/{total} bileşen kuruldu · biten fazlar: {', '.join(map(str, sorted(tamam)))}"
           + (f" · ertelenen: {', '.join(ERTELENEN)}" if ERTELENEN else ""))
    return path


IMAGES = {"00": img_hedef}   # drawio.py yalnızca hedef resmini sayfa olarak alır

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if "--faz" in args:
        tamam = [int(v) for v in args[args.index("--tamam") + 1].split(",")] if "--tamam" in args else None
        print("ok", os.path.normpath(img_faz(int(args[args.index("--faz") + 1]), "--force" in args, tamam)))
    else:
        img_hedef()
        print("ok", os.path.normpath(os.path.join(OUT, "00-hedef-mimari.svg")))
