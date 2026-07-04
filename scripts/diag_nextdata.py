# Diagnostika v2: hluboký průchod __NEXT_DATA__ + hledání XHR endpointů v HTML
import json, re, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
html = requests.get("https://www.sreality.cz/hledani/prodej/byty/praha", headers=UA, timeout=30).text
print("delka html:", len(html))
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
raw = m.group(1) if m else ""
print("delka __NEXT_DATA__:", len(raw))
for token in ('hash_id', 'price_czk', '"price"', 'estates', 'advert', 'results'):
    print(f"vyskyt {token} v next_data:", raw.count(token), "| v html:", html.count(token))

d = json.loads(raw) if raw else {}

def walk(o, path="", depth=0):
    if depth > 20: return
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}", depth+1)
    elif isinstance(o, list):
        if o and isinstance(o[0], dict) and len(o) >= 3:
            print(f"SEZNAM {path} [{len(o)}], klice[0]: {sorted(o[0].keys())[:15]}")
        for i, x in enumerate(o[:2]):
            walk(x, f"{path}[{i}]", depth+1)

walk(d)
for u in sorted(set(re.findall(r'["\'](/api/[^"\']{5,90})["\']', html)))[:30]:
    print("api cesta v html:", u)
