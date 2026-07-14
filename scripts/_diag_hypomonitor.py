"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #19)."""
import json
import re
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
URL = "https://www.cbamonitor.cz/statistika/prumerna-urokova-sazba-novych-hypotek"

r = requests.get(URL, headers=H, timeout=30)
html = r.text
out = {"status": r.status_code, "len": len(html)}

with open("docs/diag_hypomonitor_html.txt", "w", encoding="utf-8") as f:
    f.write(html)

# Hledej kontext kolem procentni hodnoty a klicovych popisku
for kw in ("Aktuální hodnota", "aktualni-hodnota", "Hodnota minulého měsíce",
           "class=\"h1", "prumerna-urokova", "csv", "CSV", "data-value", "highcharts", "Chart(", "series"):
    idxs = [m.start() for m in re.finditer(re.escape(kw), html)][:3]
    out.setdefault("najdeno", {})[kw] = idxs

with open("docs/diag_hypomonitor.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("hotovo, status:", r.status_code, "delka:", len(html))
