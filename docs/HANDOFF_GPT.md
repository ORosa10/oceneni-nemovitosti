# Handoff pro ChatGPT — Ocenění nemovitostí

> **▶ START ZDE (GPT):** Tenhle projekt už NEPOTŘEBUJE Claude. Týdenní report
> se generuje sám v **GitHub Actions** a ukládá se do repa jako
> `docs/weekly_report.md`. ChatGPT jen ten hotový (malý) soubor přečte a ukáže
> ti ho — viz „ChatGPT Task" níže. (Původní Claude verze je v
> `docs/HANDOFF_SCHEDULED_TASKS.md`, ta je už jen historická.)

Last updated: 2026-09-22

## Jak to teď funguje (bez jakéhokoli AI)
1. **Denní pipeline** (`.github/workflows/update.yml`) jako dřív stáhne data ze
   Sreality, ocení je a přepíše `docs/data.json`. Běží na GitHubu, mimo AI.
2. **Týdenní report** (`.github/workflows/weekly_report.yml`, cron pondělí
   06:00 UTC) spustí `scripts/weekly_report.py`, který z `docs/data.json`
   vybere top 10 nových podhodnocených bytů za 7 dní zvlášť pro Prahu a Střední
   Čechy (stejný filtr jako původní úloha) a commitne výsledek do
   **`docs/weekly_report.md`**. Žádný token/klíč, žádné AI.

Report je pak veřejně tady (malý soubor, ~pár kB):
`https://raw.githubusercontent.com/ORosa10/oceneni-nemovitosti/main/docs/weekly_report.md`
(a přes GitHub Pages: `https://orosa10.github.io/oceneni-nemovitosti/weekly_report.md`)

## ChatGPT Task (volitelné doručení do chatu)
V ChatGPT appce založ **Task** (Scheduled task), rozvrh **pondělí ráno**, s tímto
promptem:

```
Jsi naplánovaná úloha v ChatGPT. Každé pondělí ráno:
1. Otevři (browsing) tento soubor:
   https://raw.githubusercontent.com/ORosa10/oceneni-nemovitosti/main/docs/weekly_report.md
2. Je to už HOTOVÝ týdenní report v Markdownu (top 10 podhodnocených bytů pro
   Prahu a pro Střední Čechy). Zobraz mi jeho obsah v češtině tak, jak je —
   nadpisy, oba seznamy i odkazy zachovej, nepřepisuj čísla, nic nedomýšlej.
3. Když je v hlavičce "Data vygenerována" datum starší než 8 dní, napiš mi
   nahoru upozornění, že se možná nespustila denní/týdenní pipeline, a report
   stejně ukaž.
4. Když soubor nejde stáhnout, napiš to jasně místo tichého selhání.
Buď stručný, žádné dlouhé úvody.
```

## Jak něco změnit
- **Rozvrh:** uprav `cron` v `.github/workflows/weekly_report.yml`.
- **Filtr / formát / počet:** uprav `scripts/weekly_report.py` (konstanty
  `WINDOW_DAYS`, `TOP_N`, funkce `select`/`line`). Oceňovací logika se tu NEŘEŠÍ
  — ta zůstává výhradně v `src/valuation.py` (CLAUDE.md hard rules).
- **Ruční spuštění:** GitHub → Actions → „Týdenní report příležitostí" → Run workflow.

## Měsíční přehled (artefakt) — na GPT odpadá
Původní úloha `oceneni-prehled-refresh` obnovovala Cowork **artefakt**, což je
funkce Claude/Coworku a v ChatGPT ekvivalent nemá. Náhrada: používej rovnou
živou appku `https://orosa10.github.io/oceneni-nemovitosti/` (stejná data,
aktualizuje se denně sama), případně `docs/weekly_report.md`. Pokud bys chtěl
i statický měsíční „přehled" v repu, dá se doplnit stejným způsobem jako
týdenní report (Action + malý skript) — řekni si.
