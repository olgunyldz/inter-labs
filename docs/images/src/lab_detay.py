"""inter-labs ayrıntılı topoloji seti: genel bakıştan pod içine (service-mesh-labs demo-detay ile aynı yapı).
Çıktı: docs/images/lab-detay/NN-*.svg (PNG için lab-detay/README.md'deki komut).
Çalıştırma: python docs/images/src/lab_detay.py [resim numaraları...]   (boş: hepsi)
Kaynak: clusters/, platform/, workloads/, edge/, scripts/ ve config.env. Bir bileşen, port ya da kural değişirse resim de güncellenir.
Kırmızı kesikli kutu = bankacılık hedef mimarisinde olması gereken ama lab'da olmayan bileşen."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detay_style import D, DENY_C
from topo_style import PALETTE

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab-detay")
os.makedirs(OUT, exist_ok=True)

# Gerçek IP'ler (docker inspect, kurulumdaki değerler; Docker yeniden başlarsa değişebilir)
IP = {"edge-lb": {"lab-edge": "172.28.5.2", "lab-dmz": "172.28.10.5"},
      "dmz-a": {"lab-dmz": "172.28.10.2", "lab-app": "172.28.20.4"},
      "dmz-b": {"lab-dmz": "172.28.10.4", "lab-app": "172.28.20.6"},
      "cluster-a": {"lab-app": "172.28.20.2", "lab-data": "172.28.30.3"},
      "cluster-b": {"lab-app": "172.28.20.3", "lab-data": "172.28.30.4"},
      "data": {"lab-data": "172.28.30.2"},
      "mgmt": {"lab-mgmt": "172.28.40.2", "lab-dmz": "172.28.10.3", "lab-app": "172.28.20.5", "lab-data": "172.28.30.5"}}
INGRESS_IMG = "registry.k8s.io/ingress-nginx/controller:v1.15.1"


def out(name):
    return os.path.join(OUT, name)


def ns_pods(d, x, y, w, ns, pods, color="internal", sub=None):
    """Namespace + pod listesi (her pod tek satır: ad · tür · görev); döndürür: alt kenar"""
    h = 40 + len(pods) * 40
    d.nsbox(x, y, w, h, ns, color, sub)
    for i, (name, kind, desc) in enumerate(pods):
        agent = kind.startswith("DaemonSet")
        d.pod(x + 12, y + 36 + i * 40, w - 24, 34, name, kind, "mgmt" if agent else color, (), agent=agent)
        if desc:
            d.text(x + 12 + (w - 24) * 0.36, y + 36 + i * 40 + 19, desc, 11.5, 400, "#3a3a3a")
    return y + h


def ns_objs(d, x, y, w, ns, objs, color="internal", sub=None):
    """Namespace + pod olmayan Kubernetes nesneleri (Service, Ingress, Secret …): tür · ad · açıklama"""
    h = 40 + len(objs) * 26 + 6
    d.nsbox(x, y, w, h, ns, color, sub)
    for i, (kind, name, desc) in enumerate(objs):
        yy = y + 54 + i * 26
        d.text(x + 14, yy, kind, 11.5, 700, PALETTE[color][2])
        d.text(x + 14 + 112, yy, name, 12, 600)
        d.text(x + 14 + 112 + 190, yy, desc, 11.5, 400, "#3a3a3a")
    return y + h


def target(d, x, y, w, title, rows, size=12.5):
    """Hedef (lab'da yok): kırmızı kesikli kutu; rows: satırlar. Döndürür: alt kenar"""
    h = 36 + len(rows) * (size + 7) + 4
    d.n.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff7f6" stroke="{DENY_C}" stroke-width="1.6" stroke-dasharray="6 4"/>')
    d.t(x + 12, y + 22, title, size + 1, 700, DENY_C)
    for i, r in enumerate(rows):
        d.t(x + 12, y + 44 + i * (size + 7), "· " + r, size, 400, "#2b2b2b")
    return y + h


def target_ns(d, x, y, w, ns, pods, size=12):
    """Hedef namespace (lab'da yok): kırmızı kesikli çerçeve, satırlar: (pod, görev)"""
    h = 36 + len(pods) * 22 + 8
    d.n.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#fff7f6" stroke="{DENY_C}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    d.t(x + 12, y + 21, "ns " + ns, 13.5, 700, DENY_C)
    d.t(x + w - 10, y + 21, "hedef · lab'da yok", 11.5, 400, DENY_C, "end")
    for i, (name, desc) in enumerate(pods):
        yy = y + 44 + i * 22
        d.t(x + 14, yy, "◻ " + name, size, 600, "#2b2b2b")
        d.t(x + 14 + w * 0.36, yy, desc, size - 0.5, 400, "#3a3a3a")
    return y + h


def bh(n):
    """D.box yüksekliği: başlık + n satır"""
    return 36 + 18 * n


LEG_ZONES = [("public", "internet"), ("wan", "kurum WAN / VPN"), ("edge", "edge"), ("dmz", "DMZ"), ("internal", "uygulama"),
             ("data", "veri"), ("mgmt", "yönetim / platform"), ("identity", "kimlik (hedef)"), ("pci", "kart / PCI (hedef)")]


def target_legend(d, x, y):
    d.n.append(f'<rect x="{x}" y="{y - 12}" width="30" height="17" rx="4" fill="#fff7f6" stroke="{DENY_C}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    d.t(x + 40, y + 1, "hedef mimaride olması gereken · lab'da yok", 13)


def channels(d, y):
    """Kanallar satırı (00 ve 01 ortak)"""
    d.boundary([(20, y), (860, y), (860, y + 116), (20, y + 116)], "İNTERNET · GÜVENİLMEYEN AĞ", "public", fill_opacity=0.55)
    d.boundary([(880, y), (1400, y), (1400, y + 116), (880, y + 116)], "KURUM WAN · ÖZEL HAT", "wan", fill_opacity=0.7)
    d.boundary([(1420, y), (2180, y), (2180, y + 116), (1420, y + 116)], "KURUM AĞI · VPN", "wan", fill_opacity=0.7)
    for x, t, s in [(40, "Mobil Bankacılık", "iOS · Android"), (320, "İnternet Şubesi", "web · tarayıcı"), (600, "Partner API", "açık bankacılık · 3. taraf"),
                    (900, "ATM", "ATM ağı · ISO 8583"), (1160, "POS", "üye işyeri · acquirer")]:
        d.channel(x, y + 22, 240 if x < 880 else 220, t, s)
    d.channel(1440, y + 22, 720, "Operasyon ekibi", "VPN · kubectl · 127.0.0.1:9080 / 9443")


# =====================================================================================================================
def img00():
    W, H, OY = 2200, 1700, 40
    d = D(W, H)
    channels(d, 100)

    LX, LW = 40, 1340          # sol sütun (müşteri yolu)
    BX, BW = 64, 586           # lab kutusu
    TX, TW = 670, 686          # hedef kutusu
    RX, RW = 1420, 740         # sağ sütun

    def row(y, title, net, color, lab_title, lab, tgt, link):
        h = 56 + max(bh(len(lab)), 36 + len(tgt) * 19.5 + 4) + 20
        d.zone(LX, y, LW, h, title, right=net, color=color)
        d.box(BX, y + 56, BW, bh(len(lab)), lab_title, lab, color=color, size=13)
        target(d, TX, y + 56, TW, "Olması gereken (bankacılık hedefi · lab'da yok)", tgt)
        d.link(BX + BW - len(link) * 7.2 - 30, y + 76, link)
        return y + h

    y1 = 290
    e_bot = row(y1, "Edge zone", "lab-edge · 172.28.5.0/24", "edge", "edge-lb · HAProxy 3.0 (Docker container)",
                ["L4 round-robin → dmz-a / dmz-b", "sağlık: /healthz her 3 sn · 2 hata → DOWN", "PROXY protocol ile istemci IP'si",
                 "host 127.0.0.1:80 / :443 · istatistik :9404"],
                ["DDoS koruması · scrubbing (sağlayıcı)", "GSLB · DC1 / DC2 aktif-aktif", "F5 LB çifti (HA) · kanal başına VIP ve sertifika",
                 "WAF · OWASP CRS · bot yönetimi", "TLS 1.2+/1.3 · HSTS · sertifika yaşam döngüsü"], "Ayrıntı: 01")
    d.firewall(LX, e_bot + 10, LW, 22, "DMZ FW · yalnızca edge-lb → :80 / :443 (PROXY)", tx=480)
    y2 = e_bot + 44
    dmz_bot = row(y2, "DMZ zone · active-active", "lab-dmz · 172.28.10.0/24", "dmz", "dmz-a · dmz-b · kind · ingress-nginx",
                  ["TLS sonlandırma (edge-tls) · X-Dmz başlığı", "host kuralları: app · app-a · app-b", "app-pool → cluster-a + cluster-b",
                   "hata / 502-504'te diğer cluster'a geçer"],
                  ["kanal API gateway'leri: mobil · web · partner (ayrı VIP / ns)", "web token handler: cookie ↔ token · CSRF",
                   "auth-proxy: token introspection + exchange (iç JWT)", "rate limit · partner kotası · izin listesi",
                   "partner mTLS (istemci sertifikası) · egress gateway (tek çıkış)", "iş mantığı ve veri yok"], "Ayrıntı: 02 · 03")
    d.firewall(LX, dmz_bot + 10, LW, 22, "APP FW · yalnızca DMZ → :80", tx=480)
    y3 = dmz_bot + 44
    app_bot = row(y3, "Uygulama zone · active-active", "lab-app · 172.28.20.0/24", "internal", "cluster-a · cluster-b · kind · ingress-nginx",
                  ["ns demo: demo-app ×2 (nginx · JSON cevap)", "postgres.demo.svc · redis.demo.svc → data", "XFF'ye yalnızca DMZ subnet'inden güvenir"],
                  ["channel BFF'ler: mobil-bff · web-bff · partner-bff", "hesap · müşteri · kart servisleri", "para transferi: havale · EFT · FAST",
                   "ödeme / fatura · kredi başvurusu", "bildirim: SMS · push · e-posta", "fraud skorlama · işlem imzalama (tx-signing)",
                   "core-adapter: core banking entegrasyonu", "servisler arası mTLS · iç JWT doğrulama"], "Ayrıntı: 04 · 05")
    d.firewall(LX, app_bot + 10, LW, 22, "DATA FW · yalnızca uygulama → :5432 / :6379", tx=480)
    y4 = app_bot + 44
    data_bot = row(y4, "Data zone", "lab-data · 172.28.30.0/24", "data", "data · kind · ingress-nginx L4 (tcp-services)",
                   ["PostgreSQL 16 · StatefulSet + PVC 1Gi", "Redis 7 · Deployment (parola yok)", ":5432 / :6379 yalnızca uygulama zone'undan"],
                   ["core banking DB: Oracle / MSSQL", "PostgreSQL HA (Patroni) · DC1 ⇄ DC2 replikasyon", "Kafka (olay akışı) · RabbitMQ",
                    "Valkey / Redis cluster (oturum, OTP) · TLS + ACL", "yedekleme · şifreleme (TDE) · servis başına DB rolü",
                    "kimlik bilgileri Vault'tan (dinamik)"], "Ayrıntı: 06")

    # Sağ sütun: kart (PCI) hedef, kimlik hedef, yönetim
    d.zone(RX, y1, RW, e_bot - y1, "Kart zone · PCI DSS", right="lab'da yok", color="pci")
    target(d, RX + 24, y1 + 56, RW - 48, "Olması gereken (ayrı cluster ve segment)",
           ["ATM / POS switch · ISO 8583 · NDC / DDC", "HSM (PIN doğrulama, anahtar yönetimi)", "tokenization (PAN → token)",
            "kart şemaları: Visa · MC · TROY · BKM (özel hat)", "internet tarafından erişim yok"])
    d.zone(RX, y2, RW, dmz_bot - y2, "Kimlik zone", right="lab'da yok", color="identity")
    target(d, RX + 24, y2 + 56, RW - 48, "Olması gereken",
           ["Keycloak / RHBK (A/B) · müşteri ve personel realm'leri", "MFA · OTP · cihaz kaydı (mobil)", "consent (açık bankacılık)",
            "AD / LDAP · personel SSO", "iç JWT üretimi (RFC 8693, ≤ 2 dk)", "token introspection ucu (DMZ auth-proxy için)"])
    mb = y3 + 56 + bh(4) + 14 + 36 + 5 * 19.5 + 4 + 20
    m_bot = max(data_bot, mb)
    d.zone(RX, y3, RW, m_bot - y3, "Yönetim zone", right="lab-mgmt · 172.28.40.0/24", color="mgmt")
    d.box(RX + 24, y3 + 56, RW - 48, bh(4), "mgmt · kind · ingress-nginx", ["host 127.0.0.1:9080 / :9443 (VPN'i temsil eder)",
                                                                              "her zone'a bir ağ bacağı → API :6443", "lab-dmz .10.3 · lab-app .20.5 · lab-data .30.5",
                                                                              "kubectl: kind-* context'leri"], color="mgmt", size=13)
    d.link(RX + RW - 130, y3 + 76, "Ayrıntı: 07")
    target(d, RX + 24, y3 + 56 + bh(4) + 14, RW - 48, "Olması gereken",
           ["gözlem: Prometheus / Thanos · Grafana · Loki / ELK · Tempo", "SIEM / SOAR · tüm zone'lardan tek yönlü log", "CI/CD · imzalı image registry · admission (Kyverno)",
            "Vault (secret, PKI) · PAM / bastion", "yedekleme (Velero) · kapasite ve alarm"])
    p_bot = max(m_bot, data_bot) + 24
    d.boundary([(14, 250), (2186, 250), (2186, p_bot), (14, p_bot)], "LAB PERİMETRESİ · Docker Desktop (Windows 11) · tek host", "external")

    # Akışlar: kanallar → edge-lb
    d.e.append('<path d="M 160,216 L 160,236 L 720,236 M 440,216 L 440,236 M 720,216 L 720,236" fill="none" stroke="#2f7bd8" stroke-width="3"/>')
    d.flow([(360, 236), (360, y1 + 56)], "main", "internet · TCP 443", 372, 272)
    d.e.append('<path d="M 1010,216 L 1010,240 L 1270,240 L 1270,216" fill="none" stroke="#2f7bd8" stroke-width="3"/>')
    d.flow([(1140, 240), (1140, 270), (620, 270), (620, y1 + 56)], "main", "lab: ATM / POS da aynı edge-lb'ye", 900, 264, "middle")
    d.flow([(1270, 240), (1600, 240), (1600, y1)], "aux", "hedef: özel hat → PCI", 1612, 272)
    # zone'dan zone'a (lab kutusunun altından bir sonrakinin üstüne)
    for (ztop, nlab), nxt in (((y1, 4), y2), ((y2, 4), y3), ((y3, 3), y4)):
        d.flow([(450, ztop + 56 + bh(nlab)), (450, nxt + 56)], "main")
    # mgmt → API'ler :6443 (yönetim)
    d.flow([(RX, y3 + 30), (1400, y3 + 30), (1400, y2 + 130), (LX + LW + 2, y2 + 130)], "aux")
    d.flow([(RX, y3 + 150), (LX + LW + 2, y3 + 150)], "aux")
    d.flow([(RX, y4 + 110), (LX + LW + 2, y4 + 110)], "aux")
    for yy in (y2 + 122, y3 + 142, y4 + 102):
        d.t(1400, yy, ":6443", 12, 600, PALETTE["mgmt"][2], "middle", d.l)
    # operasyon (VPN) → mgmt: sağ kenardan, zone'ların dışından
    d.flow([(2100, 216), (2100, 236), (2172, 236), (2172, y3 + 40), (RX + RW, y3 + 40)], "req", "VPN · :9443", 2160, 272, "end")

    NY = p_bot + 30
    d.note(40, NY, 1060, "Okuma sırası · siyah etiket = ayrıntı resmi", [
        "00 · genel bakış (bu resim): her zone'da lab'da çalışan ve olması gereken servisler",
        "01 · edge zone: edge-lb (HAProxy) içi, kanallar, Docker ağları",
        "02 · DMZ cluster'ları: namespace'ler, pod'lar, ingress kuralları · 03 · DMZ ingress pod'u içi",
        "04 · uygulama cluster'ları · 05 · demo-app pod'u içi",
        "06 · data cluster'ı: PostgreSQL, Redis, TCP girişi · 07 · mgmt cluster'ı ve ağ bacakları",
        "08 · bir kind node'unun anatomisi · 09 · uçtan uca istek, adım adım"], 12.5)
    lh = d.legend(1120, NY, 1060, LEG_ZONES, extra=False, cols=3)
    target_legend(d, 1134, NY + lh + 24)
    d.save(out("00-genel-bakis.svg"), "00 · Genel bakış: zone'lar, lab'da çalışan servisler ve bankacılık hedefinde olması gerekenler",
           "her zone'da sol kutu = lab'da gerçekten çalışan · kırmızı kesikli = hedef mimaride olması gereken · siyah etiket = ayrıntı resmi · mavi = müşteri trafiği", oy=OY)


# =====================================================================================================================
def img01():
    W, H, OY = 2200, 1230, 40
    d = D(W, H)
    channels(d, 100)
    d.boundary([(20, 290), (1080, 290), (1080, 820), (20, 820)], "DOCKER AĞI lab-edge · 172.28.5.0/24 · internet tarafı", "edge", fill_opacity=0.25)
    d.badge(1060, 316, "in ← host 127.0.0.1:80 · :443 (müşteri) · :9404 (istatistik)", "in", anchor="end")
    eb = d.pod(40, 330, 1020, None, "edge-lb", "Docker container · haproxy:3.0-alpine · restart unless-stopped", "edge", [
        ("frontend http :80 · frontend https :443", "proxy", ["mode tcp · TLS'e dokunmaz (sonlandırma DMZ'de)", "timeout connect 3 sn · client / server 60 sn",
                                                           "log stdout (tcplog) → docker logs edge-lb"]),
        ("backend dmz_http · backend dmz_https", "proxy", ["balance roundrobin", "server dmz-a 172.28.10.2:80 / :443 · server dmz-b 172.28.10.4:80 / :443",
                                                         "send-proxy (PROXY v1: istemci IP'si ve portu DMZ'ye taşınır)",
                                                         "sağlık: option httpchk GET /healthz · expect 200 · check port 80",
                                                         "inter 3 sn · fall 2 · rise 2 → ~6-10 sn'de DOWN · check-send-proxy"]),
        ("frontend stats :8404", "agent", ["mode http · stats uri / · 5 sn'de yenilenir", "host 127.0.0.1:9404 · CSV: /;csv (verify.sh okur)"]),
        ("yapılandırma", "init", ["edge/haproxy.cfg.tpl → up.sh IP'leri doldurur → .edge/haproxy.cfg (salt okunur mount)",
                                  "--sysctl net.ipv4.ip_unprivileged_port_start=0 (non-root :80 / :443)"])])
    d.badge(1060, eb + 22, "out → dmz-a / dmz-b :80 · :443 (TCP + PROXY v1)", "out", anchor="end")
    d.text(40, eb + 60, "Ağ bacakları", 14, 700)
    d.text(40, eb + 84, "eth: lab-edge 172.28.5.2 (birincil · host port'ları buradan)  ·  lab-dmz 172.28.10.5 (DMZ'ye tek bacak)", 12.5)

    d.boundary([(1110, 290), (2180, 290), (2180, 820), (1110, 820)], "DOCKER AĞI lab-dmz · 172.28.10.0/24", "dmz", fill_opacity=0.2)
    for i, (n, ip, sub) in enumerate([("dmz-a-control-plane", IP["dmz-a"]["lab-dmz"], "ingress hostPort :80 / :443 · ayrıntı 02 · 03"),
                                      ("dmz-b-control-plane", IP["dmz-b"]["lab-dmz"], "dmz-a ile aynı · X-Dmz: dmz-b")]):
        y = 330 + i * 150
        d.node(1130, y, 1030, 128, n, "kindest/node v1.37.0")
        d.text(1146, y + 54, f"lab-dmz {ip} · lab-app {IP[n[:5]]['lab-app']}", 12.5, 600)
        d.text(1146, y + 76, sub, 12.5)
        d.text(1146, y + 98, "edge-lb sağlık kontrolü: :80/healthz (ingress-nginx default server)", 12, 400, "#5f5f5a")
    d.node(1130, 630, 1030, 80, "mgmt-control-plane (bacak)", "lab-dmz " + IP["mgmt"]["lab-dmz"])
    d.text(1146, 684, "yalnızca dmz-a / dmz-b API'lerine (:6443) · operasyon VPN ile mgmt'ye bağlanır · ayrıntı 07", 12.5)

    target(d, 1130, 832 - 0, 1030, "Edge zone'da olması gereken (lab'da yok)",
           ["DDoS koruması / scrubbing · CDN (sağlayıcı katmanı)", "GSLB: DC1 / DC2 aktif-aktif, sağlık bazlı yönlendirme",
            "F5 LB çifti (HA) · kanal başına VIP: mobil, web, partner", "WAF: OWASP CRS, bot yönetimi, API şema doğrulama",
            "TLS 1.2+/1.3, HSTS, sertifika yaşam döngüsü · partner mTLS"])
    d.note(40, 840, 1040, "Bu resimde", ["Kubernetes dışındaki tek bileşen edge-lb: bir Docker container'ı.",
                                         "Beş kanal da lab'da aynı girişi kullanır (127.0.0.1:443); hedefte ATM / POS özel hattan PCI zone'una gider.",
                                         "TLS DMZ'de açılır; edge-lb yalnızca TCP dağıtır ve istemci IP'sini PROXY protocol ile taşır.",
                                         "Failover: dmz-a durdurulunca ~10 sn'de DOWN, trafik dmz-b'ye geçti (verify ile denendi)."], 12.5)
    # akışlar
    d.e.append('<path d="M 160,216 L 160,240 L 720,240 M 440,216 L 440,240 M 720,216 L 720,240 M 1010,216 L 1010,240 L 1270,240 L 1270,216" fill="none" stroke="#2f7bd8" stroke-width="3"/>')
    d.flow([(1140, 240), (1140, 262), (560, 262), (560, 330)], "main")
    d.flow([(440, 240), (440, 330)], "main", "TCP :443", 452, 256)
    d.flow([(1060, 400), (1130, 400)], "main")
    d.flow([(1060, 560), (1130, 560)], "main")
    d.flow([(300, eb + 120), (300, 800), (1000, 800)], "deny", "edge-lb → lab-app / lab-data: bağlı değil, yol yok (verify: cluster-a :80 engelli)", 312, 792)
    d.legend(40, 1000, 1040, [("public", "internet"), ("wan", "kurum WAN / VPN"), ("edge", "edge"), ("dmz", "DMZ"), ("mgmt", "yönetim")],
             extra=False, cols=3)
    target_legend(d, 1130, 1010)
    d.save(out("01-edge-zone.svg"), "01 · Edge zone: kanallar, edge-lb (HAProxy) içi, Docker ağları",
           "frontend / backend · sağlık kontrolü · PROXY protocol · hangi ağa bağlı, hangisine değil · kırmızı kesikli = hedefte olması gereken", oy=OY)


# =====================================================================================================================
SYSTEM = [("coredns ×2", "Deployment", "küme DNS'i :53 (svc.cluster.local)"),
          ("kube-proxy", "DaemonSet", "Service → pod (iptables)"),
          ("kindnet", "DaemonSet", "CNI · pod rotaları · ip-masq"),
          ("kontrol düzlemi", "static pod", "apiserver · etcd · ctrl-mgr · scheduler")]
STORAGE = [("local-path-provisioner", "Deployment", "PVC → node diski (standard)")]


def ingress_ns(d, x, y, w, color, desc, sub="hostPort :80 / :443"):
    return ns_pods(d, x, y, w, "ingress-nginx", [("ingress-nginx-controller", "Deployment ×1", desc)], color, sub)


def img02():
    W, H, OY = 2200, 1110, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 790), (14, 790)], "kind dmz-a · dmz-b · tek node · iki cluster aynı manifest (workloads/dmz) · iş mantığı ve veri yok", "dmz")
    d.badge(40, 146, "in ← edge-lb 172.28.10.5 → :443 / :80 (TCP + PROXY v1) · mgmt → :6443", "in")
    d.badge(2160, 146, "out → cluster-a 172.28.20.2:80 · cluster-b 172.28.20.3:80 (HTTP · lab-app)", "out", anchor="end")
    c = [40, 760, 1480]
    cw = 680
    y = ingress_ns(d, c[0], 180, cw, "dmz", "PROXY protocol · TLS · X-Dmz · :10254 metrik") + 14
    y = ns_objs(d, c[0], y, cw, "edge", [
        ("Ingress", "app", "app.localtest.me → app-pool · next-upstream 2"),
        ("Ingress", "app-a / app-b", "→ cluster-a / cluster-b · upstream-vhost app"),
        ("Service", "app-pool", "selector'sız :80 · iki cluster"),
        ("EndpointSlice", "app-pool-static", "172.28.20.2:80 · 172.28.20.3:80"),
        ("Service + ES", "cluster-a", "172.28.20.2:80 (yalnızca A)"),
        ("Service + ES", "cluster-b", "172.28.20.3:80 (yalnızca B)"),
        ("Secret", "edge-tls", "*.localtest.me (self-signed, .certs/)")], "dmz", "up.sh IP'leri docker inspect ile yazar") + 14
    b1 = ns_pods(d, c[1], 180, cw, "kube-system", SYSTEM, "mgmt") + 14
    b1 = ns_pods(d, c[1], b1, cw, "local-path-storage", STORAGE, "mgmt") + 14
    d.text(c[1] + 12, b1 + 16, "Ingress kuralları (her iki DMZ cluster'ında)", 13, 700)
    rows = [("app.localtest.me", "app-pool (A + B)", "connect 2 sn · error/timeout/502/503/504 → diğeri"),
            ("app-a.localtest.me", "cluster-a", "upstream Host: app.localtest.me"),
            ("app-b.localtest.me", "cluster-b", "upstream Host: app.localtest.me"),
            ("diğer her host", "default server", "404 · /healthz 200 (edge-lb kontrolü)")]
    for i, (h, b, n) in enumerate(rows):
        yy = b1 + 30 + i * 26
        d.n.append(f'<rect x="{c[1] + 12}" y="{yy}" width="{cw - 24}" height="24" rx="4" fill="{"#fdf4ec" if i % 2 else "#ffffff"}" stroke="#c4c4bf" stroke-width="0.8"/>')
        d.text(c[1] + 20, yy + 17, h, 12, 700)
        d.text(c[1] + 190, yy + 17, b, 12)
        d.text(c[1] + 330, yy + 17, n, 11.5, 400, "#3a3a3a")
    y2 = target_ns(d, c[2], 180, cw, "istio-mobile · istio-web · istio-partner", [("mobile-gateway", "kanal başına ayrı VIP + sertifika"),
                                                                                ("web-gateway", "www · sso · CORS"),
                                                                                ("partner-gateway", "mTLS + izin listesi")]) + 12
    y2 = target_ns(d, c[2], y2, cw, "edge-web", [("web-token-handler", "cookie ↔ token · CSRF · oturum")]) + 12
    y2 = target_ns(d, c[2], y2, cw, "auth", [("auth-proxy", "ext_authz · introspection · exchange"), ("waypoint", "L7 kaynak kimliği kontrolü")]) + 12
    y2 = target_ns(d, c[2], y2, cw, "ratelimit", [("ratelimit", "kanal / partner kotası · sayaç Redis'te")]) + 12
    y2 = target_ns(d, c[2], y2, cw, "egress", [("dmz-egressgateway", "zone'dan TEK çıkış · kaynak AuthZ")]) + 12
    target_ns(d, c[2], y2, cw, "security · mesh", [("NetworkPolicy · mTLS (mesh)", "pod'lar arası varsayılan ret"),
                                                    ("Kyverno", "imzalı image · ayrıcalıksız pod")])
    d.flow([(360, 156), (360, 216)], "main")
    d.link(c[0] + cw - 110, 196, "Pod içi: 03")
    d.note(40, 820, 1060, "Bu resimde", ["dmz-a ve dmz-b aynı: tek fark controller.addHeaders.X-Dmz değeri.",
                                         "Karşı cluster'lar Kubernetes'te selector'sız Service + elle yazılmış EndpointSlice ile temsil edilir.",
                                         "Lab'da DMZ'de tek bileşen ingress-nginx; hedefteki gateway / auth / ratelimit / egress katmanı kırmızı kesikli.",
                                         "DMZ'den data zone'una yol yok (verify: dmz-a → 172.28.30.2:5432 engelli)."], 12.5)
    d.legend(1120, 820, 1060, [("dmz", "DMZ"), ("mgmt", "platform / node agent")], extra=True, cols=3)
    target_legend(d, 52, 960)
    d.save(out("02-dmz-cluster.svg"), "02 · DMZ cluster'ları (dmz-a, dmz-b): namespace'ler, pod'lar, ingress kuralları",
           "her kutu bir namespace · satırlar pod'lar (ad · iş yükü · görev) ya da nesneler · kırmızı kesikli = hedefte olması gereken", oy=OY)


