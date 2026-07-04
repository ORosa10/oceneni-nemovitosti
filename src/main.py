# CLI vstupní bod. Spouštět z kořene projektu: python -m src.main <příkaz>
import argparse

from . import db


def main():
    ap = argparse.ArgumentParser(prog="ocenovani",
        description="Databáze nemovitostí a hledání podhodnocených příležitostí")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="založí databázi a nahraje cenovou mapu")
    sub.add_parser("cenova-mapa", help="znovu nahraje data/price_map.csv do DB")

    p = sub.add_parser("import-file", help="import nabídek z CSV/XLSX")
    p.add_argument("cesta")

    p = sub.add_parser("import-sreality", help="import ze Sreality URL vyhledávání")
    p.add_argument("url")
    p.add_argument("--max-stranek", type=int, default=5)

    sub.add_parser("ocenit", help="spočítá tržní hodnotu všech aktivních nabídek")

    p = sub.add_parser("prilezitosti", help="vypíše podhodnocené nabídky")
    p.add_argument("--min-sleva", type=float, default=10.0)
    p.add_argument("--export", help="cesta k CSV/XLSX exportu")

    sub.add_parser("build-static", help="vygeneruje statickou appku do docs/ (GitHub Pages)")

    p = sub.add_parser("app", help="spustí webovou aplikaci")
    p.add_argument("--port", type=int, default=8000)

    a = ap.parse_args()

    if a.cmd == "init":
        db.init_db()
    elif a.cmd == "cenova-mapa":
        db.load_price_map()
    elif a.cmd == "import-file":
        from . import importers
        importers.import_file(a.cesta)
    elif a.cmd == "import-sreality":
        from . import sreality
        sreality.import_sreality(a.url, a.max_stranek)
    elif a.cmd == "ocenit":
        from . import valuation
        valuation.ocenit_vse()
    elif a.cmd == "prilezitosti":
        from . import report
        report.prilezitosti(a.min_sleva, a.export)
    elif a.cmd == "build-static":
        from . import build_static
        build_static.build()
    elif a.cmd == "app":
        from . import app as webapp
        webapp.run(a.port)


if __name__ == "__main__":
    main()
