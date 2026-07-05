# Extrakce nájemného z cenové mapy MFČR (Mapa_Praha) do data/najemne_mfcr.csv
# Zdroj: https://mf.gov.cz/.../cenova-mapa-infografika (R htmlwidget/leaflet)
import csv, json, re, requests

UA = {"User-Agent": "Mozilla/5.0"}
URL = "https://mf.gov.cz/assets/cs/cmsmedia/html_cenove-mapy/Mapa_Praha_15.5.2026.html"
html = requests.get(URL, headers=UA, timeout=60).content.decode("utf-8", errors="replace")

m = re.search(r'<script type="application/json" data-for="htmlwidget[^"]*">(.*?)</script>', html, re.S)
widget = json.loads(m.group(1))
calls = widget["x"]["calls"]

vysledky = {}   # (ctvrt, skupina) -> najem
skupiny = set()
for c in calls:
    if c["method"] not in ("addPolygons", "addPolylines"):
        continue
    args = c["args"]
    # skupina (dispozice) a popisky jsou v argumentech; najdi group + seznam labelů
    group, labels = None, None
    for a in args:
        if isinstance(a, str) and re.match(r"\d\+", a):
            group = a
        if isinstance(a, dict) and isinstance(a.get("group"), str):
            group = a["group"]
        if isinstance(a, list) and a and isinstance(a[0], str) and "Katastr" in a[0]:
            labels = a
    if not labels:
        continue
    for lab in labels:
        mm = re.search(r"Katastrální území:\s*(.+?)\s*,\s*Nájemné referenčního bytu:\s*([\d.,]+)", lab)
        if mm:
            vysledky[(mm.group(1).strip(), group or "?")] = float(mm.group(2).replace(",", "."))
            skupiny.add(group or "?")

print("skupin:", sorted(skupiny), "| záznamů:", len(vysledky))
ctvrti = sorted({k[0] for k in vysledky})
with open("data/najemne_mfcr.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    sk = sorted(skupiny)
    w.writerow(["ctvrt"] + sk)
    for ct in ctvrti:
        w.writerow([ct] + [vysledky.get((ct, s), "") for s in sk])
print("ukázka:")
for ct in ctvrti[:8]:
    print(" ", ct, {s: vysledky.get((ct, s)) for s in sorted(skupiny)})