# =====================================================================================================================
def img03():
    W, H, OY = 2200, 1110, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 800), (14, 800)], "kind dmz-a · dmz-a-control-plane node'unun içi (dmz-b aynı)", "dmz")
    d.node(36, 140, 2128, 640, "dmz-a-control-plane (kindest/node v1.37.0 · containerd · kubelet)", "lab-dmz 172.28.10.2 · lab-app 172.28.20.4 · pod CIDR 10.10.0.0/16")
    pb = d.pod(76, 222, 1160, None, "ingress-nginx-controller-…", "Deployment ×1 · SA ingress-nginx · chart 4.15.1", "dmz", [
        ("controller (nginx + ingress controller) · " + INGRESS_IMG, "proxy", [
            "hostPort :80 · :443 → node IP'si (kind extraPort yok; edge-lb doğrudan node'a gelir)",
            "use-proxy-protocol: true → her bağlantı PROXY başlığıyla başlamalı · real IP = başlıktaki istemci",
            "proxy-real-ip-cidr: 172.28.10.0/24 (yalnızca edge-lb) · use-forwarded-headers: false (dış XFF'ye güvenmez)",
            "TLS: edge-tls (*.localtest.me) · ssl-redirect (http → https 308) · hsts kapalı (demo)",
            "add-headers: X-Dmz=dmz-a · hide-headers: X-Powered-By, Server · server-tokens: false",
            "upstream: EndpointSlice'tan doğrudan pod/IP listesi · proxy-next-upstream error timeout 502-504",
            "erişim logu JSON: remote_addr · xff · host · upstream · upstream_status · request_time",
            ":10254 /healthz · /metrics (Prometheus) · :8443 admission webhook (Ingress doğrulama)"]),
        ("kimlik", "init", ["ServiceAccount ingress-nginx · RBAC: Ingress, Service, EndpointSlice, Secret okur",
                            "ValidatingWebhookConfiguration ingress-nginx-admission (geçersiz Ingress reddedilir)"])])
    d.nsbox(56, 184, 1200, pb - 184 + 54, "ingress-nginx", "dmz", "nodeSelector ingress-ready=true")
    d.badge(76, pb + 26, "in ← edge-lb :443 / :80 (PROXY v1) · :80/healthz", "in")
    d.badge(1236, pb + 26, "out → 172.28.20.2 / .3 :80 (HTTP · XFF)", "out", anchor="end")
    yo = ns_objs(d, 1290, 184, 854, "edge", [
        ("Ingress", "app", "app.localtest.me → app-pool"),
        ("Service", "app-pool", "ClusterIP · port http 80 · selector yok"),
        ("EndpointSlice", "app-pool-static", "managed-by: inter-labs · ready"),
        ("", "", "172.28.20.2:80 (A) · 172.28.20.3:80 (B)"),
        ("Secret", "edge-tls", "tls.crt / tls.key · 825 gün")], "dmz")
    d.text(1290, yo + 30, "Node agent'ları (DaemonSet) ve sistem", 14, 700)
    for i, (n, ls) in enumerate([("kube-proxy", ["Service → pod iptables", "(ingress EndpointSlice'ı", "kendisi okur, kube-proxy'yi atlar)"]),
                                 ("kindnet", ["pod ağı · rotalar", "ip-masq: pod → dış =", "node IP'si (eth1 lab-app)"]),
                                 ("coredns ×2", ["*.svc.cluster.local", ":53 · upstream: Docker DNS"])]):
        d.pod(1290 + i * 288, yo + 44, 276, None, n, "DaemonSet" if i < 2 else "Deploy", "mgmt", [(n, "agent", ls)], agent=i < 2)
    d.note(56, pb + 70, 1060, "İstek yolu (numaralar)", [
        "1 edge-lb → node :443, önce PROXY v1 satırı (istemci 172.28.5.1) sonra TLS",
        "2 nginx: real IP = PROXY başlığı · TLS edge-tls ile açılır",
        "3 Host app.localtest.me → upstream app-pool (EndpointSlice: A ve B) · round-robin",
        "4 HTTP :80 → cluster-a/b ingress (lab-app, kindnet masq) · hata / 502-504 → diğer cluster",
        "cevaba X-Dmz: dmz-a eklenir → edge-lb → istemci"], 12.5)
    d.marker(640, 196, 1, "#2f7bd8")
    d.marker(1210, 300, 2, "#2f7bd8")
    d.marker(1270, 250, 3, "#2f7bd8")
    d.marker(1270, pb + 10, 4, "#2f7bd8")
    d.flow([(620, 124), (620, 222)], "main")
    d.flow([(1236, 260), (1290, 260)], "req")
    d.flow([(1150, pb + 14), (1150, 830)], "main", "→ cluster-a / cluster-b :80 (04 · 05)", 1162, 826)
    target(d, 1290, 520, 854, "Hedef DMZ pod'unda olması gereken (lab'da yok)", [
        "kanal başına ayrı gateway (VIP, sertifika, rate limit) · ext_authz → auth-proxy",
        "header temizliği: x-user-jwt, x-channel dışarıdan gelirse silinir",
        "mTLS ile sonraki zone'a (mesh) · NetworkPolicy · read-only root · non-root",
        "erişim logu → SIEM · iz (OTel) → Tempo"], 12)
    d.legend(40, 850, 2140, [("dmz", "DMZ"), ("mgmt", "node agent / platform")], extra=True, cols=6)
    target_legend(d, 1700, 875)
    d.save(out("03-dmz-pod-detay.svg"), "03 · DMZ pod içi: ingress-nginx controller (PROXY, TLS, upstream seçimi), edge nesneleri, node agent'ları",
           "pod → container → port ve ayar · numaralar: isteğin DMZ içindeki yolu · ayarlar: platform/ingress-nginx/values-common.yaml + values-dmz.yaml", oy=OY)


