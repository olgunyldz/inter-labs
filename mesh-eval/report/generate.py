#!/usr/bin/env python3
"""mesh-eval rapor üreticisi.

results/ altındaki test koşularını toplar, mesh profili x test bazında birleştirir (tekrarların
medyanı), puan kartını ve prod projeksiyonunu hesaplar; reports/<zaman>/ altına
rapor.html (tek dosya, grafikler gömülü), rapor.md ve veri.json üretir.

Kullanım: generate.py [--results DİZİN] [--session ID] [--out DİZİN]
"""
import argparse
import datetime as dt
import html
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent          # mesh-eval/
LAB = ROOT.parent

MESH_ORDER = ["none", "istio-ambient", "istio-ambient-l7", "istio-sidecar", "linkerd"]
MESH_NAMES = {
    "none": "Mesh yok (referans)",
    "istio-ambient": "Istio ambient (L4)",
    "istio-ambient-l7": "Istio ambient + waypoint (L7)",
    "istio-sidecar": "Istio sidecar",
    "linkerd": "Linkerd",
}
MESH_COLORS = {
    "none": "#8a8f98", "istio-ambient": "#2a9d8f", "istio-ambient-l7": "#1d6fa5",
    "istio-sidecar": "#e07a2e", "linkerd": "#7b4bb7",
}
CAT_NAMES = {"performans": "Performans", "güvenlik": "Güvenlik", "dayanıklılık": "Dayanıklılık",
             "trafik": "Trafik yönetimi", "gözlem": "Gözlemlenebilirlik", "operasyon": "Operasyon"}
CAT_ORDER = ["performans", "güvenlik", "dayanıklılık", "trafik", "gözlem", "operasyon"]
STATUS_TR = {"pass": "Geçti", "fail": "Kısmen / başarısız", "na": "Uygulanamaz", "error": "Hata", None: "Koşulmadı"}
STATUS_ICON = {"pass": "✅", "fail": "⚠️", "na": "➖", "error": "❌", None: "·"}
ROLE_NAMES = {"app": "Uygulama", "sidecar": "Sidecar proxy", "ztunnel": "ztunnel (node proxy)",
              "waypoint": "Waypoint (L7 proxy)", "cni": "CNI ajanı", "control": "Kontrol düzlemi",
              "ingress": "Ingress", "loadgen": "Yük üretici", "node_app": "Servis node'u (toplam)"}
HOPS_PER_REQUEST = 8   # gateway + 7 servis: bir giriş isteği zincirde 8 servis isteği üretir


# --------------------------------------------------------------------------- veri
def read_env(path):
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        m = re.match(r"^([A-Z0-9_]+)=([^#]*)", line.strip())
        if m:
            env[m.group(1)] = m.group(2).strip()
    return env


def load_runs(results_dir):
    runs = []
    for d in sorted(Path(results_dir).glob("*/")):
        try:
            meta = json.loads((d / "meta.json").read_text())
            res = json.loads((d / "result.json").read_text())
        except (OSError, json.JSONDecodeError):
            continue
        runs.append({"id": d.name, "dir": d, "meta": meta, "result": res})
    return runs


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def aggregate(runs):
    """Aynı test x mesh için tekrarları birleştirir: metrik medyanı, en kötü durum."""
    metrics, units, descs = defaultdict(list), {}, {}
    findings, checks = [], []
    for r in runs:
        for m in r["result"].get("metrics", []):
            if num(m.get("value")):
                metrics[m["key"]].append(m["value"])
            units.setdefault(m["key"], m.get("unit", ""))
            if m.get("desc"):
                descs.setdefault(m["key"], m["desc"])
        for f in r["result"].get("findings", []):
            if f not in findings:
                findings.append(f)
    checks = runs[-1]["result"].get("checks", [])
    statuses = [r["result"]["status"] for r in runs]
    for s in ("error", "fail", "na", "pass"):
        if s in statuses:
            status = s
            break
    agg = {k: statistics.median(v) for k, v in metrics.items()}
    spread = {k: (min(v), max(v)) for k, v in metrics.items() if len(v) > 1}
    return {
        "status": status, "metrics": agg, "spread": spread, "units": units, "descs": descs,
        "findings": findings, "checks": checks, "repeats": len(runs),
        "na_reason": runs[-1]["result"].get("na_reason"),
        "runs": [r["id"] for r in runs], "session": runs[-1]["meta"].get("session"),
        "profile": runs[-1]["meta"].get("profile"), "versions": runs[-1]["meta"].get("versions", {}),
        "start": min(r["result"]["start"] for r in runs), "end": max(r["result"]["end"] for r in runs),
    }


def select(runs, session=None):
    """(test, mesh) -> birleştirilmiş sonuç. Oturum verilmezse her çift için en son oturum."""
    groups = defaultdict(list)
    for r in runs:
        t = r["meta"]["test"]["id"]
        m = r["meta"]["mesh"]
        if session and r["meta"].get("session") != session:
            continue
        groups[(t, m)].append(r)
    out = {}
    for key, rs in groups.items():
        rs.sort(key=lambda r: r["meta"]["start"])
        # en son oturum, onun içinde en son çağrı (meval test run); aynı çağrıdaki --repeat tekrarları birleştirilir
        last = rs[-1]["meta"]
        same = [r for r in rs if r["meta"].get("session") == last.get("session")
                and r["meta"].get("invocation", r["id"]) == last.get("invocation", rs[-1]["id"])]
        out[key] = aggregate(same)
    return out


def derive(data):
    """Rapor için türetilmiş metrikler."""
    for (t, m), a in data.items():
        mt = a["metrics"]
        if t == "P05":
            pods = mt.get("shop_pods_running") or mt.get("shop_pods") or 0
            rc = sum(mt.get(f"req.{r}.cpu_cores", 0) for r in ("sidecar", "ztunnel", "waypoint", "cni"))
            rm = sum(mt.get(f"req.{r}.mem_mib", 0) for r in ("sidecar", "ztunnel", "waypoint", "cni"))
            if pods:
                mt["derived.req_cpu_per_pod"] = rc / pods
                mt["derived.req_mem_per_pod"] = rm / pods
            rps = mt.get("load.rps")
            if rps:
                mt["derived.cpu_per_1k_hops"] = mt.get("dataplane.cpu_cores", 0) * 1000 / (rps * HOPS_PER_REQUEST)


