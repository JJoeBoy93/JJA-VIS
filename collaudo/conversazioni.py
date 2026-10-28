"""La chat si riapre pulita se tutto è letto; com'era se c'è qualcosa da leggere.

    CHROMIUM=/percorso/chrome python3 collaudo/conversazioni.py index.html

JJ, 2 ottobre 2026: «quando apro è pulita col nuovo saluto… una parte dove
restano i thread precedenti… se lui manda la domanda che richiede la risposta
da me e io rispondo quando lui non guarda, quando rientra ha il thread ancora
da leggere; se invece lo legge e rientra, trova la chat pulita».
La porta finta rimanda SEMPRE tutte le risposte, come quella vera.

26 ottobre 2026, JJ: «quando apro, non c'è il papiro sopra; se voglio vedere una sessione vecchia ho la scheda con le chat; ed è
così che deve apparire». La chat è la pagina (come la chat di Claude in un progetto): chi è di casa apre sulla chat a tutto
schermo sotto la testata di sempre (il globo e il nome a sinistra, «＋» e «☰» a destra); la chat vuota ha il saluto e tre tasti di
prima prova; il «☰» apre il menù di tutto (le conversazioni, la Città, una voce per ogni scheda: la barra delle schede in basso non
c'è più), non più una fisarmonica sopra la chat. Le scene 1-3 sono quelle di ottobre (aggiornate al nuovo elenco); le scene 4-9
sono del 26/10, e la 4 ha due CONTROPROVE: rimettendo la chat sotto #benvenuto (com'era) la prima prova diventa rossa, e col
globo nascosto la prova della testata diventa rossa.

La scena 10 è del 26/10 sera, ancora JJ: «la barra di digitazione deve incorporare i bottoni di invio e foto, e aggiungere un
microfono a pressione come WhatsApp». La barra è UNA casella tonda (testo e, dentro a destra, la foto) e accanto UN bottone tondo:
microfono con la casella vuota, freccia appena c'è qualcosa da mandare (senza account: solo la freccia). Si tiene premuto e
registra, si lascia e manda, si scivola a sinistra e si butta, meno di un secondo non manda niente. Il vocale si vede come audio
(▶︎, durata, si riascolta, resta solo nel telefono in IndexedDB); la trascrizione sta sotto in «▸ testo»; se fallisce, il motivo e
«riprova». Il microfono si finge con --use-fake-ui-for-media-stream e --use-fake-device-for-media-stream; la porta è finta.
La CONTROPROVA: tolto il controllo «meno di 1 secondo», la prova dei 0,5 secondi diventa rossa.

La scena 11 è del 26/10 notte, JJ dopo averla provata: «non si può continuare sulla stessa conversazione se la riprendi» e «quando
premi il suggerimento deve già rispondere subito, senza aspettare che pensa». Toccata una conversazione nel ☰ non si apre più in sola
lettura: diventa LA conversazione in corso (quella di prima, se ha messaggi, va in io.thread); con una risposta in attesa non si cambia.
I tre tasti della chat vuota rispondono con una frase fissa, subito e senza chiamare la porta; il messaggio dopo parte all'assistente
col contesto del tasto davanti (che nella bolla non si vede). La CONTROPROVA: se il tasto chiama ancora /assistente, la prima prova
della scena 11 diventa rossa.
"""
import asyncio, base64, json, os, re, struct, sys, zlib
from playwright.async_api import async_playwright
import aiuti; aiuti.sezioni_aperte()   # 28/10: le sezioni dei pannelli sono chiuse finché non si toccano; qui si aprono tutte (collaudo/sezioni.py prova le chiuse)

PAGINA = open(sys.argv[1], encoding="utf-8").read()
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
CORS = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "*"}
RISPOSTA_Q1 = {"id": "q1", "domanda": "Quanto costa un sito?", "risposta": "Dipende da cosa deve fare: ti scrivo io."}
RISPOSTE = []   # cosa rimanda la porta, scena per scena
INVIATI = []    # cosa le arriva: (rotta, corpo)
AUTORIZZATI = []  # l'intestazione Authorization di ogni POST: (rotta, valore)
PORTA = {}      # rotta -> (stato, corpo) deciso dalla scena; "rete" = la rete cade
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
            corpo = json.loads(route.request.post_data or "{}"); rotta = u.rsplit("/", 1)[-1]; INVIATI.append((rotta, corpo))
            AUTORIZZATI.append((rotta, route.request.headers.get("authorization", "")))
            if PORTA.get(rotta) == "rete": return await route.abort()
            if rotta in PORTA:
                stato, risp = PORTA[rotta]
                return await route.fulfill(status=stato, body=json.dumps(risp), content_type="application/json", headers=CORS)
            return await route.fulfill(status=201, body=json.dumps({"ok": True, "id": "n%d" % len(INVIATI)}), content_type="application/json", headers=CORS)
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": RISPOSTE}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    if u.startswith("about:"): return await route.continue_()
    return await route.abort()

async def casa_in_vista(p):
    """La casella per scrivere si vede senza scorrere (in fondo allo schermo), e il benvenuto non c'è sopra la chat."""
    d = await p.evaluate("""(()=>{
        const vis = e => !!e && e.getClientRects().length>0 && getComputedStyle(e).visibility!=="hidden";
        const c = document.getElementById("scrivi"), m = document.getElementById("manda-chat");
        const rc = c.getBoundingClientRect(), rm = m.getBoundingClientRect();
        return {scroll: window.scrollY, casella: vis(c) && rc.top >= 0 && rc.bottom <= innerHeight + 1 && rm.bottom <= innerHeight + 1,
                benvenuto: vis(document.getElementById("benvenuto")), casella_giu: Math.round(rc.bottom), schermo: innerHeight}})()""")
    return d["scroll"] == 0 and d["casella"] and not d["benvenuto"], d

async def testata_ok(p):
    """La testata di sempre: il globo a sinistra e accanto il nome (con la riga piccola); «＋» e «☰» a destra, il «☰» più a destra."""
    d = await p.evaluate("""(()=>{
        const vis = e => !!e && e.getClientRects().length>0 && getComputedStyle(e).visibility!=="hidden";
        const r = id => document.getElementById(id).getBoundingClientRect(), g = r("globo"), n = document.querySelector(".nome").getBoundingClientRect(), pi = r("nuova-conv"), me = r("apri-conv");
        return {globo: vis(document.getElementById("globo")) && g.width >= 40 && g.height >= 40, globo_a_sinistra: g.left < 40, nome_dopo_globo: n.left >= g.right - 1,
                nome: document.getElementById("nome-testata").innerText.trim(), sotto: document.getElementById("sotto-testata").innerText.trim(),
                piu_a_destra: vis(document.getElementById("nuova-conv")) && pi.left >= n.right - 1, menu_piu_a_destra: vis(document.getElementById("apri-conv")) && me.left >= pi.right - 1 && innerWidth - me.right < 24,
                in_alto: document.querySelector(".testa").getBoundingClientRect().top <= 1, schede_in_basso: vis(document.querySelector(".schede"))}})()""")
    return (d["globo"] and d["globo_a_sinistra"] and d["nome_dopo_globo"] and d["piu_a_destra"] and d["menu_piu_a_destra"] and d["in_alto"]
            and not d["schede_in_basso"] and d["nome"] == "Rebecca" and d["sotto"] == "il tuo JJA-VIS"), d

