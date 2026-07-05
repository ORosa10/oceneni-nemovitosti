# Oceňovací logika — převzata 1:1 z Oceneni_Byt_InSheetTables.xlsx (list Praha).
# JEDINÉ místo v projektu, kde se počítá tržní hodnota, sleva, výnos a hypotéka.
# Písmena v komentářích = sloupce původního sheetu.
from datetime import datetime

from . import db

ROK_OCENENI = 2025  # sheet: =min(2025-K3,80) — při aktualizaci modelu změnit

# BH5:BI7 — Koef: lokalita (%)
LOKALITA = {
    "u MHD / metro, u obchodu a služeb, tiché místo, parky v docházce": 5.0,
    "standardní dostupnost, běžná občanská vybavenost, žádné extrémy": 0.0,
    "daleko od MHD/služeb, hluk / bariéry (rušná silnice, železnice), horší pěší dostupnost": -5.0,
}

# BC4:BD6 — Koef: stav (%)
STAV = {
    "žádná / běžná údržba/novostavba": 0.0,
    "částečná rekonstrukce (kuchyň/koupelna ≤10 let)": 3.0,
    "generální rekonstrukce (≤10 let)": 6.0,
}

# AY4:AZ13 — pásma stáří: (start_věk, koef_cena %)
VEK_PASMA = [(0, 10.0), (10, 5.0), (20, 0.0), (30, -3.0), (40, -6.0),
             (50, -8.0), (60, -10.0), (70, -11.0), (80, -12.0), (90, -12.0)]

BALKON_PCT = 1.01        # BM4 — příplatek balkon/terasa (% k ceně/m2)
PARKOVANI_KC = 400000    # BM5 — příplatek parkování/garáž (Kč, absolutně)

# Výnosový model (sloupce AF–AL)
RUST_NAJMU = 0.05        # AF
RUST_CENY = 0.05         # AG
OBSAZENOST_MESICU = 10   # AB = nájem × 10 („roční 10/12")
AMORTIZACE = 0.3         # AH = 0.3 × tržní × (1+AF)^10

# Hypotéka (sloupce AN–AS)
LTV = 0.8                # AO
SAZBA = 0.042            # AP
SPLATNOST_MESICU = 360

# List „Cenová mapa", sloupce G–I: úprava základní ceny o velikost bytu
# (lineární křivka faktorů vůči průměru: 40 m2 malý, 57 střední, 75 velký)
_VELIKOST_BODY = [(40, 160150 / 145431), (57, 140682 / 145431), (75, 137215 / 145431)]


def koef_vek(vek):
    """M: lineární interpolace mezi dekádovými pásmy (vzorec ze sheetu)."""
    vek = min(vek, 80) + 0.00001
    dolni = max(s for s, _ in VEK_PASMA if s <= vek)
    horni = dolni + 10
    k = dict(VEK_PASMA)
    return k[dolni] * (horni - vek) / 10 + k[horni] * (vek - dolni) / 10


def faktor_velikosti(plocha):
    """Úprava základní ceny/m2 o velikost bytu (interpolace křivky ze sheetu)."""
    b = _VELIKOST_BODY
    if plocha <= b[0][0]:
        return b[0][1]
    if plocha >= b[-1][0]:
        return b[-1][1]
    for (x1, y1), (x2, y2) in zip(b, b[1:]):
        if x1 <= plocha <= x2:
            return y1 + (y2 - y1) * (plocha - x1) / (x2 - x1)
    return 1.0


def _irr(cena, celkem_najem, opravy, zhodnoceni):
    """AL: hledá r tak, aby AJ/(1+r)^20 + AI/(1+r)^10 − AH/(1+r)^10 − B = 0."""
    def npv(r):
        return zhodnoceni / (1 + r) ** 20 + celkem_najem / (1 + r) ** 10 \
            - opravy / (1 + r) ** 10 - cena
    lo, hi = 0.0001, 1.0
    if npv(lo) < 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _norm(s):
    return s.strip().lower().replace(" ", "_").replace("-", "_")