# =====================================================================================================================
def img04():
    W, H, OY = 2200, 1230, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 860), (14, 860)], "kind cluster-a · cluster-b · tek node · aynı manifest (workloads/app), tek fark CLUSTER_NAME", "internal")
    d.badge(40, 146, "in ← dmz-a / dmz-b (172.28.20.4 / .6) → :80 · mgmt → :6443", "in")
    d.badge(2160, 146, "out → data 172.28.30.2 :5432 / :6379 (TCP · lab-data)", "out", anchor="end")
    c = [40, 760, 1480]
    cw = 680
    y = ingress_ns(d, c[0], 180, cw, "internal", "XFF'ye yalnızca 172.28.20.0/24'ten güvenir", "hostPort :80") + 14
    y = ns_pods(d, c[0], y, cw, "demo", [("demo-app", "Deployment ×2", "nginx:1.27-alpine :8080 · JSON cevap")], "internal") + 0
    y = ns_objs(d, c[0], y + 10, cw, "demo (nesneler)", [
        ("Service", "demo-app", "ClusterIP :80 → :8080"),
        ("Ingress", "demo-app", "app.localtest.me → demo-app:80"),
        ("ConfigMap", "demo-app-nginx", "default.conf.template (envsubst)"),
        ("Service + ES", "postgres", "selector yok → 172.28.30.2:5432"),
        ("Service + ES", "redis", "selector yok → 172.28.30.2:6379")], "internal", "up.sh data IP'sini yazar") + 14
    d.link(c[0] + cw - 110, 196, "Pod içi: 05")
    b1 = ns_pods(d, c[1], 180, cw, "kube-system", SYSTEM, "mgmt") + 14
    b1 = ns_pods(d, c[1], b1, cw, "local-path-storage", STORAGE, "mgmt") + 14
    d.text(c[1] + 12, b1 + 16, "cluster-a / cluster-b farkı", 13, 700)
    for i, r in enumerate(["CLUSTER_NAME: cluster-a / cluster-b (kustomize overlay)", "pod CIDR 10.20.0.0/16 · 10.30.0.0/16",
                           "service CIDR 10.21.0.0/16 · 10.31.0.0/16", "lab-app 172.28.20.2 / .3 · lab-data 172.28.30.3 / .4"]):
        d.text(c[1] + 12, b1 + 40 + i * 20, "· " + r, 12)
    y2 = target_ns(d, c[2], 180, cw, "channel-bff", [("mobile-bff", "mobil kanala özel API birleştirme"), ("web-bff", "internet şubesi"),
                                                      ("partner-bff", "açık bankacılık API'leri")]) + 10
    y2 = target_ns(d, c[2], y2, cw, "account · customer · card", [("account-api", "hesap, bakiye, hareketler"), ("customer-api", "müşteri bilgisi, KYC"),
                                                                    ("card-api", "kart listesi, limit (PAN yok, token)")]) + 10
    y2 = target_ns(d, c[2], y2, cw, "transfer · payment", [("transfer-api", "havale · EFT · FAST"), ("payment-api", "fatura, vergi, ödeme"),
                                                             ("loan-api", "kredi başvurusu")]) + 10
    y2 = target_ns(d, c[2], y2, cw, "security", [("tx-signing", "işlem imzası / OTP doğrulama"), ("fraud-scoring", "gerçek zamanlı risk skoru")]) + 10
    y2 = target_ns(d, c[2], y2, cw, "integration · notification", [("core-adapter", "core banking (legacy) entegrasyonu"),
                                                                     ("notification", "SMS · push · e-posta")]) + 10
    target_ns(d, c[2], y2, cw, "egress · mesh", [("istio-egressgateway", "veri / dış servis çıkışı tek kapıdan"),
                                                 ("ztunnel / waypoint", "servisler arası mTLS · iç JWT")])
    d.flow([(360, 156), (360, 216)], "main")
    d.flow([(380, y - 14), (380, 840), (380, 880)], "main", "postgres.demo.svc / redis.demo.svc → data :5432 / :6379 (06)", 392, 876)
    d.note(40, 900, 1060, "Bu resimde", ["Lab'da uygulama zone'unda tek iş yükü demo-app: hangi cluster ve pod'un cevap verdiğini döner.",
                                         "Veri servislerine Kubernetes adıyla gidilir (postgres.demo.svc); adres data cluster'ının ingress'i.",
                                         "Hedefteki bankacılık servisleri (BFF, hesap, transfer, kart, fraud …) sağda kırmızı kesikli.",
                                         "data → cluster-a :80 yolu yok (verify)."], 12.5)
    d.legend(1120, 900, 1060, [("internal", "uygulama"), ("mgmt", "platform / node agent")], extra=True, cols=3)
    target_legend(d, 52, 1040)
    d.save(out("04-app-cluster.svg"), "04 · Uygulama cluster'ları (cluster-a, cluster-b): namespace'ler, pod'lar, veri servisleri",
           "her kutu bir namespace · demo-app ve veri servis nesneleri · kırmızı kesikli = bankacılık hedefinde olması gereken servisler", oy=OY)


