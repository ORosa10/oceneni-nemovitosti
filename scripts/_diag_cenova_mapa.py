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
status, ln, data = fetch("https://www.sreality.cz/cenova-mapa/hlavni-mesto-praha")
out["http_status"] = status
out["html_len"] = ln
if data is None:
    out["error"] = "__NEXT_DATA__ nenalezen"
else:
    pp = data["props"]["pageProps"]
    out["pageProps_keys"] = list(pp.keys())
    out["routeName"] = pp.get("routeName")
    out["category"] = pp.get("category")
    out["ancestorLocalities"] = pp.get("ancestorLocalities")
    out["properties_type"] = str(type(pp.get("properties")))
    out["overallPrice"] = pp.get("overallPrice")
    out["aggregatedLocalities"] = pp.get("aggregatedLocalities")
    ds = pp.get("dehydratedState") or {}
    out["query_keys"] = [q.get("queryKey") for q in ds.get("queries", [])]
    # najdi query, ktere ma data (state.data) pro PriceMapList
    for q in ds.get("queries", []):
        qk = q.get("queryKey")
        if qk and "PriceMapList" in str(qk[0]):
            out["PriceMapList_query"] = qk
            st = q.get("state", {})
            out["PriceMapList_data_type"] = str(type(st.get("data")))
            out["PriceMapList_data_sample"] = st.get("data")

with open("docs/diag_cenmapa_praha.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print("hotovo")
