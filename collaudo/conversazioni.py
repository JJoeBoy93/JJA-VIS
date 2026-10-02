"""La chat si riapre pulita se tutto è letto; com'era se c'è qualcosa da leggere.

    CHROMIUM=/percorso/chrome python3 collaudo/conversazioni.py index.html

JJ, 2 ottobre 2026: «quando apro è pulita col nuovo saluto… una parte dove
restano i thread precedenti… se lui manda la domanda che richiede la risposta
da me e io rispondo quando lui non guarda, quando rientra ha il thread ancora
da leggere; se invece lo legge e rientra, trova la chat pulita».
La porta finta rimanda SEMPRE tutte le risposte, come quella vera.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

PAGINA = open(sys.argv[1], encoding="utf-8").read()
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
CORS = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"}
RISPOSTA_Q1 = {"id": "q1", "domanda": "Quanto costa un sito?", "risposta": "Dipende da cosa deve fare: ti scrivo io."}
RISPOSTE = []   # cosa rimanda la porta, scena per scena
IO = {"id": "a1b2c3d4e5f60718", "nome": "Nova", "tema": "tech", "inviato": True, "mestiere": "Corriere o autista"}

prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))

async def instrada(route):
    u = route.request.url
    if u.startswith(BASE): return await route.fulfill(body=PAGINA, content_type="text/html")
    if "workers.dev" in u:
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": RISPOSTE}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    if u.startswith("about:"): return await route.continue_()
    return await route.abort()

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        await ctx.route("**/*", instrada)
        p = await ctx.new_page(); errori = []
        p.on("pageerror", lambda e: errori.append(str(e)))
        await p.goto(BASE + "index.html"); await p.wait_for_timeout(300)
        async def metti(io):
            await p.evaluate(f"localStorage.setItem('jjavis-io', {json.dumps(json.dumps(io))})")
        async def entra(dove=""):
            # da una pagina bianca: index.html → index.html#bottega cambierebbe solo l'ancora, senza ricaricare
            await p.goto("about:blank"); await p.goto(BASE + "index.html" + dove); await p.wait_for_timeout(1800)
        stato = lambda: p.evaluate("JSON.parse(localStorage.getItem('jjavis-io')||'{}')")
        bolle = lambda: p.evaluate("[...document.querySelectorAll('#chat .bolla')].map(b=>b.textContent)")

        # 1. tutto letto: si riapre pulita, la conversazione va nelle precedenti
        await metti({**IO, "chat": [{"ruolo": "tu", "testo": "Ciao, che fai?", "id": "x0", "attesa": False},
                                    {"ruolo": "io", "testo": "Imparo il tuo lavoro.", "id": "x0-n"}]})
        await entra()
        prova("tutto letto: la chat si riapre pulita", await bolle() == [], await bolle())
        prova("le conversazioni precedenti si vedono, con quella di prima",
              await p.evaluate("!!document.getElementById('vecchie') && !document.getElementById('vecchie').hidden && document.getElementById('vecchie-elenco').textContent.includes('Ciao, che fai?')"))

        # 2. una domanda in attesa; la risposta arriva mentre si è altrove (scheda Bottega)
        RISPOSTE.append(RISPOSTA_Q1)
        await metti({**IO, "chat": [{"ruolo": "tu", "testo": "Quanto costa un sito?", "id": "q1", "attesa": True}]})
        await entra("#bottega")
        s = await stato()
        prova("risposta arrivata ma non vista: resta da leggere", any(m.get("nuovo") for m in s.get("chat", [])), s.get("chat"))
        await entra()
        prova("rientrando, il thread è ancora lì con la risposta", "Dipende da cosa deve fare: ti scrivo io." in "".join(await bolle()), await bolle())
        s = await stato()
        prova("adesso che l'ha vista, è letta", not any(m.get("nuovo") for m in s.get("chat", [])), s.get("chat"))

        # 3. rientra di nuovo: pulita, e la risposta (che la porta rimanda sempre) non torna
        await entra()
        prova("letta e rientrato: chat pulita", await bolle() == [], await bolle())
        s = await stato()
        prova("la risposta già letta non torna nella chat nuova", not s.get("chat"), s.get("chat"))
        archivio = json.dumps(s.get("thread", []), ensure_ascii=False)
        prova("la conversazione letta è nelle precedenti, con la risposta", "Dipende da cosa deve fare" in archivio, archivio[:120])
        prova("nessun errore JavaScript", not errori, errori[:3])
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} prove\n" + ("VERDE" if all(prove) else "ROSSO"))

asyncio.run(main())
