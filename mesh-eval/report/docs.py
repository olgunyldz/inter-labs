#!/usr/bin/env python3
"""tests/*/test.yaml -> docs/mesh-eval/test-senaryolari.md (test kataloğu + test x bileşen matrisi)"""
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "docs" / "mesh-eval" / "test-senaryolari.md"
CATS = [("performans", "Performans"), ("güvenlik", "Güvenlik"), ("trafik", "Trafik yönetimi"),
        ("gözlem", "Gözlemlenebilirlik"), ("operasyon", "Operasyon"), ("dayanıklılık", "Dayanıklılık")]
MESHES = ["none", "istio-ambient", "istio-ambient-l7", "istio-sidecar", "linkerd"]
# Bileşen grupları (matris sütunları): test.yaml components alanındaki anahtar kelimelere göre
GROUPS = [
    ("k6", ["k6"]), ("Servis zinciri", ["chainsvc", "zincir"]), ("Prometheus/Grafana", ["Prometheus", "cAdvisor", "kube-state", "Grafana"]),
    ("Tempo", ["Tempo"]), ("Edge LB / DMZ", ["HAProxy", "DMZ", "edge"]), ("NetworkPolicy", ["NetworkPolicy", "kube-network-policies"]),
    ("Mesh yetki politikası", ["yetki", "AuthorizationPolicy", "MeshTLS"]), ("Mesh trafik kuralları", ["VirtualService", "HTTPRoute", "DestinationRule", "failure accrual"]),
    ("Mesh kontrol düzlemi", ["kontrol düzlemi", "istiod", "linkerd-identity", "webhook", "CA"]), ("Gateway API", ["Gateway API"]),
    ("netshoot / tcpdump", ["netshoot", "tcpdump", "socat"]), ("Data cluster", ["data cluster", "Redis", "Postgres"]),
    ("Egress hedefleri", ["EgressNetwork", "ServiceEntry", "nginx dış"]), ("CLI araçları", ["istioctl", "linkerd CLI", "helm", "kubectl"]),
]

def main():
    tests = [yaml.safe_load(p.read_text()) for p in sorted((ROOT / "tests").glob("*/test.yaml"))]
    by = {t["id"]: t for t in tests}
    L = ["# Test senaryoları", "",
         "> Bu dosya `tests/*/test.yaml` dosyalarından üretilir (`meval docs`). Elle düzenlemeyin.", "",
         f"Toplam **{len(tests)} test**. Her test her mesh profilinde ayrı koşulur; sonuçlar `mesh-eval/results/` altına kaydedilir.", "",
         "## Özet", "", "| ID | Kategori | Test | Mesh profilleri | Başarı ölçütü |", "|---|---|---|---|---|"]
    order = [t for c, _ in CATS for t in sorted(by) if by[t]["category"] == c]
    for i in order:
        t = by[i]
        ms = t.get("meshes", ["all"])
        ms = "hepsi" if "all" in ms else ", ".join(ms)
        L.append(f"| [{i}](#{i.lower()}) | {t['category']} | {t['name']} | {ms} | {t.get('pass_criteria', '')} |")
    L += ["", "## Hangi test hangi bileşenle yapılıyor", "",
          "| Test | " + " | ".join(g for g, _ in GROUPS) + " |", "|---|" + "---|" * len(GROUPS)]
    for i in order:
        comp = " ".join(by[i].get("components", [])).lower()
        L.append(f"| {i} | " + " | ".join("●" if any(k.lower() in comp for k in keys) else "" for _, keys in GROUPS) + " |")
    L += ["", "Bileşenlerin ayrıntısı ve sürümleri: [envanter.md](envanter.md).", "",
          "## Mesh profili desteği", "",
          "| Test | " + " | ".join(MESHES) + " |", "|---|" + "---|" * len(MESHES)]
    for i in order:
        ms = by[i].get("meshes", ["all"])
        L.append(f"| {i} | " + " | ".join("●" if ("all" in ms or m in ms) else "—" for m in MESHES) + " |")
    L += ["", "— : test o profilde tanımlı değil (ör. mesh yokken kimlik bazlı yetki). Test tanımlı olduğu halde mesh'in yeteneği yoksa "
          "sonuç **uygulanamaz** olarak kaydedilir ve nedeni rapora yazılır.", ""]
    for c, cn in CATS:
        ids = [i for i in order if by[i]["category"] == c]
        if not ids:
            continue
        L += [f"## {cn}", ""]
        for i in ids:
            t = by[i]
            L += [f"### {i}", "", f"**{t['name']}**", "", f"**Amaç.** {t.get('purpose', '').strip()}", "",
                  f"**Yöntem.** {t.get('method', '').strip()}", "",
                  f"**Bileşenler.** {', '.join(t.get('components', []))}", ""]
            if t.get("profiles"):
                L += ["**Süre profilleri.** " + "; ".join(f"`{k}`: {v}" for k, v in t["profiles"].items()), ""]
            if t.get("outputs"):
                outs = t["outputs"] if isinstance(t["outputs"], list) else [t["outputs"]]
                L += ["**Çıktılar.** " + "; ".join(f"`{o}`" for o in outs), ""]
            L += [f"**Başarı ölçütü.** {t.get('pass_criteria', '')}", "",
                  f"Tanım: [`mesh-eval/tests/{i}/`](../../mesh-eval/tests/{i}/) · Çalıştırma: `meval test run {i}`", ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n")
    print(OUT)

if __name__ == "__main__":
    main()
