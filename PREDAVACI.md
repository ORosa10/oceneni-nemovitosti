# PŘEDÁVACÍ PROTOKOL — Ocenění nemovitostí (stav k 7. 7. 2026)

Pro novou session: přečti nejdřív `CLAUDE.md` (závazná pravidla, hard rules),
potom celý tento soubor. Pak teprve pracuj. Komunikace s uživatelem česky,
po jedné věci, každou změnu metodiky nechat výslovně schválit.

---

## 1. CO PROJEKT DĚLÁ (jednou větou)

Každý den automaticky stáhne všechny inzeráty bytů na prodej v Praze ze
Sreality.cz, spočítá jejich tržní hodnotu podle uživatelova oceňovacího
modelu a ve webové appce ukáže, které nabídky jsou podhodnocené (sleva vůči
tržní hodnotě) a jaký mají nájemní výnos. Uživatel nic nespouští — vše běží
na serverech GitHubu.

## 2. ODKAZY A UMÍSTĚNÍ

| Co | Kde |
|---|---|
| Webová appka (výsledek pro uživatele) | https://orosa10.github.io/oceneni-nemovitosti/ |
| Repozitář (kód + data, public!) | https://github.com/ORosa10/oceneni-nemovitosti |
| Běhy automatizace (Actions) | https://github.com/ORosa10/oceneni-nemovitosti/actions |
| Ruční úpravy nabídek (Issues) | https://github.com/ORosa10/oceneni-nemovitosti/issues |
| Lokální kopie | tato připojená složka „Ocenění nemovitostí" |
| Původní model uživatele | Oceneni_Byt_InSheetTables.xlsx — export jeho Google Sheetu; nahrává do chatu, NENÍ v repu |
| Původní zadání | Report_pro_Codex_Google_Sheets_App.docx — jen ke čtení, není v repu (public repo!) |
| Zdroj nájemného | https://mf.gov.cz/cs/rozpoctova-politika/podpora-projektoveho-rizeni/cenova-mapa/cenova-mapa-infografika |

GitHub účet uživatele: **ORosa10** (přihlášený v Edge). Repo je PUBLIC —
nikdy do něj nedávat citlivé soubory.

## 3. OCEŇOVACÍ MODEL (CORNERSTONE — nikdy neměnit bez souhlasu)

Převzat 1:1 z uživatelova sheetu (list Praha), ověřen proti přepočtu
v LibreOffice na korunu. Kompletní implementace: `src/valuation.py`
(komentáře odkazují na sloupce/buňky původního sheetu).

```
tržní hodnota = plocha × základní_cena/m² × Π(1+koef) + příplatek_parkování

základní cena/m²   = ručně zadaná, jinak cenová mapa čtvrti (data/price_map.csv,
                     99 čtvrtí z uživatelova sheetu) × faktor velikosti bytu
                     (lineární křivka 40 m²→1,101 / 57 m²→0,967 / 75 m²→0,943,
                     z listu „Cenová mapa" sheetu)
koef lokalita      = +5 / 0 / −5 %  (viz bod 5c)
koef stav          = 0 % běžná údržba/novostavba; +3 % částečná rekonstrukce
                     ≤10 let; +6 % generální rekonstrukce ≤10 let
koef věk           = interpolace dekádových pásem +10 % (0 let) → −12 % (80+),
                     věk = min(rok_ocenění − rok_výstavby, 80); záporný věk
                     (kolaudace v budoucnu) = 0 let; bez roku = koef 0
koef balkon        = +1,01 % pokud balkon/terasa/lodžie
další koef         = ruční sloupec uživatele (default 0)
příplatek parkování= +400 000 Kč („Ano"), +800 000 Kč („Ano 2*")

sleva = −(cena/tržní − 1) × 100   … kladná = nabídka POD tržní hodnotou
příležitost = sleva ≥ práh (výchozí 10 %)
```

Výnosová část (jen když je známé nájemné a dispozice):
roční nájem = nájemné_Kč/m²/měs × 10 (obsazenost 10/12) × koef × plocha
+ příplatky; prostý výnos = roční/cena; IRR 20 let (růst nájmu i ceny 5 %,
amortizace 0,3×tržní×1,05^10); hypotéka LTV 80 %, sazba 4,2 %, 30 let,
pokrytí splátky nájmem. Konstanta ROK_OCENENI = 2025 (dle sheetu).