# --------------------------------------------------------------------------- puan kartı
def item_scores(data, item, meshes):
    t = item["test"]
    vals = {}
    for m in meshes:
        a = data.get((t, m))
        if not a:
            continue
        if item.get("kind") == "status":
            if a["status"] == "pass":
                vals[m] = (1.0, "geçti")
            elif a["status"] == "fail":
                c = a["checks"]
                frac = (sum(1 for x in c if x["pass"]) / len(c)) if c else 0
                vals[m] = (frac, f"{sum(1 for x in c if x['pass'])}/{len(c)} kontrol")
            elif a["status"] == "na":
                vals[m] = (0.0, "yetenek yok")
        else:
            v = a["metrics"].get(item["metric"])
            if a["status"] == "na" and v is None:
                vals[m] = (0.0, "yetenek yok")
            elif num(v):
                vals[m] = (v, None)
    if item.get("kind") != "status":
        raw = {m: v for m, (v, note) in vals.items() if note is None}
        if raw:
            if item["better"] == "lower":
                best = min(raw.values())
                for m, v in raw.items():
                    vals[m] = (1.0 if v <= 0 or best <= 0 and v <= best else (best / v if v > 0 else 1.0), fmt(v))
            else:
                best = max(raw.values())
                for m, v in raw.items():
                    vals[m] = ((v / best) if best > 0 else 0.0, fmt(v))
    return vals


def scorecard(data, meshes):
    sc = yaml.safe_load((ROOT / "report" / "scorecard.yaml").read_text())
    cats = []
    total = defaultdict(float)
    wsum = defaultdict(float)
    for c in sc["categories"]:
        rows = []
        cat_scores = defaultdict(list)
        for it in c["items"]:
            s = item_scores(data, it, meshes)
            rows.append({"label": it["label"], "test": it["test"], "scores": s})
            for m, (v, _) in s.items():
                cat_scores[m].append(v)
        cs = {m: statistics.mean(v) for m, v in cat_scores.items() if v}
        cats.append({"id": c["id"], "name": c["name"], "weight": c.get("weight", 1), "rows": rows, "scores": cs})
        for m, v in cs.items():
            total[m] += v * c.get("weight", 1)
            wsum[m] += c.get("weight", 1)
    tot = {m: total[m] / wsum[m] for m in total if wsum[m]}
    return cats, tot


# --------------------------------------------------------------------------- projeksiyon
def projection(data, env, meshes):
    g = lambda k, d: float(env.get(k, d))
    svcs, rep = g("PROD_SERVICES", 3000), g("PROD_REPLICAS_PER_SERVICE", 3)
    ppn, vcpu, memgb = g("PROD_PODS_PER_NODE", 30), g("PROD_NODE_VCPU", 16), g("PROD_NODE_MEM_GB", 64)
    rps = g("PROD_TOTAL_RPS", 30000)
    spw = g("PROD_SERVICES_PER_WAYPOINT", 10)
    pods = svcs * rep
    nodes = math.ceil(pods / ppn)
    waypoints = math.ceil(svcs / spw)
    rows = {}
    for m in meshes:
        if m == "none":
            continue
        p5 = data.get(("P05", m))
        if not p5:
            continue
        mt = p5["metrics"]
        per = lambda role, k="load": (mt.get(f"{k}.{role}.mem_mib", 0) / mt[f"{k}.{role}.containers"]) if mt.get(f"{k}.{role}.containers") else 0
        rq = lambda role, r: (mt.get(f"req.{role}.{r}", 0) / mt[f"req.{role}.containers"]) if mt.get(f"req.{role}.containers") else 0
        mem = per("sidecar") * pods + (per("ztunnel") + per("cni")) * nodes + per("waypoint") * waypoints
        req_cpu = rq("sidecar", "cpu_cores") * pods + (rq("ztunnel", "cpu_cores") + rq("cni", "cpu_cores")) * nodes + rq("waypoint", "cpu_cores") * waypoints
        req_mem = rq("sidecar", "mem_mib") * pods + (rq("ztunnel", "mem_mib") + rq("cni", "mem_mib")) * nodes + rq("waypoint", "mem_mib") * waypoints
        cph = mt.get("derived.cpu_per_1k_hops", 0)
        cpu = cph * rps / 1000
        ctl = mt.get("load.control.mem_mib", 0)
        p7 = data.get(("P07", m), {}).get("metrics", {})
        n7 = p7.get("scale_services") or 0
        ctl_growth = (p7.get("control.mem_growth_mib", 0) / n7 * svcs) if n7 else 0
        sc_growth = (max(p7.get("sidecar.mem_per_container_growth_mib", 0), 0) / n7 * svcs * pods) if n7 and per("sidecar") else 0
        o2 = data.get(("O02", m), {}).get("metrics", {})
        series = o2.get("series_mesh_per_pod", 0) * pods
        mem_total_gib = (mem + sc_growth + ctl + ctl_growth) / 1024
        node_eq_used = max(cpu / vcpu, mem_total_gib / memgb)
        node_eq_req = max(req_cpu / vcpu, req_mem / 1024 / memgb)
        rows[m] = {
            "dp_mem_gib": mem / 1024, "dp_cpu_cores": cpu, "req_cpu_cores": req_cpu, "req_mem_gib": req_mem / 1024,
            "ctl_mem_gib": (ctl + ctl_growth) / 1024, "sidecar_growth_gib": sc_growth / 1024,
            "series_m": series / 1e6, "node_eq_used": node_eq_used, "node_eq_req": node_eq_req,
        }
    assumptions = {
        "Servis": int(svcs), "Servis başına replika": fmt(rep), "Pod": int(pods), "Node başına pod": fmt(ppn),
        "Node": nodes, "Node boyutu": f"{int(vcpu)} vCPU / {int(memgb)} GB",
        "Toplam servisler arası istek hızı": f"{int(rps)} RPS",
        "Waypoint başına servis (ambient L7)": int(spw), "Waypoint": waypoints,
    }
    return rows, assumptions


# --------------------------------------------------------------------------- biçim / grafik
def fmt(v, unit=""):
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    if not num(v):
        return "—"
    a = abs(v)
    if a >= 1000:
        s = f"{v:,.0f}".replace(",", " ")   # binlik ayırıcı boşluk (nokta ondalıkla karışır)
    elif a >= 100:
        s = f"{v:.0f}"
    elif a >= 10:
        s = f"{v:.1f}"
    elif a >= 1:
        s = f"{v:.2f}"
    elif a == 0:
        s = "0"
    else:
        s = f"{v:.3f}"
    return f"{s} {unit}".strip() if unit and unit not in ("-", "bool") else s


def esc(s):
    return html.escape(str(s))