# =====================================================================================================================
def img05():
    W, H, OY = 2200, 1090, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 740), (14, 740)], "kind cluster-a · cluster-a-control-plane node'unun içi (cluster-b aynı)", "internal")
    d.node(36, 140, 2128, 570, "cluster-a-control-plane (kindest/node v1.37.0)", "lab-app 172.28.20.2 · lab-data 172.28.30.3 · pod CIDR 10.20.0.0/16")
    d.nsbox(56, 184, 700, 260, "ingress-nginx", "internal")
    ib = d.pod(76, 222, 660, None, "ingress-nginx-controller-…", "Deployment ×1", "internal", [
        ("controller · " + INGRESS_IMG, "proxy", ["hostPort :80 (DMZ'den HTTP)", "use-forwarded-headers: true · compute-full-forwarded-for",
                                                   "proxy-real-ip-cidr: 172.28.20.0/24 (yalnızca DMZ node'ları)", "Ingress demo-app: app.localtest.me → Service demo-app:80",
                                                   "upstream: demo-app pod IP'leri :8080 (EndpointSlice)", ":10254 /healthz · /metrics"])])
    d.badge(76, ib + 24, "in ← dmz-a / dmz-b :80 (X-Forwarded-For)", "in")
    d.nsbox(780, 184, 1364, 260, "demo", "internal", "Deployment demo-app ×2 · Service demo-app :80 · iki pod arasında round-robin")
    for i in range(2):
        x = 800 + i * 670
        d.pod(x, 222, 654, None, f"demo-app-…-{'59kmc' if i == 0 else '8lpv5'}", "ReplicaSet · pod", "internal", [
            ("app · nginx:1.27-alpine", "app", [":8080 http · readiness GET /healthz", "env CLUSTER_NAME=cluster-a",
                                               "requests cpu 10m · mem 16Mi · limits mem 64Mi",
                                               "GET / → {cluster, pod, host, client, xff} (JSON)"]),
            ("volume templates ← ConfigMap demo-app-nginx", "init", ["/etc/nginx/templates/default.conf.template",
                                                                     "açılışta envsubst → conf.d (yalnızca tanımlı env'ler)"])])
    d.nsbox(56, 470, 700, 210, "demo · veri servisleri", "data", "selector'sız Service + EndpointSlice")
    d.text(76, 524, "postgres.demo.svc:5432 → EndpointSlice postgres-static → 172.28.30.2:5432", 12.5, 600)
    d.text(76, 548, "redis.demo.svc:6379 → EndpointSlice redis-static → 172.28.30.2:6379", 12.5, 600)
    d.text(76, 578, "kube-proxy ClusterIP'yi data node IP'sine DNAT eder; kindnet kaynağı", 12)
    d.text(76, 598, "node'un lab-data IP'sine (172.28.30.3) maskeler → data ingress tcp-services", 12)
    d.badge(76, 650, "out → data 172.28.30.2 :5432 / :6379 (TCP, TLS yok)", "out")
    target(d, 780, 470, 1364, "Hedef bankacılık pod'unda olması gereken (lab'da yok)", [
        "securityContext: non-root · read-only root FS · capabilities drop ALL · seccomp RuntimeDefault",
        "secret'lar Vault'tan (agent / CSI) · DB kimlik bilgisi dinamik ve kısa ömürlü · TLS ile DB bağlantısı",
        "mesh: mTLS + iç JWT doğrulama · NetworkPolicy varsayılan ret · yalnızca izinli namespace'lerden giriş",
        "HPA + PodDisruptionBudget · anti-affinity (DC / node) · liveness + startup probe",
        "OpenTelemetry iz · yapılandırılmış log → SIEM · imzalı image (Kyverno doğrular)"], 12.5)
    d.marker(60, 240, 1, "#2f7bd8")
    d.marker(760, 300, 2, "#2f7bd8")
    d.marker(1460, 196, 3, "#2f7bd8")
    d.marker(60, 520, 4, "#c2410c")
    d.flow([(420, 124), (420, 222)], "main")
    d.flow([(736, 300), (800, 300)], "main")
    d.flow([(400, 680), (400, 770)], "req", "→ data ingress (06)", 412, 764)
    d.note(40, 830, 1060, "İstek yolu (numaralar)", [
        "1 DMZ'den HTTP :80 gelir; real IP = XFF'deki istemci (DMZ subnet'i güvenilir) · 2 Host app.localtest.me → demo-app",
        "3 iki pod arasında round-robin; pod cevabı JSON: hangi cluster, hangi pod, istemci, XFF zinciri",
        "4 veri yolu (verify.sh ile test edilir; demo-app henüz DB çağırmıyor): postgres.demo.svc → data ingress"], 12.5)
    d.legend(1120, 830, 1060, [("internal", "uygulama"), ("data", "veri")], extra=True, cols=3)
    target_legend(d, 52, 950)
    d.save(out("05-app-pod-detay.svg"), "05 · Uygulama pod içi: demo-app (nginx, ConfigMap şablonu), ingress controller, veri servis yönlendirmesi",
           "pod → container → port, env, probe, kaynak · numaralar: isteğin cluster içindeki yolu · kırmızı kesikli = hedef pod standardı", oy=OY)


