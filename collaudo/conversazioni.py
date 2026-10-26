"""La chat si riapre pulita se tutto è letto; com'era se c'è qualcosa da leggere.

    CHROMIUM=/percorso/chrome python3 collaudo/conversazioni.py index.html

JJ, 2 ottobre 2026: «quando apro è pulita col nuovo saluto… una parte dove
restano i thread precedenti… se lui manda la domanda che richiede la risposta
da me e io rispondo quando lui non guarda, quando rientra ha il thread ancora
da leggere; se invece lo legge e rientra, trova la chat pulita».
La porta finta rimanda SEMPRE tutte le risposte, come quella vera.

26 ottobre 2026, JJ: «quando apro, non c'è il papiro sopra; se voglio vedere una sessione vecchia ho la scheda con le chat; ed è
così che deve apparire». La chat è la pagina (come la chat di Claude in un progetto): chi è di casa apre sulla chat a tutto
schermo, con ☰ (le conversazioni), il nome, ＋ (nuova); la chat vuota ha il saluto e tre tasti di prima prova; le vecchie stanno
in una scheda che scorre da sinistra, non più in una fisarmonica sopra la chat. Le scene 1-3 sono quelle di ottobre (aggiornate
al nuovo elenco); le scene 4-8 sono del 26/10, e la 4 ha la sua CONTROPROVA: rimettendo la chat sotto #benvenuto (com'era),
la prima prova diventa rossa.
"""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright

PAGINA = open(sys.argv[1], encoding="utf-8").read()
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
CORS = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "*"}
RISPOSTA_Q1 = {"id": "q1", "domanda": "Quanto costa un sito?", "risposta": "Dipende da cosa deve fare: ti scrivo io."}
RISPOSTE = []   # cosa rimanda la porta, scena per scena
INVIATI = []    # cosa le arriva: (rotta, corpo)
IO = {"id": "a1b2c3d4e5f60718", "nome": "Nova", "tema": "tech", "inviato": True, "mestiere": "Corriere o autista"}

prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))

async def instrada(route):
    u = route.request.url
    if u.startswith(BASE): return await route.fulfill(body=PAGINA, content_type="text/html")
    if "workers.dev" in u:
        m = route.request.method
        if m == "OPTIONS": return await route.fulfill(status=204, headers={**CORS, "Access-Control-Allow-Methods": "POST, GET"})
        if m == "POST":
            corpo = json.loads(route.request.post_data or "{}"); INVIATI.append((u.rsplit("/", 1)[-1], corpo))
            return await route.fulfill(status=201, body=json.dumps({"ok": True, "id": "n%d" % len(INVIATI)}), content_type="application/json", headers=CORS)
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": RISPOSTE}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    if u.startswith("about:"): return await route.continue_()
    return await route.abort()

async def casa_in_vista(p):
    """La casella per scrivere si vede senza scorrere (sopra le schede), e il benvenuto non c'è sopra la chat."""
    d = await p.evaluate("""(()=>{
        const vis = e => !!e && e.getClientRects().length>0 && getComputedStyle(e).visibility!=="hidden";
        const c = document.getElementById("scrivi"), m = document.getElementById("manda-chat"), n = document.querySelector(".schede").getBoundingClientRect();
        const rc = c.getBoundingClientRect(), rm = m.getBoundingClientRect();
        return {scroll: window.scrollY, casella: vis(c) && rc.top >= 0 && rc.bottom <= n.top + 1 && rm.bottom <= n.top + 1,
                benvenuto: vis(document.getElementById("benvenuto")), casella_giu: Math.round(rc.bottom), schede_su: Math.round(n.top)}})()""")
    return d["scroll"] == 0 and d["casella"] and not d["benvenuto"], d

