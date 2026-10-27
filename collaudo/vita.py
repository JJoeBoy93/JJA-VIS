"""La vita prima del lavoro (27/10): «Cosa fai nella vita?» prima di «Che lavoro fai?».

    CHROMIUM=/percorso/chrome python3 collaudo/vita.py index.html

JJ, 26 ottobre 2026, accanto a sua nonna che provava JJA-VIS: «per la sua categoria,
anziani pensionati, manca totalmente il senso, il lavoro non lo fanno più». Scene,
con la porta finta (telefono 390×844):
1. dopo «come ti chiami» compare #d0 con le quattro scelte, e #d1 non c'è ancora
2. «Lavoro» → #d1 «Che lavoro fai?» come prima
3. «Studio» → mestiere Studio, si salta #d1, #d2 ha le liste di Studio
4. «Sono in pensione» → si salta #d1, #d2 «Cosa ti piacerebbe non dover più ricordare?»
   con «Bollette e scadenze», i progetti di casa, e fino in fondo manda() spedisce vita
5. ricaricando a metà, la domanda si riprende (anche senza mestiere)
6. chat vuota: con vita pensione i tasti sono i tre nuovi e il terzo risponde subito,
   senza chiamare la porta; con vita lavoro (o niente) sono i tre di sempre
7. il saluto di chi torna e le domande del ritorno: niente lavoro per pensione e casa
8. chi ha già mandato il sondaggio prima di oggi (inviato, senza vita): niente #d0
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

PAGINA = open(sys.argv[1], encoding="utf-8").read()
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
CORS = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "*"}
CHI = "4b675b9f2df739ec"
INIZIO = {"id": CHI, "nome": "Arya", "tema": "calmo", "inizio": "o3"}    # a metà dei passi iniziali: manca «come ti chiami»
DI_CASA = {"id": CHI, "nome": "Arya", "tema": "calmo", "tuo": "Rosa", "inviato": True, "primo": True,
           "tempo": "Bollette e scadenze", "conosciute": {"inizio": "Dopo le 8"}}
BASE_TASTI = ["⏰ Ricordami una cosa", "💶 Segnami una scadenza", "🎒 Cosa porto quando esco"]
CASA_TASTI = ["⏰ Ricordami una visita", "💶 Segnami una bolletta", "🛡 Un messaggio sospetto?"]
FISSA = "Incollami qui il messaggio o raccontami la telefonata: ti dico cosa ne penso. Nel dubbio non toccare link e non dare codici a nessuno."
spedite = []      # i sondaggi arrivati alla porta finta
chiamate = []     # le chiamate all'assistente e a /parla

prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))

async def instrada(route):
    r = route.request; u = r.url
    if u.startswith(BASE): return await route.fulfill(body=PAGINA if u.split("?")[0] in (BASE, BASE + "index.html") else "{}", content_type="text/html")
    if "workers.dev" in u:
        if r.method == "OPTIONS": return await route.fulfill(status=204, headers={**CORS, "Access-Control-Allow-Methods": "POST, GET"})
        if u.endswith("/risposta"):
            spedite.append(json.loads(r.post_data or "{}"))
            return await route.fulfill(status=201, body=json.dumps({"ok": True}), content_type="application/json", headers=CORS)
        if u.endswith("/assistente") or u.endswith("/parla"):
            chiamate.append(u)
            return await route.fulfill(status=502, body="{}", content_type="application/json", headers=CORS)
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": []}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    return await route.fulfill(status=404, body="")

async def apri(b, io, attesa=4500):
    ctx = await b.new_context(viewport={"width": 390, "height": 844})
    await ctx.route("**/*", instrada)
    pg = await ctx.new_page()
    await pg.goto(BASE + "index.html")
    await pg.evaluate("([io]) => { localStorage.setItem('jjavis-io', JSON.stringify(io)); localStorage.setItem('jjavis-conto', 't'.repeat(64)); }", [io])
    await pg.reload(); await pg.wait_for_timeout(attesa)
    return ctx, pg

vede = lambda pg, sel: pg.evaluate("s => { const e = document.querySelector(s); return !!e && e.offsetParent !== null }", sel)
leggi_io = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('jjavis-io'))")
testi = lambda pg, sel: pg.evaluate("s => [...document.querySelectorAll(s)].map(x => x.textContent.trim())", sel)

async def dopo_nome(b):
    """Finito «come ti chiami»: il sondaggio comincia (benvenuto(false))."""
    ctx, pg = await apri(b, INIZIO, 2500)
    await pg.click("#salta-o3"); await pg.wait_for_timeout(3300)
    return ctx, pg

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)

        print("── 1. dopo «come ti chiami»: prima la vita")
        ctx, pg = await dopo_nome(b)
        prova("1. compare #d0 «Cosa fai nella vita?»", await vede(pg, "#d0") and "Cosa fai nella vita?" in await pg.inner_text("#d0"))
        prova("1. con le quattro scelte", await testi(pg, "#d0 .scelta") == ["Lavoro", "Sono in pensione", "Studio", "Sto a casa"], await testi(pg, "#d0 .scelta"))
        prova("1. e #d1 «Che lavoro fai?» non c'è ancora", not await vede(pg, "#d1") and not await vede(pg, "#d2"))
        prova("1. «Adesso imparo te» è sopra", await vede(pg, "#tocca"))
        await ctx.close()

        print("── 2. «Lavoro» porta a #d1 come oggi")
        ctx, pg = await dopo_nome(b)
        await pg.click('#d0 .scelta:has-text("Lavoro")'); await pg.wait_for_timeout(400)
        io = await leggi_io(pg)
        prova("2. #d1 «Che lavoro fai?» c'è, #d0 se n'è andata", await vede(pg, "#d1") and "Che lavoro fai?" in await pg.inner_text("#d1") and not await vede(pg, "#d0"))
        prova("2. #d2 ancora no, e le scelte sono i mestieri di sempre", not await vede(pg, "#d2") and "Corriere o autista" in await testi(pg, "#d1 .scelta"))
        prova("2. io.vita = lavoro", io.get("vita") == "lavoro", io)
        await pg.click('#d1 .scelta:has-text("Corriere")'); await pg.wait_for_timeout(400)
        prova("2. scelto il mestiere: #d2 «Cosa ti fa perdere più tempo?» con le liste del corriere",
              await vede(pg, "#d2") and "Cosa ti fa perdere più tempo?" in await pg.inner_text("#d2") and "Costruire il giro del mattino" in await testi(pg, "#d2 .scelta"))
        await ctx.close()

        print("── 3. «Studio» salta #d1")
        ctx, pg = await dopo_nome(b)
        await pg.click('#d0 .scelta:has-text("Studio")'); await pg.wait_for_timeout(400)
        io = await leggi_io(pg)
        prova("3. salta #d1 e va a #d2", not await vede(pg, "#d1") and await vede(pg, "#d2"))
        prova("3. #d2 ha le liste di Studio", "Organizzare lo studio" in await testi(pg, "#d2 .scelta") and "Cosa ti fa perdere più tempo?" in await pg.inner_text("#d2"), await testi(pg, "#d2 .scelta"))
        prova("3. io.vita = studio e io.mestiere = Studio", io.get("vita") == "studio" and io.get("mestiere") == "Studio", io)
        await ctx.close()

        print("── 4. «Sono in pensione»: #d2 è suo, e manda() spedisce vita")
        spedite.clear(); chiamate.clear()
        ctx, pg = await dopo_nome(b)
        await pg.click('#d0 .scelta:has-text("Sono in pensione")'); await pg.wait_for_timeout(400)
        io = await leggi_io(pg)
        prova("4. salta #d1 (mestiere vuoto)", not await vede(pg, "#d1") and await vede(pg, "#d2") and not io.get("mestiere"), io)
        prova("4. io.vita = pensione", io.get("vita") == "pensione", io)
        prova("4. #d2 «Cosa ti piacerebbe non dover più ricordare?»", "Cosa ti piacerebbe non dover più ricordare?" in await pg.inner_text("#d2") and "Cosa ti fa perdere più tempo?" not in await pg.inner_text("#d2"))
        prova("4. con le sei scelte, «Bollette e scadenze» compresa",
              await testi(pg, "#d2 .scelta") == ["Visite e appuntamenti dal medico", "Bollette e scadenze", "Documenti da rinnovare", "Bandi e agevolazioni", "Compleanni e ricorrenze", "Messaggi e telefonate sospette"], await testi(pg, "#d2 .scelta"))
        prova("4. l'esempio nella casella", await pg.get_attribute("#dettaglio", "placeholder") == "Per esempio: mi dimentico sempre quando scade…")
        prova("4. niente liste dei mestieri", "Organizzare la giornata" not in await testi(pg, "#d2 .scelta") and "Costruire il giro del mattino" not in await testi(pg, "#d2 .scelta"))
        # 27/10, JJ dal telefono: scrivendo con parole sue «Vai avanti» restava spento finché non toccava una scelta
        prova("4b. senza scelta e senza testo «Vai avanti» è spento", await pg.is_disabled("#avanti2"))
        await pg.fill("#dettaglio", "mi scordo sempre la bolletta della luce")
        prova("4b. basta scrivere con parole sue: «Vai avanti» si accende", not await pg.is_disabled("#avanti2"))
        await pg.fill("#dettaglio", "   ")
        prova("4b. solo spazi non bastano", await pg.is_disabled("#avanti2"))
        await pg.fill("#dettaglio", "")
        await pg.click('#d2 .scelta:has-text("Bollette e scadenze")'); await pg.click("#avanti2"); await pg.wait_for_timeout(400)
        prova("4. #d3 resta, con la sua domanda", await vede(pg, "#d3") and "Se lo facessi io al posto tuo, quanto varrebbe al mese?" in await pg.inner_text("#d3"))
        await pg.click("#avanti3"); await pg.wait_for_timeout(400)
        progetti = await testi(pg, "#progetti .scelta")
        prova("4. #d5 ha i progetti di casa",
              progetti == ["Promemoria delle visite e delle medicine", "Bollette e scadenze sotto controllo", "Documenti da rinnovare in tempo", "Bandi e agevolazioni del mio Comune", "Compleanni e ricorrenze di famiglia", "Un messaggio sospetto? Chiedilo prima a me"], progetti)
        prova("4. e l'ultima domanda non parla del suo lavoro", "il tuo lavoro" not in await pg.evaluate("document.querySelector('#d4').textContent"))
        await pg.click("#progetti .scelta >> nth=1"); await pg.click("#avanti5"); await pg.wait_for_timeout(400)
        await pg.click("#senza"); await pg.wait_for_timeout(1500)
        prova("4. manda(): al sondaggio arriva una sola risposta", len(spedite) == 1, spedite)
        s = spedite[0] if spedite else {}
        prova("4. …con vita = pensione, mestiere vuoto e la cosa scelta in #d2", s.get("vita") == "pensione" and not s.get("mestiere") and s.get("tempo") == "Bollette e scadenze", s)
        prova("4. …e i voti", s.get("voti") == ["Bollette e scadenze sotto controllo"], s)
        await ctx.close()

        print("── 5. ricaricando a metà, si riprende")
        ctx, pg = await dopo_nome(b)
        await pg.click('#d0 .scelta:has-text("Sono in pensione")'); await pg.wait_for_timeout(400)
        await pg.click('#d2 .scelta:has-text("Documenti da rinnovare")'); await pg.wait_for_timeout(200)
        await pg.reload(); await pg.wait_for_timeout(2500)
        io = await leggi_io(pg)
        prova("5. la domanda di adesso (#d2) si riapre, non #d0", await vede(pg, "#d2") and not await vede(pg, "#d0") and not await vede(pg, "#d1"))
        prova("5. con le liste di casa e la scelta già segnata", "Bandi e agevolazioni" in await testi(pg, "#d2 .scelta") and "Cosa ti piacerebbe non dover più ricordare?" in await pg.inner_text("#d2")
              and await pg.evaluate("document.querySelector('#d2 .scelta[aria-pressed=true]') && document.querySelector('#d2 .scelta[aria-pressed=true]').textContent.trim()") == "Documenti da rinnovare")
        prova("5. io.vita resta pensione", io.get("vita") == "pensione", io)
        await ctx.close()
        # a metà di #d0: si ricomincia da #d0
        ctx, pg = await dopo_nome(b)
        await pg.reload(); await pg.wait_for_timeout(2500)
        prova("5. senza aver risposto a #d0, ricaricando c'è ancora #d0", await vede(pg, "#d0") and not await vede(pg, "#d1"))
        await ctx.close()
        # «Lavoro» detto ma mestiere no: si riprende da #d1
        ctx, pg = await dopo_nome(b)
        await pg.click('#d0 .scelta:has-text("Lavoro")'); await pg.wait_for_timeout(400)
        await pg.reload(); await pg.wait_for_timeout(2500)
        prova("5. detto «Lavoro» ma non il mestiere: ricaricando si riapre #d1", await vede(pg, "#d1") and not await vede(pg, "#d0"))
        await ctx.close()

        print("── 6. i tre tasti della chat vuota")
        chiamate.clear()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione"})
        tasti = await testi(pg, "#prove-chat .prova-chat")
        prova("6. vita pensione: «🛡 Un messaggio sospetto?» e gli altri due nuovi", tasti == CASA_TASTI, tasti)
        await pg.click('#prove-chat .prova-chat >> text=Un messaggio sospetto?'); await pg.wait_for_timeout(500)
        chat = await pg.inner_text("#chat"); io = await leggi_io(pg)
        prova("6. toccarlo dà la risposta fissa, subito", FISSA in chat and "Un messaggio sospetto?" in chat, chat[:300])
        prova("6. senza chiamare la porta", chiamate == [], chiamate)
        prova("6. e ha il suo «contesto» per la risposta che segue", "Un messaggio sospetto?" in (io.get("chat") or [{}])[-1].get("contesto", ""), io.get("chat"))
        await ctx.close()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "casa"})
        prova("6. vita casa: gli stessi tre tasti", await testi(pg, "#prove-chat .prova-chat") == CASA_TASTI)
        await pg.click('#prove-chat .prova-chat >> text=Ricordami una visita'); await pg.wait_for_timeout(400)
        prova("6. «Ricordami una visita» risponde subito", "Rosa" in await pg.inner_text("#chat") and "che visita è" in await pg.inner_text("#chat"))
        await ctx.close()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "lavoro", "mestiere": "Negozio o commercio"})
        prova("6. vita lavoro: i tre tasti di oggi", await testi(pg, "#prove-chat .prova-chat") == BASE_TASTI, await testi(pg, "#prove-chat .prova-chat"))
        await ctx.close()

        print("── 7. chi torna: il saluto e le domande")
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione"})
        saluto = await pg.evaluate("document.querySelector('#saluto2').textContent")
        prova("7. pensione: «So che sei in pensione» e la cosa scelta", "So che sei in pensione" in saluto and "bollette e scadenze" in saluto and "lavor" not in saluto, saluto)
        d = await pg.evaluate("document.querySelector('#conosci-domanda').textContent")
        prova("7. la domanda del ritorno non parla di lavoro", "lavori" not in d and "lavoro" not in d and d == "Come vuoi che ti parli?", d)
        await ctx.close()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "casa"})
        saluto = await pg.evaluate("document.querySelector('#saluto2').textContent")
        prova("7. casa: «So che stai a casa»", "So che stai a casa" in saluto, saluto)
        await ctx.close()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "lavoro", "mestiere": "Negozio o commercio", "tempo": "Scorte da controllare"})
        saluto = await pg.evaluate("document.querySelector('#saluto2').textContent")
        d = await pg.evaluate("document.querySelector('#conosci-domanda').textContent")
        prova("7. lavoro: come prima (la riga del mestiere e la domanda sul telefono)", "So che lavori nel commercio" in saluto and d == "Mentre lavori, il telefono dov'è?", [saluto, d])
        await ctx.close()

        print("── 8. chi ha già mandato il sondaggio prima di oggi")
        chiamate.clear()
        ctx, pg = await apri(b, {**DI_CASA, "mestiere": "Negozio o commercio"})
        prova("8. inviato senza vita: niente #d0, niente #tocca", not await vede(pg, "#d0") and not await vede(pg, "#tocca") and not await vede(pg, "#d1"))
        prova("8. apre direttamente la chat, coi tasti di sempre", await vede(pg, "#chat-area") and await testi(pg, "#prove-chat .prova-chat") == BASE_TASTI)
        prova("8. nessuna domanda nuova: non gli si chiede la vita", "vita" not in (await leggi_io(pg)))
        await ctx.close()
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} verdi"); print("VERDE" if all(prove) else "ROSSO"); sys.exit(0 if all(prove) else 1)   # VERDE/ROSSO: è l'ultima riga che legge Hera

asyncio.run(main())
