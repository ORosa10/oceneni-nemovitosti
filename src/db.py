import csv
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "nemovitosti.db"
PRICE_MAP_CSV = ROOT / "data" / "price_map.csv"

LISTING_SLOUPCE = [
    "source", "external_id", "url", "nazev", "dispozice", "ctvrt", "plocha_m2",
    "cena_czk", "zakladni_cena_m2", "lokalita", "stav", "rok_vystavby",
    "balkon", "parkovani", "dalsi_koef_pct", "najem_m2_mesic", "najem_priplatky_rocni",
    "lokalita_auto", "lokalita_skore", "lokalita_detail",
]


def migruj(con):
    """Doplní nové sloupce do starších databází."""
    for sql in ("ALTER TABLE listings ADD COLUMN detail_at TEXT",
                "ALTER TABLE listings ADD COLUMN lokalita_auto TEXT",
                "ALTER TABLE listings ADD COLUMN lokalita_skore REAL",
                "ALTER TABLE listings ADD COLUMN lokalita_detail TEXT",
                # Rozpad výpočtu tržní hodnoty pro zobrazení v appce (2026-07-10)
                "ALTER TABLE valuations ADD COLUMN v_cena_mapy_m2 REAL",
                "ALTER TABLE valuations ADD COLUMN v_faktor_velikosti REAL",
                "ALTER TABLE valuations ADD COLUMN v_zakladni_cena_m2 REAL",
                "ALTER TABLE valuations ADD COLUMN v_zakladni_rucne INTEGER",
                "ALTER TABLE valuations ADD COLUMN v_koef_lokalita_pct REAL",
                "ALTER TABLE valuations ADD COLUMN v_koef_stav_pct REAL",
                "ALTER TABLE valuations ADD COLUMN v_koef_vek_pct REAL",
                "ALTER TABLE valuations ADD COLUMN v_koef_balkon_pct REAL",
                "ALTER TABLE valuations ADD COLUMN v_koef_dalsi_pct REAL",
                "ALTER TABLE valuations ADD COLUMN v_vek_pouzity REAL",
                # Watchlist (hvězdička) a skrytí nabídky z appky (2026-07-13,
                # na žádost uživatele) — čistě ruční stav, import ho NIKDY
                # nepřepíše (není v LISTING_SLOUPCE), mění se jen přes
                # scripts/aplikuj_upravu.py (GitHub Issue).
                "ALTER TABLE listings ADD COLUMN watchlist INTEGER DEFAULT 0",
                "ALTER TABLE listings ADD COLUMN skryto INTEGER DEFAULT 0"):
        try:
            con.execute(sql)
        except sqlite3.OperationalError:
            pass

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY, source TEXT NOT NULL, external_id TEXT, url TEXT,
    nazev TEXT, dispozice TEXT, ctvrt TEXT, plocha_m2 REAL, cena_czk REAL,
    zakladni_cena_m2 REAL, lokalita TEXT, stav TEXT, rok_vystavby INTEGER,
    balkon TEXT DEFAULT 'Ne', parkovani TEXT DEFAULT 'Ne', dalsi_koef_pct REAL DEFAULT 0,
    najem_m2_mesic REAL, najem_priplatky_rocni REAL DEFAULT 0,
    active INTEGER DEFAULT 1, first_seen TEXT, last_seen TEXT,
    watchlist INTEGER DEFAULT 0, skryto INTEGER DEFAULT 0,
    UNIQUE (source, external_id)
);
CREATE TABLE IF NOT EXISTS price_map (
    klic TEXT PRIMARY KEY, ctvrt TEXT NOT NULL, cena_za_m2_czk REAL NOT NULL,
    pocet_transakci INTEGER, najem_m2_mesic REAL, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS valuations (
    listing_id INTEGER PRIMARY KEY REFERENCES listings(id),
    koef_celkem REAL, vysledna_cena_m2 REAL, cena_za_byt REAL, priplatky_czk REAL,
    trzni_hodnota REAL, rozdil_pct REAL, sleva_pct REAL, najem_rocni REAL,
    prosty_vynos_pct REAL, celkovy_vynos_pct REAL, splatka_mesicni REAL,
    najem_mesicni REAL, pokryti_splatky_pct REAL,
    v_cena_mapy_m2 REAL, v_faktor_velikosti REAL, v_zakladni_cena_m2 REAL,
    v_zakladni_rucne INTEGER, v_koef_lokalita_pct REAL, v_koef_stav_pct REAL,
    v_koef_vek_pct REAL, v_koef_balkon_pct REAL, v_koef_dalsi_pct REAL,
    v_vek_pouzity REAL, computed_at TEXT
);
"""

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    con.executescript(SCHEMA)
    migruj(con)
    con.commit()
    con.close()
    load_price_map()
    print(f"Databáze připravena: {DB_PATH}")

def load_price_map():
    con = connect()
    con.executescript(SCHEMA)
    try:
        con.execute("ALTER TABLE price_map ADD COLUMN najem_m2_mesic REAL")
    except sqlite3.OperationalError:
        pass  # sloupec už existuje
    now = datetime.now().isoformat(timespec="seconds")
    n = 0
    with open(PRICE_MAP_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            con.execute(
                "INSERT INTO price_map (klic, ctvrt, cena_za_m2_czk, pocet_transakci, najem_m2_mesic, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(klic) DO UPDATE SET ctvrt=excluded.ctvrt, "
                "cena_za_m2_czk=excluded.cena_za_m2_czk, pocet_transakci=excluded.pocet_transakci, "
                "najem_m2_mesic=excluded.najem_m2_mesic, updated_at=excluded.updated_at",
                (row["klic"].strip(), row["ctvrt"].strip(),
                 float(row["cena_za_m2_czk"]), int(row.get("pocet_transakci") or 0),
                 float(row["najem_m2_mesic"]) if row.get("najem_m2_mesic") else None, now))
            n += 1
    con.commit()
    con.close()
    print(f"Cenová mapa nahrána: {n} čtvrtí.")
    return n

# Pole, která import vždy přepíše (jsou v každém výpisu čerstvá).
# Ostatní (stav, rok, balkon, parkování, nájemné…) se při UPDATE zachovají,
# pokud nová hodnota chybí — jinak by denní import mazal dotažené detaily.
PREPSAT_VZDY = {"url", "nazev", "dispozice", "ctvrt", "plocha_m2", "cena_czk",
                "lokalita_auto", "lokalita_skore", "lokalita_detail"}


def upsert_listing(con, d):
    now = datetime.now().isoformat(timespec="seconds")
    data = {k: d.get(k) for k in LISTING_SLOUPCE}
    cols = ", ".join(LISTING_SLOUPCE)
    ph = ", ".join(":" + c for c in LISTING_SLOUPCE)
    upd = ", ".join(
        f"{c}=excluded.{c}" if c in PREPSAT_VZDY else f"{c}=COALESCE(excluded.{c}, {c})"
        for c in LISTING_SLOUPCE if c not in ("source", "external_id"))
    con.execute(
        f"INSERT INTO listings ({cols}, active, first_seen, last_seen) VALUES ({ph}, 1, :now, :now) "
        f"ON CONFLICT(source, external_id) DO UPDATE SET {upd}, active=1, last_seen=excluded.last_seen",
        {**data, "now": now})
