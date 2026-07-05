# Diagnostika v4: vytáhnout data (nájemné po lokalitách) z MFČR Leaflet mapy
import json, re, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
url = "https://mf.gov.cz/assets/cs/cmsmedia/html_cenove-mapy/Mapa_Praha_15.5.2026.html"
html = requests.get(url, headers=UA, timeout=60).text
print("delka:", len(html))
# unicode-escaped 'Kč'
print("vyskyt 'K\\\\u010d':", html.count("K\\u010d"))
# externí datové soubory
for u in sorted(set(re.findall(r'["\'](https?://[^"\']+\.(?:geo)?json[^"\']*)["\']', html))):
    print("EXT JSON:", u)
# vložené GeoJSON bloky — najdi properties prvního feature
for m in re.finditer(r'"properties"\s*:\s*\{', html):
    start = m.end() - 1
    depth, i = 0, start
    while i < len(html):
        if html[i] == '{': depth += 1
        elif html[i] == '}': depth -= 1
        if depth == 0: break
        i += 1
    props = html[start:i+1]
    print("PROPERTIES:", props.encode().decode('unicode_escape', errors='replace')[:600])
    print("---")
    if m.start() > 900000: break
