# Diagnostika: co vrací detail nabídky (zkusit kandidátní endpointy)
import json, sqlite3, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
      "Accept": "application/json"}
con = sqlite3.connect("data/nemovitosti.db")
hid = con.execute("SELECT external_id FROM listings WHERE source='sreality' AND active=1 LIMIT 1").fetchone()[0]
print("testovací hash_id:", hid)

for url in (f"https://www.sreality.cz/api/v1/estates/{hid}",
            f"https://www.sreality.cz/api/v1/estate/{hid}",
            f"https://www.sreality.cz/api/v1/estates/detail/{hid}"):
    try:
        r = requests.get(url, headers=UA, timeout=30)
        print(f"\n=== {url} -> HTTP {r.status_code}")
        if r.status_code != 200:
            continue
        d = r.json()
        print("top-level klice:", sorted(d.keys()))
        # items = parametry inzerátu (stav, rok, balkon…)
        for key in ("items", "params", "attributes", "labels", "labelsAll"):
            if key in d:
                v = d[key]
                print(f"--- {key}:", json.dumps(v, ensure_ascii=False)[:2500])
        for key in ("name", "locality", "text", "meta_description"):
            if key in d:
                print(f"--- {key}:", str(d[key])[:200])
        break
    except Exception as e:
        print(url, "CHYBA:", e)
