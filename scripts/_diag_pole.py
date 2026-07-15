"""DOCASNY diagnosticky skript (smazat po zjisteni poli vlastnictvi + popis)."""
import json
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
     "Accept": "application/json"}

SEARCH_API = "https://www.sreality.cz/api/v1/estates/search"
DETAIL_API = "https://www.sreality.cz/api/v1/estates/{}"

# Praha, byty, prodej
params = {"category_main_cb": 1, "category_type_cb": 1, "locality_region_id": 10, "limit": 20, "offset": 0}
r = requests.get(SEARCH_API, params=params, headers=H, timeout=30)
r.raise_for_status()
data = r.json()
results = data.get("results", [])

with open("docs/diag_search_sample.json", "w", encoding="utf-8") as f:
    json.dump(results[:5], f, ensure_ascii=False, indent=2)

report = []
report.append(f"pocet vysledku na strance: {len(results)}")

def najdi_klice(obj, hledane, cesta="", vysledky=None):
    if vysledky is None:
        vysledky = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            nova_cesta = f"{cesta}.{k}" if cesta else k
            if any(h in k.lower() for h in hledane):
                vysledky.append((nova_cesta, v if not isinstance(v, (dict, list)) else type(v).__name__))
            najdi_klice(v, hledane, nova_cesta, vysledky)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):
            najdi_klice(v, hledane, f"{cesta}[{i}]", vysledky)
    return vysledky

hledane_vlastnictvi = ["vlastnic", "ownership", "tenure"]
hledane_text = ["text", "popis", "description", "anuita", "family_house", "type_of_deal"]

report.append("=== hledani 'vlastnictvi' v search vysledcich (prvnich 5) ===")
for i, e in enumerate(results[:5]):
    nalezy = najdi_klice(e, hledane_vlastnictvi)
    report.append(f"estate {i} (hash_id={e.get('hash_id')}): {nalezy}")

# vypis vsech top-level klicu prvniho estate (pro obecny prehled struktury)
if results:
    report.append("=== top-level klice prvniho estate ===")
    report.append(str(sorted(results[0].keys())))

# detail pro prvnich par estate - hledani textu popisu a vlastnictvi
detail_dump = {}
for e in results[:3]:
    hid = str(e.get("hash_id"))
    try:
        rd = requests.get(DETAIL_API.format(hid), headers=H, timeout=30)
        rd.raise_for_status()
        dd = rd.json().get("result", {})
        detail_dump[hid] = dd
        nalezy_v = najdi_klice(dd, hledane_vlastnictvi)
        nalezy_t = najdi_klice(dd, hledane_text)
        report.append(f"--- detail {hid} ---")
        report.append(f"top-level klice: {sorted(dd.keys())}")
        report.append(f"vlastnictvi nalezy: {nalezy_v}")
        report.append(f"text/popis nalezy (jen typy/klice, hodnoty muzou byt dlouhe): {[(k, (v[:200] if isinstance(v,str) else v)) for k,v in nalezy_t]}")
        # items / labelsAll bývají tam, kde Sreality drží párové "název: hodnota" atributy
        for klic in ("items", "labelsAll", "labels"):
            if klic in dd:
                report.append(f"{klic}: {json.dumps(dd[klic], ensure_ascii=False)[:2000]}")
    except Exception as ex:
        report.append(f"chyba u detailu {hid}: {ex}")

with open("docs/diag_detail_sample.json", "w", encoding="utf-8") as f:
    json.dump(detail_dump, f, ensure_ascii=False, indent=2)

with open("docs/diag_pole_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("\n".join(report))
