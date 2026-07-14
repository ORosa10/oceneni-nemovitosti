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

**Rozsah (důležité, upřesněno 2026-07-10): projekt řeší VÝHRADNĚ byty k
prodeji v Praze.** Rodinné domy, pozemky, komerční prostory a nemovitosti
mimo Prahu NEJSOU součástí importu ani ocenění — cenová mapa i celý model
jsou kalibrované jen na byty. Když se v datech objeví nabídka, která je
fakticky dům/řadovka prodávaná přes kategorii "byt" (viz bod 8), model ji
i tak počítá bytovým vzorcem — o tom ví bod 8, řešení čeká na uživatele.

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
4. `import-detaily --limit 500` — detail inzerátu
   https://www.sreality.cz/api/v1/estates/{hash_id}, pauza 0,25 s/request.
   POZOR (2026-07-10): limit byl dočasně zvýšen na 4000/den kvůli rychlému
   dotažení počátečního zpoždění; jakmile bylo dosaženo 100% pokrytí, uživatel
   nechal vrátit zpět na 500/den — bezpečnější tempo vůči riziku IP banu ze
   Sreality. NEZVYŠOVAT bez výslovného souhlasu uživatele.
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

**Watchlist a skrytí (2026-07-13)**: stejným GitHub Issue mechanismem teď
jde i jedním kliknutím označit nabídku hvězdičkou (`watchlist`) nebo ji
skrýt z hlavního výpisu (`skryto`) — ikonky přímo v řádku tabulky i
tlačítka v detailu. Na rozdíl od ostatních polí je u těchto dvou prázdná
hodnota rovnou 0 (ne „vrátit na automatiku“ — automatika u nich neexistuje).
Sloupce `listings.watchlist`/`listings.skryto` NEJSOU v `LISTING_SLOUPCE`,
takže je denní import nikdy nepřepíše.

**Oprava (2026-07-13)**: při té příležitosti se zjistilo, že funkce
`ulozUpravu()` byla v `index.html` volaná (`onclick`), ale nikde
definovaná — tlačítko „💾 Uložit“ u ruční úpravy tak reálně nefungovalo
(JS chyba, tichá, appka nespadla). Opraveno — `ulozUpravu()` i sdílené
`otevriIssue()`/`prepni()` teď existují a jsou pokryté smoke testem
(jsdom). Zároveň doplněno předvyplnění selectů aktuální hodnotou nabídky,
aby „Uložit“ bez úprav nesmazalo existující ruční vstupy.

### e) Měsíční aktualizace cenové mapy (cenova_mapa.yml — schváleno 2026-07-10)
Uživatel potvrdil, že `data/price_map.csv` původně vzniklo ze Sreality
Atlasu cen prodaných bytů (`sreality.cz/cenova-mapa`) a odsouhlasil, že se
bude 1× měsíčně automaticky obnovovat ze stejného zdroje.

**Jak se zdroj podařilo najít**: stránka je Next.js appka bez viditelných
API volání ani hrefů v HTML (klasické guessování URL typu
`/cenova-mapa/hlavni-mesto-praha` skončilo 404 — vyzkoušeno přes diagnostiku
v Actions). Uživatel poslal skutečné URL, na které se díval v prohlížeči,
např.:
`sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10/hlavni-mesto-praha-47/praha-3468/josefov-8722`
Z toho vyplynula hierarchie region→okres→obec→městská část
(`{typ}-{entityId}` segmenty). Klíčové zjištění: stačí zavolat URL na úrovni
**regionu** —
`https://www.sreality.cz/cenova-mapa/hledani/byty/hlavni-mesto-praha-10` —
a stránka rovnou vrátí VŠECH ~100 pražských městských částí najednou (v
`<script id="__NEXT_DATA__">` → `pageProps.aggregatedLocalities`, položky s
`entityType:"ward"`), každou s `avgPricePerSqm` a `numTransactions` za
posledních 12 měsíců. Není potřeba procházet 100 jednotlivých URL.

**Implementace**: `scripts/sreality_cenova_mapa.py` stáhne tuto jednu URL,
vytáhne `aggregatedLocalities`, přepíše `data/price_map.csv` (sloupce klic,
ctvrt, cena_za_m2_czk, pocet_transakci) — sloupec `najem_m2_mesic` (ručně
dopočtený, dnes jen Radlice+Dejvice) se VŽDY přenáší beze změny ze
stávajícího CSV, skript ho nikdy nepřepisuje. Pojistka: pokud by Sreality
vrátila méně než 50 čtvrtí (změna struktury stránky), skript skončí chybou
a NIC nepřepíše (žádná tichá náhrada).

