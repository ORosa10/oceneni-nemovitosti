# PŘEDÁVACÍ PROTOKOL — Ocenění nemovitostí (stav k 7. 7. 2026)

Pro novou session: přečti nejdřív `CLAUDE.md` (závazná pravidla, hard rules),
potom celý tento soubor. Pak teprve pracuj. Komunikace s uživatelem česky,
po jedné věci, každou změnu metodiky nechat výslovně schválit.

---

## 1. CO PROJEKT DĚLÁ (jednou větou)

Každý den automaticky stáhne všechny inzeráty bytů na prodej v Praze a
(od 2026-08) velkých městech Středočeského kraje ze Sreality.cz, spočítá
jejich tržní hodnotu podle uživatelova oceňovacího modelu a ve webové
appce ukáže, které nabídky jsou podhodnocené (sleva vůči tržní hodnotě)
a jaký mají nájemní výnos. Uživatel nic nespouští — vše běží na serverech
GitHubu.

**Rozsah (upřesněno 2026-07-10, rozšířeno 2026-08): projekt řeší VÝHRADNĚ
byty k prodeji.** Rodinné domy, pozemky, komerční prostory NEJSOU součástí
importu ani ocenění — cenová mapa i celý model jsou kalibrované jen na
byty. Geograficky: Praha (všech ~99 čtvrtí) + velká města Středočeského
kraje nad 5000 obyvatel (42 měst, viz sekce 10, 2026-08) — MENŠÍ obce
Středočeského kraje se importují (celý kraj), ale nemají cenovou mapu,
takže se automaticky deaktivují (žádná "tichá náhrada" — stejný mechanismus
jako u pražských nabídek bez shody ve čtvrti). Když se v datech objeví
nabídka, která je fakticky dům/řadovka prodávaná přes kategorii "byt"
(viz bod 8), model ji i tak počítá bytovým vzorcem — o tom ví bod 8,
řešení čeká na uživatele.

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

### g) Vlastnictví, anuita a doplňkové informace z detailu (2026-07-15)
Uživatel si hrál s appkou a navrhl tři vylepšení filtrů: rozsah slevy (ne jen
minimum), filtr na vlastnictví (osobní/družstevní), a red-flag na nesplacenou
anuitu u družstevních bytů. Provedena diagnostika přes Actions proti reálným
datům ze Sreality (dočasný skript `scripts/_diag_pole.py`, smazán po dokončení):

- **Vlastnictví**: pole `ownership.name` v detailu Sreality vrací přímo
  "Osobní" / "Družstevní" / "Státní/obecní" — stejné hodnoty jako filtr na
  samotném Sreality.cz. Spolehlivé, žádná heuristika potřeba.
- **Anuita**: pole `annuity` ze Sreality NENÍ použitelné — u ověřených
  vzorků vždy `0`/`null`, i když text popisu jasně mluví o konkrétní
  nesplacené částce (např. "nesplacená anuita ve výši přibližně 670 000 Kč").
  Stav anuity se proto odvozuje HEURISTIKOU z volného textu
  `advert_description` (klíčová slova "nesplacen"/"neuhrazen"/"zbývá
  doplatit" → red flag; "splacen"/"uhrazen"/"vypořádán" → v pořádku;
  zmíněno, ale nejednoznačné → "neznámo"; nezmíněno vůbec → nelze určit).
  Otestováno na 7 reálných textech ze Sreality, všechny prošly správně.
  V appce jasně označeno jako heuristika, ne jistota.
- Sleva: doplněn horní limit vedle spodního (stejný `row2` vzor jako cena/
  plocha).

Uživatel se dále zeptal, jestli by šlo odhadnout stáří domu z fotky (AI
vision). Zamítnuto — přesnost by byla hrubá (dekády, ne konkrétní rok) a
CORNERSTONE koeficient věku je na přesnost citlivý; chybný odhad by mohl
zkreslit hodnotu hůř, než když rok chybí a koeficient je 0. Navíc by šlo
o odvozený/odhadnutý vstup bez jistoty — přesně proti hard rule "žádné
tiché náhrady". Neimplementováno.

Následně uživatel navrhl využít stejný denní screening (detail inzerátu,
stejně jako pro vlastnictví/anuitu) k dotažení dalších polí, která Sreality
posílá zdarma spolu s detailem. Ověřeno diagnostikou, uživatel vybral:
energetický štítek (PENB, pole `energy_efficiency_rating_cb`) a sadu
"patro/výtah/sklep/zahrada/typ stavby" (pole `floor_number`, `floors`,
`elevator`, `cellar`, `cellar_area`, `garden_area`, `building_type`). Navíc
doplněno `datum_vlozeni` (pole `since` — skutečné datum zveřejnění na
Sreality, přesnější než `first_seen`, což je jen okamžik prvního zachycení
naším importem). Uživatel VYNECHAL nabízenou možnost sledovat historii ceny
(pole `price_summary_old_czk`) — zůstává jako možné budoucí rozšíření,
neimplementováno.

