# Jednorázová diagnostika: struktura __NEXT_DATA__ na stránce vyhledávání Sreality
import json, re, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
html = requests.get("https://www.sreality.cz/hledani/prodej/byty/praha", headers=UA, timeout=30).text
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
if not m:
    print("__NEXT_DATA__ nenalezen; delka html:", len(html))
    for x in re.findall(r'<script[^>]*id="([^"]*)"', html)[:20]:
        print("script id:", x)
    raise SystemExit(0)
d = json.loads(m.group(1))

def walk(o, path="", depth=0):
    if depth > 8: return
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}", depth+1)
    elif isinstance(o, list) and o and isinstance(o[0], dict):
        keys = set(o[0].keys())
        if keys & {"price", "hash_id", "name", "locality", "gps"}:
            print(f"KANDIDAT {path} [{len(o)} polozek], klice: {sorted(keys)[:20]}")
            print("  ukazka:", json.dumps(o[0], ensure_ascii=False)[:600])
        else:
            walk(o[0], path+"[0]", depth+1)

print("top-level klice:", list(d.keys()))
walk(d)
