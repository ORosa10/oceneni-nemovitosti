"""DOCASNY diagnosticky skript #2 (ukol #20): najit nenulovou hodnotu 'annuity'
a potvrdit vyznam pole u druzstevnich bytu."""
import json
import re
import time

import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
     "Accept": "application/json"}
SEARCH_API = "https://www.sreality.cz/api/v1/estates/search"
DETAIL_API = "https://www.sreality.cz/api/v1/estates/{}"

nalezene_anuita = []
ownership_hodnoty = {}
vzorky_popisu = []
zkontrolovano = 0

for offset in range(0, 2000, 100):
    r = requests.get(SEARCH_API, params={"category_main_cb": 1, "category_type_cb": 1,
                                          "locality_region_id": 10, "limit": 100, "offset": offset},
                      headers=H, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        break
    for e in results:
        hid = str(e.get("hash_id"))
        try:
            rd = requests.get(DETAIL_API.format(hid), headers=H, timeout=30)
            rd.raise_for_status()
            dd = rd.json().get("result", {})
        except Exception as ex:
            continue
        zkontrolovano += 1
        own = dd.get("ownership") or {}
        own_name = own.get("name")
        ownership_hodnoty[own_name] = ownership_hodnoty.get(own_name, 0) + 1
        ann = dd.get("annuity")
        popis = dd.get("advert_description") or ""
        if ann not in (None, {}):
            nalezene_anuita.append({"hash_id": hid, "ownership": own, "annuity": ann,
                                     "popis_kolem_anuity": (popis[max(0, popis.lower().find("anuit")-80):popis.lower().find("anuit")+150]
                                                            if "anuit" in popis.lower() else None)})
        if own_name == "Družstevní" and len(vzorky_popisu) < 8:
            m = re.search(r".{0,60}anuit\w*.{0,150}", popis, re.I)
            vzorky_popisu.append({"hash_id": hid, "annuity_pole": ann, "text_o_anuite": m.group(0) if m else "(anuita v textu nezmíněna)"})
        if len(nalezene_anuita) >= 5:
            break
        time.sleep(0.15)
    if len(nalezene_anuita) >= 5 or zkontrolovano >= 300:
        break
    time.sleep(0.5)

report = {
    "zkontrolovano_detailu": zkontrolovano,
    "ownership_rozlozeni": ownership_hodnoty,
    "pocet_nenulovych_annuity": len(nalezene_anuita),
    "nenulove_annuity_priklady": nalezene_anuita,
    "druzstevni_text_o_anuite_vzorky": vzorky_popisu,
}
with open("docs/diag_pole2_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(json.dumps(report, ensure_ascii=False, indent=2)[:3000])