def ocenit_nabidku(l, mapa, mapa_najmu=None):
    """Ocení jednu nabídku dle modelu. `mapa` = {klic: cena_za_m2} z price_map,
    `mapa_najmu` = {klic: najem_m2_mesic} (fallback, když nabídka nemá ruční nájemné)."""
    plocha, cena = l.get("plocha_m2"), l.get("cena_czk")
    if not plocha or not cena:
        return None

    # F: základní cena/m2 — ručně zadaná, jinak cenová mapa × faktor velikosti
    zakladni = l.get("zakladni_cena_m2")
    if not zakladni:
        cena_mapy = mapa.get(_norm(l.get("ctvrt") or ""))
        if cena_mapy is None:
            return None
        zakladni = cena_mapy * faktor_velikosti(plocha)

    k_lok = LOKALITA.get(l.get("lokalita") or "", 0.0)                        # H
    k_stav = STAV.get((l.get("stav") or "").strip().lower(), 0.0)             # J×100
    k_vek = koef_vek(ROK_OCENENI - l["rok_vystavby"]) if l.get("rok_vystavby") else 0.0  # M
    k_balkon = BALKON_PCT if (l.get("balkon") or "").strip().lower() == "ano" else 0.0  # O
    park = (l.get("parkovani") or "Ne").strip().lower()                       # P/Q
    priplatky = PARKOVANI_KC if park == "ano" else (0 if park == "ne" else 2 * PARKOVANI_KC)
    k_dalsi = float(l.get("dalsi_koef_pct") or 0.0)                           # R

    # S, T, U, V, W, X — přesně dle sheetu
    koef = (1 + k_lok / 100) * (1 + k_stav / 100) * (1 + k_vek / 100) \
        * (1 + k_balkon / 100) * (1 + k_dalsi / 100)
    vysledna_m2 = zakladni * koef
    cena_za_byt = plocha * vysledna_m2
    trzni = cena_za_byt + priplatky
    rozdil = (cena / trzni - 1) * 100        # X: záporný = nabídka pod tržní hodnotou

    v = {
        "koef_celkem": round(koef, 4), "vysledna_cena_m2": round(vysledna_m2),
        "cena_za_byt": round(cena_za_byt), "priplatky_czk": priplatky,
        "trzni_hodnota": round(trzni), "rozdil_pct": round(rozdil, 2),
        "sleva_pct": round(-rozdil, 2), "najem_rocni": None, "prosty_vynos_pct": None,
        "celkovy_vynos_pct": None, "splatka_mesicni": None, "najem_mesicni": None,
        "pokryti_splatky_pct": None,
    }

    # Nájem a výnos (AA–AL) — ruční nájemné z MFČR, jinak nájemní mapa čtvrti
    najem_m2 = l.get("najem_m2_mesic") or (mapa_najmu or {}).get(_norm(l.get("ctvrt") or ""))
    if najem_m2:
        rocni_m2 = najem_m2 * OBSAZENOST_MESICU                               # AB
        najem_rocni = rocni_m2 * koef * plocha + float(l.get("najem_priplatky_rocni") or 0)  # AD
        opravy = trzni * AMORTIZACE * (1 + RUST_NAJMU) ** 10                  # AH
        celkem_najem = ((1 + RUST_NAJMU) ** 20 - 1) / RUST_NAJMU * najem_rocni  # AI
        zhodnoceni = (1 + RUST_CENY) ** 20 * trzni                            # AJ
        irr = _irr(cena, celkem_najem, opravy, zhodnoceni)                    # AL
        splatka = cena * LTV * (1 + SAZBA / 12) ** SPLATNOST_MESICU * (SAZBA / 12) \
            / ((1 + SAZBA / 12) ** SPLATNOST_MESICU - 1)                      # AQ
        najem_mesicni = najem_rocni / 12                                      # AR
        v.update({
            "najem_rocni": round(najem_rocni),
            "prosty_vynos_pct": round(najem_rocni / cena * 100, 2),           # AE
            "celkovy_vynos_pct": round(irr * 100, 2) if irr else None,
            "splatka_mesicni": round(splatka),
            "najem_mesicni": round(najem_mesicni),
            "pokryti_splatky_pct": round(najem_mesicni / splatka * 100, 1),   # AS
        })
    return v


def ocenit_vse():
    """Ocení všechny aktivní nabídky a uloží do tabulky valuations."""
    con = db.connect()
    pm = [dict(r) for r in con.execute("SELECT * FROM price_map")]
    mapa = {_norm(r["klic"]): r["cena_za_m2_czk"] for r in pm}
    mapa.update({_norm(r["ctvrt"]): r["cena_za_m2_czk"] for r in pm})
    mapa_najmu = {_norm(r["klic"]): r["najem_m2_mesic"] for r in pm if r.get("najem_m2_mesic")}
    mapa_najmu.update({_norm(r["ctvrt"]): r["najem_m2_mesic"] for r in pm if r.get("najem_m2_mesic")})
    now = datetime.now().isoformat(timespec="seconds")
    n, bez_mapy = 0, set()
    for l in con.execute("SELECT * FROM listings WHERE active=1"):
        l = dict(l)
        v = ocenit_nabidku(l, mapa, mapa_najmu)
        if v is None:
            if l.get("ctvrt") and _norm(l["ctvrt"]) not in mapa:
                bez_mapy.add(l["ctvrt"])
            continue
        cols = ", ".join(v)
        ph = ", ".join(":" + c for c in v)
        upd = ", ".join(f"{c}=excluded.{c}" for c in v)
        con.execute(
            f"INSERT INTO valuations (listing_id, {cols}, computed_at) VALUES (:lid, {ph}, :now) "
            f"ON CONFLICT(listing_id) DO UPDATE SET {upd}, computed_at=excluded.computed_at",
            {**v, "lid": l["id"], "now": now})
        n += 1
    con.commit()
    con.close()
    print(f"Oceněno {n} nabídek.")
    if bez_mapy:
        print("Čtvrti chybějící v cenové mapě (doplň data/price_map.csv, nebo zadej "
              "zakladni_cena_m2 ručně): " + ", ".join(sorted(bez_mapy)))
    return n
