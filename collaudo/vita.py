"""La vita prima del lavoro (27/10): «Cosa fai nella vita?» prima di «Che lavoro fai?».

    CHROMIUM=/percorso/chrome python3 collaudo/vita.py index.html

JJ, 26 ottobre 2026, accanto a sua nonna che provava JJA-VIS: «per la sua categoria,
anziani pensionati, manca totalmente il senso, il lavoro non lo fanno più». Scene,
con la porta finta (telefono 390×844):
1. dopo «come ti chiami» compare #d0 con le quattro scelte, e #d1 non c'è ancora
2. «Lavoro» → #d1 «Che lavoro fai?» come prima
3. «Studio» → mestiere Studio, si salta #d1, #d2 ha le liste di Studio
4. «Sono in pensione» → si salta #d1, #d2 «In cosa ti piacerebbe essere assistito da me?»
   con «Bollette e scadenze», i progetti di casa, e fino in fondo manda() spedisce vita
5. ricaricando a metà, la domanda si riprende (anche senza mestiere)
6. chat vuota: con vita pensione i tasti sono i tre nuovi e il terzo risponde subito,
   senza chiamare la porta; con vita lavoro (o niente) sono i tre di sempre
7. il saluto di chi torna e le domande del ritorno: niente lavoro per pensione e casa
8. chi ha già mandato il sondaggio prima di oggi (inviato, senza vita): niente #d0
9. (28/10) le domande del ritorno: con vita pensione o casa mai «soldi» e prima o poi «spese»
   («Dove ti farebbe più comodo risparmiare?»); con vita lavoro mai «spese», e «soldi» c'è
10. (28/10) #ricordo: con l'account «su ogni telefono da cui entri col tuo account», senza
   «solo su questo telefono»; e cambia quando l'account arriva o se ne va, senza ricaricare
11. (28/10) parlaAssistente() e parla() mandano la vita alla porta (profilo.vita)
12. (28/10) «Imparo te», nel Profilo (JJ: «tutto ciò che riguarda le domande personali e l'imparo te va nel Profilo»;
   «bisogna poter modificare le voci senza dimentica tutto»): la domanda di oggi, il lavoro di una vita (solo pensione/casa)
   e le passioni (per tutti, scelta multipla, casella libera, un testo ≤120) SI VEDONO nel Profilo, non nella chat né nel
   benvenuto; «Cambia» riapre una voce già segnata, «Togli» chiede conferma e toglie solo quella; cambiare la vita cambia
   le domande; il pallino sul ☰ e sulla voce Profilo del menù c'è finché c'è una domanda
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
import aiuti; aiuti.sezioni_aperte()   # 28/10: le sezioni dei pannelli sono chiuse finché non si toccano; qui si aprono tutte (collaudo/sezioni.py prova le chiuse)

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
conoscenze = []   # le risposte del ritorno arrivate a /conoscenza
chiamate = []     # le chiamate all'assistente e a /parla
corpi = []        # e cosa mandano: (url, corpo)

prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))

async def instrada(route):
    r = route.request; u = r.url
    if u.startswith(BASE): return await route.fulfill(body=PAGINA if u.split("?")[0] in (BASE, BASE + "index.html") else "{}", content_type="text/html")
    if "workers.dev" in u:
        if r.method == "OPTIONS": return await route.fulfill(status=204, headers={**CORS, "Access-Control-Allow-Methods": "POST, GET"})
        if u.endswith("/conoscenza"):
            conoscenze.append(json.loads(r.post_data or "{}"))
            return await route.fulfill(status=201, body=json.dumps({"ok": True}), content_type="application/json", headers=CORS)
        if u.endswith("/risposta"):
            spedite.append(json.loads(r.post_data or "{}"))
            return await route.fulfill(status=201, body=json.dumps({"ok": True}), content_type="application/json", headers=CORS)
        if u.endswith("/assistente") or u.endswith("/parla"):
            chiamate.append(u); corpi.append((u, json.loads(r.post_data or "{}")))
            return await route.fulfill(status=502, body="{}", content_type="application/json", headers=CORS)
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": []}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    return await route.fulfill(status=404, body="")

async def apri(b, io, attesa=4500, conto=True):
    ctx = await b.new_context(viewport={"width": 390, "height": 844})
    await ctx.route("**/*", instrada)
    pg = await ctx.new_page()
    await pg.goto(BASE + "index.html")
    await pg.evaluate("([io, conto]) => { localStorage.setItem('jjavis-io', JSON.stringify(io)); if (conto) localStorage.setItem('jjavis-conto', 't'.repeat(64)); }", [io, conto])
    await pg.reload(); await pg.wait_for_timeout(attesa)
    return ctx, pg

vede = lambda pg, sel: pg.evaluate("s => { const e = document.querySelector(s); return !!e && e.offsetParent !== null }", sel)
leggi_io = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('jjavis-io'))")
vl = lambda pg, sel: pg.locator(sel).first.is_visible()   # selettori di Playwright («>> text=…»): visibile davvero, antenati compresi
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
        prova("4. #d2 «In cosa ti piacerebbe essere assistito da me?»", "In cosa ti piacerebbe essere assistito da me?" in await pg.inner_text("#d2") and "Cosa ti fa perdere più tempo?" not in await pg.inner_text("#d2"))
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
        # 27/10, JJ: il cursore parte da 0 e «Vai avanti» si accende solo dopo averlo mosso (o toccato, per dire 0)
        prova("4c. il cursore parte da 0", await pg.input_value("#prezzo") == "0" and await pg.inner_text("#valore") == "0")
        prova("4c. senza toccarlo «Vai avanti» è spento", await pg.is_disabled("#avanti3"))
        await pg.evaluate("(()=>{const r=document.querySelector('#prezzo');r.value=25;r.dispatchEvent(new Event('input'))})()")
        prova("4c. mosso a 25: «Vai avanti» si accende e il numero segue", not await pg.is_disabled("#avanti3") and await pg.inner_text("#valore") == "25")
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
        # 27/10, JJ: «finite le domande resta così, qui muore il giro, non sai più cosa fare»
        await pg.wait_for_timeout(1200)
        vis = await pg.evaluate("[...document.querySelectorAll('#prove-chat .prova-chat')].filter(b=>b.getClientRects().length).map(b=>b.textContent.trim())")
        prova("4d. finite le domande, sotto «Ricevuto» ci sono i tre tasti (di casa)", vis == CASA_TASTI and await pg.locator("#chat > *").count() >= 1, vis)
        await pg.click('#prove-chat .prova-chat >> text=Ricordami una visita'); await pg.wait_for_timeout(400)
        prova("4d. toccato un tasto, i tasti se ne vanno", not await pg.is_visible("#prove-chat"))
        await ctx.close()

        print("── 5. ricaricando a metà, si riprende")
        ctx, pg = await dopo_nome(b)
        await pg.click('#d0 .scelta:has-text("Sono in pensione")'); await pg.wait_for_timeout(400)
        await pg.click('#d2 .scelta:has-text("Documenti da rinnovare")'); await pg.wait_for_timeout(200)
        await pg.reload(); await pg.wait_for_timeout(2500)
        io = await leggi_io(pg)
        prova("5. la domanda di adesso (#d2) si riapre, non #d0", await vede(pg, "#d2") and not await vede(pg, "#d0") and not await vede(pg, "#d1"))
        prova("5. con le liste di casa e la scelta già segnata", "Bandi e agevolazioni" in await testi(pg, "#d2 .scelta") and "In cosa ti piacerebbe essere assistito da me?" in await pg.inner_text("#d2")
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

        print("── 9. le domande del ritorno: «soldi» a chi lavora, «spese» a chi no")
        SEQ = "() => { const k = []; io.conosciute = {}; for (let i = 0; i < 20; i++) { const q = prossimaDomanda(); if (!q) break; k.push(q.k); io.conosciute[q.k] = 'x'; } return k; }"
        for vita, extra in (("pensione", {}), ("casa", {}), ("lavoro", {"mestiere": "Negozio o commercio"})):
            ctx, pg = await apri(b, {**DI_CASA, "vita": vita, **extra}, 2500)
            seq = await pg.evaluate(SEQ)
            if vita == "lavoro":
                prova(f"9. vita {vita}: «soldi» c'è e «spese» non c'è mai", "soldi" in seq and "spese" not in seq, seq)
            else:
                prova(f"9. vita {vita}: mai «soldi», e prima o poi «spese»", "soldi" not in seq and "spese" in seq, seq)
            await ctx.close()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione"}, 2500)
        d = await pg.evaluate("() => { io.conosciute = {inizio: 'x', parlare: 'x', mestiere_di_una_vita: 'x', passioni: 'x', voce: 'x'}; mostraDomanda(); return [document.querySelector('#conosci-domanda').textContent, [...document.querySelectorAll('#conosci-scelte .scelta')].map(x => x.textContent)]; }")
        prova("9. pensione: la domanda mostrata è «Dove ti farebbe più comodo risparmiare?» con le quattro scelte",
              d[0] == "Dove ti farebbe più comodo risparmiare?" and d[1] == ["Bollette di luce e gas", "La spesa", "Medicine e visite", "Abbonamenti che non uso"], d)
        await ctx.close()

        print("── 10. #ricordo: dipende dall'account")
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione"}, 2500)
        t = await pg.evaluate("document.querySelector('#ricordo').textContent")
        prova("10. con l'account: «su ogni telefono da cui entri col tuo account»", "su ogni telefono da cui entri col tuo account" in t and "solo su questo telefono" not in t, t)
        prova("10. e il Profilo si cambia ancora da lì", "Nome e colore li cambi nel Profilo." in t and await pg.evaluate("!!document.querySelector('#ricordo a[href=\"#profilo\"]')"), t)
        await pg.evaluate("() => { localStorage.removeItem('jjavis-conto'); window.dispatchEvent(new StorageEvent('storage', {key: 'jjavis-conto'})); }")
        t = await pg.evaluate("document.querySelector('#ricordo').textContent")
        prova("10. l'account se ne va (senza ricaricare): «solo su questo telefono»", "solo su questo telefono" in t and "ogni telefono" not in t, t)
        await pg.evaluate("() => { localStorage.setItem('jjavis-conto', 't'.repeat(64)); window.dispatchEvent(new StorageEvent('storage', {key: 'jjavis-conto'})); }")
        t = await pg.evaluate("document.querySelector('#ricordo').textContent")
        prova("10. l'account arriva (senza ricaricare): di nuovo «su ogni telefono»", "su ogni telefono da cui entri col tuo account" in t, t)
        await ctx.close()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione"}, 2500, conto=False)
        t = await pg.evaluate("document.querySelector('#ricordo').textContent")
        prova("10. senza account: «solo su questo telefono», come prima", "Mi ricordo di te solo su questo telefono." in t and "ogni telefono" not in t, t)
        await ctx.close()

        print("── 11. la vita arriva alla porta")
        corpi.clear()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione"}, 2500)
        await pg.evaluate("() => parlaAssistente('Ciao')")
        ass = [c for u, c in corpi if u.endswith("/assistente")]
        prova("11. parlaAssistente manda profilo.vita e chi", bool(ass) and ass[-1].get("profilo", {}).get("vita") == "pensione" and ass[-1].get("chi") == CHI, corpi)
        await pg.evaluate("() => { localStorage.removeItem('jjavis-conto'); }")
        await pg.evaluate("() => parla('Ciao')")
        pa = [c for u, c in corpi if u.endswith("/parla")]
        prova("11. parla manda profilo.vita", bool(pa) and pa[-1].get("profilo", {}).get("vita") == "pensione", corpi)
        await ctx.close()

        print("── 12. «Imparo te», nel Profilo")
        SEQ = "() => { const k = []; io.conosciute = {}; for (let i = 0; i < 20; i++) { const q = prossimaDomanda(); if (!q) break; k.push(q.k); io.conosciute[q.k] = 'x'; } return k; }"
        for vita, extra in (("pensione", {}), ("casa", {}), ("lavoro", {"mestiere": "Negozio o commercio"}), ("studio", {"mestiere": "Studio"})):
            ctx, pg = await apri(b, {**DI_CASA, "vita": vita, **extra}, 2500)
            seq = await pg.evaluate(SEQ)
            if vita in ("pensione", "casa"):
                prova(f"12. vita {vita}: «mestiere_di_una_vita» c'è, dopo «parlare» e prima di «passioni»", "mestiere_di_una_vita" in seq and seq.index("parlare") < seq.index("mestiere_di_una_vita") < seq.index("passioni"), seq)
            else:
                prova(f"12. vita {vita}: «mestiere_di_una_vita» non compare mai", "mestiere_di_una_vita" not in seq, seq)
            prova(f"12. vita {vita}: «passioni» compare (per tutti)", "passioni" in seq, seq)
            await ctx.close()
        PRIMA = {"inizio": "Dopo le 8", "parlare": "Breve e diretto"}
        MESTIERI = ["Corriere o autista", "Negozio o commercio", "Artigiano o tecnico", "Sanità", "Ufficio", "Guida turistica", "Creator o gamer", "Altro"]
        NOVE = ["Orto e giardino", "Cucina", "Nipoti e famiglia", "Lettura", "Viaggi e gite", "Musica e ballo", "Sport", "Volontariato", "Fai da te"]
        punto = lambda pg, sel: pg.evaluate("s => { const e = document.querySelector(s); return !!e && getComputedStyle(e, '::after').content !== 'none' }", sel)
        async def profilo(pg):
            await pg.click("#apri-conv"); await pg.wait_for_timeout(450)
            await pg.click('#menu-schede .menu-scheda[data-vai="profilo"]'); await pg.wait_for_timeout(500)

        # la domanda di oggi sta nel Profilo, non più nel benvenuto né nella chat; si VEDE
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione", "conosciute": PRIMA}, 3000)
        prova("12. nella chat e nel benvenuto la domanda non c'è più", await pg.evaluate("!document.querySelector('#chat-area #conosci, #benvenuto #conosci')"))
        prova("12. «Il benvenuto» nel menù (non più «…e le domande del giorno»)", await pg.evaluate("document.querySelector('#conv-resto').textContent.trim()") == "Il benvenuto")
        prova("12. pallino sul ☰ (c'è una domanda per oggi)", await punto(pg, "#apri-conv") and await vede(pg, "#apri-conv"))
        await pg.click("#apri-conv"); await pg.wait_for_timeout(450)
        prova("12. e sulla voce Profilo del menù", await punto(pg, '#menu-schede .menu-scheda[data-vai="profilo"]'))
        await pg.click('#menu-schede .menu-scheda[data-vai="profilo"]'); await pg.wait_for_timeout(500)
        prova("12. Profilo: la sezione «Imparo te» si vede, sotto nome e colore", await vede(pg, "#imparo-te") and await pg.evaluate("document.querySelector('#imparo-te').getBoundingClientRect().top > document.querySelector('#temi-profilo').getBoundingClientRect().top"))
        prova("12. pensione: «Che lavoro hai fatto nella vita?» si vede", await vede(pg, "#conosci") and await pg.inner_text("#conosci-domanda") == "Che lavoro hai fatto nella vita?", await pg.inner_text("#conosci-domanda"))
        prova("12. con i mestieri di #d1, senza «Studio»", await testi(pg, "#conosci-scelte .scelta") == MESTIERI, await testi(pg, "#conosci-scelte .scelta"))
        prova("12. la casella libera e «Segna» si vedono", await vede(pg, "#conosci-testo") and await vede(pg, "#conosci-ok"))
        await pg.fill("#conosci-testo", "il falegname"); await pg.click("#conosci-ok"); await pg.wait_for_timeout(300)
        io = await leggi_io(pg)
        prova("12. scritto con parole sue: salvato com'è", io["conosciute"].get("mestiere_di_una_vita") == "il falegname", io["conosciute"])
        prova("12. e arrivato a /conoscenza", any(c.get("chiave") == "mestiere_di_una_vita" and c.get("risposta") == "il falegname" and c.get("chi") == CHI for c in conoscenze), conoscenze)
        prova("12. e compare subito nell'elenco «Cosa so di te»", await vede(pg, '#so-di-te li[data-voce="c:mestiere_di_una_vita"]') and "il falegname" in await pg.inner_text('#so-di-te li[data-voce="c:mestiere_di_una_vita"]'))
        await pg.wait_for_timeout(1200)
        prova("12. poi viene «Cosa ti appassiona?»", await pg.inner_text("#conosci-domanda") == "Cosa ti appassiona?", await pg.inner_text("#conosci-domanda"))
        # passioni: scelta multipla, casella libera, un testo solo
        prova("12. passioni: le nove scelte, e la casella dice «per esempio: il burraco, le bocce, il coro»", await testi(pg, "#conosci-scelte .scelta") == NOVE and "per esempio: il burraco, le bocce, il coro" in (await pg.get_attribute("#conosci-testo", "placeholder")))
        prova("12. senza scelte né testo «Segna» è spento", await pg.is_disabled("#conosci-ok"))
        await pg.click('#conosci-scelte .scelta:has-text("Orto e giardino")'); await pg.click('#conosci-scelte .scelta:has-text("Cucina")')
        prova("12. due scelte restano accese insieme", await pg.evaluate("document.querySelectorAll('#conosci-scelte .scelta[aria-pressed=true]').length") == 2 and not await pg.is_disabled("#conosci-ok"))
        await pg.fill("#conosci-testo", "il burraco"); await pg.click("#conosci-ok"); await pg.wait_for_timeout(300)
        p = (await leggi_io(pg))["conosciute"].get("passioni")
        prova("12. salvato UN testo, separato da virgole", p == "Orto e giardino, Cucina, il burraco", p)
        prova("12. e arrivato a /conoscenza", any(c.get("chiave") == "passioni" and c.get("risposta") == p for c in conoscenze), conoscenze)
        await ctx.close()

        # casa: la versione per casa
        ctx, pg = await apri(b, {**DI_CASA, "vita": "casa", "conosciute": PRIMA}, 3000)
        await profilo(pg)
        prova("12. casa: «C'è un lavoro che hai fatto, o che ti sarebbe piaciuto fare?»", await vede(pg, "#conosci") and await pg.inner_text("#conosci-domanda") == "C'è un lavoro che hai fatto, o che ti sarebbe piaciuto fare?", await pg.inner_text("#conosci-domanda"))
        await pg.click('#conosci-scelte .scelta:has-text("Ufficio")'); await pg.wait_for_timeout(300)
        prova("12. una scelta sola risponde subito", (await leggi_io(pg))["conosciute"].get("mestiere_di_una_vita") == "Ufficio")
        await ctx.close()

        # passioni per chi lavora; tutte le scelte + testo lungo ≤120; arriva alla porta
        conoscenze.clear()
        ctx, pg = await apri(b, {**DI_CASA, "vita": "lavoro", "mestiere": "Negozio o commercio", "conosciute": {**PRIMA, "telefono": "x"}}, 3000)
        await profilo(pg)
        prova("12. lavoro: «Cosa ti appassiona?» si vede, e non il lavoro di una vita", await vede(pg, "#conosci") and await pg.inner_text("#conosci-domanda") == "Cosa ti appassiona?")
        for t in NOVE: await pg.click(f'#conosci-scelte .scelta:text-is("{t}")')
        await pg.fill("#conosci-testo", "y" * 60); await pg.click("#conosci-ok"); await pg.wait_for_timeout(300)
        p = (await leggi_io(pg))["conosciute"].get("passioni")
        prova("12. tutte le scelte e un testo lungo: un testo solo di al massimo 120 caratteri", isinstance(p, str) and 0 < len(p) <= 120 and p.startswith("Orto e giardino, Cucina"), p)
        corpi.clear()
        await pg.evaluate("() => { localStorage.removeItem('jjavis-conto'); }")
        await pg.evaluate("() => parla('Ciao')")
        pa = [c for u, c in corpi if u.endswith("/parla")]
        prova("12. parla manda profilo.conosciute.passioni (e la porta la taglia a 120)", bool(pa) and pa[-1].get("profilo", {}).get("conosciute", {}).get("passioni") == p, corpi)
        await ctx.close()

        # «Cambia»: si riapre segnata, si cambia, l'elenco e la porta hanno il valore nuovo
        conoscenze.clear()
        PROF = {**PRIMA, "mestiere_di_una_vita": "Ufficio", "passioni": "Orto e giardino, Cucina, il burraco", "voce": "A voce"}
        ctx, pg = await apri(b, {**DI_CASA, "vita": "pensione", "conosciute": PROF}, 3000)
        await profilo(pg)
        riga = lambda k: f'#so-di-te li[data-voce="{k}"]'
        prova("12. nell'elenco ogni voce ha «Cambia» e «Togli»", await vl(pg, riga("c:passioni") + " >> text=Cambia") and await vl(pg, riga("c:passioni") + " >> text=Togli") and await vl(pg, riga("vita") + " >> text=Cambia"))
        prova("12. e le etichette sono quelle di sempre", "Le tue passioni" in await pg.inner_text(riga("c:passioni")) and "Il lavoro che hai fatto" in await pg.inner_text(riga("c:mestiere_di_una_vita")))
        await pg.click(riga("c:passioni") + " >> text=Cambia"); await pg.wait_for_timeout(200)
        accese = await pg.evaluate("s => [...document.querySelectorAll(s + ' .editor .scelta[aria-pressed=true]')].map(x => x.textContent)", riga("c:passioni"))
        prova("12. «Cambia» passioni: si riapre già segnata (le scelte e la casella)", accese == ["Orto e giardino", "Cucina"] and await pg.input_value(riga("c:passioni") + " .editor input") == "il burraco" and await vl(pg, riga("c:passioni") + " .editor input"), accese)
        await pg.click(riga("c:passioni") + ' .editor .scelta:has-text("Cucina")'); await pg.click(riga("c:passioni") + ' .editor .scelta:has-text("Lettura")')
        await pg.click(riga("c:passioni") + " .editor >> text=Segna"); await pg.wait_for_timeout(300)
        io = await leggi_io(pg)
        prova("12. l'elenco mostra il valore nuovo", "Orto e giardino, Lettura, il burraco" in await pg.inner_text(riga("c:passioni")), await pg.inner_text(riga("c:passioni")))
        prova("12. salvato nel telefono e arrivato alla porta", io["conosciute"]["passioni"] == "Orto e giardino, Lettura, il burraco" and any(c.get("chiave") == "passioni" and c.get("risposta") == "Orto e giardino, Lettura, il burraco" for c in conoscenze), conoscenze)
        await pg.click(riga("c:voce") + " >> text=Cambia"); await pg.wait_for_timeout(200)
        prova("12. una voce a scelta singola: si riapre con la scelta segnata", await pg.evaluate("s => [...document.querySelectorAll(s + ' .editor .scelta[aria-pressed=true]')].map(x => x.textContent)", riga("c:voce")) == ["A voce"])
        await pg.click(riga("c:voce") + ' .editor .scelta:has-text("Scrivendo")'); await pg.click(riga("c:voce") + " .editor >> text=Segna"); await pg.wait_for_timeout(300)
        prova("12. e «Segna» la cambia", "Scrivendo" in await pg.inner_text(riga("c:voce")) and (await leggi_io(pg))["conosciute"]["voce"] == "Scrivendo")

        # «Togli»: una conferma di una riga, poi sparisce solo quella voce
        await pg.click(riga("c:passioni") + " >> text=Togli"); await pg.wait_for_timeout(200)
        prova("12. «Togli» chiede conferma: «Tolgo “Le tue passioni”?»", await vl(pg, riga("c:passioni") + " >> text=Tolgo “Le tue passioni”?"))
        await pg.click(riga("c:passioni") + " button:text-is(\"No\")"); await pg.wait_for_timeout(200)
        prova("12. «No»: la voce resta", "passioni" in (await leggi_io(pg))["conosciute"] and await vl(pg, riga("c:passioni") + " >> text=Togli"))
        conoscenze.clear()
        await pg.click(riga("c:passioni") + " >> text=Togli"); await pg.click(riga("c:passioni") + " >> text=Sì, togli"); await pg.wait_for_timeout(300)
        io = await leggi_io(pg)
        prova("12. «Sì, togli»: sparisce solo quella voce, le altre restano",
              "passioni" not in io["conosciute"] and io["conosciute"].get("mestiere_di_una_vita") == "Ufficio" and io["conosciute"].get("voce") == "Scrivendo" and io["conosciute"].get("inizio") == "Dopo le 8", io["conosciute"])
        prova("12. e dall'elenco", await pg.locator(riga("c:passioni")).count() == 0 and await pg.locator(riga("c:mestiere_di_una_vita")).count() == 1 and await pg.locator(riga("c:voce")).count() == 1)
        prova("12. la porta riceve la voce tolta come risposta vuota", any(c.get("chiave") == "passioni" and c.get("risposta") == "" for c in conoscenze), conoscenze)
        prova("12. la domanda tolta può tornare: oggi si chiede di nuovo «Cosa ti appassiona?»", await vede(pg, "#conosci") and await pg.inner_text("#conosci-domanda") == "Cosa ti appassiona?", await pg.inner_text("#conosci-domanda"))
        await ctx.close()

        # cambiare la vita cambia cosa chiedo dopo
        ctx, pg = await apri(b, {**DI_CASA, "vita": "lavoro", "mestiere": "Negozio o commercio", "tempo": "Scorte da controllare", "conosciute": PRIMA}, 3000)
        await profilo(pg)
        prova("12. vita lavoro: oggi si chiede una domanda da lavoro («Mentre lavori, il telefono dov'è?»)", await pg.inner_text("#conosci-domanda") == "Mentre lavori, il telefono dov'è?", await pg.inner_text("#conosci-domanda"))
        prova("12. e nell'elenco ci sono la vita e il lavoro", await vede(pg, riga("vita")) and await vede(pg, riga("mestiere")))
        await pg.click(riga("vita") + " >> text=Cambia"); await pg.wait_for_timeout(200)
        prova("12. «Cambia» la vita: si riapre con «Lavoro» segnata", await pg.evaluate("s => [...document.querySelectorAll(s + ' .editor .scelta[aria-pressed=true]')].map(x => x.textContent)", riga("vita")) == ["Lavoro"])
        await pg.click(riga("vita") + ' .editor .scelta:has-text("Sono in pensione")'); await pg.click(riga("vita") + " >> text=Segna"); await pg.wait_for_timeout(400)
        io = await leggi_io(pg)
        prova("12. io.vita = pensione, e l'elenco lo dice", io.get("vita") == "pensione" and "Sono in pensione" in await pg.inner_text(riga("vita")), io.get("vita"))
        prova("12. spariscono le domande da lavoro e compare «Che lavoro hai fatto nella vita?»", await vede(pg, "#conosci") and await pg.inner_text("#conosci-domanda") == "Che lavoro hai fatto nella vita?", await pg.inner_text("#conosci-domanda"))
        seq = await pg.evaluate(SEQ)
        prova("12. da pensione non si chiede più niente di lavoro", not any(k in seq for k in ("telefono", "giorni", "soldi", "sera")) and "spese" in seq, seq)
        prova("12. il lavoro non è più nell'elenco e il tempo cambia parola", await pg.locator(riga("mestiere")).count() == 0 and "Vorresti essere assistito in" in await pg.inner_text(riga("tempo")), await pg.inner_text("#so-di-te"))
        await ctx.close()

        # il pallino: c'è finché c'è una domanda, poi se ne va (senza ricaricare)
        ctx, pg = await apri(b, {**DI_CASA, "vita": "lavoro", "mestiere": "Negozio o commercio", "conosciute": {k: "x" for k in ("inizio", "telefono", "parlare", "passioni", "voce", "giorni", "soldi")}}, 3000)
        prova("12. pallino sul ☰: manca solo «sera»", await punto(pg, "#apri-conv") and await pg.evaluate("prossimaDomanda().k") == "sera")
        await profilo(pg)
        await pg.click('#conosci-scelte .scelta >> nth=0'); await pg.wait_for_timeout(1300)
        prova("12. risposta l'ultima: il pallino se ne va, «Di te so già parecchio» si vede", not await punto(pg, "#apri-conv") and await vede(pg, "#conosci-fine") and not await vede(pg, "#conosci"), await pg.inner_text("#imparo-te"))
        await pg.click(riga("c:sera") + " >> text=Togli"); await pg.click(riga("c:sera") + " >> text=Sì, togli"); await pg.wait_for_timeout(300)
        prova("12. toltane una, il pallino torna (la domanda può tornare)", await punto(pg, "#apri-conv") and await vede(pg, "#conosci"))
        await ctx.close()
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} verdi"); print("VERDE" if all(prove) else "ROSSO"); sys.exit(0 if all(prove) else 1)   # VERDE/ROSSO: è l'ultima riga che legge Hera

asyncio.run(main())