Všechna tato pole jsou ČISTĚ INFORMAČNÍ — zobrazují se v detailu nabídky
a částečně jako filtr (vlastnictví, energetický štítek, výtah), ale
NEVSTUPUJÍ do oceňovacího vzorce v `valuation.py` (ten zůstává cornerstone,
beze změny).

**Backfill existujících nabídek**: všech ~4700 nabídek už má `detail_at`
vyplněné (100% pokrytí z dřívějška), takže normální denní běh (500/den,
selektor `detail_at IS NULL`) je nedotáhne zpětně. Uživatel odsouhlasil
NEZRYCHLOVAT limit (zůstává 500/den, stejné zdůvodnění jako u cenové mapy —
riziko IP banu) — nová pole se tedy do appky postupně doplní přirozeně
v horizontu ~9–10 dní, jak import prochází existující nabídky (potřeboval by
se ale nejdřív resetovat `detail_at` u starých záznamů, což zatím NENÍ
provedeno — bez toho `WHERE detail_at IS NULL` nevybere žádné existující
řádky a nová pole se naplní jen u NOVÝCH nabídek, které denní import teprve
uvidí poprvé. Backfill starých záznamů je otevřený bod, viz sekce 8).

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
- 2026-07-20: přidán filtr patra (od-do) proti levným nabídkám jen kvůli
  přízemí/0. patru (úkol #25); filtr "jen s výtahem" zůstal beze změny.
- 2026-07-20: na žádost uživatele (detail nabídky měl "hodně čísel" bez
  jasného zvýraznění) upraveno CSS: běžné hodnoty méně tučné, jen klíčové
  řádky (Rozdíl sleva vs. tržní, Celkový výnos IRR, Pokrytí splátky nájmem)
  zvýrazněny barevně/velikostí (`.kv.hi`). Žádná logika ani data se
  neměnily. Následně přidáno i `align-items:start` do `.grid` — karty
  v detailu se přestaly natahovat na výšku nejdelší karty (méně
  prázdného místa).
- 2026-07-20: uživatel při kontrole týdenního reportu příležitostí upozornil
  na riziko, že extrémní slevy u nových nabídek mohou být (stejně jako
  dřív u anuit) uměle nafouknuté nějakou externalitou, kterou ještě
  neznáme, protože detail (vlastnictví/anuita) se k nim ještě nedotáhl.
  Diagnostikou zjištěno: fronta `import_detaily()` byla čistě FIFO podle
  `id` (nejstarší nabídka první), takže nové nabídky s obřím zdáním slevy
  čekaly na verifikaci detailu jako poslední — přesně ty, co se objeví
  v top 10 týdenního reportu. Uživatel navrhl řadit frontu podle aktuálně
  spočtené slevy (`valuations.sleva_pct`, počítá se denně i bez detailu na
  defaultních koeficientech) sestupně, s tím že úplně nové nabídky bez
  jakéhokoli ocenění mají nejvyšší prioritu ze všech. Implementováno
  v `src/sreality_detail.py` (`import_detaily`), rychlost 500/den beze
  změny. Vedlejší zjištění při diagnostice: fronta bez detailu se od
  cca 15.–16. 7. přestala smysluplně čistit (~370 nabídek trvale
  nezpracováno) i přes zdánlivě úspěšné denní běhy (`docs/detail_log.txt`
  hlásil "500 nabídek, chyb 0") — příčina nebyla dál zkoumána, sledovat
  po nasazení, jestli se s novým řazením fronta reálně zmenšuje.
- 2026-07-27/28: uživatel při procházení top nabídek narazil na konkrétní
  případ (byt Strašnice, Strančická, 138 m²), kde popis inzerátu psal
  "užitná plocha 138,5 m2 (75,3 m2 podlaha + terasa 61,2 m2 + sklep 2 m2)"
  — Sreality u tohohle inzerátu (na rozdíl od jiných) NEODEČETLA terasu
  z "Užitné plochy", takže náš model počítal 61 m2 terasy stejnou sazbou
  jako obytný prostor. Ověřeno přímo v syrových datech REST API
  (`/api/v1/estates/{id}`, ne jen zobrazený text): Sreality MÁ strukturovaná
  číselná pole `floor_area`, `terrace_area`, `loggia_area`, `balcony_area`,
  `garden_area`, `cellar_area` — ale realitky je vyplňují nekonzistentně
  (u jiných 2 testovaných bytů — Řeporyje se zahradou 335 m2, Stodůlky
  s komorou — byla buď všechna prázdná, nebo naopak dobře oddělená).
  Uživatel navrhl a schválil obecný algoritmus (žádné hádání z volného
  textu, jen strukturovaná pole):
  1. Když Sreality dá `floor_area` MENŠÍ než Užitná plocha (`plocha_m2`) A
     zároveň nějakou nenulovou plochu terasy/lodžie/balkonu, jádrová
     plocha bytu = floor_area, ne Užitná plocha.
  2. Terasa+lodžie+balkon (m²) se k jádru přičítají s váhou 25 %
     (`VAHA_TERASA_LODZIE_BALKON`), zahrada s váhou 15 %
     (`VAHA_ZAHRADA`) — "efektivní plocha", která nahrazuje `plocha_m2`
     všude ve vzorci (faktor velikosti bytu i finální × plocha).
  3. Sklep se nepočítá (zůstává čistě informační, `sklep_m2`).
  4. Kde strukturovaná data chybí, plocha se NEMĚNÍ (žádný odhad).
  Tohle NAHRAZUJE původní plochý bonus `BALKON_PCT` (+1,01 % za pouhou
  přítomnost balkonu bez ohledu na velikost) — ten byl u velkých teras
  extrémně nedostatečný (viz Strašnice: falešná "sleva" 28,3 % se po
  opravě propadla na −9,6 %, tedy spíš mírně předražené, ne příležitost).
  Implementováno: `src/valuation.py` (`jadro_a_vedlejsi_plocha`,
  `VAHA_TERASA_LODZIE_BALKON`, `VAHA_ZAHRADA` — `BALKON_PCT` odstraněn),
  nové sloupce `plocha_cista_m2`/`terasa_m2`/`lodzie_m2`/`balkon_m2`
  v `listings` (`src/db.py`, `src/sreality_detail.py`), nový krok
  "Efektivní plocha" v rozpadu výpočtu v appce. Ověřeno na 3 reálných
  příkladech před nasazením (Strašnice, Stodůlky, Řeporyje) — mechanismus
  se choval přesně podle očekávání. Proveden jednorázový reset
  `detail_at=NULL` pro všechny aktivní nabídky (nová pole je potřeba
  dotáhnout), fronta je řazená podle slevy (viz výše), takže se nejdřív
  opraví nejpodezřelejší "příležitosti".
- 2026-07-27: souběžně schváleno a implementováno "postoupení" jako nový
  red-flag (textová heuristika na "postoupen*" v popisu, `postoupeni_stav`
  sloupec + filtr v appce) — u rozestavěných bytů prodávaných na splátky
  bývá inzerovaná cena jen 1. splátka developerovi, ne celková cena
  (konkrétní příklad: byt Kamýk, Imrychova, inzerováno 1 263 720 Kč,
  skutečná celková cena 6 990 000 Kč na 4 splátky do kolaudace 09/2028).
  `cena_czk` se NEMĚNÍ (nejistota o přesné celkové ceně), jen se to
  zobrazí jako varování a dá se vyfiltrovat.
- Vedlejší zjištění (2026-07-27, nedořešeno): u bytu Stodůlky byl
  `v_koef_lokalita_pct` v produkčně uložené valuaci 0,0, přestože
  `lokalita_auto` odpovídala kategorii +5 % — možný samostatný bug
  v `ocenit_vse()` nesouvisející s touto úpravou, nebyl dál zkoumán,
  stojí za prověření příště.
- 2026-07-28: na žádost uživatele nahrazen filtr u víceoborových polí
  (Čtvrť, Dispozice, Energetický štítek) — dřív `<select multiple>` +
  jedno souhrnné "vyloučit vybrané" — checklistem: každá položka má
  vlastní zaškrtávátko (tick/křížek), defaultně vše zaškrtnuto (žádný
  filtr), tlačítka "vše"/"žádné" pro rychlý postup "vyřaď vše, pak
  ručně zaškrtni co chci". Zároveň přidán nový checklist filtr
  "Stav (dle Sreality)" nad `stav_sreality` (surová kategorie ze
  Sreality — Novostavba/Projekt/Před rekonstrukcí/Po rekonstrukci…),
  odlišný od zjednodušeného 3-stavového `stav` používaného ve výpočtu.
  Ověřeno jsdom testem (boot, odškrtnutí položky, "žádné"/"vše",
  `reset()` correctly vrací vše na zaškrtnuto) před nasazením.
- 2026-07-28: uživatel si všiml, že appka ukazuje jen 1 nabídku na
  watchlistu, přestože jich přidal aspoň 10 — diagnostikován skutečný
  bug, ne uživatelská chyba: workflow "Ruční úprava nabídky" sdílel
  concurrency skupinu `aktualizace-dat` s denní/měsíční pipeline;
  GitHub u `cancel-in-progress:false` drží ve frontě jen JEDEN čekající
  běh na skupinu, takže rychlá série otevřených issues (nebo souběh
  s denní pipeline) TICHO zrušila starší čekající běhy — issue zůstalo
  navždy otevřené, bez chybové hlášky. Nalezeny 4 takhle ztracené issues
  (#2, #3, #4, #10). Oprava: `uprava.yml` má teď vlastní concurrency
  skupinu `uprava-<číslo issue>` (viz commit 341fe25), + všechny tři
  workflow mají push zpevněný retry smyčkou místo `|| true` bez
  opakování. Ručně dopsáno do databáze (commit 8038d20) — ALE první
  pokus byl chybný: mylně jsem předpokládal, že všechny 4 issues byly
  watchlist:1 (ověřil jsem si to jen u #2), zatímco #3/#4/#10 byly ve
  skutečnosti celé editační formuláře (stav/rok/balkon/parkování/
  lokalita). Opraveno v commitu f96c6ce (watchlist vrácen na 0 tam, kam
  nepatřil, doplněny skutečné hodnoty z těla issues) + comment na
  GitHubu na všech 3 dotčených issues s vysvětlením chyby. Poučení:
  nikdy nepředpokládat obsah issue z názvu/kontextu sousedních issues —
  vždy si přečíst tělo KAŽDÉHO jednotlivě před zápisem.
- 2026-07-30: uživatel se ptal na konkrétní byt (Košíře, Vrchlického,
  id 1865, 4. patro ze 7, panelák) se slevou 46,5 % — Sreality pole
  `garden_area` bylo 500 m², ale popis mluvil jen o "vlastní klidný
  vnitroblok domu" (dětské atrakce, pískoviště), žádná zmínka o podílu.
  Sdílený vnitroblok velkého domu (klidně 20-30 bytů) bez definovaného
  podílu nemá pro JEDEN byt soukromou hodnotu — započítání celých
  500 m² × 0,15 do efektivní plochy (78→153 m²) dělalo tržní hodnotu
  skoro dvojnásobnou. Uživatel rozlišil: sdílená zahrada domu s výslovně
  napsaným podílem (typicky menší domy) = reálná ocenitelná hodnota;
  velký nerozdělený vnitroblok/pozemek bez podílu = neoceňovat vůbec.
  Implementováno jako heuristika na slovo "podíl" v popisu inzerátu
  (`_zahrada_m2()` v `src/sreality_detail.py`, stejný princip jako
  anuita/postoupení) — bez podílu se `zahrada_m2` nezapisuje (None),
  i když `garden_area` je vyplněné. Backfill: `detail_at=NULL` pro
  352 nabídek s dosud vyplněnou zahrada_m2 (přehodnotí se v běžném
  denním běhu, 352 < 500/den limit). Commit 3433bd1.
- 2026-08: uživatel se zeptal, jestli jsme "ready" rozšířit appku i na
  Střední Čechy — po prozkoumání (viz PLÁN níže) schváleno ve dvou
  krocích s explicitním rozhodnutím uživatele: (1) cenová mapa jen pro
  velká města Středočeského kraje nad 5000 obyvatel (ne celý kraj — moc
  malých obcí s pár transakcemi/rok, nespolehlivá cena/m²), (2) zůstat
  jen u bytů, žádné rodinné domy (ty by chtěly úplně jiný oceňovací
  model — pozemek, zastavěná plocha).
  - **Cenová mapa** (commit afd4cf8): Sreality má pro kraje 3stupňovou
    hierarchii (kraj → 12 okresů → obce), na rozdíl od ploché pražské
    stránky — nový `scripts/stredocesky_cenova_mapa.py` dělá 1+12
    requestů. Filtr na velká města: `data/mesta_stredocechy.csv`
    (42 měst, zdroj: Wikipedie "Seznam měst ve Středočeském kraji",
    stav ~2023 — je to seznam obcí s oficiálním STATUSEM města, ne
    čistě podle populace; při hraní si s uživatelem vyšlo najevo, že
    Horoměřice mají dle novějšího zdroje už 5496 obyvatel, ale nemají
    status města, takže na seznamu chybí — známá mezera, neřešeno na
    žádost uživatele ("neřeš to"), k případné revizi později.
  - `price_map.csv`/DB: nový sloupec `kraj` (Praha/Středočeský) — každý
    regionální scraper smí přepisovat JEN svoje řádky (vzájemně
    ověřeno testem).
  - **Bug nalezený cestou**: `_ctvrt()` v `src/sreality.py` mimo Prahu
    bral `citypart` stejně jako u Prahy (rozdělit podle pomlčky) — u
    Sreality mimo Prahu je ale `citypart` tvar "Beroun-Závodí" (místní
    část obce), takže by to vytáhlo "Závodí" místo "Beroun" a nabídka
    by v cenové mapě nenašla shodu. Oprava: mimo Prahu (`city != "Praha"`)
    se bere přímo `city`. Ověřeno na reálném API vzorku, Praha beze
    změny chování.
  - **Druhý, závažnější bug nalezený cestou** (commit bcd50b5, KRITICKÝ
    před zapojením importu): `import_sreality()` deaktivovalo "zmizelé"
    nabídky globálně přes všechny kraje (`WHERE source='sreality' AND
    active=1`, bez ohledu na region) — import Středočeského kraje by
    logicky "neviděl" žádnou pražskou nabídku ve svých výsledcích, a
    pojistka (`len(videne) > 50 % aktivních`) by u větší dávky
    středočeských nabídek klidně mohla vyhodnotit "zmizelo přes 50 %"
    a deaktivovat VŠECHNY pražské nabídky. Oprava: nový sloupec
    `listings.kraj` (odvozený z `locality_region_id` při importu),
    deaktivační dotaz i počítání aktivních teď scoped přes
    `WHERE kraj=:kraj`. Jednorázový backfill: všech 6747 stávajících
    sreality nabídek dostalo `kraj='Praha'` (jisté, ne odhad — do té
    chvíle se importovala jen Praha). Ověřeno testem: scénář s 5
    novými středočeskými nabídkami (>50 % z celkových 7 aktivních)
    by pod starým kódem smazal aktivní flag pražským nabídkám — nový
    kód je nechal beze změny.
  - **Import zapojen do denní pipeline** (commit 0de97df):
    `python -m src.main import-sreality ".../byty/stredocesky-kraj"
    --max-stranek 25` (celý kraj má ~1942 nabídek byty/prodej celkem,
    kapacita 2500). Nabídky mimo těch 42 velkých měst nenajdou shodu
    v cenové mapě a automaticky se deaktivují — stejný mechanismus,
    který už roky běží u pražských nabídek bez shody ve čtvrti, žádná
    nová logika.
  - Všechno ověřeno na mock datech (reálně zachycená struktura ze
    Sreality přes Claude in Chrome) PŘED nasazením, plus end-to-end
    test s testovací nabídkou. Skutečný běh cenové mapy i denní
    pipeline po nasazení ověřen přímo v GitHub Actions.
  - **Ostrý běh po zapojení (2026-08-03, run #113, commit c3ded45)**:
    naimportováno 1374 středočeských nabídek, 1336 z nich se podařilo
    ocenit (97 %), 38 bez ocenění (chybí detailní data typu plocha_m2,
    ne nutně chybějící shoda v cenové mapě — u části z nich je i
    Beroun/Kladno/Kolín, které cenovou mapu MAJÍ). Nalezeno 142 nových
    příležitostí (sleva ≥ 10 %) jen ve Středních Čechách.

- **Oddělení Prahy a Středních Čech v UI** (2026-08-03, commit 02e5d03,
  na žádost uživatele — "prahu a stredocesky bych oddelil"): appka
  dřív ukazovala oba kraje pomíchané v jedné tabulce. Teď `index.html`
  bez `?kraj=` parametru zobrazí výběrovou stránku (karty Praha /
  Střední Čechy, živé počty nabídek a příležitostí z `data.json`).
  Kliknutím se otevře STEJNÉ rozhraní jako doteď (filtry, tabulka,
  detail, peer group), ale s `?kraj=praha` nebo `?kraj=stredocesky`:
  - `ALL` (nabídky) i `MAPA` (cenová mapa) se filtrují na daný kraj
    HNED po načtení `data.json` — zbytek appky (checklist filtry
    Čtvrť/Dispozice/Stav/Štítek, tabulka, peer group, detail) o
    druhém kraji vůbec neví.
  - Checklist "Čtvrť" se teď generuje jen z nabídek daného kraje —
    důležité, protože Praha a Střední Čechy mají úplně jiné
    čtvrti/obce (žádná společná množina, žádné riziko záměny).
  - V appce je nahoře odkaz `⇄ vybrat jiný kraj` (vede na `?`, tedy
    zpět na výběrovou stránku).
  - Neplatný/chybějící `kraj` parametr → bezpečný default: zobrazí se
    výběrová stránka (ne prázdná appka, ne obě data pomíchaně).
  - Žádná změna v oceňovací logice ani v `build_static.py` (jeden
    `data.json` pro oba kraje zůstává, jen se v appce filtruje podle
    parametru) — všechno jen `src/static/index.html`.
  - Ověřeno jsdom testem (4 scénáře: bez parametru, praha, stredocesky,
    neplatný parametr) proti mock i reálným produkčním datům (6257
    nabídek), a pak přímo živě na GitHub Pages přes Claude in Chrome
    (landing ukázal správné počty 4883/637 Praha, 1374/142 Střední
    Čechy; `?kraj=praha` scoped appka měla 99 čtvrtí a title
    "— Praha").

- **Typově a lokalitně rozlišený příplatek parkování** (2026-08-04, commit
  28c5f23, JEN PRAHA, na žádost uživatele): uživatel se zeptal, jestli
  pevných 400 000 Kč za parkování (`PARKOVANI_KC`, hodnota 1:1 z
  uživatelova originálního Excelu, buňka BM5 — bez komentáře/vzorce,
  jen ruční číslo, ověřeno diagnostikou) sedí i pro Střední Čechy, a
  navrhl rozlišit garáž / stání ve velké garáži / venkovní stání.
  - **Reálný trh (Sreality, 2026-08-04)**: zjišťováno přímo přes
    Sreality API (Claude in Chrome, stejný endpoint jako import) —
    samostatná garáž v Praze medián 990 000 Kč (n=86, průměr 1 209 910,
    rozsah 350k–3,78M), garážové stání medián 710 000 Kč (n=67 po
    vyřazení 1 zjevně chybného outlieru — "801 m² za 15 mil. Kč" =
    více stání najednou). Venkovní stání Sreality NErozlišuje jako
    kategorii ani jako datový příznak u bytů — bez spolehlivého čísla.
  - **Uživatel schválil kulatá čísla**: Garáž 1 000 000 Kč, Stání
    750 000 Kč, Venkovní 500 000 Kč (venkovní bez tržního podkladu,
    uživatelův odhad).
  - **Lokalitní koeficient** (uživatelův návrh): koef = cena_mapy dané
    čtvrti / průměr Prahy (100 čtvrtí, prostý průměr = 145 259 Kč/m²),
    OMEZENO na rozsah ⟨0,8; 1,2⟩ — bez omezení by rozsah byl 0,68–2,15
    (ověřeno na reálné cenové mapě), takže cap skutečně něco dělá.
  - **Rozlišení Garáž/Stání/Venkovní**: Sreality má u detailu bytu
    strukturovaná pole `garage`/`garage_count` (garáž) a
    `parking`/`parking_lots` (nějaké parkovací místo) — spolehlivé,
    ne heuristika. Venkovní ale Sreality strukturovaně nerozlišuje
    vůbec, takže se hledá JEN textovou heuristikou v popisu ("venkovní
    stání/parkování", "nekryté stání", "otevřené stání") — stejný typ
    heuristiky jako anuita_stav/postoupeni_stav, výslovně jako méně
    jistá. Priorita: Garáž > (text) Venkovní > Stání (výchozí, protože
    "garážové stání" je v inzerátech běžnější formulace) > žádné.
  - **Nový sloupec `listings.typ_parkovani`**, nastavuje se v
    `import_detaily()` (nové nabídky automaticky) a přes novou funkci
    `doplnit_typ_parkovani()` (dohání starší nabídky, které detail
    dostaly PŘED zavedením pole — `import_detaily` se řídí
    `detail_at IS NULL`, takže by je normálně nikdy znovu nenavštívilo).
  - **Jednorázový backfill** (mimo běžnou pipeline, přes Claude in
    Chrome — sandbox nemá přímý síťový přístup na sreality.cz):
    1742 existujících pražských nabídek s `parkovani` Ano/Ano 2*,
    klasifikováno: 911 Garáž, 789 Stání, 26 Venkovní, 16 bez parkování
    přes strukturovaná pole (`parkovani`="Ano" jen z textu/edge-case).
    Nula chyb při dotahování. Zbylo ~649 nabídek z importu ze stejného
    dne (mezi mým prvním a druhým dotazem na DB) — ty dojedou přes nový
    krok v denní pipeli (`doplnit-typ-parkovani`, 500/den, stejné tempo
    jako `import-detaily`).
  - **Střední Čechy beze změny**: žádná reálná tržní data k dispozici
    pro ten kraj — `PARKOVANI_KC`=400k a koeficient lokality 1,0
    (fixně) zůstávají, dokud uživatel neschválí totéž rozlišení i tam.
  - `src/static/index.html`: detail nabídky teď u příplatku parkování
    zobrazuje typ (Garáž/Stání/Venkovní) a koeficient lokality —
    transparentní rozpad, stejně jako ostatní kroky výpočtu.
  - Ověřeno na reálných produkčních datech (6218 aktivních nabídek,
    spočítané `priplatky_czk` odpovídají typ × koef na korunu) a
    jsdom testem detailu nabídky (text „příplatek (parkování: Ano —
    Garáž, koef. lokalita ×1.024)" se vykresluje správně).

- **Totéž rozšířeno na Střední Čechy** (2026-08-04, commit 574fd22,
  navazuje na 28c5f23): uživatel se zeptal, jestli ceny sedí i pro
  Střední Čechy.
  - **Reálný trh (Sreality, 2026-08-04, region Středočeský)**: garáž
    medián 699 000 Kč (n=55, průměr 718 192, rozsah 350k–1,29M);
    garážové stání medián 395 000 Kč — ALE jen n=10 platných nabídek
    v celém kraji (rozsah 200k–1,14M), výslovně upozorněno uživateli
    jako málo spolehlivé. Venkovní stání opět bez dat (Sreality to
    nerozlišuje ani tady).
  - **Uživatel schválil**: Garáž 700 000 Kč, Stání 450 000 Kč (vyšší
    než zjištěný medián 395k — uživatelova vlastní volba, ne můj
    návrh), Venkovní 300 000 Kč (uživatelovo číslo, žádný tržní
    podklad).
  - **Koeficient lokality**: stejný mechanismus jako Praha (cena_mapy
    města / průměr kraje, ⟨0,8; 1,2⟩), potvrzeno uživatelem. Bez capu
    by rozsah byl 0,67–1,52 (Roztoky 60 750 Kč/m² nejlevnější, Černošice
    137 280 Kč/m² nejdražší ze 43 měst v cenové mapě).
  - `valuation.py`: `PARKOVANI_ZAKLAD_KRAJ` zobecněno na slovník
    `{kraj: {typ: Kč}}` (dřív jen Praha, natvrdo). `koef_lok_park` teď
    generický pro libovolný kraj v tomhle slovníku.
  - `sreality_detail.py`: `doplnit_typ_parkovani()` zobecněna (dřív
    `WHERE kraj='Praha'` natvrdo) — dohání typ parkování pro libovolný
    kraj, kde chybí.
  - **Jednorázový backfill** 341 středočeských nabídek s parkováním
    (přes Sreality API, stejně jako Praha): 209 Stání, 119 Garáž,
    11 Venkovní, 2 bez parkování přes strukturovaná pole (edge-case).
    Nula chyb.
  - Ověřeno na reálných produkčních datech — `priplatky_czk` odpovídá
    typ × koef × počet na korunu, včetně správného clampování na
    hranice 0,8 (Čáslav) a 1,2 (Brandýs nad Labem-Stará Boleslav).

- **Oprava: stejnojmenné obce ve Středočeském kraji v jiném okrese**
  (2026-08-04, commit c98e736): uživatel chtěl odkaz na cenovou mapu a
  na nabídku v Roztokách — při tom vyšel najevo skutečný bug, ne jen
  dotaz na odkaz.
  - **Bug**: Sreality má ve Středočeském kraji STEJNÁ jména obcí ve
    RŮZNÝCH okresech — "Roztoky" existují jako velké město v okrese
    Praha-západ (8971 obyv., na našem seznamu velkých měst) i jako
    malá vesnice v okrese Rakovník; totéž "Jesenice" (Praha-západ vs.
    Rakovník). `scripts/stredocesky_cenova_mapa.py` i `src/sreality.py`
    matchovaly a klíčovaly čtvrť JEN podle normalizovaného jména, bez
    ohledu na okres — starý komentář v kódu doslova tvrdil "jedno
    město nemůže být ve více okresech? ne", což bylo mylné.
  - **Reálný dopad (zjištěno před opravou)**: `price_map.csv` měl u
    klíče `roztoky` hodnotu 60 750 Kč/m² — neodpovídala AKTUÁLNÍ ceně
    ani jednoho z obou okresů, zbytek z doby, kdy scraper "vyhrál"
    malou vesnici v Rakovníku. Všech 7 aktivních nabídek v Roztokách
    (adresy jasně Roztoky u Prahy — Lederova, Masarykova, Lidická,
    Braunerova) se tak oceňovalo cenou špatné (levné) obce. Sleva vůči
    "tržní hodnotě" u nich vycházela −49 % až −126 % (vypadaly jako
    extrémně přeplacené), ve skutečnosti šlo o chybu modelu, ne o
    realitu trhu. Stejný pattern u Jesenice (9 správných + 1 skutečně
    z Rakovníka).
  - **Ověření disambiguace**: Sreality API u každé nabídky (`locality.
    municipality_id`) odpovídá přesně `entityId` z cenové mapy na
    úrovni obce — spolehlivý identifikátor, ne heuristika (na rozdíl
    od venkovního parkování výše).
  - **Oprava (obecná, ne hardcoded na Roztoky/Jesenice)**:
    `src/sreality.py` `_ctvrt()` teď u každého z 43 velkých měst ověří
    okres nabídky (pole `district` ze Sreality) proti okresu
    zaznamenanému v `data/mesta_stredocechy.csv`; při nesouladu připojí
    okres k názvu (např. "Roztoky (Rakovník)"), takže nabídka nenajde
    shodu v cenové mapě a spadne do stávajícího mechanismu "bez shody →
    deaktivovat" — stejně jako jakákoli jiná malá obec mimo seznam,
    žádný nový speciální kód.
    `scripts/stredocesky_cenova_mapa.py` `aktualizuj()` teď při stahování
    cenové mapy stejně ověřuje okres každé nalezené obce; stejnojmennou
    obec v jiném okrese přeskočí a vypíše do logu, nezapíše ji pod
    špatný klíč.
  - **Jednorázová manuální korekce**: `price_map.csv`/DB řádek `roztoky`
    opraven na 132 675 Kč/m² (40 transakcí, reálná aktuální hodnota pro
    Praha-západ). V okamžiku opravy jsem si přes Sreality API ověřil
    okres jen u listingu 8000 (Roztoky) a manuálně ho i listing 7844
    (Jesenice) přesunul na disambiguovaný název čtvrti — u 7844 to byl
    OMYL: po nasazení kódové opravy a jejím prověření živě přes API se
    ukázalo, že listing 7844 je ve skutečnosti Jesenice, Praha-západ
    (district="Praha-západ" z detailu Sreality) — tedy ta SPRÁVNÁ
    Jesenice ze seznamu velkých měst, ne ta z Rakovníka. Následný denní
    automatický import (`ctvrt` je v `PREPSAT_VZDY`, přepisuje se při
    každém importu) tuhle mou chybu sám opravil zpět na `ctvrt='Jesenice'`,
    `active=1` — přesně jak má u správně zařazené obce být. Skutečná
    „Jesenice v Rakovníku" je listing **8337** (ověřeno stejným
    způsobem přes API), ten je korektně disambiguovaný na
    "Jesenice (Rakovník)" a deaktivovaný.
  - **Výsledek po přepočtu** (`python -m src.main ocenit`): listingy
    8000 (Roztoky) a 8337 (Jesenice) správně deaktivovány jako „bez
    shody v cenové mapě". Zbylých 6 aktivních Roztok (Praha-západ) mělo
    PŘED opravou slevu −49 % až −126 %, PO opravě: +30,22 %, +26,54 %,
    −3,38 %, 0,0 %, +16,46 %, −3,59 % — 3 z nich jsou reálné podhodnocené
    příležitosti, které bug dřív skrýval. (Přesný výčet Jesenice před/po
    jsem si při první opravě nezaznamenal — jen jsem u 7844 udělal
    chybnou manuální korekci, viz výše; oprava kódu i tak funguje
    správně, ověřeno na obou listingách 8000 i 8337.)
  - **Update 2026-08-04**: nájemní pokrytí Středních Čech (0,07 %) bylo
    mezitím vyřešeno, viz další záznam níže — uživatel dal jiný zdroj
    dat, ne že by to tak zůstalo.

- **Nájemní benchmark MFČR: celostátní XLSX namísto scrapingu jen Prahy**
  (2026-08-04, commit 0525b2d, na návrh uživatele): uživatel při ukázce
  cenové mapy nájemného narazil na to, že MFČR na stejné stránce nabízí i
  strukturovaný XLSX "Cenová mapa - tabulkové výstupy" pokrývající
  VŠECHNY kraje ČR — ne jen samostatnou mapu pro Prahu, kterou jsme
  scrapovali doteď (regex na textové popisky z Leaflet mapy, `Mapa_Praha`
  widget). Uživatel: "ten excel je možná lepší než se snažit scrapovat tu
  mapu, ten má ta data mnohem lépe organizovaná".
  - **Zdroj**: list "Cenové mapy nájemného" v XLSX (aktualizuje se 4x
    ročně, URL se hledá dynamicky na stránce MFČR, ne natvrdo). Sloupce
    Kraj/Katastrální území/Obec/Kód obce + 4 opakující se bloky (VK1-4 =
    velikostní kategorie bytu 1+kk…4+ pokojů) se sloupcem "Nájemné
    referenčního bytu za m² v Kč za 1 měsíc".
  - **Praha**: matchuje se podle katastrálního území stejně jako dřív
    (1:1, žádná změna výstupního formátu pro `src/valuation.py`).
  - **Střední Čechy**: náš model matchuje nájem na úroveň celé OBCE, ale
    velká města mají v XLSX víc katastrálních území (Kladno: 7 — Kladno,
    Dubí u Kladna, Kročehlavy, Motyčín, Rozdělov, Vrapice, Hnidousy).
    Agreguje se **prostým průměrem** přes všechna katastrální území
    obce — schváleno uživatelem: "pro prvotní screening asi můžeme
    pracovat s průměry a pak při tom detailnějším hledání to nějak
    zohlední a upraví si podle toho koeficient lokality" (přesnější
    rozlišení čtvrtí uvnitř obce je vědomě mimo scope automatického
    modelu).
  - **Stejná kolize jmen jako u cenové mapy bytů (Roztoky, Jesenice, viz
    záznam výše)** se objevila i tady — XLSX má obě jména víckrát pod
    různým "Kód obce". Rozlišeno přes Kód obce, ověřeno webovým
    vyhledáváním proti RUIAN/ČSÚ registru obcí: Roztoky Praha-západ =
    539627 (ne 598526 = Roztoky Rakovník), Jesenice Praha-západ = 539325
    (ne 540391/541834 = jiné Jesenice mimo náš seznam). **Důležité
    rozlišení**: víc řádků se stejnou obcí a RŮZNÝM Kód obce je u
    velkých měst běžné a NENÍ to kolize (každé katastrální území má
    vlastní kód) — skutečná kolize se pozná podle víc než 1 řádku se
    stejnou obcí a PRÁZDNÝM katastrálním územím (malé, dál nedělené obce
    sdílející jméno). Ověřeno na celém Středočeském kraji: 49 takových
    jmen, z našich 43 velkých měst jen tato dvě.
  - **Bezpečnostní pojistka**: nová, dosud neznámá kolize (mimo tyto dvě)
    shodí skript s chybou, ne tichý výběr prvního řádku — testováno
    syntetickým příkladem.
  - **Ověření před nasazením**: end-to-end test na syntetickém XLSX
    (openpyxl, včetně testu kolize i bezpečnostní pojistky) + logika
    porovnána s reálnými daty přes SheetJS v prohlížeči (Kladno průměr
    VK1 = 318,4 sedí na desetinu, Roztoky správně vybere kód 539627 a
    vynechá 598526, 43/43 velkých měst má po přepočtu pokrytí, 0 nových
    kolizí, 112 pražských katastrálních území).
  - **Výsledek po nasazení a automatickém běhu pipeline** (run #121):
    pokrytí nájmu ve Středních Čechách vyskočilo z 0,07 % (1/1340) na
    **97,0 % (1341/1382)** — na úrovni Prahy (96,2 %, 4698/4885).
