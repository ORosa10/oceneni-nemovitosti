"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #16).
Uzivatel poskytl skutecne URL primo z prohlizece, napr.:
https://www.sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10/hlavni-mesto-praha-47/praha-3468/josefov-8722
Cilem je zjistit format cele hierarchie a najit uroven, kde aggregatedLocalities
vypise VSECHNY prazske ctvrti (mestske casti) s cenou/m2 a poctem transakci.
"""
import json
import re
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def next_data(url):
    r = requests.get(url, headers=H, timeout=30)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m:
        return r.status_code, None
    return r.status_code, json.loads(m.group(1))["props"]["pageProps"]


out = {}
urls_to_try = [
    "https://www.sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10",
    "https://www.sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10/hlavni-mesto-praha-47",
    "https://www.sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10/hlavni-mesto-praha-47/praha-3468",
    "https://www.sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10/hlavni-mesto-praha-47/praha-3468/josefov-8722",
]
for u in urls_to_try:
    st, pp = next_data(u)
    entry = {"status": st}
    if pp:
        entry["routeName"] = pp.get("routeName")
        entry["overallPrice"] = pp.get("overallPrice")
        entry["ancestorLocalities"] = pp.get("ancestorLocalities")
        al = pp.get("aggregatedLocalities") or []
        entry["num_aggregatedLocalities"] = len(al)
        entry["aggregatedLocalities_all"] = [
            (a["locality"]["entityType"], a["locality"]["name"], a["locality"]["seoName"], a["locality"]["entityId"],
             a["avgPricePerSqm"], a["numTransactions"]) for a in al
        ]
    out[u] = entry

with open("docs/diag_cenmapa_praha.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print("hotovo")