async def main():
    global PAGINA
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None,
                                     args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
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
        ok_t, d = await testata_ok(p)
        prova("4. in alto la testata di JARVIS: il globo a sinistra e il nome accanto, «＋» e «☰» a destra (il «☰» più a destra); niente barra delle schede in basso", ok_t, d)
        prova("4. una sola testata: niente seconda barra sottile", await p.evaluate("!document.querySelector('.chat-barra') && document.querySelectorAll('header, .testa').length === 1"))
        await p.add_style_tag(content="#globo{display:none!important}")
        ok_senza, d = await testata_ok(p)
        prova("4. CONTROPROVA: con #globo nascosto la prova della testata diventa rossa", not ok_senza, d)
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
        await p.click("#prove-chat .prova-chat >> nth=0"); await p.wait_for_timeout(300)
        prova("5. toccato «⏰ Ricordami una cosa», entro 300 ms c'è la bolla della persona e la risposta fissa, e alla porta non va niente",
              await bolle() == ["⏰ Ricordami una cosa", "Certo, Annamaria. Dimmi cosa devo ricordarti e per quando: il giorno e, se ce l'hai, anche l'ora."] and INVIATI == [], (await bolle(), INVIATI))
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
        await p.click("#conv-elenco .riga-conv >> nth=1 >> .riga-apri"); await p.wait_for_timeout(450)
        ripresa = await p.evaluate("""(()=>{ const c = document.getElementById("scrivi").getBoundingClientRect(), sopra = document.elementFromPoint(c.left + c.width/2, c.top + c.height/2);
            return {bolle: [...document.querySelectorAll("#chat .bolla")].map(b => b.textContent), casella: !!sopra && sopra.id === "scrivi", menu: document.getElementById("conversazioni").classList.contains("aperta"),
                    lettura: !!document.getElementById("lettura-conv") || !!document.getElementById("lettura-indietro")}})()""")
        prova("6. toccata una riga, quella conversazione è la chat in corso: i suoi messaggi, il menù si chiude, la casella per scrivere c'è",
              ripresa["bolle"] == ["Ciao, come va?", "Quanto costa un sito?", "Dipende da cosa deve fare."] and ripresa["casella"] and not ripresa["menu"], ripresa)
        prova("6. la lettura a tutto schermo non c'è più (né «← Indietro»)", not ripresa["lettura"], ripresa)
        s = await stato()
        prova("6. la riga ripresa esce da io.thread (restano le altre due, chat era vuota) e i messaggi sono in io.chat",
              [m["id"] for m in s.get("chat", [])] == ["t2-n", "t2", "t2-r"] and len(s.get("thread", [])) == 2 and all("Quanto costa un sito?" not in json.dumps(c) for c in s["thread"]), s)
        # il ✕ per cancellarne una resta, con la conferma di oggi; la cancellata non torna
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        p.once("dialog", lambda dlg: asyncio.ensure_future(dlg.dismiss()))
        await p.click("#conv-elenco .riga-conv >> nth=0 >> .via"); await p.wait_for_timeout(200)
        prova("6. ✕ chiede conferma: se si risponde no, la conversazione resta", len((await stato()).get("thread", [])) == 2 and await p.locator("#conv-elenco .riga-conv").count() == 2)
        p.once("dialog", lambda dlg: asyncio.ensure_future(dlg.accept()))
        await p.click("#conv-elenco .riga-conv >> nth=0 >> .via"); await p.wait_for_timeout(300)
        s = await stato()
        prova("6. se si risponde sì, la conversazione se ne va dall'elenco e da io.thread, e i suoi messaggi finiscono in io.viste",
              await p.locator("#conv-elenco .riga-conv").count() == 1 and len(s.get("thread", [])) == 1 and {"t1", "t1-n"} <= set(s.get("viste", [])), s)

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
        await p.click("#nuova-conv", force=True); await p.wait_for_timeout(300)
        s = await stato()
        prova("7. e toccarlo non fa niente: la conversazione resta dov'è", len(s.get("chat", [])) == 1 and not s.get("thread") and len(await bolle()) >= 1, s)
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        prova("7. anche «＋ Nuova conversazione» nell'elenco è grigio", await p.evaluate("document.getElementById('conv-nuova').classList.contains('grigio')")
              and "aspetto la risposta" in await p.inner_text("#conv-nuova"))
        await p.click("#conv-nuova", force=True); await p.wait_for_timeout(300)
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


        # 9. il menù di tutto: conversazioni, Città, una voce per ogni scheda (la barra in basso non c'è più)
        print("── 9. il menù ☰ porta a tutto")
        await metti({**CASA, "thread": THREAD[:2], "chat": []}); await entra()
        schede = await p.evaluate("[...document.querySelectorAll('.schede button[data-scheda]')].map(b=>b.dataset.scheda)")
        prova("9. la barra delle schede in basso non si vede più (ma le schede ci sono: otto)", not await p.is_visible(".schede") and len(schede) >= 7, schede)
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        menu = await p.evaluate("""(()=>{ const y = e => e.getBoundingClientRect().top, q = s => document.querySelector(s);
            const voci = [...document.querySelectorAll("#menu-schede .menu-scheda")];
            return {chiudi: q("#chiudi-conv").innerText.trim(), citta: q("#menu-citta").getAttribute("href"), cittaTesto: q("#menu-citta").innerText.trim(),
                    ordine: y(q("#conv-nuova")) < y(q("#conv-elenco .riga-conv")) && y(q("#conv-elenco .riga-conv:last-child")) < y(q("#menu-citta")) && y(q("#menu-citta")) < y(voci[0]),
                    voci: voci.map(v => v.dataset.vai), icone: voci.every(v => !!v.querySelector("svg")), etichette: voci.map(v => v.innerText.trim()), righe: document.querySelectorAll("#conv-elenco .riga-conv").length}})()""")
        prova("9. il menù ha «✕ Chiudi»", menu["chiudi"] == "✕ Chiudi", menu)
        prova("9. dentro, in ordine: «＋ Nuova conversazione» e l'elenco, poi «🏙 Città», poi le schede", menu["ordine"] and menu["righe"] == 2, menu)
        prova("9. «🏙 Città» apre citta.html", menu["citta"] == "citta.html" and "🏙" in menu["cittaTesto"] and "Città" in menu["cittaTesto"], menu)
        prova("9. un pulsante per ogni scheda della barra, nello stesso ordine e con la loro icona", menu["voci"] == schede and menu["icone"], (menu["voci"], schede))
        prova("9. la scheda della chat si chiama «Chat»", menu["etichette"][0] == "Chat" and menu["voci"][0] == "inizia", menu["etichette"])
        await p.click("#chiudi-conv"); await p.wait_for_timeout(450)
        prova("9. «✕ Chiudi» chiude il menù", not await p.is_visible("#conversazioni"))
        async def dal_menu(k):
            await p.click("#apri-conv"); await p.wait_for_timeout(450)
            await p.click(f'#menu-schede .menu-scheda[data-vai="{k}"]'); await p.wait_for_timeout(350)
        for k in [x for x in schede if x != "inizia"]:
            await dal_menu(k)
            aperta = await p.evaluate("document.body.dataset.scheda"); chiuso = not await p.is_visible("#conversazioni")
            prova(f"9. toccato «{k}» nel menù: il menù si chiude e si apre quella scheda", aperta == k and chiuso and await p.is_visible(f"#p-{k}"), (aperta, chiuso))
        # da una scheda il menù c'è ancora, e «Chat» riporta alla chat
        prova("9. da ogni scheda in alto ci sono «＋» e «☰»", await p.is_visible("#apri-conv") and await p.is_visible("#nuova-conv"))
        await dal_menu("inizia")
        ok_, d = await casa_in_vista(p)
        prova("9. dal menù «Chat» si torna alla chat, con la casella in vista", await p.evaluate("document.body.dataset.scheda") == "inizia" and ok_, d)
        # il tasto indietro del telefono
        await dal_menu("chi-sono"); await p.go_back(); await p.wait_for_timeout(500)
        ok_, d = await casa_in_vista(p)
        prova("9. il tasto indietro del telefono torna alla chat", await p.evaluate("document.body.dataset.scheda") == "inizia" and ok_, d)
        # ＋ da un'altra scheda: la nuova conversazione si apre sulla chat
        await metti({**CASA, "thread": [], "chat": DA_LEGGERE}); await entra()
        await dal_menu("profilo"); await p.click("#nuova-conv"); await p.wait_for_timeout(500)
        s = await stato()
        prova("9. «＋» da un'altra scheda: la conversazione va in io.thread e si torna alla chat vuota", await p.evaluate("document.body.dataset.scheda") == "inizia"
              and not s.get("chat") and len(s.get("thread", [])) == 1 and await p.locator("#prove-chat .prova-chat:visible").count() == 3, s)


        # 10. la barra come quella di WhatsApp: una casella, un bottone tondo che è microfono o freccia, il vocale a pressione
        print("── 10. la barra: casella, foto dentro, microfono a pressione")
        TOKEN = "tok-prova-123"
        def png(w, h):   # una foto finta: un rettangolo grigio, abbastanza grande da avere un'anteprima vera
            riga = b"\x00" + b"\x80\x80\x80" * w
            pezzo = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
            return b"\x89PNG\r\n\x1a\n" + pezzo(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + pezzo(b"IDAT", zlib.compress(riga * h)) + pezzo(b"IEND", b"")
        UNA_FOTO = png(200, 120)
        TIPI = ("audio/webm;codecs=opus", "audio/mp4", "audio/ogg")
        modo = lambda: p.evaluate("document.getElementById('manda-chat').dataset.modo")
        icone = lambda: p.evaluate("""(()=>{ const v = s => { const e = document.querySelector('#manda-chat ' + s); return !!e && getComputedStyle(e).display !== 'none' && e.getClientRects().length > 0 };
                                     return {mic: v('.ic-mic'), freccia: v('.ic-invia')} })()""")
        richieste = lambda rotta: [c for (r, c) in INVIATI if r == rotta]
        async def centro():
            return await p.evaluate("(()=>{ const r = document.getElementById('manda-chat').getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2} })()")
        async def tieni(ms, dx=0, ancora=1200):
            """Mouse: premo il bottone, tengo `ms`; se dx scivolo di dx px (dopo `ancora` ms) e lascio."""
            c = await centro(); await p.mouse.move(c["x"], c["y"]); await p.mouse.down(); await p.wait_for_timeout(ms if not dx else ancora)
            if dx: await p.mouse.move(c["x"] + dx, c["y"], steps=8); await p.wait_for_timeout(150)
            await p.mouse.up(); await p.wait_for_timeout(900)
        async def rientra(io_extra=None, token=True):
            await metti({**CASA, "primo": True, **(io_extra or {})})   # «primo»: l'assistente ha già fatto il primo incontro, non lo rifà aprendo
            await p.evaluate(f"localStorage.setItem('jjavis-conto','{TOKEN}')" if token else "localStorage.removeItem('jjavis-conto')")
            await entra()

        # senza account: solo la freccia
        await rientra(token=False)
        prova("10. senza account il microfono non c'è: resta la freccia", await modo() == "invia" and (await icone()) == {"mic": False, "freccia": True}, (await modo(), await icone()))
        # con l'account: microfono a casella vuota, freccia appena si scrive
        await rientra()
        prova("10. casella vuota: il bottone è il microfono", await modo() == "mic" and (await icone()) == {"mic": True, "freccia": False}, (await modo(), await icone()))
        await p.fill("#scrivi", "ciao")
        prova("10. scrivo «ciao»: diventa la freccia di invio", await modo() == "invia" and (await icone()) == {"mic": False, "freccia": True}, (await modo(), await icone()))
        await p.fill("#scrivi", "")
        prova("10. svuoto la casella: torna il microfono", await modo() == "mic" and (await icone()) == {"mic": True, "freccia": False}, (await modo(), await icone()))
        await p.set_input_files("#foto-file", files=[{"name": "bolletta.png", "mimeType": "image/png", "buffer": UNA_FOTO}]); await p.wait_for_timeout(600)
        prova("10. una foto pronta (casella vuota): il bottone è la freccia", await modo() == "invia" and await p.is_visible("#anteprima-foto"), await modo())
        await p.click("#anteprima-via"); await p.wait_for_timeout(200)
        prova("10. tolta la foto, torna il microfono", await modo() == "mic", await modo())
        forma = await p.evaluate("""(()=>{ const r = id => document.getElementById(id).getBoundingClientRect(), cas = r("casella-chat"), f = r("foto-chat"), t = r("scrivi"), b = r("manda-chat");
            const fc = document.getElementById("foto-chat"), bt = document.getElementById("manda-chat");
            return {foto_dentro: f.left >= cas.left && f.right <= cas.right && f.top >= cas.top && f.bottom <= cas.bottom, testo_dentro: t.left >= cas.left && t.right <= cas.right,
                    foto_a_destra_del_testo: f.left >= t.right - 1, bottone_fuori_a_destra: b.left >= cas.right, foto_svg: !!fc.querySelector("svg") && !/[\\u{1F300}-\\u{1FAFF}]/u.test(fc.textContent),
                    casella_tonda: parseFloat(getComputedStyle(document.getElementById("casella-chat")).borderTopLeftRadius) >= 20, bottone_tondo: Math.abs(b.width - b.height) < 1 && getComputedStyle(bt).borderRadius === "50%",
                    colore: getComputedStyle(bt).backgroundColor === getComputedStyle(document.documentElement).getPropertyValue("--accento") ? "-" : getComputedStyle(bt).backgroundColor}})()""")
        prova("10. l'icona della foto sta DENTRO la casella, a destra del testo, ed è un disegno (SVG), non un emoji", forma["foto_dentro"] and forma["testo_dentro"] and forma["foto_a_destra_del_testo"] and forma["foto_svg"], forma)
        prova("10. la casella ha i bordi arrotondati; il bottone è tondo e sta accanto, fuori dalla casella, a destra", forma["casella_tonda"] and forma["bottone_tondo"] and forma["bottone_fuori_a_destra"], forma)
        # cresce fino a 5 righe, poi scorre
        alte = []
        for n in (1, 3, 5, 9):
            await p.fill("#scrivi", "\n".join(f"riga {i}" for i in range(n)))
            alte.append(await p.evaluate("(()=>{ const t = document.getElementById('scrivi'); return {h: Math.round(t.getBoundingClientRect().height), scorre: t.scrollHeight > t.clientHeight + 1} })()"))
        prova("10. la casella cresce con le righe (1 → 3 → 5) e da 5 righe in poi non cresce più: scorre", alte[0]["h"] < alte[1]["h"] < alte[2]["h"] and alte[3]["h"] == alte[2]["h"] and alte[3]["scorre"] and not alte[2]["scorre"], alte)
        await p.fill("#scrivi", ""); await p.wait_for_timeout(100)
        prova("10. svuotata, la casella torna a una riga", await p.evaluate("Math.round(document.getElementById('scrivi').getBoundingClientRect().height)") == alte[0]["h"])
        for tema in ("calmo", "deciso", "naturale", "tech"):
            await p.evaluate(f"applicaTema('{tema}')")
            ok_, d = await casa_in_vista(p)
            t_ = await p.evaluate("""(()=>{ const b = document.getElementById('manda-chat'), c = getComputedStyle(b), a = getComputedStyle(document.documentElement).getPropertyValue('--accento').trim();
                return {sfondo: c.backgroundColor, bordo: c.borderTopColor, visibile: b.getClientRects().length > 0} })()""")
            prova(f"10. tema {tema}: la barra c'è, in vista, col bottone nei colori del tema", ok_ and t_["visibile"] and t_["sfondo"] != "rgba(0, 0, 0, 0)", (d, t_))

        # il vocale: 2 secondi → UNA richiesta a /assistente/voce → la bolla audio → il testo all'assistente
        print("── 10. il vocale a pressione")
        await rientra(); INVIATI.clear(); AUTORIZZATI.clear()
        PORTA.clear(); PORTA["voce"] = (200, {"testo": "ricordami il dentista"}); PORTA["assistente"] = (200, {"risposta": "Fatto: ti ricordo il dentista."})
        c = await centro(); await p.mouse.move(c["x"], c["y"]); await p.mouse.down(); await p.wait_for_timeout(1500)
        reg = await p.evaluate("""(()=>{ const v = id => { const e = document.getElementById(id); return !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden' };
            return {pallino: v('rec-pallino'), tempo: document.getElementById('rec-tempo').textContent, annulla: document.getElementById('rec-annulla').textContent.trim(), annulla_visibile: v('rec-annulla'),
                    casella_rec: document.getElementById('casella-chat').classList.contains('registra'), dentro: (()=>{ const a = document.getElementById('rec-pallino').getBoundingClientRect(), c = document.getElementById('casella-chat').getBoundingClientRect(); return a.left >= c.left && a.right <= c.right })()}})()""")
        prova("10. tenendo premuto: nella barra il pallino rosso, il tempo che scorre e «‹ scorri per annullare»", reg["pallino"] and reg["dentro"] and reg["tempo"] in ("0:01", "0:02") and reg["annulla"] == "‹ scorri per annullare" and reg["annulla_visibile"], reg)
        await p.wait_for_timeout(500); await p.mouse.up(); await p.wait_for_timeout(1200)
        voci = richieste("voce")
        prova("10. premo 2 secondi e lascio: parte UNA richiesta a /assistente/voce, con audio e tipo", len(voci) == 1 and voci[0].get("tipo") in TIPI and len(voci[0].get("audio", "")) > 200 and set(voci[0]) == {"audio", "tipo"}, [(list(v), v.get("tipo")) for v in voci])
        prova("10. la richiesta porta «Authorization: Bearer» col token dell'account", [a for (r, a) in AUTORIZZATI if r == "voce"] == ["Bearer " + TOKEN], AUTORIZZATI)
        prova("10. l'audio è davvero una registrazione (base64 che si decodifica, non vuota)", bool(voci) and len(base64.b64decode(voci[0]["audio"])) > 500, voci and len(voci[0]["audio"]))
        ass = richieste("assistente")
        prova("10. arrivata la trascrizione, parte UNA richiesta a /assistente con quel testo, come un messaggio scritto", len(ass) == 1 and ass[0].get("testo") == "ricordami il dentista", ass)
        bolla_v = await p.evaluate("""(()=>{ const b = document.querySelector('#chat .bolla.voce'); if(!b) return null; const g = b.querySelector('.voce-gioca'), t = b.querySelector('.voce-testo'), a = b.querySelector('.voce-apri');
            const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none';
            return {n_voce: document.querySelectorAll('#chat .bolla.voce').length, n_tu: document.querySelectorAll('#chat .bolla.tu').length, gioca: g && g.textContent.trim(), durata: b.querySelector('.voce-durata').textContent,
                    testo_visibile: vis(t), apri: a && a.textContent.trim(), tutto: [...document.querySelectorAll('#chat .bolla')].map(x => x.textContent)} })()""")
        prova("10. nella chat il vocale è una bolla audio: ▶︎ e la durata (circa 2 secondi)", bolla_v and bolla_v["gioca"].startswith("▶") and re.match(r"^0:0[123]$", bolla_v["durata"]) is not None and bolla_v["n_voce"] == 1, bolla_v)
        prova("10. la trascrizione sta sotto, chiusa: si vede «▸ testo», non il testo; e non c'è un secondo messaggio scritto", bolla_v and bolla_v["apri"] == "▸ testo" and not bolla_v["testo_visibile"] and bolla_v["n_tu"] == 1
              and "Fatto: ti ricordo il dentista." in "".join(bolla_v["tutto"]), bolla_v)
        await p.click("#chat .voce-apri"); await p.wait_for_timeout(150)
        aperto = await p.evaluate("(()=>{ const t = document.querySelector('#chat .voce-testo'); return {testo: t.textContent, visibile: t.getClientRects().length > 0, apri: document.querySelector('#chat .voce-apri').textContent.trim(), fs: parseFloat(getComputedStyle(t).fontSize)} })()")
        prova("10. toccato «▸ testo» si apre: «ricordami il dentista», piccolo, e il tasto diventa «▾ testo»", aperto["testo"] == "ricordami il dentista" and aperto["visibile"] and aperto["apri"] == "▾ testo" and aperto["fs"] < 16, aperto)
        await p.click("#chat .voce-apri"); await p.wait_for_timeout(100)
        prova("10. toccato di nuovo, si richiude", not await p.evaluate("document.querySelector('#chat .voce-testo').getClientRects().length > 0"))
        # si riascolta
        await p.click("#chat .voce-gioca"); await p.wait_for_timeout(500)
        suona = await p.evaluate("document.querySelector('#chat .voce-gioca').textContent.trim()")
        prova("10. toccato ▶︎ il vocale suona (il tasto diventa «❚❚»)", suona == "❚❚", suona)
        await p.wait_for_function("document.querySelector('#chat .voce-gioca').textContent.trim().startsWith('▶')", timeout=8000)
        prova("10. finito di suonare, il tasto torna ▶︎", True)
        # resta solo nel telefono
        dentro = await p.evaluate("""(async()=>{ const db = await new Promise((ok, no) => { const r = indexedDB.open('jjavis-voci', 1); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error) });
            const tutti = await new Promise(ok => { const q = db.transaction('voci').objectStore('voci').getAll(); q.onsuccess = () => ok(q.result) }); db.close();
            return {n: tutti.length, grandezza: tutti[0] ? tutti[0].size : 0, tipo: tutti[0] ? tutti[0].type : ''} })()""")
        s = await stato()
        prova("10. la registrazione sta nel telefono, in IndexedDB (una, non vuota)", dentro["n"] == 1 and dentro["grandezza"] > 500 and dentro["tipo"].startswith("audio/"), dentro)
        prova("10. nella memoria della chat c'è solo la scheda del vocale (id, durata, tipo): niente audio", any(m.get("voce") and set(m["voce"]) >= {"id", "durata", "tipo"} and len(json.dumps(m)) < 300 for m in s.get("chat", [])), s.get("chat"))
        prova("10. l'audio è partito una volta sola, nella richiesta di trascrizione (nessun'altra richiesta lo porta)", sum(1 for (r, c) in INVIATI if "audio" in c) == 1, [(r, list(c)) for (r, c) in INVIATI])
        # la conversazione si chiude e si rilegge: il vocale c'è ancora e suona
        await entra()
        s = await stato()
        prova("10. riaperta la pagina, la conversazione è nelle precedenti col suo vocale", s.get("thread") and any(m.get("voce") for m in s["thread"][0]["messaggi"]), s.get("thread"))
        await p.click("#apri-conv"); await p.wait_for_timeout(450); await p.click("#conv-elenco .riga-conv >> nth=0 >> .riga-apri"); await p.wait_for_timeout(400)
        vecchio = await p.evaluate("(()=>{ const g = document.querySelector('#chat .voce-gioca'); return {c: !!g, testo: document.querySelector('#chat .voce-apri') ? document.querySelector('#chat .voce-apri').textContent.trim() : null, riprova: !!document.querySelector('#chat .voce-riprova')} })()")
        prova("10. nella conversazione ripresa il vocale si vede ancora, con «▸ testo» e senza «riprova»", vecchio["c"] and vecchio["testo"] == "▸ testo" and not vecchio["riprova"], vecchio)
        await p.click("#chat .voce-gioca"); await p.wait_for_timeout(500)
        prova("10. e si riascolta anche dopo aver chiuso e riaperto la pagina e ripreso la conversazione", await p.evaluate("document.querySelector('#chat .voce-gioca').textContent.trim()") == "❚❚")
        # avanti e indietro: la conversazione col vocale va nelle precedenti (＋) e si riprende ancora; l'audio non dipende da dove sta
        await p.click("#chat .voce-gioca"); await p.wait_for_timeout(200)   # lo fermo (toccato di nuovo, smette)
        await p.click("#nuova-conv"); await p.wait_for_timeout(300)
        prova("10. ＋: il vocale va in io.thread con la sua conversazione", not (await stato()).get("chat") and any(m.get("voce") for m in (await stato())["thread"][0]["messaggi"]), await stato())
        await p.click("#apri-conv"); await p.wait_for_timeout(450); await p.click("#conv-elenco .riga-conv >> nth=0 >> .riga-apri"); await p.wait_for_timeout(400)
        await p.click("#chat .voce-gioca"); await p.wait_for_timeout(500)
        prova("10. ripresa una seconda volta, il ▶︎ suona ancora (l'audio si ritrova dall'id del vocale)", await p.evaluate("document.querySelector('#chat .voce-gioca').textContent.trim()") == "❚❚")

        # meno di un secondo: non manda niente
        async def mezzo_secondo():
            await rientra(); INVIATI.clear(); PORTA.clear(); PORTA["voce"] = (200, {"testo": "non dovrei partire"})
            await tieni(500); await p.wait_for_timeout(600)
            return {"voce": len(richieste("voce")), "assistente": len(richieste("assistente")), "messaggio": await p.inner_text("#esito-chat"), "bolle": await p.evaluate("document.querySelectorAll('#chat .bolla').length")}
        r05 = await mezzo_secondo()
        prova("10. premo 0,5 secondi: nessuna richiesta, e il messaggio «Tieni premuto per registrare»", r05["voce"] == 0 and r05["assistente"] == 0 and r05["bolle"] == 0 and "Tieni premuto per registrare" in r05["messaggio"], r05)
        # scivolo a sinistra: si butta
        await rientra(); INVIATI.clear()
        c = await centro(); await p.mouse.move(c["x"], c["y"]); await p.mouse.down(); await p.wait_for_timeout(1300)
        await p.mouse.move(c["x"] - 40, c["y"], steps=4); await p.wait_for_timeout(100)
        ancora = await p.evaluate("document.getElementById('casella-chat').classList.contains('registra')")
        await p.mouse.move(c["x"] - 120, c["y"], steps=6); await p.wait_for_timeout(200)
        fermo = not await p.evaluate("document.getElementById('casella-chat').classList.contains('registra')")
        await p.mouse.up(); await p.wait_for_timeout(900)
        prova("10. premo, scivolo a sinistra di 120 px, lascio: nessuna richiesta, e la barra torna normale", len(richieste("voce")) == 0 and len(richieste("assistente")) == 0 and fermo and await modo() == "mic" and await p.evaluate("document.querySelectorAll('#chat .bolla').length") == 0, (len(INVIATI), ancora, fermo))
        prova("10. con soli 40 px di scivolata (sotto gli 80) si sta ancora registrando", ancora)
        # la porta dice di no (502): il motivo, «riprova», niente all'assistente
        await rientra(); INVIATI.clear(); PORTA.clear(); PORTA["voce"] = (502, {"errore": "Groq giù"}); PORTA["assistente"] = (200, {"risposta": "Segnato."})
        await tieni(2000)
        e502 = await p.evaluate("""(()=>{ const b = document.querySelector('#chat .bolla.voce'); return b && {nota: (b.querySelector('.voce-nota')||{}).textContent, riprova: !!b.querySelector('.voce-riprova'), gioca: !!b.querySelector('.voce-gioca'), apri: !!b.querySelector('.voce-apri')} })()""")
        prova("10. la porta risponde 502 «Groq giù»: la bolla dice il motivo, c'è «riprova», e la registrazione si riascolta lo stesso",
              e502 and "non ho capito il vocale: Groq giù" in e502["nota"] and e502["riprova"] and e502["gioca"] and not e502["apri"], e502)
        prova("10. e a /assistente non parte niente", len(richieste("assistente")) == 0 and len(richieste("voce")) == 1, [r for (r, c) in INVIATI])
        prova("10. il bottone torna normale (microfono, non bloccato)", await modo() == "mic" and not await p.evaluate("document.getElementById('manda-chat').disabled"))
        # «riprova»: la porta ora risponde bene
        PORTA["voce"] = (200, {"testo": "ricordami il dentista"})
        await p.click("#chat .voce-riprova"); await p.wait_for_timeout(1200)
        ass = richieste("assistente")
        prova("10. «riprova»: stessa registrazione alla porta (senza registrare di nuovo), e adesso il testo va all'assistente", len(richieste("voce")) == 2 and richieste("voce")[0]["audio"] == richieste("voce")[1]["audio"]
              and len(ass) == 1 and ass[0].get("testo") == "ricordami il dentista", [(r, list(c)) for (r, c) in INVIATI])
        prova("10. dopo «riprova» la bolla è una sola, con «▸ testo» e senza il motivo", await p.evaluate("(()=>{ const bb = document.querySelectorAll('#chat .bolla.voce'); return bb.length === 1 && !bb[0].querySelector('.voce-riprova') && !bb[0].querySelector('.voce-nota.errore') && !!bb[0].querySelector('.voce-apri') })()"))
        # la rete cade
        await rientra(); INVIATI.clear(); PORTA.clear(); PORTA["voce"] = "rete"
        await tieni(1700)
        rete = await p.evaluate("(()=>{ const b = document.querySelector('#chat .bolla.voce'); return b && {nota: (b.querySelector('.voce-nota')||{}).textContent, riprova: !!b.querySelector('.voce-riprova')} })()")
        prova("10. la rete cade: la bolla lo dice in chiaro e c'è «riprova»; niente parte all'assistente", rete and "non ho capito il vocale: la rete non c'è" in rete["nota"] and rete["riprova"] and len(richieste("assistente")) == 0, (rete, [r for (r, c) in INVIATI]))
        # la trascrizione c'è ma l'assistente non risponde: «riprova» rimanda il testo, senza trascrivere di nuovo
        await rientra(); INVIATI.clear(); PORTA.clear(); PORTA["voce"] = (200, {"testo": "ricordami il dentista"}); PORTA["assistente"] = (500, {"errore": "occupato"})
        await tieni(1700)
        mezzo = await p.evaluate("(()=>{ const b = document.querySelector('#chat .bolla.voce'); return b && {apri: !!b.querySelector('.voce-apri'), nota: (b.querySelector('.voce-nota')||{}).textContent, riprova: !!b.querySelector('.voce-riprova')} })()")
        prova("10. trascritto ma l'assistente non risponde: «▸ testo» c'è, la bolla dice «non è partito» e c'è «riprova»", mezzo and mezzo["apri"] and "non è partito" in mezzo["nota"] and mezzo["riprova"], mezzo)
        PORTA["assistente"] = (200, {"risposta": "Segnato."}); n_voce = len(richieste("voce"))
        await p.click("#chat .voce-riprova"); await p.wait_for_timeout(900)
        prova("10. «riprova» rimanda il testo all'assistente senza rimandare l'audio", len(richieste("voce")) == n_voce and len(richieste("assistente")) == 2 and "Segnato." in "".join(await bolle()), [(r, list(c)) for (r, c) in INVIATI])

        # il permesso del microfono negato: un messaggio chiaro, una volta sola
        await rientra(); INVIATI.clear()
        await p.evaluate("(()=>{ navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('negato', 'NotAllowedError')) })()")
        await tieni(400); prima = await p.inner_text("#esito-chat")
        await p.evaluate("document.getElementById('esito-chat').textContent=''")
        await tieni(400); seconda = await p.inner_text("#esito-chat")
        prova("10. permesso negato: un messaggio chiaro sul microfono", "microfono" in prima and "consent" in prima, prima)
        prova("10. …una volta sola (la seconda volta non lo ripete), niente parte e il bottone resta il microfono", "microfono" not in seconda and len(INVIATI) == 0 and await modo() == "mic"
              and not await p.evaluate("document.getElementById('casella-chat').classList.contains('registra')"), (seconda, await modo()))

        # a 60 secondi si ferma e manda da solo (il tempo della pagina si manda avanti con l'orologio di Playwright)
        pg60 = await ctx.new_page(); pg60.on("pageerror", lambda e: errori.append(str(e)))
        await pg60.clock.install(); await pg60.goto(BASE + "index.html"); await pg60.wait_for_timeout(300)
        await pg60.evaluate(f"localStorage.setItem('jjavis-io', {json.dumps(json.dumps({**CASA, 'primo': True}))}); localStorage.setItem('jjavis-conto','{TOKEN}')")
        await pg60.goto("about:blank"); await pg60.goto(BASE + "index.html"); await pg60.wait_for_timeout(1500)
        INVIATI.clear(); PORTA.clear(); PORTA["voce"] = (200, {"testo": "sessanta secondi"}); PORTA["assistente"] = (200, {"risposta": "Ok."})
        r60 = await pg60.evaluate("(()=>{ const r = document.getElementById('manda-chat').getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2} })()")
        await pg60.mouse.move(r60["x"], r60["y"]); await pg60.mouse.down(); await pg60.wait_for_timeout(700)
        prima60 = len(richieste("voce"))
        await pg60.clock.fast_forward(61000); await pg60.wait_for_timeout(1200)
        prova("10. a 60 secondi, senza lasciare il bottone, si ferma e manda da solo (UNA richiesta)", prima60 == 0 and len(richieste("voce")) == 1, (prima60, len(richieste("voce"))))
        await pg60.mouse.up(); await pg60.wait_for_timeout(500)
        prova("10. e lasciando il bottone dopo, non ne parte un'altra", len(richieste("voce")) == 1, len(richieste("voce")))
        await pg60.close()

        # col dito (eventi touch veri, passando dal protocollo del browser): tenere premuto manda, scivolare butta
        cdp = await ctx.new_cdp_session(p)
        await rientra(); INVIATI.clear(); PORTA.clear(); PORTA["voce"] = (200, {"testo": "ricordami il dentista"}); PORTA["assistente"] = (200, {"risposta": "Fatto."})
        c = await centro()
        tocco = lambda tipo, x=None, y=None: cdp.send("Input.dispatchTouchEvent", {"type": tipo, "touchPoints": ([{"x": x, "y": y}] if x is not None else [])})
        await tocco("touchStart", c["x"], c["y"]); await p.wait_for_timeout(1800); await tocco("touchEnd"); await p.wait_for_timeout(1200)
        prova("10. col dito: tengo premuto 2 secondi e lascio → UNA richiesta a /assistente/voce, e poi il testo all'assistente", len(richieste("voce")) == 1 and len(richieste("assistente")) == 1, [r for (r, c) in INVIATI])
        await rientra(); INVIATI.clear(); c = await centro()
        await tocco("touchStart", c["x"], c["y"]); await p.wait_for_timeout(1300)
        for dx in (-30, -60, -100, -130): await tocco("touchMove", c["x"] + dx, c["y"]); await p.wait_for_timeout(40)
        await p.wait_for_timeout(200); await tocco("touchEnd"); await p.wait_for_timeout(800)
        prova("10. col dito: scivolo a sinistra di 130 px e lascio → niente parte", len(INVIATI) == 0 and not await p.evaluate("document.getElementById('casella-chat').classList.contains('registra')"), INVIATI)
        await cdp.detach()
        tocca = await p.evaluate("getComputedStyle(document.getElementById('manda-chat')).touchAction")
        prova("10. il bottone ha touch-action:none (il dito che scivola non fa scorrere la pagina)", tocca == "none", tocca)

        # CONTROPROVA: senza il controllo «meno di 1 secondo», la prova dei 0,5 secondi diventa rossa
        vera = PAGINA; segno = "const troppoCorto=durata<1000;"
        prova("10. (controprova) il controllo «meno di 1 secondo» c'è nella pagina", segno in PAGINA)
        PAGINA = PAGINA.replace(segno, "const troppoCorto=false;")
        senza = await mezzo_secondo()
        prova("10. CONTROPROVA: tolto il controllo «meno di 1 secondo», i 0,5 secondi mandano la richiesta e la prova diventa rossa",
              not (senza["voce"] == 0 and senza["assistente"] == 0 and senza["bolle"] == 0 and "Tieni premuto per registrare" in senza["messaggio"]), senza)
        PAGINA = vera
        await entra()

        # 11. 26/10 notte, JJ: «non si può continuare sulla stessa conversazione se la riprendi» e «quando premi il suggerimento deve già
        # rispondere subito, senza aspettare che pensa». I tre tasti rispondono con una frase fissa, senza chiamare la porta; il messaggio
        # dopo parte all'assistente col contesto del tasto davanti (invisibile). Una riga del menù è LA conversazione in corso.
        print("── 11. i tasti rispondono subito; una conversazione si riprende e si continua")
        FRASI = ["Certo, Annamaria. Dimmi cosa devo ricordarti e per quando: il giorno e, se ce l'hai, anche l'ora.",
                 "Va bene, Annamaria. Cosa scade, quando, e se vuoi l'importo: te la ricordo io prima della scadenza.",
                 "Dimmi le cose che ti porti sempre dietro quando esci (chiavi, portafoglio, badge…): te le ricordo io."]
        async def tasto_subito():
            """Col token: tocco il primo tasto; dopo 300 ms c'è la risposta fissa e alla porta non è andato niente."""
            await rientra({"chat": [], "thread": []}); INVIATI.clear(); PORTA.clear(); PORTA["assistente"] = (200, {"risposta": "Segnato, ti ricordo il dentista."})
            await p.click("#prove-chat .prova-chat >> nth=0"); await p.wait_for_timeout(300)
            return {"bolle": await bolle(), "porta": [r for (r, c) in INVIATI]}
        r = await tasto_subito()
        prova("11. tocco «⏰ Ricordami una cosa»: entro 300 ms la bolla della persona e «Certo, …», e NESSUNA richiesta a /assistente",
              r["bolle"] == ["⏰ Ricordami una cosa", FRASI[0]] and r["porta"] == [], r)
        await p.fill("#scrivi", "dentista domani alle 10"); await p.click("#manda-chat"); await p.wait_for_timeout(800)
        ass = richieste("assistente")
        prova("11. scrivo «dentista domani alle 10»: UNA richiesta a /assistente, col contesto del tasto davanti e il testo in fondo",
              len(ass) == 1 and ass[0]["testo"].startswith("[ha toccato «Ricordami una cosa»") and ass[0]["testo"].endswith("] dentista domani alle 10"), ass)
        bb = await bolle()
        prova("11. nella bolla della persona c'è solo «dentista domani alle 10»: il contesto non si vede, in nessuna bolla",
              bb == ["⏰ Ricordami una cosa", FRASI[0], "dentista domani alle 10", "Segnato, ti ricordo il dentista."] and not any("ha toccato" in x for x in bb), bb)
        await p.fill("#scrivi", "e poi?"); await p.click("#manda-chat"); await p.wait_for_timeout(800)
        prova("11. il contesto vale per il messaggio che segue il tasto, non per i successivi", len(richieste("assistente")) == 2 and richieste("assistente")[1]["testo"] == "e poi?", richieste("assistente"))
        # tutti e tre i tasti, con e senza nome
        for nome, attesa in (("Annamaria", FRASI), (None, ["Certo. Dimmi cosa devo ricordarti e per quando: il giorno e, se ce l'hai, anche l'ora.",
                                                          "Va bene. Cosa scade, quando, e se vuoi l'importo: te la ricordo io prima della scadenza.", FRASI[2]])):
            dati = []
            for n in range(3):
                await metti({**{k: v for k, v in CASA.items() if k != "tuo"}, **({"tuo": nome} if nome else {}), "primo": True, "chat": [], "thread": []}); await entra()
                INVIATI.clear(); await p.click(f"#prove-chat .prova-chat >> nth={n}"); await p.wait_for_timeout(300)
                dati.append(((await bolle())[1:], [r_ for (r_, c) in INVIATI]))
            prova(f"11. {'col nome' if nome else 'senza io.tuo'}: le tre risposte fisse sono giuste, senza «undefined» né virgole sbagliate, e nessuna richiesta",
                  [d[0] for d in dati] == [[x] for x in attesa] and all(d[1] == [] for d in dati) and not any("undefined" in x or ",." in x or ", ." in x for d in dati for x in d[0]), dati)
        for n, chiave in enumerate(("Segnami una scadenza", "Cosa porto quando esco")):
            await rientra({"chat": [], "thread": []}); INVIATI.clear(); PORTA["assistente"] = (200, {"risposta": "Ok."})
            await p.click(f"#prove-chat .prova-chat >> nth={n + 1}"); await p.wait_for_timeout(300)
            await p.fill("#scrivi", "il mio testo"); await p.click("#manda-chat"); await p.wait_for_timeout(700)
            a_ = richieste("assistente")
            prova(f"11. il tasto «{chiave}» porta il suo contesto davanti al messaggio dopo", len(a_) == 1 and a_[0]["testo"].startswith(f"[ha toccato «{chiave}»") and a_[0]["testo"].endswith("] il mio testo"), a_)

        # riprendere: 2 conversazioni in io.thread e una in corso → tocco la seconda
        COPIA = lambda: json.loads(json.dumps(THREAD[:2]))
        await rientra({"chat": DA_LEGGERE, "thread": COPIA()}); INVIATI.clear(); PORTA.clear(); PORTA["assistente"] = (200, {"risposta": "Perché dipende dal sito."})
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        await p.click("#conv-elenco .riga-conv >> nth=1 >> .riga-apri"); await p.wait_for_timeout(450)
        s = await stato()
        prova("11. con 2 conversazioni in io.thread e una in corso: tocco la seconda → la chat mostra i suoi messaggi",
              await bolle() == ["Ciao, come va?", "Quanto costa un sito?", "Dipende da cosa deve fare."], await bolle())
        ok_, d = await casa_in_vista(p)
        prova("11. la casella per scrivere c'è, in vista, e il menù si è chiuso", ok_ and not await p.is_visible("#conversazioni"), d)
        prova("11. quella che era in corso è finita in io.thread, che ha sempre 2 conversazioni, e la ripresa non c'è più lì",
              len(s["thread"]) == 2 and [m["id"] for m in s["thread"][0]["messaggi"]] == ["y0", "y0-n"] and [m["id"] for m in s["chat"]] == ["t2-n", "t2", "t2-r"]
              and not any("t2" in json.dumps(c) for c in s["thread"]), s)
        await p.fill("#scrivi", "e poi?"); await p.click("#manda-chat"); await p.wait_for_timeout(800)
        s = await stato()
        prova("11. scrivo «e poi?»: parte a /assistente e la risposta arriva in QUELLA conversazione (non nelle altre)",
              [x["testo"] for x in richieste("assistente")] == ["e poi?"] and [m["testo"] for m in s["chat"]][-2:] == ["e poi?", "Perché dipende dal sito."]
              and len(s["thread"]) == 2 and not any("Perché dipende" in json.dumps(c) for c in s["thread"]), (richieste("assistente"), s))
        # ripresa e rimessa: andata e ritorno senza perdere né raddoppiare niente
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        await p.click("#conv-elenco .riga-conv >> nth=0 >> .riga-apri"); await p.wait_for_timeout(450)
        s = await stato()
        prova("11. andata e ritorno: riprendo l'altra, le due conversazioni si scambiano e io.thread ne ha ancora 2",
              len(s["thread"]) == 2 and [m["id"] for m in s["chat"]] == ["y0", "y0-n"] and any(m.get("testo") == "e poi?" for m in s["thread"][0]["messaggi"]), s)

        # con una risposta in attesa non si cambia
        await metti({**CASA, "primo": True, "thread": COPIA(), "chat": [{"ruolo": "tu", "testo": "Quanto costa un sito?", "id": "w1", "attesa": True}]}); await entra()
        await p.click("#apri-conv"); await p.wait_for_timeout(450)
        prima_ = await stato()
        await p.click("#conv-elenco .riga-conv >> nth=0 >> .riga-apri"); await p.wait_for_timeout(300)
        s = await stato()
        prova("11. con una risposta in attesa: toccare un'altra conversazione non cambia niente", s.get("chat") == prima_.get("chat") and s.get("thread") == prima_.get("thread")
              and len(await bolle()) == 1 and (await bolle())[0].startswith("Quanto costa un sito?"), ({"prima": prima_.get("chat"), "dopo": s.get("chat")}, await bolle()))
        prova("11. e compare «aspetto la risposta…», vicino all'elenco", await p.is_visible("#conv-aspetto") and "aspetto la risposta" in await p.inner_text("#conv-aspetto"), await p.inner_text("#conversazioni"))
        await p.click("#chiudi-conv"); await p.wait_for_timeout(300); await p.click("#apri-conv"); await p.wait_for_timeout(450)
        prova("11. riaperto il menù, l'avviso non c'è più (finché non si tocca di nuovo)", not await p.is_visible("#conv-aspetto"))
        await p.click("#chiudi-conv"); await p.wait_for_timeout(300)

        # CONTROPROVA: se il tasto chiama ancora /assistente invece della risposta fissa, la prima prova diventa rossa
        vera = PAGINA; segno = 'b.addEventListener("click", ()=>tastoChat(b.textContent.trim()))'
        prova("11. (controprova) il punto da spegnere c'è nella pagina", segno in PAGINA)
        PAGINA = PAGINA.replace(segno, 'b.addEventListener("click", ()=>parla(b.textContent.trim(),"chat"))')
        r = await tasto_subito()
        prova("11. CONTROPROVA: se il tasto chiama ancora /assistente, la prova «risposta subito, nessuna richiesta» diventa rossa",
              not (r["bolle"] == ["⏰ Ricordami una cosa", FRASI[0]] and r["porta"] == []), r)
        PAGINA = vera
        await entra()

        prova("nessun errore JavaScript", not errori, errori[:3])
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} prove\n" + ("VERDE" if all(prove) else "ROSSO"))

asyncio.run(main())