def svg_line(series, title, xlab, ylab, logy=False, w=640, h=320):
    """series: {mesh: [(x, y), ...]}"""
    pts = [(x, y) for s in series.values() for x, y in s if num(x) and num(y) and (y > 0 or not logy)]
    if not pts:
        return ""
    L, R, T, B = 60, 160, 30, 46
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = (min(ys), max(ys)) if logy else (0, max(ys) * 1.1)
    if x1 == x0:
        x1 = x0 + 1
    if logy:
        y0, y1 = math.log10(max(y0, 0.1)), math.log10(y1) + 0.1
    fy = (lambda y: math.log10(max(y, 0.1))) if logy else (lambda y: y)
    sx = lambda x: L + (x - x0) / (x1 - x0) * (w - L - R)
    sy = lambda y: T + (1 - (fy(y) - y0) / ((y1 - y0) or 1)) * (h - T - B)
    o = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{esc(title)}">',
         f'<text x="{L}" y="18" class="ct">{esc(title)}</text>']
    # eksenler ve ızgara
    for i in range(5):
        yv = (10 ** (y0 + (y1 - y0) * i / 4)) if logy else (y0 + (y1 - y0) * i / 4)
        yy = sy(yv)
        o.append(f'<line x1="{L}" x2="{w - R}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/>')
        o.append(f'<text x="{L - 6}" y="{yy + 4:.1f}" class="ax" text-anchor="end">{esc(fmt(yv))}</text>')
    for xv in sorted(set(xs)):
        o.append(f'<text x="{sx(xv):.1f}" y="{h - B + 16}" class="ax" text-anchor="middle">{esc(fmt(xv))}</text>')
    o.append(f'<text x="{(L + w - R) / 2}" y="{h - 8}" class="ax" text-anchor="middle">{esc(xlab)}</text>')
    o.append(f'<text x="14" y="{(T + h - B) / 2}" class="ax" text-anchor="middle" transform="rotate(-90 14 {(T + h - B) / 2})">{esc(ylab)}</text>')
    ly = T + 4
    for m in MESH_ORDER:
        s = [(x, y) for x, y in series.get(m, []) if num(x) and num(y) and (y > 0 or not logy)]
        if not s:
            continue
        c = MESH_COLORS[m]
        d = " ".join(f"{'M' if i == 0 else 'L'}{sx(x):.1f},{sy(y):.1f}" for i, (x, y) in enumerate(s))
        dash = ' stroke-dasharray="5 4"' if m == "none" else ""
        o.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2.2"{dash}/>')
        for x, y in s:
            o.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3.2" fill="{c}"><title>{esc(MESH_NAMES[m])}: {esc(fmt(x))} -> {esc(fmt(y))}</title></circle>')
        o.append(f'<rect x="{w - R + 12}" y="{ly}" width="12" height="3" fill="{c}"/>')
        o.append(f'<text x="{w - R + 30}" y="{ly + 5}" class="lg">{esc(MESH_NAMES[m])}</text>')
        ly += 18
    o.append("</svg>")
    return "\n".join(o)


def svg_bars(groups, title, unit="", w=640, h=None):
    """groups: [(etiket, {mesh: değer})] — yatay gruplu çubuklar"""
    rows = [(g, {m: v for m, v in vals.items() if num(v)}) for g, vals in groups]
    rows = [r for r in rows if r[1]]
    if not rows:
        return ""
    nb = sum(len(v) for _, v in rows)
    bh, gap = 14, 12
    h = h or 40 + nb * (bh + 3) + len(rows) * gap + 10
    L, R = 190, 90
    vmax = max(v for _, vals in rows for v in vals.values()) or 1
    o = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{esc(title)}">',
         f'<text x="10" y="18" class="ct">{esc(title)}</text>']
    y = 34
    for g, vals in rows:
        o.append(f'<text x="10" y="{y + 11}" class="ax">{esc(g)}</text>')
        for m in MESH_ORDER:
            if m not in vals:
                continue
            v = vals[m]
            bw = max(1, v / vmax * (w - L - R))
            o.append(f'<rect x="{L}" y="{y}" width="{bw:.1f}" height="{bh}" rx="2" fill="{MESH_COLORS[m]}"><title>{esc(MESH_NAMES[m])}: {esc(fmt(v, unit))}</title></rect>')
            o.append(f'<text x="{L + bw + 5:.1f}" y="{y + 11}" class="ax">{esc(fmt(v, unit))}</text>')
            y += bh + 3
        y += gap
    o.append("</svg>")
    return "\n".join(o)


def legend_html(meshes):
    return "".join(f'<span class="lgi"><i style="background:{MESH_COLORS[m]}"></i>{esc(MESH_NAMES[m])}</span>' for m in meshes)


# --------------------------------------------------------------------------- rapor
def build(args):
    env = {**read_env(LAB / "config.env"), **read_env(ROOT / "config.env"), **read_env(ROOT / "config.local.env")}
    runs = load_runs(args.results)
    if not runs:
        sys.exit(f"sonuç bulunamadı: {args.results}")
    data = select(runs, args.session)
    derive(data)
    tests = {}
    for d in sorted((ROOT / "tests").glob("*/test.yaml")):
        t = yaml.safe_load(d.read_text())
        tests[t["id"]] = t
    meshes = [m for m in MESH_ORDER if any(k[1] == m for k in data)]
    scored = [m for m in meshes if m != "none"]
    cats, total = scorecard(data, scored)
    proj, assumptions = projection(data, env, meshes)
    static = yaml.safe_load((ROOT / "report" / "static.yaml").read_text())
    now = dt.datetime.now()
    versions = next((a["versions"] for a in data.values() if a.get("versions")), {})
    sessions = sorted({a["session"] for a in data.values() if a.get("session")})
    profiles = sorted({a["profile"] for a in data.values() if a.get("profile")})

    ctx = dict(data=data, tests=tests, meshes=meshes, scored=scored, cats=cats, total=total, proj=proj,
               assumptions=assumptions, static=static, now=now, versions=versions, sessions=sessions,
               profiles=profiles, env=env)
    out = Path(args.out or (ROOT / "reports" / now.strftime("%Y%m%d-%H%M%S")))
    out.mkdir(parents=True, exist_ok=True)
    (out / "rapor.html").write_text(render_html(ctx))
    (out / "rapor.md").write_text(render_md(ctx))
    (out / "veri.json").write_text(json.dumps({
        "generated": now.isoformat(), "sessions": sessions, "versions": versions,
        "results": {f"{t}/{m}": {k: v for k, v in a.items() if k not in ("units", "descs")} for (t, m), a in data.items()},
        "scorecard": {"total": total, "categories": {c["id"]: c["scores"] for c in cats}},
        "projection": proj, "assumptions": assumptions,
    }, ensure_ascii=False, indent=1, default=str))
    print(out)


def summary_points(ctx):
    d, scored, proj = ctx["data"], ctx["scored"], ctx["proj"]
    pts = []
    if ctx["total"]:
        rank = sorted(ctx["total"].items(), key=lambda kv: -kv[1])
        pts.append("Puan kartı sıralaması (eşit ağırlık): " + ", ".join(f"{MESH_NAMES[m]} {v * 100:.0f}" for m, v in rank) + ".")
    g = lambda t, m, k: d.get((t, m), {}).get("metrics", {}).get(k)
    base = g("P01", "none", "knee_slo_rps")
    for m in scored:
        k = g("P01", m, "knee_slo_rps")
        if k and base:
            pts.append(f"{MESH_NAMES[m]}: SLO (p99 ≤ {fmt(g('P01', m, 'slo_p99_ms'))} ms) kapasitesi {fmt(k)} RPS — mesh'siz referansın (%{k / base * 100:.0f}'i).")
    a, s = proj.get("istio-ambient"), proj.get("istio-sidecar")
    if a and s:
        pts.append(f"3.000 servis projeksiyonu: veri düzlemi belleği ambient {fmt(a['dp_mem_gib'])} GiB, sidecar {fmt(s['dp_mem_gib'])} GiB; "
                   f"ayrılan (requests) CPU ambient {fmt(a['req_cpu_cores'])}, sidecar {fmt(s['req_cpu_cores'])} çekirdek.")
    for m in scored:
        bad = [t for (t, mm), x in d.items() if mm == m and x["status"] in ("fail", "error")]
        nas = [t for (t, mm), x in d.items() if mm == m and x["status"] == "na"]
        if bad or nas:
            pts.append(f"{MESH_NAMES[m]}: başarısız/kısmi {', '.join(sorted(bad)) or '—'}; yetenek yok {', '.join(sorted(nas)) or '—'}.")
    nf = sum(len(x["findings"]) for x in d.values())
    pts.append(f"Toplam {nf} bulgu kaydedildi (bölüm 6).")
    return pts


