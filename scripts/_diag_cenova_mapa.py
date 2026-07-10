"""DOCASNY diagnosticky skript (smazat po dokonceni ukolu #16)."""
import re
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

r = requests.get("https://www.sreality.cz/cenova-mapa", headers=H, timeout=30)
html = r.text

out_lines = []
out_lines.append(f"status={r.status_code} len={len(html)}")

# hrefy vedouci na cenova-mapa podstranky
hrefy = sorted(set(re.findall(r'href=\\?"(/cenova-mapa[^"\\]*)"?', html)))
out_lines.append(f"pocet unikatnich hrefu /cenova-mapa*: {len(hrefy)}")
out_lines.extend(hrefy[:60])

# API volani pouzivana klientskym JS (hleda /api/ retezce)
apis = sorted(set(re.findall(r'"(/api/[a-zA-Z0-9/_\\-]*)"', html)))
out_lines.append(f"--- /api/ retezce ({len(apis)}) ---")
out_lines.extend(apis[:60])

# cokoliv obsahujici 'priceMap' nebo 'pricemap' case-insensitive kolem API
pm = sorted(set(re.findall(r'[\\w/-]*[Pp]rice[Mm]ap[\\w/-]*', html)))
out_lines.append(f"--- priceMap retezce ({len(pm)}) ---")
out_lines.extend(pm[:60])

with open("docs/diag_cenmapa_hrefy.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print("hotovo")
