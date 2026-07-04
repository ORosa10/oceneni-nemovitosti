# Diagnostika v3: struktura odpovědi /api/v1/estates/search
import json, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
r = requests.get("https://www.sreality.cz/api/v1/estates/search",
                 params={"category_main_cb": 1, "category_type_cb": 1,
                         "locality_region_id": 10, "per_page": 3, "page": 1},
                 headers=UA, timeout=30)
print("HTTP", r.status_code)
d = r.json()
print("top-level klice:", sorted(d.keys()))
for k, v in d.items():
    if isinstance(v, list) and v and isinstance(v[0], dict):
        print(f"SEZNAM {k} [{len(v)}], klice: {sorted(v[0].keys())}")
        print("  ukazka:", json.dumps(v[0], ensure_ascii=False)[:1200])
    elif isinstance(v, dict):
        print(f"DICT {k}: {sorted(v.keys())[:15]}")
        for k2, v2 in v.items():
            if isinstance(v2, list) and v2 and isinstance(v2[0], dict):
                print(f"  SEZNAM {k}.{k2} [{len(v2)}], klice: {sorted(v2[0].keys())}")
                print("   ukazka:", json.dumps(v2[0], ensure_ascii=False)[:1200])
