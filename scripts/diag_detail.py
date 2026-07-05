# Diagnostika v5: jak MFČR mapa načítá data
import re, requests

UA = {"User-Agent": "Mozilla/5.0"}
base = "https://mf.gov.cz/assets/cs/cmsmedia/html_cenove-mapy/"
html = requests.get(base + "Mapa_Praha_15.5.2026.html", headers=UA, timeout=60).text
print("delka:", len(html))
for tok in ("bindTooltip", "bindPopup", "L.geoJson", "L.geoJSON", "fetch(", "getJSON", "XMLHttpRequest", "<script src", "addSource"):
    print(f"'{tok}':", html.count(tok))
# vsechny src/href (i relativni)
for u in sorted(set(re.findall(r'(?:src|href)=["\']([^"\']{4,120})["\']', html)))[:40]:
    print("URL:", u)
# okoli prvnich vyskytu geojson
for m in list(re.finditer(r'geojson', html, re.I))[:6]:
    print("CTX:", html[max(0,m.start()-120):m.start()+180].replace("\n"," ")[:300])
    print("---")
