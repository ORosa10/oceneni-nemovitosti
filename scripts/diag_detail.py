# Diagnostika v6: odkud mapa bere data (getJSON/XHR kontexty)
import re, requests

UA = {"User-Agent": "Mozilla/5.0"}
base = "https://mf.gov.cz/assets/cs/cmsmedia/html_cenove-mapy/"
html = requests.get(base + "Mapa_Praha_15.5.2026.html", headers=UA, timeout=60).text
for tok in ("getJSON", "XMLHttpRequest", 'open("GET"', "open('GET'", ".json", ".js\"", "bindPopup"):
    for m in list(re.finditer(re.escape(tok), html))[:4]:
        print(f"[{tok}] CTX:", html[max(0,m.start()-200):m.start()+250].replace("\n"," ")[:450])
        print("---")