CSS = """
:root{--bg:#fff;--fg:#1d2330;--mut:#5d6575;--bd:#dde1e8;--card:#f6f7f9;--acc:#1d6fa5;--ok:#1f8a4c;--bad:#b3261e;--warn:#9a6700}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#14171d;--fg:#e6e8ec;--mut:#9aa3b2;--bd:#2c323d;--card:#1b1f27;--acc:#6cb4ee;--ok:#5cc28a;--bad:#ff8a80;--warn:#e3b341}}
:root[data-theme=dark]{--bg:#14171d;--fg:#e6e8ec;--mut:#9aa3b2;--bd:#2c323d;--card:#1b1f27;--acc:#6cb4ee;--ok:#5cc28a;--bad:#ff8a80;--warn:#e3b341}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 80px}h1{font-size:28px;margin:8px 0 4px}h2{font-size:21px;margin:40px 0 12px;padding-top:12px;border-top:1px solid var(--bd)}
h3{font-size:17px;margin:28px 0 8px}h4{font-size:15px;margin:18px 0 6px;color:var(--mut)}.mut{color:var(--mut)}.small{font-size:13px}
table{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:13.5px}th,td{border-bottom:1px solid var(--bd);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--card);font-weight:600}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}.wrap{overflow-x:auto}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px 16px;margin:12px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}.kpi{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px}
.kpi b{display:block;font-size:22px}.kpi span{color:var(--mut);font-size:13px}
.chart{width:100%;max-width:720px;height:auto;margin:8px 0}.chart .ct{font-weight:600;font-size:13px;fill:var(--fg)}.chart .ax,.chart .lg{font-size:11px;fill:var(--mut)}
.chart .grid{stroke:var(--bd);stroke-width:1}.lgi{display:inline-flex;align-items:center;gap:6px;margin-right:14px;font-size:13px}.lgi i{width:12px;height:12px;border-radius:3px;display:inline-block}
.st-pass{color:var(--ok)}.st-fail{color:var(--warn)}.st-error{color:var(--bad)}.st-na{color:var(--mut)}
.bar{height:8px;border-radius:4px;background:var(--acc);display:inline-block;vertical-align:middle;margin-right:6px}
ul.f li{margin:4px 0}code{font-size:12.5px;background:var(--card);padding:1px 4px;border-radius:4px}
nav.toc a{color:var(--acc);text-decoration:none}nav.toc li{margin:2px 0}
@media print{h2{page-break-before:always}.card,.kpi{break-inside:avoid}}
"""


def status_cell(a):
    if not a:
        return '<span class="st-na">·</span>'
    s = a["status"]
    tip = a.get("na_reason") or STATUS_TR[s]
    return f'<span class="st-{s}" title="{esc(tip)}">{STATUS_ICON[s]} {esc(STATUS_TR[s])}</span>'


def metric_table(ctx, tid, keys=None, skip=None):
    d, meshes = ctx["data"], ctx["meshes"]
    present = [m for m in meshes if (tid, m) in d]
    if not present:
        return "<p class='mut'>Bu test için kayıtlı koşu yok.</p>"
    allk = []
    for m in present:
        for k in d[(tid, m)]["metrics"]:
            if k not in allk:
                allk.append(k)
    if keys:
        allk = [k for k in keys if k in allk]
    if skip:
        allk = [k for k in allk if not re.search(skip, k)]
    units, descs = {}, {}
    for m in present:
        units.update(d[(tid, m)]["units"])
        descs.update(d[(tid, m)]["descs"])
    h = ['<div class="wrap"><table><tr><th>Metrik</th>' + "".join(f'<th class="n">{esc(MESH_NAMES[m])}</th>' for m in present) + "</tr>"]
    h.append("<tr><td>Durum</td>" + "".join(f'<td class="n">{status_cell(d[(tid, m)])}</td>' for m in present) + "</tr>")
    for k in allk:
        u = units.get(k, "")
        label = f"<code>{esc(k)}</code>" + (f'<br><span class="mut small">{esc(descs[k])}</span>' if k in descs else "")
        cells = []
        for m in present:
            a = d[(tid, m)]
            v = a["metrics"].get(k)
            if u == "-" and k in a["descs"]:
                cells.append(f'<td class="n small">{esc(a["descs"][k])}</td>')
                continue
            sp = a["spread"].get(k)
            extra = f'<br><span class="mut small">{esc(fmt(sp[0]))}…{esc(fmt(sp[1]))}</span>' if sp else ""
            cells.append(f'<td class="n">{esc(fmt(v, u))}{extra}</td>')
        h.append(f"<tr><td>{label}</td>{''.join(cells)}</tr>")
    h.append("</table></div>")
    return "\n".join(h)


def checks_table(ctx, tid):
    d, meshes = ctx["data"], ctx["meshes"]
    present = [m for m in meshes if (tid, m) in d and d[(tid, m)]["checks"]]
    if not present:
        return ""
    names = []
    for m in present:
        for c in d[(tid, m)]["checks"]:
            if c["name"].split(" [")[0] not in names:
                names.append(c["name"].split(" [")[0])
    h = ['<h4>Kontroller</h4><div class="wrap"><table><tr><th>Kontrol</th>' + "".join(f'<th class="n">{esc(MESH_NAMES[m])}</th>' for m in present) + "</tr>"]
    for n in names:
        row = [f"<td>{esc(n)}</td>"]
        for m in present:
            c = next((c for c in d[(tid, m)]["checks"] if c["name"].split(" [")[0] == n), None)
            if not c:
                row.append('<td class="n mut">·</td>')
            else:
                code = re.search(r"\[(\d+)\]", c["name"])
                act = c["actual"] + (f" ({code.group(1)})" if code else "")
                row.append(f'<td class="n {"st-pass" if c["pass"] else "st-error"}" title="beklenen: {esc(c["expected"])}">{"✔" if c["pass"] else "✘"} {esc(act)}</td>')
        h.append(f"<tr>{''.join(row)}</tr>")
    h.append("</table></div>")
    return "\n".join(h)


