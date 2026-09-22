# Naplánované úlohy + migrace na nový Claude — handoff

Doplněk k `PREDAVACI.md` a `CLAUDE.md`. Popisuje 2 naplánované Cowork úlohy
tohoto projektu a jak je obnovit na **novém Claude účtu** (Cowork), kdyby ses
přesunul jinam. Vlastní denní/měsíční pipeline (import ze Sreality → ocenění →
build appky) běží na **GitHub Actions v tomto repu, mimo Claude**, takže poběží
dál bez ohledu na Claude účet. Úlohy níže jen čtou hotová data.

Last updated: 2026-09-22

## Přehled

| Úloha | Rozvrh (cron) | Co dělá |
|---|---|---|
| `tydenni-report-prilezitosti` | `0 8 * * 1` (Po ráno) | Přečte `docs/data.json`, vybere nové podhodnocené byty za 7 dní (Praha + Střední Čechy) a pošle top 10/kraj do chatu |
| `oceneni-prehled-refresh` | `0 9 2 * *` (2. den v měsíci) | Měsíčně obnoví Cowork artefakt „Ocenění nemovitostí — přehled" čerstvými daty z repa |

Obě úlohy pracují jen nad **veřejnými daty** (`https://orosa10.github.io/oceneni-nemovitosti/`
a klon tohoto public repa) — **žádný token, žádná připojená složka**.

## Obnovení na novém Claude
Na novém Claude řekni „Založ tyhle naplánované úlohy podle tohoto dokumentu" —
Claude pro každou zavolá `create_scheduled_task` s uvedeným cronem a promptem
(níže doslovně). `tydenni-report-prilezitosti` zapni; `oceneni-prehled-refresh`
viz poznámka o artefaktu.

---

## ÚLOHA 1 — `tydenni-report-prilezitosti`  (cron `0 8 * * 1`, zapnout)

```
Toto je projekt "Ocenění nemovitostí" (databáze bytů k prodeji v Praze a velkých městech Středočeského kraje s automatickým oceněním tržní hodnoty a hledáním podhodnocených příležitostí — stejná oceňovací metodika pro oba kraje, jen jiná geografická data). Veškerý import, ocenění a publikace běží automaticky na GitHubu (denně) — TENTO úkol nic neimportuje ani nepočítá, jen si přečte už hotová data a pošle uživateli krátký souhrn do chatu.

Postup:
1. Stáhni https://orosa10.github.io/oceneni-nemovitosti/data.json (JSON, pole "listings" a "generated"). Každý záznam má pole "kraj" s hodnotou "Praha" nebo "Středočeský".
2. Rozděl "listings" na dvě skupiny podle pole "kraj": Praha a Středočeský. Na KAŽDOU skupinu zvlášť (stejná pravidla, zvlášť pro každou) vyber jen záznamy, kde:
   - "first_seen" spadá do posledních 7 dní od teď (formát ISO, např. "2026-07-04T17:43:22"),
   - "sleva_pct" není null,
   - "cena_czk" není null (přeskoč nabídky "cena na vyžádání"),
   - "skryto" není 1 (uživatel nabídku ručně skryl — nezobrazovat ji v reportu),
   - "vlastnictvi" NENÍ "Družstevní" (schváleno uživatelem 2026-07-20: družstevní byty
     mají strukturálně nižší cenu než osobní vlastnictví — model s tím nepočítá a slevu
     by u nich uměle nafukoval; položky, kde "vlastnictvi" je null/chybí — detail se
     ještě nedotáhl — NEVYLUČUJ, jen do reportu u nich připiš "(vlastnictví zatím
     neověřeno)"),
   - "patro" NENÍ 0 (schváleno uživatelem 2026-07-20: přízemí bývá levné jen kvůli
     patru, ne kvůli skutečné podhodnocenosti; položky s "patro" null/chybí — detail
     se ještě nedotáhl — NEVYLUČUJ, jen do reportu u nich připiš "(patro zatím
     neověřeno)").
3. V KAŽDÉ skupině zvlášť seřaď sestupně podle "sleva_pct" a vezmi top 10.
4. Pošli uživateli do chatu stručné shrnutí v ČEŠTINĚ ve DVOU sekcích — nejdřív "Praha", pak "Střední Čechy" — s nadpisem (např. "## Praha" / "## Střední Čechy"). V KAŽDÉ sekci jednoduchý seznam (žádné tabulky ani nadměrné formátování), pro každou nabídku: čtvrť/obec, dispozice, plocha (m²), cena (Kč), sleva vs. tržní hodnota (%), a odkaz (pole "url"); pokud je vlastnictví/patro u dané nabídky neověřené (viz krok 2), připiš to na konec řádku. Pokud má nabídka "watchlist": 1, přidej na začátek řádku hvězdičku (★). Na úplný začátek (před oběma sekcemi) napiš jednu větu s datem generování dat (pole "generated") a počtem nových nabídek za posledních 7 dní, které splnily filtr, zvlášť pro Prahu a zvlášť pro Střední Čechy.
5. Pokud v některém z kraji za posledních 7 dní nepřibyla žádná nabídka splňující filtr, napiš u té sekce jednu větu "žádné nové příležitosti tento týden" místo prázdné sekce.
6. Pokud se data.json nepodaří stáhnout nebo má neočekávaný formát, napiš to jasně místo tichého selhání — nic nevymýšlej.

Buď stručný — žádné dlouhé úvody ani vysvětlování, rovnou obě sekce se seznamy nabídek.
```