## 4. STRUKTURA REPOZITÁŘE

```
CLAUDE.md                    pravidla projektu (hard rules!)
PREDAVACI.md                 tento soubor
README.md                    návod pro člověka
requirements.txt             pandas, openpyxl, requests, flask
data/
  nemovitosti.db             SQLite — JE verzovaná v gitu (Actions ji commitují)
  price_map.csv              cenová mapa 99 čtvrtí (klic, ctvrt, cena_za_m2_czk,
                             pocet_transakci, najem_m2_mesic) — z uživatelova sheetu
  najemne_mfcr.csv           nájemné MFČR: 112 katastrálních území × 4 dispozice
                             (generuje scripts/mfcr_najemne.py, aktualizuje se samo)
  lokalita_matice.csv        bodovací matice lokality + prahy (KALIBRUJE SE ZDE)
docs/                        GitHub Pages — statická appka
  index.html                 UI (kopíruje se ze src/static/index.html)
  data.json                  všechna data pro appku (generuje build_static)
  import_log.txt, detail_log.txt, ocenit_log.txt, build_log.txt
                             logy posledního běhu — TAKHLE SE ČTOU VÝSLEDKY AUTOMATIZACE
src/
  db.py                      schéma DB, migrace, upsert (COALESCE logika — bod 6!)
  sreality.py                import výpisu + POI skórování lokality + deaktivace zmizelých
  sreality_detail.py         dotažení detailu inzerátu → stav/rok/balkon/parkování
  valuation.py               CORNERSTONE — jediné místo s oceňovací logikou
  importers.py               ruční import CSV/XLSX
  report.py                  CLI výpis/export příležitostí
  build_static.py            DB → docs/data.json + index.html
  app.py                     lokální Flask varianta (volitelná)
  main.py                    CLI: init, import-sreality, import-detaily, ocenit,
                             prilezitosti, cenova-mapa, build-static, app
scripts/
  mfcr_najemne.py            extrakce nájemného z MFČR mapy (leaflet HTML)
  aplikuj_upravu.py          zápis ruční úpravy z GitHub Issue do DB
.github/workflows/
  update.yml                 denní pipeline (viz bod 5a)
  uprava.yml                 zpracování ručních úprav (viz bod 5d)
```

## 5. JAK AUTOMATIZACE FUNGUJE

### a) Denní pipeline (update.yml)
Spouští se: denně 4:00 UTC, při každém pushi do main, ručně tlačítkem
(Actions → Run workflow). Concurrency zámek „aktualizace-dat" — bez něj
běhy padaly na kolizi git push. Kroky:
1. `init` — DB + cenová mapa
2. `import-sreality` — výpis přes https://www.sreality.cz/api/v1/estates/search
   (parametry category_main_cb=1, category_type_cb=1, locality_region_id=10,
   limit/offset po 100; STARÉ /api/cs/v2 API JE ZRUŠENÉ — vrací 404).
   Součástí: POI skórování lokality a po kompletním průchodu deaktivace
   nabídek, které z trhu zmizely (active=0; mazat se NIKDY nesmí).
   Nabídky „cena na vyžádání" (Sreality posílá 1 Kč) → cena_czk=NULL,
   speciální kategorie bez ceny (v appce checkbox).
3. extrakce nájemného MFČR (jen když se změní mapa na mf.gov.cz)
4. `import-detaily --limit 4000` — detail inzerátu
   https://www.sreality.cz/api/v1/estates/{hash_id}, pauza 0,25 s/request
