"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #16).
Zjistuje strukturu sreality.cz/cenova-mapa: stahne Prahu a jeji potomky
(mestske casti), aby bylo videt, na jake urovni site nabizi ceny za m2
odpovidajici 99 ctvrtim v data/price_map.csv.
"""
import json
import re

import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def next_data(url):
    r = requests.get(url, headers=H, timeout=30)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m:
        return {"_error": f"HTTP {r.status_code}, __NEXT_DATA__ nenalezen", "_len": len(r.text)}
    return json.loads(m.group(1))["props"]["pageProps"]


out = {}
praha = next_data("https://www.sreality.cz/cenova-mapa/hlavni-mesto-praha")
out["praha_overallPrice"] = praha.get("overallPrice")
out["praha_ancestorLocalities"] = praha.get("ancestorLocalities")
al = praha.get("aggregatedLocalities") or []
out["praha_num_aggregatedLocalities"] = len(al)
out["praha_aggregatedLocalities_sample"] = al[:5]
out["praha_aggregatedLocalities_all_names"] = [
    (a["locality"]["entityType"], a["locality"]["name"], a["locality"]["seoName"],
     a["avgPricePerSqm"], a["numTransactions"]) for a in al
]

if al:
    prvni = al[0]["locality"]
    if prvni["entityType"] != "ward":
        try:
            sub = next_data(f"https://www.sreality.cz/cenova-mapa/hlavni-mesto-praha/{prvni['seoName']}")
            sub_al = sub.get("aggregatedLocalities") or []
            out["uroven2_zdroj"] = prvni["seoName"]
            out["uroven2_ancestorLocalities"] = sub.get("ancestorLocalities")
            out["uroven2_num"] = len(sub_al)
            out["uroven2_vsechny"] = [
                (a["locality"]["entityType"], a["locality"]["name"], a["locality"]["seoName"],
                 a["avgPricePerSqm"], a["numTransactions"]) for a in sub_al
            ]
        except Exception as e:
            out["uroven2_chyba"] = str(e)

with open("docs/diag_cenmapa_praha.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("hotovo, klicu:", list(out.keys()))