Workflow `cenova_mapa.yml`: cron 1. den v měsíci 5:00 UTC + `workflow_dispatch`
pro ruční ověření. Kroky: `init` (pojistka) → `sreality_cenova_mapa.py` →
`cenova-mapa` (nahrání CSV do DB) → `ocenit` (přepočet s novou mapou) →
`build-static` → commit `data/price_map.csv` + DB + `docs/`.

Diagnostické soubory z hledání zdroje (`scripts/_diag_cenova_mapa.py`,
`docs/diag_cenmapa_*.{txt,json}`) byly po dokončení smazány z repa.

### f) Měsíční aktualizace sazby hypotéky (cenova_mapa.yml — schváleno 2026-07-14)
Uživatel navrhl automatizovat i dosud napevno zadanou sazbu hypotéky (4,2 %)
podobně jako cenovou mapu — 1× měsíčně z „hypomonitoru". Po AskUserQuestion
selhání ("Tool permission stream closed") uživatel potvrdil doporučenou
variantu zprávou "Potvrzuji".

**Zdroj**: ČBA Hypomonitor, `cbamonitor.cz/statistika/prumerna-urokova-sazba-novych-hypotek`
— oficiální statistika České bankovní asociace, aktualizovaná cca 1× měsíčně.
Na rozdíl od Sreality cenové mapy (Next.js, JS-rendered) je tahle stránka
vykreslená na serveru, takže stačí obyčejný `requests.get()`.

**Extrakční logika** (`scripts/cba_hypomonitor.py`): hodnota "Aktuální hodnota
pro nové hypotéky" je v HTML PŘED svým popiskem (velké číslo → "%" → teprve
pak text popisku; hned za tím následuje druhý blok "Hodnota minulého měsíce"
se starší hodnotou — snadná záměna, ověřeno na reálném vzorku HTML, kde
aktuální = 4,67 %, minulý měsíc = 4,52 %). Regex proto anchoruje na popisek
a číslo hledá ZPĚTNĚ před ním, ne za ním. Pojistka: hodnota mimo rozsah
1–15 % → chyba, nic se nezapíše (žádná tichá náhrada).

**Implementace**: skript zapíše `data/sazba_hypoteky.csv` (sloupce sazba_pct,
datum_aktualizace, zdroj). `src/valuation.py` načítá `SAZBA` přes
`nacti_sazbu_hypoteky()` — pokud soubor chybí nebo je hodnota mimo rozumný
rozsah, použije se záložní konstanta `SAZBA_ZALOZNI = 0.042` (stejná jako
původní napevno zadaná hodnota). Samotný vzorec splátky v `valuation.py` se
nezměnil, jen zdroj vstupní sazby.

Workflow: krok `python scripts/cba_hypomonitor.py` přidán do
`cenova_mapa.yml` (přejmenováno na "Měsíční aktualizace cenové mapy a sazby
hypotéky"), hned po nahrání cenové mapy do DB. Commit kroku doplněn o
`data/sazba_hypoteky.csv`.

**Vedlejší nález a oprava — concurrency bug (exit 128)**: při ručním ověření
workflow selhal na `git push` (exit 128). Diagnóza: `workflow_dispatch`
zafixuje SHA při zařazení běhu do fronty, ne při skutečném startu; když běh
čekal ve frontě za souběžně běžící denní pipeline (sdílený concurrency zámek
`aktualizace-dat`), checkout byl při skutečném spuštění zastaralý. Lokální
změny (DB, docs/) se pak srazily s mezitím posunutým main při
`git pull --rebase`, což kvůli `|| true` fallbacku prošlo tiše dál do
rozbitého stavu a `git push` spadl. **Oprava**: do obou workflow (`update.yml`
i `cenova_mapa.yml`) přidán krok `git fetch origin main && git reset --hard
origin/main` hned po checkoutu — běh vždy začíná z opravdu nejnovějšího
main. Po opravě proběhl ruční test úspěšně.

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

4 733 aktivních nabídek, detaily dotažené u všech (100 %). Z toho 168
v kategorii „bez ceny" (Sreality „cena na vyžádání" — úmyslně zachovaná
kategorie, nedeaktivuje se). Oceněno (tabulka valuations) 4 565 nabídek.
Nájemné MFČR načtené pro 112 katastrálních území. Lokalita: ~8 % nabídek
+5 %, ~84 % standard, ~7 % −5 % — symetrické dle kalibrace v bodě 5c.
Neaktivních (zmizelých ze Sreality + nově i bez shody v cenové mapě, viz
bod 8.3) je celkem 344. DB, data.json i appka jsou v sync s posledním
denním během.

## 8. OTEVŘENÉ BODY (další práce)

1. **Scheduled task v Coworku** „tydenni-report-prilezitosti" (pondělí 8:00)
   je ZASTARALÝ — dělá lokální import, který dnes řeší GitHub. Uživatel chce
   rozhodnout o novém pojetí „až bude jasné, co chceme a můžeme". Nabízené
   varianty: ranní/týdenní přehled top příležitostí z docs/data.json do chatu,
   hlídání nových nabídek nad prahem slevy, sledování zlevnění. Task smazat
   nebo předělat přes update_scheduled_task.