# =====================================================================================================================
def img06():
    W, H, OY = 2200, 1080, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 790), (14, 790)], "kind data · data-control-plane node'unun içi · yalnızca lab-data ağında", "data")
    d.badge(40, 146, "in ← cluster-a 172.28.30.3 · cluster-b 172.28.30.4 → :5432 / :6379 · mgmt 172.28.30.5 → :6443", "in")
    d.node(36, 170, 2128, 600, "data-control-plane (kindest/node v1.37.0)", "lab-data 172.28.30.2 · pod CIDR 10.40.0.0/16 · service CIDR 10.41.0.0/16")
    d.nsbox(56, 214, 700, 380, "ingress-nginx", "data", "L4 giriş")
    ib = d.pod(76, 252, 660, None, "ingress-nginx-controller-…", "Deployment ×1", "data", [
        ("controller · " + INGRESS_IMG, "proxy", ["hostPort :5432 · :6379 (+ :80 / :443 kullanılmıyor)", "ConfigMap tcp-services (values-data.yaml):",
                                                   "  5432 → data/postgres:5432", "  6379 → data/redis:6379",
                                                   "nginx stream modülü: düz TCP proxy · TLS yok", "kaynak IP filtresi yok: segmentasyon ağ seviyesinde"])])
    d.text(76, ib + 30, "kube-system · local-path-storage: 02'deki ile aynı", 12, 400, "#5f5f5a")
    d.nsbox(780, 214, 1364, 380, "data", "data")
    pg = d.pod(800, 252, 660, None, "postgres-0", "StatefulSet ×1 · serviceName postgres", "data", [
        ("postgres · postgres:16-alpine", "data", [":5432 · readiness pg_isready -U app (5 sn)", "envFrom Secret postgres: POSTGRES_USER=app · DB=app",
                                                  "PGDATA /var/lib/postgresql/data/pgdata", "requests cpu 50m · mem 128Mi · limits mem 512Mi"]),
        ("PVC data-postgres-0", "init", ["1Gi · RWO · StorageClass standard (local-path)", "node diski: /var/local-path-provisioner/…"])])
    d.pod(1474, 252, 654, None, "redis-…", "Deployment ×1", "data", [
        ("redis · redis:7-alpine", "data", [":6379 · readiness redis-cli ping", "requests cpu 25m · mem 32Mi · limits mem 256Mi",
                                           "kalıcılık yok (pod silinirse veri gider)", "parola / ACL / TLS yok"])])
    d.text(800, pg + 24, "Service postgres :5432 · Service redis :6379 (ClusterIP)", 12.5, 600)
    d.text(800, pg + 46, "Secret postgres: parola 'demo-pass' düz metin (yalnızca demo)", 12.5, 600, DENY_C)
    target(d, 56, 612, 2088, "Data zone'da olması gereken (lab'da yok)", [
        "core banking DB (Oracle / MSSQL) · PostgreSQL HA (Patroni, senkron replika) · DC1 ⇄ DC2 replikasyon · Kafka (olay akışı) · RabbitMQ",
        "TLS zorunlu bağlantı · servis başına DB rolü · kimlik bilgileri Vault'tan (dinamik) · disk / TDE şifreleme",
        "Valkey / Redis cluster: ACL + TLS + kalıcılık (AOF) · yedekleme ve geri dönüş testi (PITR) · erişim ve sorgu denetim logu → SIEM"], 12.5)
    d.flow([(300, 124), (300, 252)], "main")
    d.flow([(736, 330), (800, 330)], "main")
    d.flow([(736, 380), (770, 380), (770, 540), (1800, 540), (1800, 400)], "main")
    d.flow([(2000, 124), (2000, 170)], "deny", "dmz → data: yol yok (verify)", 1988, 140, "end")
    d.note(40, 820, 1060, "Bu resimde", ["Data cluster'ı yalnızca lab-data ağında: DMZ ve edge'den ağ yolu yok.",
                                         "Uygulamalar data ingress'inin TCP portlarına gelir; ingress düz TCP olarak servise iletir.",
                                         "Kırmızı yazılar lab'ın bilinçli açık noktaları: düz metin parola, Redis'te ACL yok.",
                                         "Hedefteki veri katmanı kırmızı kesikli kutuda."], 12.5)
    d.legend(1120, 820, 1060, [("data", "veri"), ("mgmt", "platform")], extra=True, cols=3)
    target_legend(d, 52, 960)
    d.save(out("06-data-cluster.svg"), "06 · Data cluster'ı: TCP girişi (tcp-services), PostgreSQL StatefulSet, Redis",
           "pod → container → port, probe, kaynak, depolama · kırmızı yazı = lab'ın açık noktası · kırmızı kesikli = hedefte olması gereken", oy=OY)