5. `ocenit` → 6. `build-static` → 7. commit DB + docs/ zpět do repa
Všechny kroky logují do docs/*.txt (continue-on-error u importů).

### b) Mapování detailu Sreality → vstupy modelu (schváleno 6. 7.)
- stav: „Po rekonstrukci" → generální +6 % (pokud rekonstrukce ≤10 let či rok
  neuveden, jinak 0); „Částečně po rekonstrukci" → částečná +3 % (stejně);
  vše ostatní (novostavba, velmi dobrý, špatný…) → 0 %
- rok výstavby: object_age → acceptance_year → rok z finish_date;
  novostavba/ve výstavbě/projekt bez roku → aktuální rok (věk 0)
- balkon: balcony NEBO terrace NEBO loggia → „Ano"
- parkování: ≥2 stání/garáže → „Ano 2*"; jakékoli stání/garáž → „Ano"; jinak „Ne"

### c) Koeficient lokality — POI matice (schváleno + kalibrováno 6. 7.)
Sreality výpis posílá vzdálenosti k POI (poi_metro_distance atd.). Matice
v `data/lokalita_matice.csv` dává body: metro ≤500 m +2 / ≤1000 m +1 /
>1500 m −1; MHD ≤300 m +1 / >800 m −1; obchod ≤500 m +1 / >1000 m −1;
škola ≤800 m +1; lékař ≤1000 m +1; park/hřiště ≤600 m +1; železnice ≤250 m −2.
Prahy (poslední 2 řádky CSV): skóre ≥7 → +5 % (~8 % nabídek), ≤1 → −5 %
(~7 %), jinak 0 %. KALIBRAČNÍ ZÁSADA od uživatele: průměr koeficientu přes
trh ≈ 0, jen extrémy smí dostat ±5 % (žádná skewness). Změna matice = upravit
CSV + push; skóre se přepočítá dalším importem. Rozpad skóre je vidět
v detailu nabídky v appce (lokalita_detail).

### d) Ruční úpravy nabídek (uprava.yml + formulář v appce)
V detailu nabídky v appce je karta „✏️ Upravit vstupy" (stav, rok, balkon,
parkování, lokalita, další koef, nájemné, základní cena/m²). Uložení otevře
předvyplněné GitHub Issue s titulkem `uprava:<id>` a JSON tělem; uživatel
klikne „Submit new issue"; workflow úpravu zapíše, přepočítá, publikuje
a issue zavře. Bezpečnost: přijímají se jen issues od vlastníka repa.
Prázdné pole = vrátit na automatiku (NULL).

## 6. PRIORITY HODNOT A OCHRANA RUČNÍCH VSTUPŮ (klíčové!)

Ruční hodnota u nabídky > automatika (detail Sreality / MFČR / POI matice).
Technicky: `db.upsert_listing` při denním importu přepisuje jen pole
z výpisu (url, nazev, dispozice, ctvrt, plocha, cena, lokalita_auto+skóre);
VŠECHNA ostatní pole se aktualizují přes `COALESCE(excluded.c, c)` — tzn.
nikdy se nepřepíšou na NULL/default. `import-detaily` zpracovává jen řádky
s `detail_at IS NULL`, takže jednou dotažené (či ručně upravené) hodnoty
už nepřepisuje. Při jakémkoli zásahu do importů TOHLE NEROZBÍT.

Nájemné: ruční `najem_m2_mesic` u nabídky > tabulka MFČR (čtvrť × skupina
dispozice: 1+kk/1+1, 2+kk/2+1, 3+kk/3+1, 4+ a víc). Bez dispozice se výnos
nepočítá — žádné odhadování (výslovný požadavek uživatele).

## 7. STAV DAT K PŘEDÁNÍ

4 934 aktivních nabídek, detaily dotažené u všech 4 934 (100 %). Z toho
168 v kategorii „bez ceny" (Sreality „cena na vyžádání"). Oceněno (tabulka
valuations) 4 701 nabídek — zbytek nemá cenu/plochu, nebo má čtvrť mimo
99 čtvrtí cenové mapy (~12 takových čtvrtí/oblastí, typicky jen „Praha 5"
bez konkrétní čtvrti). Nájemné MFČR načtené pro 112 katastrálních území.
Lokalita: 8,2 % nabídek +5 % (405 ks), 84,4 % standard (4 164 ks), 7,4 %
−5 % (365 ks) — symetrické dle kalibrace v bodě 5c. Neaktivních (zmizelých/
deaktivovaných) je celkem 142 z 5 076 řádků historie. DB, data.json i appka
jsou v sync s posledním denním během.

## 8. OTEVŘENÉ BODY (další práce)

1. **Scheduled task v Coworku** „tydenni-report-prilezitosti" (pondělí 8:00)
   je ZASTARALÝ — dělá lokální import, který dnes řeší GitHub. Uživatel chce
   rozhodnout o novém pojetí „až bude jasné, co chceme a můžeme". Nabízené
   varianty: ranní/týdenní přehled top příležitostí z docs/data.json do chatu,
   hlídání nových nabídek nad prahem slevy, sledování zlevnění. Task smazat
   nebo předělat přes update_scheduled_task.
2. **Kalibrace lokality** pokračuje podle zpětné vazby (viz zásada v 5c).
3. **~200 nabídek bez čtvrti** (Sreality uvádí jen „Praha 5" apod.) se
   neoceňuje. Možné řešení: mapování městská část → vážený průměr jejích
   čtvrtí — JEN po schválení uživatelem.
4. **List MimoPrahu** ze sheetu není implementován (jiná města).
5. **Rok výstavby** u většiny inzerátů chybí (inzerenti neuvádějí) → koef
   věku 0. Případné dohledávání (katastr…) jen po dohodě.
6. **Historie cen** — evidují se first_seen/last_seen, ale ne změny cen;
   uživatel dřív projevil zájem (zlevněné nabídky = motivovaný prodejce).

## 9. PROVOZNÍ POZNÁMKY PRO AGENTA (ušetří hodiny)

- **Sandbox NEMÁ přístup** na sreality.cz, mf.gov.cz ani api.github.com.
  Ověřování dat/API dělej PŘES GITHUB ACTIONS: přidej dočasný krok, který
  vypíše výstup do docs/*.txt, pushni, počkej ~2–10 min na commit „Denní
  aktualizace dat", pak si log stáhni gitem (`git checkout origin/main -- docs/...`).
- **git push funguje** (github.com je povolený). Autentizace: OAuth device
  flow s client_id GitHub CLI (uživatel potvrdí kód na github.com/login/device);
  token ulož do /tmp, remote `https://x-access-token:TOKEN@github.com/...`.
  Token z minulé session NEPŘEŽIL — bude potřeba nový device flow.
- **Na připojené složce nefunguje SQLite zápis ani git** (mount omezení)
  a velké zápisy nástrojem Write se někdy synchronizují ořezané — OVĚŘ TO
  VŽDY po zápisu (přečti si soubor zpět, zkontroluj počet řádků/konec textu).
  Bezpečnější je psát rovnou v sandboxu (`/tmp/push` klon nebo heredoc přes
  bash) a teprve hotový, ověřený obsah kopírovat/zapisovat do připojené
  složky — ne naopak (kopírovat Z připojené složky DO sandboxu je náchylné
  na zpoždění synchronizace mountu a může vrátit starý obsah).
- **Workflow konvence:** před prací vždy `git fetch && reset --hard origin/main
  && clean -fd` (v /tmp klonu se hromadí smetí a pushe pak padají).
- **GitHub je zdroj pravdy pro produkci** — Actions běží z GitHubu, ne
  z připojené složky. Při pochybnosti o aktuálním stavu kódu/dat vždy
  ověřit `raw.githubusercontent.com/ORosa10/oceneni-nemovitosti/main/<soubor>`.
- Mazání souborů v připojené složce vyžaduje povolení (allow_cowork_file_delete).
- Sreality API je neoficiální — když se rozbije, diagnostika přes Actions
  (viz výše). Struktura odpovědí zdokumentovaná v kódu.

## 10. HISTORIE KLÍČOVÝCH ROZHODNUTÍ UŽIVATELE

- Google Sheet je jen inspirace/zdroj logiky; vše běží lokálně/na GitHubu.
- Model ze sheetu je cornerstone — změny jen s výslovným souhlasem.
- HARD RULE „žádné tiché náhrady": když něco nejde přesně dle zadání,
  ZASTAVIT SE a zeptat. (Vzniklo po incidentu s odvozenými nájmy, které
  jsem doplnil bez schválení — uživatel je nechal odstranit a nahradit
  skutečnými daty MFČR.)
- Nabídky se nikdy nemažou, jen active=0.
- Koeficient lokality: průměr trhu ≈ 0, jen extrémy ±5 %.
- Detaily Sreality → vstupy modelu dle mapování v bodě 5b (schváleno).
- Nájemné MFČR dle čtvrti × dispozice (schváleno), ruční hodnota vítězí.
- 2026-07-07: přechod chatu z modelu Fable 5 na Sonnet 5 (v téže session/
  projektu, bez zakládání nové konverzace); protokol doplněn a čísla v
  bodě 7 aktualizována k tomuto dni.
