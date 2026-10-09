"""Poly Haven per JJA-VIS: cerca e scarica modelli CC0 (JJ, 9/10: «fai una action diretta per usare poly, io ho difficoltà
a scaricarle sul telefono»). Gira nelle Actions (.github/workflows/polyhaven.yml), che hanno la rete; la sandbox di Athena no.

  python3 strumenti/polyhaven.py catalogo            -> modelli/polyhaven/catalogo.json e catalogo.md
  python3 strumenti/polyhaven.py scarica id1,id2 1k  -> modelli/polyhaven/<id>.glb (un file solo, texture dentro)

Le regole (verificate il 9/10 su github.com/Poly-Haven/Public-API, ToS.md): gli asset sono CC0, senza attribuzione; l'API
è gratis anche per uso commerciale ma vuole uno User-Agent col nome del programma. Il credito «Powered by Poly Haven»
serve solo se un prodotto chiama l'API dal vivo per mostrare i loro contenuti: la città no, i file stanno nel nostro repo.
Endpoint (swagger.yml del loro repo): /assets?type=models, /files/{id} -> gltf[ris].gltf = {url, md5, size, include}.
"""
import hashlib, json, os, subprocess, sys, urllib.request

API = "https://api.polyhaven.com"
UA = "JJA-VIS-polyhaven/1.0 (+https://jjoeboy93.github.io/JJA-VIS/)"
DOVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "modelli", "polyhaven")

def prendi(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
        return r.read()

def catalogo():
    dati = json.loads(prendi(f"{API}/assets?type=models"))
    voci = {}
    for i, a in dati.items():
        voci[i] = {"nome": a.get("name"), "categorie": a.get("categories", []), "tag": a.get("tags", []),
                   "poligoni": a.get("polycount"), "dimensioni_mm": a.get("dimensions")}
    os.makedirs(DOVE, exist_ok=True)
    json.dump(voci, open(os.path.join(DOVE, "catalogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    per = {}
    for i, v in voci.items():
        for c in v["categorie"] or ["(senza categoria)"]: per.setdefault(c, []).append(i)
    righe = [f"# Catalogo dei modelli di Poly Haven — {len(voci)} modelli", "",
             "Scritto dalla Action «polyhaven» (strumenti/polyhaven.py). Tutti CC0. Per scaricarne uno: Action → scarica → id.", ""]
    for c in sorted(per):
        righe.append(f"## {c} ({len(per[c])})"); righe.append(", ".join(sorted(per[c]))); righe.append("")
    open(os.path.join(DOVE, "catalogo.md"), "w", encoding="utf-8").write("\n".join(righe))
    print(f"catalogo: {len(voci)} modelli, {len(per)} categorie")

def scarica(ids, ris):
    os.makedirs(DOVE, exist_ok=True); fatti, mancati = [], []
    for i in [x.strip() for x in ids.split(",") if x.strip()]:
        try:
            f = json.loads(prendi(f"{API}/files/{i}"))
            g = f.get("gltf", {})
            r = ris if ris in g else sorted(g, key=lambda k: int(k.rstrip("k") or 0))[0]
            voce = g[r]["gltf"]; tmp = os.path.join("/tmp/polyhaven", i); os.makedirs(tmp, exist_ok=True)
            for rel, ff in [(os.path.basename(voce["url"]), voce)] + list(voce.get("include", {}).items()):
                b = prendi(ff["url"])
                if ff.get("md5") and hashlib.md5(b).hexdigest() != ff["md5"]: raise RuntimeError(f"md5 diverso per {rel}")
                p = os.path.join(tmp, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(b)
            fuori = os.path.join(DOVE, f"{i}.glb")
            subprocess.run(["npx", "--yes", "gltf-pipeline@4.1.0", "-i", os.path.join(tmp, os.path.basename(voce["url"])), "-o", fuori], check=True)
            fatti.append(f"{i} ({r}, {os.path.getsize(fuori)//1024} kB)")
        except Exception as e:   # un guasto si dice: «non ci sono riuscito» non è «zero»
            mancati.append(f"{i}: {e}")
    print("scaricati:", fatti or "nessuno"); print("NON scaricati:", mancati or "nessuno")
    if mancati: sys.exit(1)

if __name__ == "__main__":
    cosa = sys.argv[1] if len(sys.argv) > 1 else ""
    if cosa == "catalogo": catalogo()
    elif cosa == "scarica": scarica(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "1k")
    else: sys.exit(__doc__)