# =====================================================================================================================
def img07():
    W, H, OY = 2200, 1060, 40
    d = D(W, H)
    d.boundary([(14, 108), (2186, 108), (2186, 720), (14, 720)], "kind mgmt · mgmt-control-plane · dört ağa bağlı tek node", "mgmt")
    d.badge(40, 146, "in ← operasyon (VPN) host 127.0.0.1:9080 / :9443 · kubectl → 127.0.0.1:<rastgele> → :6443", "in")
    d.badge(2160, 146, "out → tüm cluster API'leri :6443 (yalnızca yönetim)", "out", anchor="end")
    d.node(36, 170, 1000, 470, "mgmt-control-plane (kindest/node v1.37.0)", "pod CIDR 10.50.0.0/16")
    y = ingress_ns(d, 56, 214, 960, "mgmt", "host :9080 / :9443 · henüz Ingress kuralı yok", "extraPortMappings") + 14
    y = ns_pods(d, 56, y, 960, "kube-system", SYSTEM, "mgmt") + 14
    d.text(56, y + 18, "Ağ arayüzleri (docker network connect)", 13.5, 700)
    for i, (net, ip, why) in enumerate([("lab-mgmt", IP["mgmt"]["lab-mgmt"], "birincil · kind oluştururken"),
                                        ("lab-dmz", IP["mgmt"]["lab-dmz"], "→ dmz-a / dmz-b API"), ("lab-app", IP["mgmt"]["lab-app"], "→ cluster-a / cluster-b API"),
                                        ("lab-data", IP["mgmt"]["lab-data"], "→ data API")]):
        d.text(70, y + 42 + i * 20, f"{net:<10} {ip:<14} {why}", 12)
    d.text(1070, 196, "mgmt'nin ulaştığı API server'lar (verify: hepsi açık)", 14, 700)
    rows = [("dmz-a", "172.28.10.2:6443", "lab-dmz"), ("dmz-b", "172.28.10.4:6443", "lab-dmz"), ("cluster-a", "172.28.20.2:6443", "lab-app"),
            ("cluster-b", "172.28.20.3:6443", "lab-app"), ("data", "172.28.30.2:6443", "lab-data"), ("edge-lb", "—", "lab-edge'e bacak yok")]
    for i, (n, a, v) in enumerate(rows):
        yy = 210 + i * 30
        d.n.append(f'<rect x="1070" y="{yy}" width="1094" height="26" rx="4" fill="{"#f1f8f1" if i % 2 else "#ffffff"}" stroke="#c4c4bf" stroke-width="0.8"/>')
        d.text(1082, yy + 18, n, 12.5, 700)
        d.text(1260, yy + 18, a, 12.5)
        d.text(1480, yy + 18, v, 12.5, 400, "#5f5f5a")
    target(d, 1070, 410, 1094, "Yönetim zone'unda olması gereken (lab'da yok)", [
        "gözlem: Prometheus / Thanos · Grafana · Loki / ELK · Tempo · Alertmanager",
        "SIEM / SOAR: tüm zone'lardan tek yönlü log (zone'lar mgmt'ye yazar, mgmt okumaz)",
        "CI/CD · imzalı image registry · Kyverno / admission politikaları",
        "Vault: secret, PKI, dinamik DB kimlik bilgisi · PAM / bastion (kayıtlı oturum)",
        "yedekleme (Velero) · kapasite / maliyet izleme · runbook otomasyonu"], 12.5)
    d.flow([(500, 124), (500, 214)], "req")
    d.flow([(1036, 300), (1070, 300)], "aux")
    d.note(40, 740, 1060, "Bu resimde", ["mgmt diğer zone'lara uygulama trafiği taşımaz; yalnızca API (:6443) erişimi var.",
                                         "Bacaklar L3 seviyesinde: port bazlı kısıt yok, DMZ'den mgmt'ye de erişim mümkün (bilinen sınır).",
                                         "API sertifikası node'un birincil IP'sini içerir; mgmt bu IP'lerle bağlanır."], 12.5)
    d.legend(1120, 740, 1060, [("mgmt", "yönetim / platform")], extra=True, cols=3)
    target_legend(d, 52, 860)
    d.save(out("07-mgmt-cluster.svg"), "07 · Mgmt cluster'ı: ağ bacakları, API erişim tablosu, olması gereken yönetim servisleri",
           "dört ağa bağlı tek node · yalnızca yönetim erişimi · kırmızı kesikli = hedefte olması gereken", oy=OY)


