# Diagnostika v3: data z MFČR mapy Prahy (vložený HTML soubor)
import json, re, requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
url = "https://mf.gov.cz/assets/cs/cmsmedia/html_cenove-mapy/Mapa_Praha_15.5.2026.html"
r = requests.get(url, headers=UA, timeout=60)
html = r.text
print("HTTP", r.status_code, "| delka:", len(html))
# typicky folium/plotly/leaflet: hledej GeoJSON/data bloky
for token in ("najem", "nájemné", "Kč/m", "geojson", "GeoJSON", "features", "plotly", "folium", "leaflet", "customdata", "hovertext"):
    print(f"vyskyt '{token}':", html.count(token))
# ukázky kontextu kolem 'Kč' a nazvu mestske casti
for m in re.finditer(r'Praha[ 0-9]{0,3}[^{}<>]{0,120}', html):
    s = m.group(0)
    if any(c.isdigit() for c in s):
        print("KONTEXT:", s[:150])
        if m.start() > 60000: break