def p01_section(ctx):
    d, meshes = ctx["data"], ctx["meshes"]
    p99, p50, cpu = {}, {}, {}
    for m in meshes:
        a = d.get(("P01", m))
        if not a:
            continue
        mt = a["metrics"]
        n = int(mt.get("stages", 0))
        p99[m] = [(mt.get(f"stage{i}.target_rps"), mt.get(f"stage{i}.p99_ms")) for i in range(n)]
        p50[m] = [(mt.get(f"stage{i}.target_rps"), mt.get(f"stage{i}.p50_ms")) for i in range(n)]
        cpu[m] = [(mt.get(f"stage{i}.target_rps"), mt.get(f"stage{i}.node_app.cpu_cores")) for i in range(n)]
    o = [svg_line(p99, "p99 gecikme — hedef istek hızına göre (log ölçek)", "hedef RPS", "p99 (ms)", logy=True),
         svg_line(p50, "p50 gecikme — hedef istek hızına göre", "hedef RPS", "p50 (ms)"),
         svg_line(cpu, "Servis node'u CPU kullanımı (4 çekirdek sınırı)", "hedef RPS", "çekirdek")]
    o.append(metric_table(ctx, "P01", skip=r"^stage\d+\.(app|sidecar|ztunnel|waypoint|cni|control|ingress|loadgen|node_\w+)\.|\.(start|end)$"))
    return "\n".join(o)


def p05_section(ctx):
    d, meshes = ctx["data"], ctx["meshes"]
    roles = ["app", "sidecar", "ztunnel", "waypoint", "cni", "control"]
    groups_cpu = [(ROLE_NAMES[r], {m: d[("P05", m)]["metrics"].get(f"load.{r}.cpu_cores") for m in meshes if ("P05", m) in d}) for r in roles]
    groups_mem = [(ROLE_NAMES[r], {m: d[("P05", m)]["metrics"].get(f"idle.{r}.mem_mib") for m in meshes if ("P05", m) in d}) for r in roles]
    o = [svg_bars(groups_cpu, "Yük altında CPU (250 RPS) — rol bazında", "çekirdek"),
         svg_bars(groups_mem, "Boşta bellek — rol bazında", "MiB")]
    keys = ["load.rps", "load.p99_ms", "dataplane.cpu_cores", "dataplane.cpu_per_1k_rps", "derived.cpu_per_1k_hops",
            "dataplane.mem_idle_mib", "dataplane.mem_per_pod_mib", "derived.req_cpu_per_pod", "derived.req_mem_per_pod",
            "node_overhead_cores", "shop_pods"]
    for r in roles:
        keys += [f"idle.{r}.mem_mib", f"load.{r}.mem_mib", f"load.{r}.cpu_cores", f"req.{r}.cpu_cores", f"req.{r}.mem_mib", f"idle.{r}.containers"]
    for m in meshes:
        if ("P05", m) in d:
            d[("P05", m)]["units"].update({"derived.req_cpu_per_pod": "çekirdek", "derived.req_mem_per_pod": "MiB", "derived.cpu_per_1k_hops": "çekirdek"})
            d[("P05", m)]["descs"].update({"derived.req_cpu_per_pod": "pod başına ayrılan veri düzlemi CPU'su",
                                           "derived.req_mem_per_pod": "pod başına ayrılan veri düzlemi belleği",
                                           "derived.cpu_per_1k_hops": "1000 servis isteği (hop) başına veri düzlemi CPU"})
    o.append(metric_table(ctx, "P05", keys=keys))
    return "\n".join(o)


def cost_table(ctx):
    """Ambient / sidecar / Linkerd maliyet kalemleri (tek tablo)"""
    d, meshes = ctx["data"], [m for m in ctx["meshes"] if m != "none"]
    g = lambda t, m, k: d.get((t, m), {}).get("metrics", {}).get(k)
    items = [
        ("Veri düzlemi CPU, 250 RPS yükte", "P05", "dataplane.cpu_cores", "çekirdek"),
        ("1000 servis isteği başına veri düzlemi CPU", "P05", "derived.cpu_per_1k_hops", "çekirdek"),
        ("Veri düzlemi belleği, boşta (toplam)", "P05", "dataplane.mem_idle_mib", "MiB"),
        ("Uygulama pod'u başına veri düzlemi belleği", "P05", "dataplane.mem_per_pod_mib", "MiB"),
        ("Pod başına ayrılan CPU (requests)", "P05", "derived.req_cpu_per_pod", "çekirdek"),
        ("Pod başına ayrılan bellek (requests)", "P05", "derived.req_mem_per_pod", "MiB"),
        ("Servis node'unda app+proxy dışı CPU (kernel/ağ)", "P05", "node_overhead_cores", "çekirdek"),
        ("Kontrol düzlemi belleği", "P05", "load.control.mem_mib", "MiB"),
        ("Kontrol düzlemi büyümesi (N servis eklenince)", "P07", "control.mem_growth_mib", "MiB"),
        ("Her proxy'nin büyümesi (N servis eklenince)", "P07", "sidecar.mem_per_container_growth_mib", "MiB"),
        ("Orta yükte uçtan uca p99", "P01", "stage1.p99_ms", "ms"),
        ("SLO kırılma noktası", "P01", "knee_slo_rps", "RPS"),
        ("Pod hazır olma süresi (medyan)", "P06", "ready_p50_s", "sn"),
        ("Güncellemede yeniden başlatılan uygulama pod'u", "R05", "restarted_pods", "adet"),
        ("Güncelleme süresi", "R05", "upgrade_duration_s", "sn"),
        ("Güncelleme sırasında başarısız istek", "R05", "failed_requests", "istek"),
        ("Node proxy'si yeniden başlarken başarısız istek", "R04", "B.failed_requests", "istek"),
        ("Pod başına metrik serisi", "O02", "series_mesh_per_pod", "seri"),
        ("Pod'a eklenen konteyner", "O03", "added_containers_per_pod", "adet"),
        ("Ayrıcalıklı (NET_ADMIN/privileged) bileşen türü", "O03", "privileged_components", "adet"),
        ("CRD sayısı", "O03", "crds", "adet"),
    ]
    h = ['<div class="wrap"><table><tr><th>Kalem</th><th>Kaynak</th>' + "".join(f'<th class="n">{esc(MESH_NAMES[m])}</th>' for m in meshes) + "</tr>"]
    for label, t, k, u in items:
        vals = {m: g(t, m, k) for m in meshes}
        if not any(num(v) for v in vals.values()):
            continue
        nums = [v for v in vals.values() if num(v)]
        best = min(nums) if k not in ("knee_slo_rps",) else max(nums)
        cells = []
        for m in meshes:
            v = vals[m]
            b = ' style="font-weight:700"' if num(v) and v == best and len(nums) > 1 else ""
            cells.append(f'<td class="n"{b}>{esc(fmt(v, u))}</td>')
        h.append(f"<tr><td>{esc(label)}</td><td class='mut small'>{t}</td>{''.join(cells)}</tr>")
    h.append("</table></div><p class='mut small'>Kalın: kalemdeki en iyi değer. Değerler lab ortamındandır; mutlak değil göreli kıyas içindir.</p>")
    return "\n".join(h)