# =====================================================================================================================
def img08():
    W, H, OY = 2200, 1000, 40
    d = D(W, H)
    d.boundary([(14, 96), (2186, 96), (2186, 760), (14, 760)], "BİR kind NODE'U = BİR DOCKER CONTAINER (ör. cluster-a-control-plane)", "internal", fill_opacity=0.1)
    d.node(30, 130, 1600, 600, "cluster-a-control-plane", "kindest/node v1.37.0 · containerd · kubelet :10250 · kindnet (CNI)")
    d.text(50, 186, "Kontrol düzlemi (static pod · kube-system) · lab'da aynı node'da", 14, 700)
    for i, (n, ls) in enumerate([("kube-apiserver", [":6443 · mgmt ve host kubectl", "SAN: node IP'si"]), ("etcd", ["cluster durumu", ":2379 · metrik :2381"]),
                                 ("controller-manager", ["ReplicaSet, EndpointSlice", ":10257"]), ("scheduler", ["pod → node (tek node)", ":10259"])]):
        d.pod(50 + i * 392, 198, 380, None, n, "static pod", "external", [(n, "app", ls)])
    d.text(50, 330, "Uygulama ve giriş pod'ları", 14, 700)
    d.pod(50, 344, 380, None, "ingress-nginx-controller", "Deployment · ingress-nginx", "internal", [("controller", "proxy", ["hostPort :80 → pod :80", "portmap CNI: node IP DNAT"])])
    d.pod(442, 344, 380, None, "demo-app ×2", "Deployment · demo", "internal", [("app", "app", [":8080 (yalnızca pod ağında)", "pod IP 10.20.0.x"])])
    d.pod(834, 344, 380, None, "coredns ×2", "Deployment · kube-system", "mgmt", [("coredns", "agent", [":53 · *.svc.cluster.local", "dış ad → Docker DNS"])])
    d.pod(1226, 344, 384, None, "local-path-provisioner", "Deployment", "mgmt", [("provisioner", "agent", ["PVC → hostPath", "(data'da postgres PVC)"])])
    d.text(50, 480, "DaemonSet'ler", 14, 700)
    d.pod(50, 494, 760, None, "kube-proxy", "DaemonSet · kube-system", "mgmt", [("kube-proxy", "agent", [
        "Service ClusterIP → pod IP (iptables DNAT)", "selector'sız Service: EndpointSlice'taki dış IP'ye (ör. data 172.28.30.2:5432)",
        "ingress-nginx Service yerine EndpointSlice'ı doğrudan kullanır"])], agent=True)
    d.pod(830, 494, 780, None, "kindnet", "DaemonSet · kube-system", "mgmt", [("kindnetd", "agent", [
        "pod CIDR (10.20.0.0/24) · pod arayüzleri ve rotalar", "ip-masq: pod CIDR dışına giden trafik node IP'sine maskelenir",
        "→ eth1 (lab-data) üzerinden data node'una çıkar"])], agent=True)
    d.note(50, 650, 1560, "Paket yolu (numaralar)", [
        "1 DMZ'den gelen TCP node IP'sinin :80'ine (172.28.20.2) · 2 portmap DNAT → ingress pod :80 · 3 ingress → demo-app pod IP :8080 (kindnet rotası)",
        "4 pod → postgres.demo.svc:5432 · 5 kube-proxy DNAT → 172.28.30.2:5432 · 6 kindnet masq → kaynak 172.28.30.3 · eth1 → data node'u (06)"], 12.5)
    d.marker(44, 380, 1, "#2f7bd8")
    d.marker(240, 340, 2, "#2f7bd8")
    d.marker(436, 380, 3, "#2f7bd8")
    d.marker(632, 340, 4, "#c2410c")
    d.marker(44, 540, 5, "#c2410c")
    d.marker(824, 540, 6, "#c2410c")
    d.flow([(430, 400), (442, 400)], "main")
    d.text(1660, 150, "Portlar", 15, 700)
    ports = [(":80 / :443", "ingress hostPort (DMZ, uygulama)"), (":5432 / :6379", "ingress hostPort (yalnızca data)"), (":6443", "kube-apiserver"),
             (":10250", "kubelet"), (":2379 / :2381", "etcd istemci / metrik"), (":10257 / :10259", "controller-manager / scheduler"),
             (":10254", "ingress /healthz · /metrics"), (":8443", "ingress admission webhook"), (":53", "coredns"), (":8080", "demo-app (pod içi)"),
             (":9404 (host)", "edge-lb istatistik"), (":9080 / :9443 (host)", "mgmt ingress")]
    for i, (pt, desc) in enumerate(ports):
        y = 164 + i * 28
        d.n.append(f'<rect x="1660" y="{y}" width="500" height="24" rx="4" fill="{"#f4f7fc" if i % 2 else "#ffffff"}" stroke="#c4c4bf" stroke-width="0.8"/>')
        d.text(1670, y + 17, pt, 12.5, 700)
        d.text(1830, y + 17, desc, 12.5)
    d.text(1660, 530, "Cluster CIDR'ları", 15, 700)
    for i, (c, p, s) in enumerate([("dmz-a", "10.10.0.0/16", "10.11.0.0/16"), ("dmz-b", "10.12.0.0/16", "10.13.0.0/16"),
                                   ("cluster-a", "10.20.0.0/16", "10.21.0.0/16"), ("cluster-b", "10.30.0.0/16", "10.31.0.0/16"),
                                   ("data", "10.40.0.0/16", "10.41.0.0/16"), ("mgmt", "10.50.0.0/16", "10.51.0.0/16")]):
        y = 544 + i * 28
        d.n.append(f'<rect x="1660" y="{y}" width="500" height="24" rx="4" fill="{"#f4f7fc" if i % 2 else "#ffffff"}" stroke="#c4c4bf" stroke-width="0.8"/>')
        d.text(1670, y + 17, c, 12.5, 700)
        d.text(1790, y + 17, "pod " + p, 12.5)
        d.text(1970, y + 17, "svc " + s, 12.5)
    target(d, 30, 790, 1600, "Gerçek ortamda farklı olması gereken (lab'da yok)", [
        "ayrı master'lar (3) ve worker havuzları · DC başına node · kontrol düzlemi iş yükü taşımaz",
        "CNI: NetworkPolicy destekli (Cilium / Calico) · kindnet politika uygulamaz",
        "node sertleştirme (CIS) · audit logu → SIEM · otomatik sertifika yenileme"], 12.5)
    d.legend(1660, 790, 500, [("internal", "uygulama"), ("mgmt", "node agent"), ("external", "kontrol düzlemi")], extra=False, cols=1)
    target_legend(d, 1674, 920)
    d.save(out("08-node-anatomisi.svg"), "08 · Bir kind node'unun anatomisi: kontrol düzlemi, pod'lar, DaemonSet'ler, paket yolu",
           "lab'da her cluster tek node: kontrol düzlemi ve iş yükleri aynı Docker container'ında · portlar ve CIDR'lar sağda", oy=OY)


