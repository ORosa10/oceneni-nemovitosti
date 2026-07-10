"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #16)."""
import json
import re
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

r = requests.get("https://www.sreality.cz/cenova-mapa", headers=H, timeout=30)
html = r.text

scripts = sorted(set(re.findall(r'src="(/_next/static/[^"]+\.js)"', html)))
out_lines = [f"pocet js chunku: {len(scripts)}"]

hits = []
for s in scripts:
    url = "https://www.sreality.cz" + s
    try:
        rr = requests.get(url, headers=H, timeout=30)
        js = rr.text
    except Exception as e:
        out_lines.append(f"CHYBA {s}: {e}")
        continue
    if "aggregatedLocalities" in js or "PriceMapList" in js:
        hits.append((s, len(js)))
        # najdi kontext kolem klicovych retezcu
        for kw in ("aggregatedLocalities", "PriceMapList", "price-map", "priceMap/"):
            for mm in re.finditer(re.escape(kw), js):
                a, b = max(0, mm.start() - 150), min(len(js), mm.end() + 150)
                out_lines.append(f"--- {s} kw={kw} ---")
                out_lines.append(js[a:b])

out_lines.append(f"souboru s vyskytem: {len(hits)}: {hits[:20]}")

with open("docs/diag_cenmapa_jschunks.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print("hotovo, chunku:", len(scripts), "hits:", len(hits))
