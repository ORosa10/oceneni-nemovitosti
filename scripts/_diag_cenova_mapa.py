"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #16)."""
import json
import re
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

out = {}

# buildId z korenove stranky
r = requests.get("https://www.sreality.cz/cenova-mapa", headers=H, timeout=30)
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
data = json.loads(m.group(1))
out["buildId"] = data.get("buildId")
out["page"] = data.get("page")

def fetch(url):
    rr = requests.get(url, headers=H, timeout=30)
    mm = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', rr.text, re.S)
    routeName = None
    if mm:
        try:
            dd = json.loads(mm.group(1))
            routeName = dd["props"]["pageProps"].get("routeName")
        except Exception as e:
            routeName = f"parse_err:{e}"
    return rr.status_code, routeName

kandidati = [
    "https://www.sreality.cz/cenova-mapa/byty/hlavni-mesto-praha",
    "https://www.sreality.cz/cenova-mapa/hlavni-mesto-praha-10",
    f"https://www.sreality.cz/_next/data/{out['buildId']}/cenova-mapa/hlavni-mesto-praha.json",
    "https://www.sreality.cz/sitemap.xml",
]
out["kandidati"] = {}
for u in kandidati:
    try:
        st, rn = fetch(u)
        out["kandidati"][u] = {"status": st, "routeName": rn}
    except Exception as e:
        out["kandidati"][u] = {"chyba": str(e)}

# zkusime i sitemapindex
try:
    rs = requests.get("https://www.sreality.cz/sitemap.xml", headers=H, timeout=30)
    out["sitemap_status"] = rs.status_code
    out["sitemap_snippet"] = rs.text[:2000]
except Exception as e:
    out["sitemap_chyba"] = str(e)

with open("docs/diag_cenmapa_praha.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print("hotovo")