async def main():
    global PAGINA
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
        # 26/10: l'elenco a fisarmonica (#vecchie) non c'è più; le precedenti stanno nella scheda ☰, una riga per conversazione
        await p.click("#apri-conv"); await p.wait_for_timeout(400)
        prova("le conversazioni precedenti si vedono nella scheda ☰, con quella di prima",
              await p.is_visible("#conversazioni") and "Ciao, che fai?" in await p.inner_text("#conv-elenco"), await p.inner_text("#conversazioni"))

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

        # ═══ 26 ottobre: la chat è la pagina ═══
        RISPOSTE.clear(); INVIATI.clear()
        CASA = {**IO, "nome": "Rebecca", "tuo": "Annamaria"}
        DA_LEGGERE = [{"ruolo": "tu", "testo": "Mi servono i documenti per il furgone", "id": "y0", "attesa": False},
                      {"ruolo": "io", "testo": "Te li preparo io: libretto e assicurazione.", "id": "y0-n", "nuovo": True}]

        # 4. chi è di casa apre la pagina: la chat è la pagina
        print("── 4. chi è di casa apre sulla chat")
        await metti(CASA); await entra()
        ok_, d = await casa_in_vista(p)
        prova("4. chi è di casa: la casella per scrivere è visibile senza scorrere, e #benvenuto non è sopra la chat", ok_, d)
        barra = await p.evaluate("""(()=>{ const r = id => document.getElementById(id).getBoundingClientRect(), b = r("chat-barra"), a = r("apri-conv"), t = r("tp"), n = r("nuova-conv");
            return {su: b.top <= 1, sottile: b.height <= 64, sx: a.right <= t.left + 1, dx: n.left >= t.right - 1, nome: document.getElementById("tp").innerText.trim(), larga: b.width}})()""")
        prova("4. in alto una barra sottile: ☰ a sinistra, il nome dell'assistente in mezzo, ＋ a destra",
              barra["su"] and barra["sottile"] and barra["sx"] and barra["dx"] and barra["nome"] == "Rebecca", barra)
        # CONTROPROVA: la chat rimessa sotto #benvenuto (com'era, senza la chat a tutto schermo) fa diventare rossa la prima prova
        vera = PAGINA
        segno = 'document.body.classList.toggle("chat-sola", diCasa())'
        prova("4. (controprova) il punto da spegnere c'è nella pagina", segno in PAGINA)
        PAGINA = PAGINA.replace(segno, 'document.body.classList.toggle("chat-sola", false)')
        await entra()
        ok_vecchio, d = await casa_in_vista(p)
        prova("4. CONTROPROVA: con la chat sotto #benvenuto (com'era) la prima prova diventa rossa", not ok_vecchio, d)
        PAGINA = vera
        # la tastiera: l'altezza che si vede si restringe e la casella resta dentro (lo script lo fa con visualViewport)
        await entra()
        dentro = await p.evaluate("""(()=>{ const r = document.documentElement; r.style.setProperty("--vv-h", "470px"); r.classList.add("tastiera");
            const c = document.getElementById("scrivi").getBoundingClientRect(), m = document.getElementById("manda-chat").getBoundingClientRect();
            return {giu: Math.round(Math.max(c.bottom, m.bottom)), su: Math.round(c.top)}})()""")
        prova("4. con la tastiera aperta (470 px visibili) la casella resta sopra la tastiera", 0 <= dentro["su"] and dentro["giu"] <= 470, dentro)
        for tema in ("calmo", "deciso", "naturale", "tech"):
            await p.evaluate(f"applicaTema('{tema}')")
            ok_, d = await casa_in_vista(p)
            prova(f"4. tema {tema}: la chat è la pagina, casella in vista", ok_, d)

        # 5. chat vuota: il saluto e i tre tasti di prima prova
        print("── 5. la chat vuota: saluto e tre tasti")
        await entra()
        prova("5. il saluto col nome dell'assistente e quello della persona",
              (await p.inner_text("#saluto-vuoto")).strip() == "Ciao Annamaria, sono Rebecca. Cosa facciamo oggi?", await p.inner_text("#saluto-vuoto"))
        tasti = await p.evaluate("[...document.querySelectorAll('#prove-chat .prova-chat')].filter(b=>b.getClientRects().length).map(b=>({t:b.textContent.trim(), h:b.getBoundingClientRect().height, w:b.getBoundingClientRect().width}))")
        prova("5. tre tasti di prima prova, grandi, con le tre frasi",
              [t["t"] for t in tasti] == ["⏰ Ricordami una cosa", "💶 Segnami una scadenza", "🎒 Cosa porto quando esco"] and all(t["h"] >= 56 and t["w"] >= 240 for t in tasti), tasti)
        await p.click("#prove-chat .prova-chat >> nth=0"); await p.wait_for_timeout(500)
        manda = [c for (r, c) in INVIATI if r == "parla"]
        prova("5. toccato «⏰ Ricordami una cosa», parte proprio quel messaggio alla porta, come se l'avesse scritto la persona",
              len(manda) == 1 and manda[0].get("testo") == "⏰ Ricordami una cosa" and manda[0].get("da_dove") == "chat", INVIATI)
        prova("5. e i tasti spariscono: c'è già il primo messaggio", not await p.is_visible("#prove-chat") and "⏰ Ricordami una cosa" in "".join(await bolle()), await bolle())
        prova("5. con un messaggio nella conversazione il saluto della chat vuota non c'è più", not await p.is_visible("#saluto-vuoto"))

        # 6. ☰: le conversazioni
        print("── 6. ☰ apre le conversazioni")
        ora = await p.evaluate("Date.now()")
        ieri = await p.evaluate("(()=>{const d=new Date(); d.setDate(d.getDate()-1); d.setHours(12,0,0,0); return d.getTime()})()")
        vecchia = await p.evaluate("(()=>{const d=new Date(); d.setDate(d.getDate()-40); d.setHours(12,0,0,0); return d.getTime()})()")
        LUNGA = "Ricordami di chiamare il commercialista domani mattina presto per la fattura"
        THREAD = [{"quando": ora, "messaggi": [{"ruolo": "tu", "testo": LUNGA, "id": "t1"}, {"ruolo": "io", "testo": "Fatto: lo segno alle otto.", "id": "t1-n"}]},
                  {"quando": ieri, "messaggi": [{"ruolo": "io", "testo": "Ciao, come va?", "id": "t2-n"}, {"ruolo": "tu", "testo": "Quanto costa un sito?", "id": "t2"}, {"ruolo": "io", "testo": "Dipende da cosa deve fare.", "id": "t2-r"}]},
                  {"quando": vecchia, "messaggi": [{"ruolo": "tu", "testo": "Supercalifragilistichespiralidosissimosupercalifragilistichespiralidosissimo è una parola lunghissima", "id": "t3"}, {"ruolo": "io", "testo": "Che parola!", "id": "t3-n"}]}]
        await metti({**CASA, "thread": THREAD}); await entra()
        prova("6. il <details id=\"vecchie\"> a fisarmonica non c'è più", await p.evaluate("!document.getElementById('vecchie') && !document.querySelector('details.vecchia, details.vecchie')"))
        prova("6. prima di toccare ☰ l'elenco non si vede", not await p.is_visible("#conversazioni"))
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        prova("6. ☰ apre la scheda delle conversazioni, che scorre da sinistra sopra la chat", await p.is_visible("#conversazioni")
              and await p.evaluate("(()=>{const r=document.getElementById('conversazioni').getBoundingClientRect(); return r.left<=1 && r.width>=240 && r.width<=390})()"))
        righe = await p.evaluate("[...document.querySelectorAll('#conv-elenco .riga-conv')].map(r=>({titolo:r.querySelector('.riga-titolo').textContent, quando:r.querySelector('.riga-quando').textContent}))")
        prova("6. tre conversazioni in io.thread: tre righe", len(righe) == 3, righe)
        prova("6. ogni titolo è al massimo di 40 caratteri, e ognuna ha la sua data", all(0 < len(r["titolo"]) <= 40 and r["quando"] for r in righe), righe)
        if len(righe) == 3:
            prova("6. il titolo è il primo messaggio della persona, tagliato tra due parole", righe[0]["titolo"].endswith("…") and LUNGA.startswith(righe[0]["titolo"][:-1])
                  and LUNGA[len(righe[0]["titolo"]) - 1] == " " and righe[1]["titolo"] == "Quanto costa un sito?", righe)
            prova("6. una parola sola più lunga di 40 caratteri si taglia lo stesso, entro i 40", righe[2]["titolo"].endswith("…") and len(righe[2]["titolo"]) == 40, righe[2])
            prova("6. le date: «oggi», «ieri» e il giorno per esteso", righe[0]["quando"] == "oggi" and righe[1]["quando"] == "ieri"
                  and re.match(r"^\d{1,2}\s[a-zà-ù]+(\s\d{4})?$", righe[2]["quando"]) is not None, righe)
        su = await p.evaluate("(()=>{const y=id=>document.getElementById(id).getBoundingClientRect().top; return y('conv-nuova') < document.querySelector('#conv-elenco .riga-conv').getBoundingClientRect().top})()")
        prova("6. in cima «＋ Nuova conversazione»", su and "Nuova conversazione" in await p.inner_text("#conv-nuova"))
        await p.click("#conv-elenco .riga-conv >> nth=1 >> .riga-apri"); await p.wait_for_timeout(300)
        lettura = await p.evaluate("""(()=>{ const l = document.getElementById("lettura-conv"), c = document.getElementById("scrivi").getBoundingClientRect();
            const sopra = document.elementFromPoint(c.left + c.width/2, c.top + c.height/2);
            return {visibile: !l.hidden && l.getClientRects().length > 0, testo: l.innerText, scrive: l.querySelectorAll("textarea,input").length, copre: !!sopra && l.contains(sopra),
                    tutto: l.getBoundingClientRect().height >= innerHeight * 0.8}})()""")
        prova("6. toccata una riga, la conversazione si apre a tutto schermo", lettura["visibile"] and lettura["tutto"] and "Quanto costa un sito?" in lettura["testo"] and "Dipende da cosa deve fare." in lettura["testo"], lettura)
        prova("6. è in sola lettura: niente casella, e quella della chat è coperta", lettura["scrive"] == 0 and lettura["copre"], lettura)
        prova("6. c'è «← Indietro»", "← Indietro" in await p.inner_text("#lettura-indietro"))
        await p.click("#lettura-indietro"); await p.wait_for_timeout(450)
        torna = await p.evaluate("""(()=>{ const c = document.getElementById("scrivi").getBoundingClientRect(), su = document.elementFromPoint(c.left + c.width/2, c.top + c.height/2);
            return {lettura: !document.getElementById("lettura-conv").hidden, scheda: document.getElementById("conversazioni").classList.contains("aperta"), casella: su && su.id === "scrivi"}})()""")
        prova("6. «← Indietro» torna alla chat", not torna["lettura"] and not torna["scheda"] and torna["casella"], torna)
        # il ✕ per cancellarne una resta, con la conferma di oggi; la cancellata non torna
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        p.once("dialog", lambda dlg: asyncio.ensure_future(dlg.dismiss()))
        await p.click("#conv-elenco .riga-conv >> nth=0 >> .via"); await p.wait_for_timeout(200)
        prova("6. ✕ chiede conferma: se si risponde no, la conversazione resta", len((await stato()).get("thread", [])) == 3 and await p.locator("#conv-elenco .riga-conv").count() == 3)
        p.once("dialog", lambda dlg: asyncio.ensure_future(dlg.accept()))
        await p.click("#conv-elenco .riga-conv >> nth=0 >> .via"); await p.wait_for_timeout(300)
        s = await stato()
        prova("6. se si risponde sì, la conversazione se ne va dall'elenco e da io.thread, e i suoi messaggi finiscono in io.viste",
              await p.locator("#conv-elenco .riga-conv").count() == 2 and len(s.get("thread", [])) == 2 and {"t1", "t1-n"} <= set(s.get("viste", [])), s)

        # 7. ＋: nuova conversazione
        print("── 7. ＋ nuova conversazione")
        await metti({**CASA, "chat": DA_LEGGERE, "thread": []}); await entra()
        prova("7. la conversazione in corso c'è, e il ＋ si può toccare", len(await bolle()) == 2 and not await p.evaluate("document.getElementById('nuova-conv').classList.contains('grigio')"), await bolle())
        await p.click("#nuova-conv"); await p.wait_for_timeout(300)
        s = await stato()
        prova("7. ＋: la conversazione in corso va in io.thread, intera", not s.get("chat") and len(s.get("thread", [])) == 1
              and [m["id"] for m in s["thread"][0]["messaggi"]] == ["y0", "y0-n"], s)
        prova("7. la chat riparte vuota, con i tre tasti", await bolle() == [] and await p.locator("#prove-chat .prova-chat:visible").count() == 3, await bolle())
        prova("7. e la conversazione di prima è nell'elenco", await p.evaluate("(async()=>{document.getElementById('apri-conv').click(); return document.getElementById('conv-elenco').textContent.includes('Mi servono i documenti per il furgone')})()"))
        await p.click("#chiudi-conv"); await p.wait_for_timeout(300)
        # con una risposta in attesa il ＋ non si può
        await metti({**CASA, "thread": [], "chat": [{"ruolo": "tu", "testo": "Quanto costa un sito?", "id": "w1", "attesa": True}]}); await entra()
        att = await p.evaluate("(()=>{const b=document.getElementById('nuova-conv'); return {grigio: b.classList.contains('grigio'), disabilitato: b.getAttribute('aria-disabled'), testo: b.innerText}})()")
        prova("7. con una risposta in attesa il ＋ è grigio e dice «aspetto la risposta»", att["grigio"] and att["disabilitato"] == "true" and "aspetto la risposta" in att["testo"], att)
        await p.click("#nuova-conv"); await p.wait_for_timeout(300)
        s = await stato()
        prova("7. e toccarlo non fa niente: la conversazione resta dov'è", len(s.get("chat", [])) == 1 and not s.get("thread") and len(await bolle()) >= 1, s)
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        prova("7. anche «＋ Nuova conversazione» nell'elenco è grigio", await p.evaluate("document.getElementById('conv-nuova').classList.contains('grigio')")
              and "aspetto la risposta" in await p.inner_text("#conv-nuova"))
        await p.click("#conv-nuova"); await p.wait_for_timeout(300)
        s = await stato()
        prova("7. e anche da lì non fa niente", len(s.get("chat", [])) == 1 and not s.get("thread"), s)
        # la risposta arriva: il ＋ torna buono
        RISPOSTE.append({"id": "w1", "domanda": "Quanto costa un sito?", "risposta": "Dipende da cosa deve fare."})
        await p.evaluate("controllaRisposte().then(()=>{})"); await p.wait_for_timeout(500)
        prova("7. arrivata la risposta, il ＋ torna buono", not await p.evaluate("document.getElementById('nuova-conv').classList.contains('grigio')")
              and not await p.is_visible("#nuova-aspetto"))
        RISPOSTE.clear()

        # 8. il resto della scheda, le animazioni ridotte
        print("── 8. il resto della scheda e le animazioni ridotte")
        await metti({**CASA, "thread": [], "chat": []}); await entra()
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        await p.click("#conv-resto"); await p.wait_for_timeout(400)
        prova("8. dal pannello ☰ si arriva al benvenuto; la chat non c'è finché lo si guarda", await p.is_visible("#benvenuto") and not await p.is_visible("#scrivi") and await p.is_visible("#torna-chat"))
        await p.click("#torna-chat"); await p.wait_for_timeout(300)
        ok_, d = await casa_in_vista(p)
        prova("8. «← Torna alla chat»: di nuovo la chat a tutto schermo", ok_, d)
        ctx2 = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce")
        await ctx2.route("**/*", instrada)
        await ctx2.add_init_script(f"localStorage.setItem('jjavis-io', {json.dumps(json.dumps(CASA))})")
        q = await ctx2.new_page(); q.on("pageerror", lambda e: errori.append(str(e)))
        await q.goto(BASE + "index.html"); await q.wait_for_timeout(1500)
        mov = await q.evaluate("(()=>{const c=getComputedStyle(document.getElementById('conversazioni')); return {t: c.transitionDuration, v: getComputedStyle(document.getElementById('conv-velo')).transitionDuration}})()")
        prova("8. con le animazioni ridotte la scheda delle conversazioni non scorre: compare e basta", mov["t"] == "0s" and mov["v"] == "0s", mov)
        await ctx2.close()

        prova("nessun errore JavaScript", not errori, errori[:3])
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} prove\n" + ("VERDE" if all(prove) else "ROSSO"))

asyncio.run(main())
