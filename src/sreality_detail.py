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
#
# Vlastnictví a anuita (2026-07-15, na žádost uživatele; ověřeno diagnostikou
# v Actions proti reálným datům, viz PREDAVACI.md bod 5g):
#   vlastnictví: pole `ownership.name` ze Sreality ("Osobní"/"Družstevní"/
#     "Státní/obecní") — stejné jako filtr na samotném Sreality.cz.
#   anuita: pole `annuity` ze Sreality NENÍ spolehlivé (u ověřených vzorků
#     vždy 0/null, i když text popisu jasně mluví o konkrétní nesplacené
#     částce) — proto se stav anuity odvozuje z volného textu
#     `advert_description`. Je to HEURISTIKA na klíčová slova, ne jistota:
#       "nesplacen(á)"/"neuhrazen(á)"/"dluh...anuit"/"zbývá doplatit"/
#         "zbývá splatit" u zmínky o anuitě → "nesplacena" (RED FLAG)
#       "splacen(á)"/"uhrazen(á)"/"vypořádán(á)" u zmínky o anuitě
#         (a NEobsahuje předchozí negaci) → "splacena"
#       anuita zmíněná, ale žádný z výše uvedených vzorů nesedí → "neznamo"
#       anuita v textu vůbec nezmíněná → None (nelze určit / nevztahuje se)
import re
import sqlite3
import time

import requests

ANUITA_NESPLACENA_VZORY = (
    r"nesplacen\w*", r"neuhrazen\w*", r"dluh\w*\s*(?:na|za)?\s*anuit\w*",
    r"zbýv\w*\s+(?:doplatit|splatit)", r"k\s+doplacení",
)
ANUITA_SPLACENA_VZORY = (r"splacen\w*", r"uhrazen\w*", r"vypořádán\w*")


def _anuita_stav(popis: str):
    """Vrátí 'nesplacena' / 'splacena' / 'neznamo' / None (bez zmínky)."""
    if not popis or "anuit" not in popis.lower():
        return None
    for vzor in ANUITA_NESPLACENA_VZORY:
        if re.search(vzor, popis, re.I):
            return "nesplacena"
    for vzor in ANUITA_SPLACENA_VZORY:
        if re.search(vzor, popis, re.I):
            return "splacena"
    return "neznamo"

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


def _vlastnictvi(d):
    nazev = _nazev(d.get("ownership")).strip()
    return nazev or None


# Doplňkové informační pole (2026-07-15, na žádost uživatele) — čistě pro
# zobrazení/filtr v appce, NEVSTUPUJÍ do oceňovacího vzorce (valuation.py
# je cornerstone a mění se jen s výslovným souhlasem). Ověřeno diagnostikou
# proti reálným datům ze Sreality, viz PREDAVACI.md.

def _energeticky_stitek(d):
    nazev = _nazev(d.get("energy_efficiency_rating_cb")).strip()
    return nazev or None


def _patro(d):
    v = d.get("floor_number")
    return int(v) if isinstance(v, (int, float)) else None


def _pater_celkem(d):
    v = d.get("floors")
    return int(v) if isinstance(v, (int, float)) else None


def _vytah(d):
    nazev = _nazev(d.get("elevator")).strip()
    if not nazev or nazev.lower().startswith("- nezad"):
        return None
    return nazev


def _sklep(d):
    return 1 if d.get("cellar") else 0


def _sklep_m2(d):
    v = d.get("cellar_area")
    return float(v) if isinstance(v, (int, float)) else None


def _zahrada_m2(d):
    v = d.get("garden_area")
    return float(v) if isinstance(v, (int, float)) else None


def _typ_stavby(d):
    nazev = _nazev(d.get("building_type")).strip()
    return nazev or None


def _datum_vlozeni(d):
    """Skutečné datum zveřejnění inzerátu na Sreality (pole `since`),
    přesnější než first_seen (což je jen okamžik prvního zachycení
    naším importem — u zpětně dotahovaných nabídek může být pozdější)."""
    v = d.get("since")
    return str(v) if v else None


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
                "vlastnictvi=?, anuita_stav=?, energeticky_stitek=?, patro=?, "
                "pater_celkem=?, vytah=?, sklep=?, sklep_m2=?, zahrada_m2=?, "
                "typ_stavby=?, datum_vlozeni=?, detail_at=datetime('now') WHERE id=?",
                (_stav(d), _rok(d), _balkon(d), _parkovani(d),
                 _vlastnictvi(d), _anuita_stav(d.get("advert_description")),
                 _energeticky_stitek(d), _patro(d), _pater_celkem(d), _vytah(d),
                 _sklep(d), _sklep_m2(d), _zahrada_m2(d), _typ_stavby(d),
                 _datum_vlozeni(d), r["id"]))
            n += 1
        except Exception as e:
            chyby += 1
            if chyby <= 3:
                print(f"chyba u {r['external_id']}: {e}")
            if chyby > 20:
                print("příliš mnoho chyb, končím")
                break
        time.sleep(0.25)
    con.commit()
    con.close()
    print(f"Detaily dotaženy: {n} nabídek (chyb: {chyby}).")
    return n