def render_html(ctx):
    d, tests, meshes, scored = ctx["data"], ctx["tests"], ctx["meshes"], ctx["scored"]
    e = []
    w = e.append
    w(f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
      f'<title>Service Mesh Değerlendirmesi</title><style>{CSS}</style></head><body><main>')
    w('<p class="mut small">inter-labs · mesh-eval</p><h1>Service Mesh Değerlendirme Raporu</h1>')
    w(f'<p class="mut">Oluşturma: {ctx["now"]:%d.%m.%Y %H:%M} · Oturum(lar): {esc(", ".join(ctx["sessions"]) or "—")} · '
      f'Profil: {esc(", ".join(ctx["profiles"]) or "—")} · Kıyaslanan: {legend_html(meshes)}</p>')
    w('<nav class="toc card"><b>İçindekiler</b><ol>'
      '<li><a href="#ozet">Yönetici özeti</a></li><li><a href="#puan">Puan kartı</a></li>'
      '<li><a href="#maliyet">Maliyet: kalem kalem</a></li><li><a href="#proj">Prod projeksiyonu (3.000 servis)</a></li>'
      '<li><a href="#matris">Test sonuç matrisi</a></li><li><a href="#bulgular">Bulgular</a></li>'
      '<li><a href="#detay">Test detayları</a></li><li><a href="#lisans">Lisans, destek, olgunluk</a></li>'
      '<li><a href="#yontem">Yöntem ve sınırlar</a></li><li><a href="#envanter">Envanter</a></li></ol></nav>')

    # 1 özet
    w('<h2 id="ozet">1. Yönetici özeti</h2><div class="kpis">')
    for m in scored:
        sc = ctx["total"].get(m)
        k = d.get(("P01", m), {}).get("metrics", {}).get("knee_slo_rps")
        mem = d.get(("P05", m), {}).get("metrics", {}).get("dataplane.mem_per_pod_mib")
        w(f'<div class="kpi" style="border-top:4px solid {MESH_COLORS[m]}"><span>{esc(MESH_NAMES[m])}</span>'
          f'<b>{fmt(sc * 100 if sc is not None else None)} / 100</b><span>SLO kapasitesi {fmt(k, "RPS")} · pod başına {fmt(mem, "MiB")}</span></div>')
    w('</div><ul class="f">' + "".join(f"<li>{esc(p)}</li>" for p in summary_points(ctx)) + "</ul>")
    w('<p class="mut small">Bu özet ölçümlerden otomatik üretilir. Sunuma eklenecek değerlendirme ve öneri metni bu verilere dayanarak ekip tarafından yazılmalıdır.</p>')

    # 2 puan kartı
    w('<h2 id="puan">2. Puan kartı</h2><p>Her kalem 0–100 arası puanlanır: durum kalemlerinde geçti = 100, kısmen = geçen kontrol oranı, '
      'yetenek yok = 0; ölçü kalemlerinde en iyi mesh 100, diğerleri en iyiye oranla. Kategoriler eşit ağırlıklıdır '
      '(<code>report/scorecard.yaml</code>). "Mesh yok" puanlanmaz.</p>')
    w('<div class="wrap"><table><tr><th>Kategori / kalem</th><th>Test</th>' + "".join(f'<th class="n">{esc(MESH_NAMES[m])}</th>' for m in scored) + "</tr>")
    for c in ctx["cats"]:
        w(f'<tr><th colspan="2">{esc(c["name"])}</th>' + "".join(f'<th class="n">{fmt(c["scores"].get(m, None) * 100 if m in c["scores"] else None)}</th>' for m in scored) + "</tr>")
        for r in c["rows"]:
            cells = []
            for m in scored:
                if m in r["scores"]:
                    v, note = r["scores"][m]
                    cells.append(f'<td class="n"><span class="bar" style="width:{v * 40:.0f}px"></span>{v * 100:.0f}<br><span class="mut small">{esc(note or "")}</span></td>')
                else:
                    cells.append('<td class="n mut">·</td>')
            w(f'<tr><td>{esc(r["label"])}</td><td class="mut small">{r["test"]}</td>{"".join(cells)}</tr>')
    w('<tr><th colspan="2">TOPLAM</th>' + "".join(f'<th class="n">{fmt(ctx["total"].get(m, None) * 100 if m in ctx["total"] else None)}</th>' for m in scored) + "</tr></table></div>")

    # 3 maliyet
    w('<h2 id="maliyet">3. Maliyet: kalem kalem</h2><p>Ambient, sidecar ve Linkerd arasındaki maliyet farkı; ölçüldüğü test ile birlikte. '
      'Ambient L4 ve ambient + waypoint ayrı sütundur: waypoint yalnızca L7 özellik gereken servislere eklenebilir.</p>')
    w(cost_table(ctx))
    w(p05_section(ctx) if any(("P05", m) in d for m in meshes) else "")

    # 4 projeksiyon
    w('<h2 id="proj">4. Prod projeksiyonu (3.000 servis)</h2><p>Lab\'da ölçülen birim maliyetler aşağıdaki varsayımlarla ölçeklenir. '
      'Varsayımlar <code>mesh-eval/config.env</code> (PROD_*) ile değiştirilip rapor yeniden üretilebilir.</p>')
    w('<div class="wrap"><table><tr><th>Varsayım</th><th>Değer</th></tr>' + "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in ctx["assumptions"].items()) + "</table></div>")
    if ctx["proj"]:
        pm = [m for m in scored if m in ctx["proj"]]
        rows = [("Veri düzlemi belleği (yük altında)", "dp_mem_gib", "GiB"), ("Veri düzlemi CPU (toplam trafik)", "dp_cpu_cores", "çekirdek"),
                ("Ayrılan CPU (requests)", "req_cpu_cores", "çekirdek"), ("Ayrılan bellek (requests)", "req_mem_gib", "GiB"),
                ("Kontrol düzlemi belleği (servis sayısıyla)", "ctl_mem_gib", "GiB"), ("Proxy'lerin servis sayısıyla büyümesi", "sidecar_growth_gib", "GiB"),
                ("Mesh metrik serisi", "series_m", "milyon"), ("Node eşdeğeri — kullanılan", "node_eq_used", "node"),
                ("Node eşdeğeri — ayrılan (requests)", "node_eq_req", "node")]
        w('<div class="wrap"><table><tr><th>Kalem</th>' + "".join(f'<th class="n">{esc(MESH_NAMES[m])}</th>' for m in pm) + "</tr>")
        for lab, k, u in rows:
            w(f"<tr><td>{esc(lab)}</td>" + "".join(f'<td class="n">{esc(fmt(ctx["proj"][m][k], u))}</td>' for m in pm) + "</tr>")
        w("</table></div>")
        w(svg_bars([("Node eşdeğeri (kullanılan)", {m: ctx["proj"][m]["node_eq_used"] for m in pm}),
                    ("Node eşdeğeri (ayrılan)", {m: ctx["proj"][m]["node_eq_req"] for m in pm})], "Mesh'in prod'da gerektirdiği ek kapasite", "node"))
        w('<p class="mut small">Sınırlar: doğrusal ölçekleme; lab node\'u 4 çekirdekli ve tek makinedir. Sidecar büyümesi Istio <code>Sidecar</code> kaynağıyla '
          'kapsam daraltılarak azaltılabilir; Linkerd proxy\'leri hedefleri istek anında öğrenir. Ayrılan kaynaklar mesh\'lerin varsayılan değerleridir: '
          'Istio sidecar başına 100m CPU / 128 Mi, ztunnel node başına 200m / 512 Mi; <b>Linkerd proxy\'sine varsayılan olarak kaynak isteği tanımlanmaz</b> '
          '(0 görünmesi maliyetsiz olduğu anlamına gelmez; prod\'da tanımlanmalıdır, kullanılan değerler bir alt sınırdır).</p>')

    # 5 matris
    w('<h2 id="matris">5. Test sonuç matrisi</h2><div class="wrap"><table><tr><th>Test</th>' + "".join(f'<th class="n">{esc(MESH_NAMES[m])}</th>' for m in meshes) + "</tr>")
    for cat in CAT_ORDER:
        ids = [t for t in sorted(tests) if tests[t]["category"] == cat]
        if not ids:
            continue
        w(f'<tr><th colspan="{len(meshes) + 1}">{esc(CAT_NAMES[cat])}</th></tr>')
        for t in ids:
            w(f'<tr><td><a href="#t-{t}">{t}</a> {esc(tests[t]["name"])}</td>' + "".join(f'<td class="n">{status_cell(d.get((t, m)))}</td>' for m in meshes) + "</tr>")
    w("</table></div><p class='mut small'>✅ geçti · ⚠️ bazı kontroller başarısız · ➖ bu mesh'te yetenek yok / uygulanamaz (nedeni hücre ipucunda) · ❌ test hatası · · koşulmadı</p>")

    # 6 bulgular
    w('<h2 id="bulgular">6. Bulgular</h2><p>Testlerin otomatik kaydettiği, karar için önemli gözlemler.</p>')
    for m in meshes:
        fs = [(t, f) for (t, mm), a in sorted(d.items()) if mm == m for f in a["findings"]]
        nas = [(t, a["na_reason"]) for (t, mm), a in sorted(d.items()) if mm == m and a["status"] == "na" and a.get("na_reason")]
        if not fs and not nas:
            continue
        w(f'<h3 style="color:{MESH_COLORS[m]}">{esc(MESH_NAMES[m])}</h3><ul class="f">')
        for t, f in fs:
            w(f'<li><a href="#t-{t}">{t}</a> — {esc(f)}</li>')
        for t, r in nas:
            w(f'<li><a href="#t-{t}">{t}</a> — <span class="mut">uygulanamaz:</span> {esc(r)}</li>')
        w("</ul>")

    # 7 detay
    w('<h2 id="detay">7. Test detayları</h2>')
    for cat in CAT_ORDER:
        ids = [t for t in sorted(tests) if tests[t]["category"] == cat]
        if not ids:
            continue
        w(f"<h3>{esc(CAT_NAMES[cat])}</h3>")
        for t in ids:
            td = tests[t]
            w(f'<div class="card" id="t-{t}"><h4 style="color:var(--fg);font-size:16px">{t} — {esc(td["name"])}</h4>')
            w(f'<p><b>Amaç.</b> {esc(td.get("purpose", ""))}</p><p><b>Yöntem.</b> {esc(td.get("method", ""))}</p>')
            w(f'<p class="small"><b>Bileşenler:</b> {esc(", ".join(td.get("components", [])))}<br><b>Başarı ölçütü:</b> {esc(td.get("pass_criteria", ""))}'
              + (f'<br><b>Profiller:</b> {esc("; ".join(f"{k}: {v}" for k, v in td.get("profiles", {}).items()))}' if td.get("profiles") else "") + "</p>")
            if t == "P01":
                w(p01_section(ctx))
            elif t == "P05":
                w('<p class="mut small">Grafikler ve ayrıntılı tablo: bölüm 3.</p>')
            else:
                w(metric_table(ctx, t))
            w(checks_table(ctx, t))
            fs = [(m, f) for m in meshes for f in d.get((t, m), {}).get("findings", [])]
            if fs:
                w('<h4>Bulgular</h4><ul class="f">' + "".join(f'<li><b style="color:{MESH_COLORS[m]}">{esc(MESH_NAMES[m])}:</b> {esc(f)}</li>' for m, f in fs) + "</ul>")
            runs = [(m, r) for m in meshes for r in d.get((t, m), {}).get("runs", [])]
            if runs:
                w('<p class="mut small">Koşular: ' + ", ".join(f"<code>{esc(r)}</code>" for _, r in runs) + "</p>")
            w("</div>")

    # 8 lisans
    st = ctx["static"]
    w(f'<h2 id="lisans">8. Lisans, destek, olgunluk</h2><p class="mut small">Test edilmez; kaynaklardan derlenmiştir (doğrulama: {esc(st.get("verified_on", ""))}).</p>')
    w('<div class="wrap"><table><tr><th></th>' + "".join(f"<th>{esc(v['name'])}</th>" for v in st["meshes"].values()) + "</tr>")
    for k, lab in [("license", "Lisans"), ("cncf", "CNCF"), ("releases", "Sürüm modeli"), ("support", "Destek"), ("risk", "Değerlendirme")]:
        w(f"<tr><td><b>{lab}</b></td>" + "".join(f"<td>{esc(v.get(k, ''))}</td>" for v in st["meshes"].values()) + "</tr>")
    w("<tr><td><b>Kaynak</b></td>" + "".join("<td class='small'>" + "<br>".join(esc(s) for s in v.get("sources", [])) + "</td>" for v in st["meshes"].values()) + "</tr></table></div>")
    w("<ul class='f small mut'>" + "".join(f"<li>{esc(n)}</li>" for n in st.get("notes", [])) + "</ul>")

    # 9 yöntem
    w('<h2 id="yontem">9. Yöntem ve sınırlar</h2><ul class="f">'
      '<li>Ortam: tek host üzerinde kind cluster\'ları (prod topolojisinin kopyası: edge LB, DMZ A/B, cluster A/B, data, mgmt). Mesh yalnızca cluster-a\'da.</li>'
      f'<li>CPU ayrımı: servis node\'u {esc(ctx["env"].get("CPUSET_APP", ""))}, yük üretici node\'u {esc(ctx["env"].get("CPUSET_LOADGEN", ""))}, '
      f'kontrol düzlemi {esc(ctx["env"].get("CPUSET_CONTROL", ""))} numaralı çekirdeklere sabitlendi (docker cpuset); yük üretici ölçülen servislerle CPU paylaşmaz.</li>'
      '<li>Adil kıyas: her mesh, sıfırdan kurulmuş bench cluster\'ında (<code>meval mesh use &lt;profil&gt; --fresh</code>) aynı servis zinciri ve aynı yükle ölçülür. '
      'Tüm mesh\'lerde zorunlu mTLS açık, erişim logu ve tracing (O01 hariç) kapalı, kaynak istekleri mesh varsayılanında.</li>'
      '<li>Servis zinciri: 8 servis (HTTP + bir gRPC kademesi), derinlik 5, paralel dallanma; her servis yapay 1–5 ms işlem süresi (chainsvc, <code>mesh-eval/apps/chainsvc</code>).</li>'
      '<li>Bağlantılar: servisler HTTP keep-alive ve kalıcı gRPC bağlantısı kullanır (gerçek servislerdeki gibi bağlantı havuzu).</li>'
      '<li>Mutlak değerler (RPS, ms) prod donanımına aktarılamaz; mesh\'ler arası göreli fark ve kırılma davranışı değerlendirilmelidir. '
      'Bulguların prod benzeri donanımda doğrulanması önerilir.</li>'
      '<li>Ambient + waypoint profilinde lab\'da tek waypoint replikası vardır ve shop namespace\'inin tüm servisler arası trafiği bu tek Envoy\'dan geçer; '
      'bu profildeki L7 kapasite sonucu (P01) waypoint ölçeklenmesine bağlıdır. Prod\'da waypoint\'ler namespace / servis bazında ve HPA ile ölçeklenir.</li>'
      '<li>Tekrarlanan koşularda metriklerin medyanı alınır, durum en kötü sonuçtur; yayılım (min…max) tablolarda gösterilir.</li></ul>')

    # 10 envanter
    w('<h2 id="envanter">10. Envanter</h2><div class="wrap"><table><tr><th>Bileşen</th><th>Sürüm</th></tr>')
    for k, v in ctx["versions"].items():
        w(f"<tr><td>{esc(k)}</td><td><code>{esc(v)}</code></td></tr>")
    w("</table></div><p class='mut small'>Ayrıntılı envanter: <code>docs/mesh-eval/envanter.md</code>. Ham sonuçlar: <code>mesh-eval/results/&lt;koşu&gt;/</code>.</p>")
    w("</main></body></html>")
    return "\n".join(e)


def render_md(ctx):
    d, tests, meshes, scored = ctx["data"], ctx["tests"], ctx["meshes"], ctx["scored"]
    L = []
    w = L.append
    w("# Service Mesh Değerlendirme Raporu\n")
    w(f"Oluşturma: {ctx['now']:%d.%m.%Y %H:%M} · Oturum: {', '.join(ctx['sessions']) or '—'} · Profil: {', '.join(ctx['profiles']) or '—'}\n")
    w("> Grafikli tam sürüm: `rapor.html`\n")
    w("## 1. Yönetici özeti\n")
    for p in summary_points(ctx):
        w(f"- {p}")
    w("\n## 2. Puan kartı\n")
    w("| Kategori | " + " | ".join(MESH_NAMES[m] for m in scored) + " |")
    w("|---|" + "---:|" * len(scored))
    for c in ctx["cats"]:
        w(f"| {c['name']} | " + " | ".join(fmt(c["scores"][m] * 100) if m in c["scores"] else "—" for m in scored) + " |")
    w("| **Toplam** | " + " | ".join(f"**{fmt(ctx['total'][m] * 100)}**" if m in ctx["total"] else "—" for m in scored) + " |")
    if ctx["proj"]:
        pm = [m for m in scored if m in ctx["proj"]]
        w("\n## 4. Prod projeksiyonu (3.000 servis)\n")
        w("| Varsayım | Değer |\n|---|---|")
        for k, v in ctx["assumptions"].items():
            w(f"| {k} | {v} |")
        w("\n| Kalem | " + " | ".join(MESH_NAMES[m] for m in pm) + " |")
        w("|---|" + "---:|" * len(pm))
        for lab, k, u in [("Veri düzlemi belleği", "dp_mem_gib", "GiB"), ("Veri düzlemi CPU", "dp_cpu_cores", "çekirdek"),
                          ("Ayrılan CPU", "req_cpu_cores", "çekirdek"), ("Ayrılan bellek", "req_mem_gib", "GiB"),
                          ("Node eşdeğeri (kullanılan)", "node_eq_used", "node"), ("Node eşdeğeri (ayrılan)", "node_eq_req", "node")]:
            w(f"| {lab} | " + " | ".join(fmt(ctx["proj"][m][k], u) for m in pm) + " |")
    w("\n## 5. Test sonuç matrisi\n")
    w("| Test | " + " | ".join(MESH_NAMES[m] for m in meshes) + " |")
    w("|---|" + "---|" * len(meshes))
    for t in sorted(tests, key=lambda x: (CAT_ORDER.index(tests[x]["category"]), x)):
        w(f"| {t} {tests[t]['name']} | " + " | ".join(f"{STATUS_ICON[d[(t, m)]['status']]} {STATUS_TR[d[(t, m)]['status']]}" if (t, m) in d else "·" for m in meshes) + " |")
    w("\n## 6. Bulgular\n")
    for m in meshes:
        fs = [(t, f) for (t, mm), a in sorted(d.items()) if mm == m for f in a["findings"]]
        if fs:
            w(f"\n### {MESH_NAMES[m]}\n")
            for t, f in fs:
                w(f"- **{t}** — {f}")
    w("\n## 7. Test detayları (metrikler)\n")
    for t in sorted(tests, key=lambda x: (CAT_ORDER.index(tests[x]["category"]), x)):
        present = [m for m in meshes if (t, m) in d]
        if not present:
            continue
        w(f"\n### {t} — {tests[t]['name']}\n\n{tests[t].get('purpose', '').strip()}\n")
        keys = []
        for m in present:
            for k in d[(t, m)]["metrics"]:
                if k not in keys and not re.search(r"\.(app|sidecar|ztunnel|waypoint|cni|control|ingress|loadgen|node_\w+)\.(cpu|mem|cont)|\.(start|end)$", k):
                    keys.append(k)
        w("| Metrik | " + " | ".join(MESH_NAMES[m] for m in present) + " |")
        w("|---|" + "---:|" * len(present))
        w("| durum | " + " | ".join(STATUS_TR[d[(t, m)]["status"]] for m in present) + " |")
        for k in keys[:40]:
            u = next((d[(t, m)]["units"].get(k) for m in present if k in d[(t, m)]["units"]), "")
            w(f"| `{k}` | " + " | ".join(fmt(d[(t, m)]["metrics"].get(k), u) for m in present) + " |")
    w("\n## 10. Envanter\n")
    for k, v in ctx["versions"].items():
        w(f"- {k}: `{v}`")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results"))
    ap.add_argument("--session")
    ap.add_argument("--out")
    build(ap.parse_args())