---

## ÚLOHA 2 — `oceneni-prehled-refresh`  (cron `0 9 2 * *`)

> **Přenos artefaktu:** Cowork artefakt `oceneni-prehled` je vázaný na účet, na
> kterém vznikl — na novém účtu s tím id neexistuje. Proto je do promptu níže
> **přidán krok 4a**: při prvním běhu artefakt vytvoř nově (`create_artifact`)
> a dál používej jeho nové id. (Alternativa, pokud artefakt nechceš: úlohu
> nezakládat a používat živou appku `https://orosa10.github.io/oceneni-nemovitosti/`.)

```
Toto je součást projektu "Ocenění nemovitostí". Existuje persistentní Cowork artefakt s id "oceneni-prehled" (titulek "Ocenění nemovitostí — přehled"), který ukazuje snímek dat z GitHub repozitáře https://github.com/ORosa10/oceneni-nemovitosti. Tvým úkolem je artefakt jednou měsíčně obnovit čerstvými daty (spouští se den po měsíční automatizaci cenové mapy/sazby hypotéky v repu, cron 1. den v měsíci 5:00 UTC).

POSTUP:
1. V bash sandboxu naklonuj repo (mělký klon stačí): `git clone --depth 1 https://github.com/ORosa10/oceneni-nemovitosti.git /tmp/refresh` (pokud github.com není přímo dostupný přes bash, zkus totéž, sandbox má github.com povolený v allowliste).
2. Přečti `/tmp/refresh/data/sazba_hypoteky.csv` (sloupce sazba_pct, datum_aktualizace, zdroj) — to je aktuální sazba hypotéky.
3. Přečti `/tmp/refresh/docs/data.json` (klíče: generated, listings, price_map). Spočítej pomocí Pythonu:
   - generated (timestamp posledního běhu)
   - počet čtvrtí v price_map a nejnovější updated_at datum
   - listings s active==1 a cena_czk a trzni_hodnota vyplněné = "aktivní/oceněné nabídky", jejich počet, a celkový počet všech listings
   - z aktivních (a bez skryto==1) vyber top 8 podle sleva_pct sestupně (příležitosti), a spočítej kolik jich má sleva_pct >= 10
   - spočítej počet nabídek s watchlist==1 (mezi aktivními, bez skryto)
4. Zavolej `list_artifacts` (pokud je potřeba zjistit cestu k aktuální verzi), pak vytvoř nový HTML soubor podle STEJNÉHO layoutu/stylu jako má aktuální artefakt (světlý motiv, karty se statistikami: Sazba hypotéky + datum + odkaz na cbamonitor.cz, Cenová mapa (počet čtvrtí + datum), Aktivní nabídky (oceněné/celkem), Příležitosti (sleva>=10%), Watchlist; tabulka top 8 příležitostí se sloupci Čtvrť/Dispozice/Cena/Sleva/odkaz na Sreality; nahoře odkazy na https://orosa10.github.io/oceneni-nemovitosti/ , https://github.com/ORosa10/oceneni-nemovitosti a https://github.com/ORosa10/oceneni-nemovitosti/actions ; dole poznámka, že Dolní Měcholupy jsou v žebříčku známý edge-case (domy prodávané jako byt, viz PREDAVACI.md bod 8.3) — pokud se tam objeví, poznámku zachovej, jinak ji vynech). Data napevno zapiš do <script> tagu (žádné externí fetch v samotném artefaktu, sandbox artefaktu blokuje síť mimo povolené CDN).
4a. PŘENOS NA NOVÝ ÚČET: pokud artefakt s id "oceneni-prehled" na tomto účtu neexistuje (list_artifacts ho nenajde), vytvoř ho POPRVÉ nově přes create_artifact z vygenerovaného HTML (titulek "Ocenění nemovitostí — přehled"), poznamenej si jeho nové id a v dalších bězích už jen updatuj to.
5. Ulož HTML soubor do svého outputs adresáře a zavolej `update_artifact` s id "oceneni-prehled" (resp. novým id z kroku 4a), html_path na tento soubor, update_summary "měsíční refresh dat (YYYY-MM)".
6. Po update zavolej `verify_artifact` a zkontroluj, že nejsou chyby v konzoli.
7. Pošli krátké shrnutí do chatu (česky): aktuální sazba, počet příležitostí nad 10 %, a že artefakt je aktualizovaný. Pokud se cokoliv nepodaří (repo nedostupné, soubory chybí, formát dat se změnil), NEHÁDEJ hodnoty — napiš uživateli přesně, co selhalo, a artefakt neaktualizuj (žádné tiché náhrady, dle CLAUDE.md hard rules tohoto projektu).
```
