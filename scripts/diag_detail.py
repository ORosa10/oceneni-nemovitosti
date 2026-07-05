# Diagnostika v2: struktura result v detailu + zdroj dat cenové mapy MFČR
import json, re, sqlite3, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

print("###### 1) DETAIL NABÍDKY SREALITY ######")
con = sqlite3.connect("data/nemovitosti.db")
hid = con.execute("SELECT external_id FROM listings WHERE source='sreality' AND active=1 LIMIT 1").fetchone()[0]
r = requests.get(f"https://www.sreality.cz/api/v1/estates/{hid}", headers={**UA, "Accept": "application/json"}, timeout=30)
d = r.json().get("result", {})
print("hash_id:", hid, "| klice result:", sorted(d.keys()))
for key in ("items", "params", "labels", "labelsAll", "codeItems"):
    if key in d:
        print(f"--- {key}:", json.dumps(d[key], ensure_ascii=False)[:3000])
for key in ("name", "locality", "category_sub_cb", "text", "description"):
    if key in d:
        print(f"--- {key}:", str(d[key])[:300])

print("\n###### 2) CENOVÁ MAPA MFČR ######")
try:
    r = requests.get("https://mf.gov.cz/cs/rozpoctova-politika/podpora-projektoveho-rizeni/cenova-mapa/cenova-mapa-infografika", headers=UA, timeout=30)
    print("HTTP", r.status_code, "| delka:", len(r.text))
    html = r.text
    # iframy a odkazy na datové služby
    for u in sorted(set(re.findall(r'(?:src|href)="(https?://[^"]{10,160})"', html))):
        if any(t in u.lower() for t in ("arcgis", "mapa", "iframe", "embed", "api", "data", "cenova")):
            print("odkaz:", u)
    for u in sorted(set(re.findall(r'<iframe[^>]+src="([^"]+)"', html))):
        print("IFRAME:", u)
except Exception as e:
    print("CHYBA:", e)
