# Dotahování detailů nabídek ze Sreality a mapování na vstupy modelu.
# Mapování schváleno uživatelem 2026-07-05:
#   stav:  Po rekonstrukci → Generální (+6 %) [jen ≤10 let či rok neuveden, jinak 0 %]
#          Částečně po rekonstrukci → Částečná (+3 %) [stejná logika]
#          Novostavba/Ve výstavbě/Projekt/Velmi dobrý/Dobrý/Špatný/Před rek. → 0 %
#   rok:   object_age → acceptance_year → rok z finish_date;
#          novostavba/ve výstavbě/projekt bez roku → ROK_OCENENI (věk 0)
#   balkon: balcony NEBO terrace NEBO loggia → "Ano"
#   parkování: ≥2 stání/garáže → "Ano 2*"; garáž či stání → "Ano"; jinak "Ne"
# Lokalita se zde NEnastavuje (samostatný budoucí krok).
import sqlite3
import time

import requests

from . import db
from .valuation import ROK_OCENENI

API = "https://www.sreality.cz/api/v1/estates/{}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
           "Accept": "application/json"}

STAV_BEZNA = "Žádná / běžná údržba/Novostavba"
STAV_CASTECNA = "Částečná rekonstrukce (kuchyň/koupelna ≤10 let)"
STAV_GENERALNI = "Generální rekonstrukce (≤10 let)"
NOVOSTAVBY = {"novostavba", "ve výstavbě", "projekt"}


def _nazev(pole):
    return (pole or {}).get("name", "") if isinstance(pole, dict) else str(pole or "")


def _stav(d):
    bc = _nazev(d.get("building_condition")).strip().lower()
    rek = d.get("reconstruction_year")
    stary = bool(rek) and (ROK_OCENENI - int(rek)) > 10
    if bc == "po rekonstrukci":
        return STAV_BEZNA if stary else STAV_GENERALNI
    if "částečně po rekonstrukci" in bc:
        return STAV_BEZNA if stary else STAV_CASTECNA
    return STAV_BEZNA


def _rok(d):
    for k in ("object_age", "acceptance_year"):
        v = d.get(k)
        if v and str(v).isdigit() and 1800 <= int(v) <= ROK_OCENENI + 10:
            return int(v)
    fd = str(d.get("finish_date") or "")
    if len(fd) >= 4 and fd[:4].isdigit():
        return int(fd[:4])
    if _nazev(d.get("building_condition")).strip().lower() in NOVOSTAVBY:
        return ROK_OCENENI
    return None


def _balkon(d):
    return "Ano" if (d.get("balcony") or d.get("terrace") or d.get("loggia")) else "Ne"


def _parkovani(d):
    stani = 0
    for k in ("parking", "garage_count"):
        v = d.get(k)
        if isinstance(v, (int, float)):
            stani = max(stani, int(v))
    if stani >= 2:
        return "Ano 2*"
    if stani >= 1 or d.get("garage") or d.get("parking_lots"):
        return "Ano"
    return "Ne"


def import_detaily(limit: int = 500) -> int:
    con = db.connect()
    try:
        con.execute("ALTER TABLE listings ADD COLUMN detail_at TEXT")
    except sqlite3.OperationalError:
        pass
    radky = con.execute(
        "SELECT id, external_id FROM listings WHERE source='sreality' AND active=1 "
        "AND detail_at IS NULL ORDER BY id LIMIT ?", (limit,)).fetchall()
    n, chyby = 0, 0
    for r in radky:
        try:
            resp = requests.get(API.format(r["external_id"]), headers=HEADERS, timeout=30)
            resp.raise_for_status()
            d = resp.json().get("result", {})
            con.execute(
                "UPDATE listings SET stav=?, rok_vystavby=?, balkon=?, parkovani=?, "
                "detail_at=datetime('now') WHERE id=?",
                (_stav(d), _rok(d), _balkon(d), _parkovani(d), r["id"]))
            n += 1
        except Exception as e:
            chyby += 1
            if chyby <= 3:
                print(f"chyba u {r['external_id']}: {e}")
            if chyby > 20:
                print("příliš mnoho chyb, končím")
                break
        time.sleep(0.4)
    con.commit()
    con.close()
    print(f"Detaily dotaženy: {n} nabídek (chyb: {chyby}).")
    return n
