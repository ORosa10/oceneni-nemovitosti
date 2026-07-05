# Diagnostika v7: obsah popupů v mapě + všechny mapové soubory na stránce MFČR
import re, requests

UA = {"User-Agent": "Mozilla/5.0"}
base = "https://mf.gov.cz"

print("### všechny Mapa_* soubory na stránce infografiky:")
p = requests.get(base + "/cs/rozpoctova-politika/podpora-projektoveho-rizeni/cenova-mapa/cenova-mapa-infografika", headers=UA, timeout=60).text
for u in sorted(set(re.findall(r'["\']([^"\']*(?:[Mm]apa|cenov)[^"\']*\.html[^"\']*)["\']', p))):
    print("MAPA:", u)

print("\n### Mapa_Praha — hledání českých textů (unicode escapy i diakritika):")
html = requests.get(base + "/assets/cs/cmsmedia/html_cenove-mapy/Mapa_Praha_15.5.2026.html", headers=UA, timeout=60).text
for tok in ("\\u00e1jem", "\\u011bs\\u00edc", "nájem", "měsíc", "Průměr", "prodej", "Byty", "byty", "Kč"):
    n = html.count(tok)
    print(f"'{tok}': {n}")
    if n:
        m = re.search(re.escape(tok), html)
        print("  CTX:", html[max(0,m.start()-250):m.start()+300].replace("\n"," ")[:500])
print("\n### konec souboru (posledních 1500 znaků):")
print(html[-1500:])