# =====================================================================================================================
def img09():
    W, H, OY = 2200, 1150, 40
    d = D(W, H)
    parts = [("Müşteri (mobil / web)", "public"), ("edge-lb", "edge"), ("dmz-a ingress", "dmz"), ("cluster-a ingress", "internal"),
             ("demo-app pod", "internal"), ("data ingress", "data"), ("postgres-0", "data")]
    x0, dx = 150, 315
    xs = [x0 + i * dx for i in range(len(parts))]
    top, bot = 120, 960
    for x, (n, c) in zip(xs, parts):
        fill, stroke, tcol = PALETTE[c]
        d.n.append(f'<rect x="{x - 125}" y="{top}" width="250" height="44" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        d.text(x, top + 28, n, 13.5, 700, tcol, "middle")
        d.e.append(f'<line x1="{x}" y1="{top + 44}" x2="{x}" y2="{bot}" stroke="{stroke}" stroke-width="1.4" stroke-dasharray="5 5"/>')
    steps = [(0, 1, "main", "GET https://app.localtest.me/ → 127.0.0.1:443 (Docker port)", "TLS ClientHello (SNI app.localtest.me) · edge-lb TLS'i açmaz"),
             (1, 2, "main", "TCP 172.28.10.2:443 + PROXY v1 (istemci 172.28.5.1)", "backend dmz_https · roundrobin · yalnızca UP sunucular (/healthz)"),
             (2, 3, "main", "TLS sonlanır (edge-tls) · real IP = PROXY · HTTP :80 → 172.28.20.2", "Host app.localtest.me → app-pool · XFF: 172.28.5.1 · hata/502-504 → cluster-b"),
             (3, 4, "main", "Service demo-app :80 → pod :8080", "real IP = XFF (yalnızca 172.28.20.0/24 güvenilir) · iki pod arasında round-robin"),
             (4, 3, "ret", "200 {cluster: cluster-a, pod, client, xff: \"172.28.5.1, 172.28.20.4\"}", ""),
             (3, 2, "ret", "200", "cluster-a ingress erişim logu (JSON)"),
             (2, 1, "ret", "200 + X-Dmz: dmz-a", "dmz-a ingress erişim logu: upstream 172.28.20.2:80"),
             (1, 0, "ret", "TLS kaydı olduğu gibi döner", "edge-lb tcplog: dmz_https/dmz-a"),
             (4, 5, "req", "postgres.demo.svc:5432 → 172.28.30.2:5432 (verify.sh'te)", "kube-proxy DNAT · kindnet masq (172.28.30.3) · lab-data · TLS yok"),
             (5, 6, "req", "tcp-services 5432 → data/postgres:5432", "nginx stream (L4) · pg_isready kabul edilir"),
             (6, 4, "ret", "accepting connections", "aynı yol: redis.demo.svc:6379 → PONG")]
    y = top + 84
    for i, (a, b, kind, lab, sub) in enumerate(steps):
        xa, xb = xs[a], xs[b]
        d.flow([(xa, y), (xb, y)], "aux" if kind == "ret" else kind)
        mx = min(xa, xb)
        d.marker(mx + 2, y - 18, i + 1, "#2f7bd8" if kind == "main" else ("#5f5f5a" if kind == "ret" else "#c2410c"))
        d.text(mx + 22, y - 12, lab, 12.5, 600)
        if sub:
            d.text(mx + 22, y + 14, sub, 11.5, 400, "#5f5f5a")
        y += 68
        if i == 7:
            d.text(40, y - 20, "Veri yolu (scripts/verify.sh probe pod'u ile test edilir · demo-app henüz DB çağırmıyor)", 13, 700, "#c2410c")
            y += 10
    d.note(40, 990, 1050, "Nasıl okunur", ["Sütunlar istekten geçen bileşenler (renk = zone), yukarıdan aşağı zaman.",
                                           "Mavi: müşteri isteği · turuncu: veri yolu · gri kesikli: yanıt.",
                                           "Ayrıntılar: edge 01 · DMZ 02-03 · uygulama 04-05 · data 06 · node 08."], 12.5)
    d.legend(1110, 990, 1070, [("public", "istemci"), ("edge", "edge"), ("dmz", "DMZ"), ("internal", "uygulama"), ("data", "veri")], extra=False, cols=3)
    d.save(out("09-uctan-uca-istek.svg"), "09 · Uçtan uca istek: müşteriden demo-app'e ve veri katmanına, adım adım",
           "her adım: kimden → kime · port / protokol · yapılan iş · gerçek IP'ler (verify.sh'in sınadığı yol)", oy=OY)


IMAGES = {"00": img00, "01": img01, "02": img02, "03": img03, "04": img04, "05": img05, "06": img06, "07": img07, "08": img08, "09": img09}

if __name__ == "__main__":
    for k in (sys.argv[1:] or IMAGES):
        IMAGES[k]()
        print("ok", k)
