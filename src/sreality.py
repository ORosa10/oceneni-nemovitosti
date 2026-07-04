# Import nabídek ze Sreality.cz přes jejich veřejné JSON API.
# Použití: python -m src.main import-sreality "https://www.sreality.cz/hledani/prodej/byty/praha"
#
# POZOR: Neoficiální API — Sreality může formát kdykoli změnit. Pokud import
# přestane fungovat, je potřeba upravit mapování níže.
import re
import time
from urllib.parse import urlparse, parse_qs

import requests

from . import db

API = "https://www.sreality.cz/api/cs/v2/estates"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Mapování segmentů URL na API parametry
CATEGORY_MAIN = {"byty": 1, "domy": 2, "pozemky": 3, "komercni": 4, "ostatni": 5}
CATEGORY_TYPE = {"prodej": 1, "pronajem": 2, "drazby": 3}
# Kraje (locality_region_id)
REGIONY = {"praha": 10, "hlavni-mesto-praha": 10, "stredocesky-kraj": 11,
           "jihocesky-kraj": 12, "plzensky-kraj": 13, "karlovarsky-kraj": 14,
           "ustecky-kraj": 15, "liberecky-kraj": 16, "kralovehradecky-kraj": 17,
           "pardubicky-kraj": 18, "vysocina": 19, "jihomoravsky-kraj": 20,
           "olomoucky-kraj": 21, "zlinsky-kraj": 25, "moravskoslezsky-kraj": 14}


def _params_from_url(url: str) -> dict:
    """Best-effort převod URL vyhledávání na parametry API."""
    parsed = urlparse(url)
    seg = [s for s in parsed.path.split("/") if s]
    params = {"per_page": 60}
    for s in seg:
        if s in CATEGORY_TYPE:
            params["category_type_cb"] = CATEGORY_TYPE[s]
        if s in CATEGORY_MAIN:
            params["category_main_cb"] = CATEGORY_MAIN[s]
    # lokalita = poslední segment za kategorií (např. 'praha', 'praha-2')
    znama = set(CATEGORY_TYPE) | set(CATEGORY_MAIN) | {"hledani"}
    lokalita = [s for s in seg if s not in znama]
    if lokalita:
        reg = REGIONY.get(lokalita[-1].lower())
        if reg:
            params["locality_region_id"] = reg
    # převezmi i případné query parametry z URL (cena, plocha…)
    for k, v in parse_qs(parsed.query).items():
        params[k] = v[0]
    return {k: v for k, v in params.items() if v is not None}


def _ctvrt(locality: str) -> str:
    """Z lokality typu 'Praha 5 - Radlice' vytáhne část obce 'Radlice' (klíč cenové mapy)."""
    if "-" in (locality or ""):
        return locality.split("-", 1)[1].strip()
    return (locality or "").strip()


def _plocha(nazev: str) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m", nazev or "")
    return float(m.group(1).replace(",", ".")) if m else None


def _dispozice(nazev: str) -> str | None:
    m = re.search(r"(\d\+(?:kk|\d))", nazev or "")
    return m.group(1) if m else None


def import_sreality(url: str, max_pages: int = 5) -> int:
    params = _params_from_url(url)
    con = db.connect()
    n = 0
    for page in range(1, max_pages + 1):
        r = requests.get(API, params={**params, "page": page}, headers=HEADERS, timeout=30)
        print(f"strana {page}: HTTP {r.status_code}, url: {r.url}")
        r.raise_for_status()
        data = r.json()
        if page == 1:
            print(f"celkem nabídek dle API: {data.get('result_size')}")
        estates = data.get("_embedded", {}).get("estates", [])
        if not estates:
            break
        for e in estates:
            nazev = e.get("name", "")
            cena = e.get("price_czk", {}).get("value_raw") or e.get("price")
            if not cena:
                continue  # "cena na vyžádání" přeskočit
            hash_id = str(e.get("hash_id"))
            db.upsert_listing(con, {
                "source": "sreality",
                "external_id": hash_id,
                "url": f"https://www.sreality.cz/detail/x/x/x/x/{hash_id}",
                "nazev": nazev,
                "dispozice": _dispozice(nazev),
                "ctvrt": _ctvrt(e.get("locality", "")),
                "plocha_m2": _plocha(nazev),
                "cena_czk": float(cena),
                # Výchozí kategorie modelu — stav, lokalitu, rok atd. doplň ručně
                "lokalita": "standardní dostupnost, běžná občanská vybavenost, žádné extrémy",
                "stav": "Žádná / běžná údržba/Novostavba",
            })
            n += 1
        time.sleep(1)  # šetrnost k API
