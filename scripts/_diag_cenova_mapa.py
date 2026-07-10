"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #16)."""
import json
import re

import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def fetch(url):
    r = requests.get(url, headers=H, timeout=30)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    return r.status_code, len(r.text), (json.loads(m.group(1)) if m else None)


out = {}

# 1) Znovu koren, tentokrat dumpneme i 'properties' pole a hledame odkazy/href
status, ln, data = fetch("https://www.sreality.cz/cenova-mapa")
pp = data["props"]["pageProps"]
out["root_properties"] = pp.get("properties")
out["root_languageUrlItems"] = pp.get("languageUrlItems")
al = pp.get("aggregatedLocalities") or []
out["root_praha_entry"] = next((a for a in al if a["locality"]["seoName"] == "hlavni-mesto-praha"), None)

# 2) Zkusime ruzne kandidatni URL pro Prahu
kandidati = [
    "https://www.sreality.cz/cenova-mapa/ceska-republika/hlavni-mesto-praha",
    "https://www.sreality.cz/cenova-mapa/praha",
    "https://www.sreality.cz/cenova-mapa/hlavni-mesto-praha/",
    "https://www.sreality.cz/cenova-mapa/10/hlavni-mesto-praha",
]
out["kandidati"] = {}
for url in kandidati:
    try:
        st, l, d = fetch(url)
        info = {"status": st, "len": l}
        if d:
            pp2 = d["props"]["pageProps"]
            info["routeName"] = pp2.get("routeName")
            info["has_aggregatedLocalities"] = bool(pp2.get("aggregatedLocalities"))
            info["num_agg"] = len(pp2.get("aggregatedLocalities") or [])
        out["kandidati"][url] = info
    except Exception as e:
        out["kandidati"][url] = {"chyba": str(e)}

with open("docs/diag_cenmapa_praha.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print("hotovo")
