# Předávací shrnutí projektu (k 6. 7. 2026)

Nová session: přečti nejdřív CLAUDE.md (pravidla, hard rules), pak tento soubor.

## Co to je
Automatizovaná appka „vlastní Sreality": denně stahuje všechny pražské byty
ze Sreality, oceňuje je uživatelovým modelem (cornerstone z jeho Google Sheetu,
NIKDY neměnit bez souhlasu) a hledá podhodnocené příležitosti. Běží samo na
GitHubu, uživatel nic nespouští.

## Odkazy
- Appka (GitHub Pages): https://orosa10.github.io/oceneni-nemovitosti/
- Repozitář: https://github.com/ORosa10/oceneni-nemovitosti
- Běhy (Actions): https://github.com/ORosa10/oceneni-nemovitosti/actions
- Lokální kopie = tato složka (synchronizovat s repem při změnách!)
- Zdroj modelu: Oceneni_Byt_InSheetTables.xlsx (uživatel nahrává do chatu; list Praha)
- Zdroj nájemného: cenová mapa MFČR (mf.gov.cz → cenova-mapa-infografika)

## Architektura
GitHub Actions (denně 4:00 UTC + při pushi, workflow update.yml):
import Sreality (/api/v1/estates/search, staré v2 API zrušeno) → extrakce
nájemného MFČR → dotažení detailů nabídek (stav, rok, balkon, parkování;
--limit 4000) → ocenit → build-static → commit. Pages servírují docs/
(statická appka nad docs/data.json). Ruční úpravy nabídek: GitHub Issue
„uprava:<id>" (vytváří formulář v appce) → workflow uprava.yml zapíše a přepočítá.

## Stav dat (k předání)
~4 900 aktivních nabídek; detaily dotaženy u ~1 500 + běžel velký běh na zbytek
(ověřit!). Nájemné MFČR: 112 území × 4 dispozice (data/najemne_mfcr.csv).
Lokalita: POI matice (data/lokalita_matice.csv), kalibrace: +5 % od 7 b. (8 %
nabídek), −5 % do 1 b. (7 %), jinak 0 — záměr: průměr ≈ 0, žádná skewness.
Zmizelé nabídky se deaktivují (active=0, nikdy nemazat). „Cena na vyžádání" =
kategorie bez ceny (checkbox v appce).

## Priority hodnot (dohodnuto)
ruční hodnota u nabídky > automatika (detail Sreality / MFČR / POI matice).
Denní import nesmí přepsat dotažené/ruční hodnoty (COALESCE v db.upsert_listing).

## Otevřené body
1. Ověřit doběhnutí velkého dotažení detailů (Actions) a pokrytí v appce.
2. Odložený scheduled task v Coworku „tydenni-report-prilezitosti" (pondělí 8:00)
   — je zastaralý (dělá lokální import, který dnes řeší GitHub); předělat na
   přehled top příležitostí z docs/data.json do chatu, nebo smazat. Uživatel
   chtěl rozhodnout, „až bude jasné, co chceme a můžeme".
3. Kalibrace lokalita_matice.csv pokračuje dle zpětné vazby uživatele.
4. ~200 nabídek bez čtvrti (Sreality uvádí jen „Praha 5" apod.) se neoceňuje —
   možné mapování MČ → průměr čtvrtí (jen se souhlasem!).
5. List MimoPrahu ze sheetu není implementován.
6. Rok výstavby chybí u většiny inzerátů (inzerenti neuvádějí) — koef věku 0.

## Ponaučení pro práci (kromě hard rules v CLAUDE.md)
- Sandbox nemá přístup na sreality.cz ani mf.gov.cz — testovat přes GitHub
  Actions (log do docs/*.txt, číst přes git).
- SQLite/git nefungují na připojené složce v sandboxu — pracovní kopie /tmp/push,
  změny commitovat do repa A kopírovat zpět do složky.
- api.github.com je z sandboxu blokované; git push funguje (token z device flow).
- Workflow mají concurrency zámek „aktualizace-dat" (jinak padají na push race).