2. **Kalibrace lokality** pokračuje podle zpětné vazby (viz zásada v 5c).
3. ~~**Nabídky bez shody v cenové mapě**~~ — VYŘEŠENO 2026-07-07: bylo
   198 nabídek (typicky „Praha 5" bez konkrétní čtvrti, nebo pár okrajových
   čtvrtí mimo 99 ze sheetu jako Lipence/Královice/Koloděje). Uživatel
   rozhodl nebudovat náhradní mapování (příliš málo případů) a nabídky
   rovnou deaktivovat — viz `ocenit_vse()` ve `valuation.py`, trvale
   zapojeno do denní pipeline (deaktivuje se to samo i u budoucích nových
   nabídek se stejným problémem).
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
  a velké zápisy nástrojem Write se někdy synchronizují ořezané. Pracuj
  v klonu v /tmp (např. /tmp/push), commituj do repa, a změněné soubory
  VŽDY zkopíruj i zpět do připojené složky (cp přes shell je spolehlivý).
- **Workflow konvence:** před prací vždy `git fetch && reset --hard origin/main
  && clean -fd` (v /tmp klonu se hromadí smetí a pushe pak padají).
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
- 2026-07-09: opravena URL na Sreality (skutečný SEO slug místo placeholderu
  x/x) a opravena appka, která zamrzávala u 4600+ nabídek (omezeno vykreslení
  tabulky na 400 řádků).
- 2026-07-10: uživatel upřesnil, že projekt/model je VÝHRADNĚ pro byty (bod 1)
  — domy/pozemky nejsou a nebudou tiše zahrnuty do "hotovo". Uživatel také
  nechal snížit `import-detaily` zpět na 500/den kvůli riziku IP banu ze
  Sreality (dočasné zvýšení na 4000/den bylo jen pro rychlé dotažení
  počátečního dluhu, ne trvalé nastavení).
- 2026-07-10: uživatel potvrdil zdroj `data/price_map.csv` (Sreality Atlas
  cen prodaných bytů, `sreality.cz/cenova-mapa`) a schválil 1× měsíční
  automatickou aktualizaci ze stejného zdroje. Implementováno jako
  `scripts/sreality_cenova_mapa.py` + `.github/workflows/cenova_mapa.yml`
  (viz bod 5e). Skutečnou URL hierarchii poskytl sám uživatel (odhadování
  URL v Actions selhávalo na 404).
- 2026-07-10: detail nabídky v appce byl „moc skoupý" — doplněna karta
  „Postup výpočtu tržní hodnoty" ukazující celý řetězec (cena z mapy →
  faktor velikosti → základní cena/m² → koeficienty lokalita/stav/věk/
  balkon/další → výsledná cena/m² → cena za byt → příplatky → tržní
  hodnota). Samotný výpočet v `valuation.py` se nezměnil, jen se nově
  ukládají a zobrazují mezivýsledky (nové `v_*` sloupce v `valuations`).
- 2026-07-13: starý naplánovaný Coworkový úkol „tydenni-report-prilezitosti"
  (lokální import, dnes nefunkční — sandbox nemá přístup na Sreality)
  přepsán na čtení hotových dat z `docs/data.json` na GitHubu a zaslání
  souhrnu top 10 nových příležitostí za týden přímo do chatu (bez e-mailu —
  dostupný Gmail konektor umí jen draft, ne odeslání; uživatel zvolil chat).
- 2026-07-13: přidán watchlist (hvězdička) a skrytí nabídky (bod 5d), a
  cestou opravena reálně nefunkční funkce `ulozUpravu()` v appce (viz 5d).
  Zároveň opakovaně narazeno na známý bug „mount sync/truncation" (bod 9)
  — tentokrát postihl `src/db.py` i `scripts/aplikuj_upravu.py` po Edit
  nástroji; `python -m py_compile` to NEODHALÍ (useknutý soubor může
  skončit na syntakticky platném místě, např. osamocený identifikátor —
  jen se nic nestane za běhu). Napříště: po každé netriviální Edit dávce
  na klíčové soubory ověřit přes bash byte-přesně (`tail -c`, porovnat
  poslední řádek s očekávaným koncem funkce), ne jen že `py_compile`
  neshodí chybu.
- 2026-07-14: schválena ("Potvrzuji") 1× měsíční automatická aktualizace
  sazby hypotéky z ČBA Hypomonitoru (bod 5f), se záložní hodnotou 4,2 % při
  chybě/nedostupnosti zdroje. Cestou nalezen a opraven concurrency bug
  (exit 128 na git push) v obou měsíčních/denních workflow — viz bod 5f.
