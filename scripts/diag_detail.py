# Diagnostika: hodnoty polí detailu u 8 nabídek (pro návrh mapování na model)
import json, sqlite3, time, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
      "Accept": "application/json"}
POLE = ["building_condition", "state_cb", "object_age", "acceptance_year", "finish_date",
        "reconstruction_year", "balcony", "balcony_area", "terrace", "terrace_area",
        "loggia", "garage", "garage_count", "parking", "parking_lots", "elevator",
        "ownership", "building_type", "flat_class", "low_energy", "usable_area"]
con = sqlite3.connect("data/nemovitosti.db")
ids = [r[0] for r in con.execute(
    "SELECT external_id FROM listings WHERE source='sreality' AND active=1 ORDER BY id LIMIT 8")]
for hid in ids:
    try:
        r = requests.get(f"https://www.sreality.cz/api/v1/estates/{hid}", headers=UA, timeout=30)
        d = r.json().get("result", {})
        print(f"### {hid} | {d.get('advert_name','')[:50]}")
        for k in POLE:
            v = d.get(k)
            if v not in (None, "", [], {}):
                print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:120]}")
        time.sleep(1)
    except Exception as e:
        print(hid, "CHYBA:", e)
