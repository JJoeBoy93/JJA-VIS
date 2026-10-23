"""NASCE (22/10): /nato appena finiti nome, tema e «come ti chiami». Riusa la porta finta di primo.py.
Il primo incontro: con l'account, la prima volta l'assistente propone subito (22/10).

    CHROMIUM=/percorso/chrome python3 collaudo/primo.py index.html

JJ, 22 ottobre 2026: «quando viene usato per la prima volta, è proprio quando
deve colpire per la sua utilità… in questo caso non ha neanche proposto
niente, deve farlo». Scene, con la porta finta:
1. sondaggio già fatto, account, mai avuta la proposta: all'apertura parte UNA
   richiesta {primo:true, chi}, la risposta compare in chat, io.primo resta
2. si ricarica: nessuna seconda richiesta
3. la porta dice «gia» (aveva già parlato): niente bolla, io.primo segnato
4. la porta cade: lo dice («non ci sono riuscito»), io.primo NON segnato
5. senza account: nessuna richiesta all'assistente
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

PAGINA = open(sys.argv[1], encoding="utf-8").read()
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
CORS = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "*"}
IO = {"id": "4b675b9f2df739ec", "nome": "Arya", "tema": "calmo", "tuo": "Giada", "inviato": True, "mestiere": "Negozio o commercio",
      "tempo": "Ricordarmi dei clienti abituali", "conosciute": {"inizio": "Cambia ogni giorno"}}
PROPOSTA = "Ciao Giada, sono Arya. Da oggi ti ricordo gli impegni e cosa portarti dietro. Cosa hai domani?"
scena = {"porta": "ok"}
chiamate = []
nati = []

prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))

async def instrada(route):
    r = route.request; u = r.url
    if u.startswith(BASE): return await route.fulfill(body=PAGINA if u.split("?")[0] in (BASE, BASE + "index.html") else "{}", content_type="text/html")
    if "workers.dev" in u:
        if r.method == "OPTIONS": return await route.fulfill(status=204, headers={**CORS, "Access-Control-Allow-Methods": "POST, GET"})
        if u.endswith("/nato"):
            nati.append(json.loads(r.post_data or "{}"))
            return await route.fulfill(status=201, body=json.dumps({"ok": True, "detto": True}), content_type="application/json", headers=CORS)
        if u.endswith("/assistente"):
            chiamate.append(json.loads(r.post_data or "{}"))
            if scena["porta"] == "giu": return await route.fulfill(status=502, body="{}", content_type="application/json", headers=CORS)
            if scena["porta"] == "gia": return await route.fulfill(body=json.dumps({"gia": True}), content_type="application/json", headers=CORS)
            return await route.fulfill(body=json.dumps({"risposta": PROPOSTA, "primo": True}), content_type="application/json", headers=CORS)
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": []}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    return await route.fulfill(status=404, body="")

async def apri(b, io, token):
    ctx = await b.new_context(viewport={"width": 390, "height": 840})
    await ctx.route("**/*", instrada)
    pg = await ctx.new_page()
    await pg.goto(BASE + "index.html")
    await pg.evaluate("([io, t]) => { localStorage.setItem('jjavis-io', JSON.stringify(io)); if (t) localStorage.setItem('jjavis-conto', t); }", [io, token])
    await pg.reload(); await pg.wait_for_timeout(4500)
    return ctx, pg

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        # 1: alla fine di «come ti chiami» (salta) parte /nato, prima di qualsiasi domanda
        nati.clear(); io0 = {"id": "4b675b9f2df739ec", "nome": "Arya", "tema": "calmo", "inizio": "o3"}
        ctx, pg = await apri(b, io0, "t" * 64)
        prova("0. a metà dei passi iniziali non nasce ancora", len(nati) == 0, nati)
        await pg.click("#salta-o3"); await pg.wait_for_timeout(1500)
        io = json.loads(await pg.evaluate("localStorage.getItem('jjavis-io')"))
        prova("1. finiti nome, tema e nome suo: parte /nato col codice, il nome e il tema", len(nati) == 1 and nati[0]["chi"] == io0["id"] and nati[0]["nome_assistente"] == "Arya" and nati[0]["tema"] == "calmo", nati)
        prova("1. io.nato segnato, e il sondaggio non è ancora fatto", io.get("nato") is True and not io.get("inviato"), io)
        await pg.reload(); await pg.wait_for_timeout(3000)
        prova("2. ricaricando: una volta sola", len(nati) == 1, nati)
        await ctx.close()
        # 3: chi aveva già finito senza nascita la riceve all'apertura
        nati.clear(); ctx, pg = await apri(b, {**IO}, "t" * 64)
        prova("3. all'apertura, chi non era ancora nato nasce", len(nati) == 1, nati); await ctx.close()
        # 4: senza account niente
        nati.clear(); ctx, pg = await apri(b, {**IO}, "")
        prova("4. senza account: niente /nato", len(nati) == 0, nati); await ctx.close()
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} verdi"); print("VERDE" if all(prove) else "ROSSO"); sys.exit(0 if all(prove) else 1)   # VERDE/ROSSO: è l'ultima riga che legge Hera

asyncio.run(main())
