# Import nabídek ze Sreality.cz přes /api/v1/estates/search (nové API, 2026).
# Použití: python -m src.main import-sreality "https://www.sreality.cz/hledani/prodej/byty/praha"
#
# POZOR: Neoficiální API — Sreality může formát kdykoli změnit. Diagnostika
# posledního běhu v Actions: docs/import_log.txt
import re
import time
from urllib.parse import urlparse, parse_qs

import requests

from . import db

API = "https://www.sreality.cz/api/v1/estates/search"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
           "Accept": "application/json"}
LIMIT = 100

CATEGORY_MAIN = {"byty": 1, "domy": 2, "pozemky": 3, "komercni": 4, "ostatni": 5}
CATEGORY_TYPE = {"prodej": 1, "pronajem": 2, "drazby": 3}
REGIONY = {"praha": 10, "hlavni-mesto-praha": 10, "stredocesky-kraj": 11,
           "jihocesky-kraj": 12, "plzensky-kraj": 13, "karlovarsky-kraj": 3,
           "ustecky-kraj": 15, "liberecky-kraj": 16, "kralovehradecky-kraj": 17,
           "pardubicky-kraj": 18, "vysocina": 19, "jihomoravsky-kraj": 20,
           "olomoucky-kraj": 21, "zlinsky-kraj": 25, "moravskoslezsky-kraj": 24}


def _params_from_url(url: str) -> dict:
    """Best-effort převod URL vyhledávání na parametry API."""
    parsed = urlparse(url)
    seg = [s for s in parsed.path.split("/") if s]
    params = {}
    for s in seg:
        if s in CATEGORY_TYPE:
            params["category_type_cb"] = CATEGORY_TYPE[s]
        if s in CATEGORY_MAIN:
            params["category_main_cb"] = CATEGORY_MAIN[s]
    znama = set(CATEGORY_TYPE) | set(CATEGORY_MAIN) | {"hledani"}
    lokalita = [s for s in seg if s not in znama]
    if lokalita:
        reg = REGIONY.get(lokalita[-1].lower())
        if reg:
            params["locality_region_id"] = reg
    for k, v in parse_qs(parsed.query).items():
        params[k] = v[0]
    return params


def _ctvrt(locality) -> str:
    """Z lokality typu 'Štorkánova, Praha 5 - Smíchov' vytáhne 'Smíchov'."""
    if isinstance(locality, dict):
        locality = locality.get("citypart") or locality.get("city") or ""
    s = str(locality or "")
    if "-" in s:
        return s.rsplit("-", 1)[1].strip()
    return s.split(",")[-1].strip()


def _plocha(nazev: str):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m", nazev or "")
    return float(m.group(1).replace(",", ".")) if m else None


def _dispozice(nazev: str):
    m = re.search(r"(\d\+(?:kk|\d)|atypick)", nazev or "", re.I)
    return m.group(1) if m else None


def _cena(r) -> float | None:
    for k in ("price_czk", "price_summary_czk", "price"):
        v = r.get(k)
        if isinstance(v, dict):
            v = v.get("value_raw") or v.get("amount")
        if v:
            try:
                return float(str(v).replace(" ", ""))
            except ValueError:
                continue
    return None


def import_sreality(url: str, max_pages: int = 5) -> int:
    params = _params_from_url(url)
    con = db.connect()
    n, offset, total = 0, 0, None
    for _ in range(max_pages):
        r = requests.get(API, params={**params, "limit": LIMIT, "offset": offset},
                         headers=HEADERS, timeout=30)
        print(f"offset {offset}: HTTP {r.status_code}, url: {r.url}")
        r.raise_for_status()
        data = r.json()
        if total is None:
            total = (data.get("pagination") or {}).get("total")
            print(f"celkem nabídek dle API: {total}")
        results = data.get("results", [])
        if not results:
            break
        for e in results:
            nazev = e.get("advert_name", "")
            cena = _cena(e)
            if not cena:
                continue  # "cena na vyžádání" přeskočit
            hash_id = str(e.get("hash_id"))
            db.upsert_listing(con, {
                "source": "sreality",
                "external_id": hash_id,
                "url": f"https://www.sreality.cz/detail/prodej/byt/x/x/{hash_id}",
                "nazev": nazev,
                "dispozice": _dispozice(nazev),
                "ctvrt": _ctvrt(e.get("locality")),
                "plocha_m2": _plocha(nazev),
                "cena_czk": cena,
                # Výchozí kategorie modelu — stav, lokalitu, rok atd. doplň ručně
                "lokalita": "standardní dostupnost, běžná občanská vybavenost, žádné extrémy",
                "stav": "Žádná / běžná údržba/Novostavba",
            })
            n += 1
        offset += LIMIT
        if total and offset >= total:
            break
        time.sleep(1)  # šetrnost k API
    con.commit()
    con.close()
    print(f"Importováno {n} nabídek ze Sreality.")
    return n
