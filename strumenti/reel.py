# Il primo reel di JJA-VIS (26 settembre 2026, Athena).
# Uso: python3 strumenti/reel.py  (dalla radice del repository; serve playwright con chromium)
# Poi: ffmpeg -framerate 24 -i fotogrammi/%05d.png -f lavfi -i anullsrc=r=44100:cl=stereo -shortest -vf "fade=t=in:st=0:d=0.3,fade=t=out:st=19.1:d=0.3,format=yuv420p" -c:v libx264 -crf 18 -movflags +faststart -c:a aac reel.mp4
"""Il primo reel di JJA-VIS, girato sulla pagina vera (JJA-VIS@1d70416).
Tempo del browser finto: 24 fotogrammi al secondo esatti, anche se ogni
fotografia ne richiede di più. Nessuna chiamata esce: la porta è finta."""
import asyncio, json, os, shutil
from playwright.async_api import async_playwright
PAGINA=open("index.html",encoding="utf-8").read()
CONTO=open("conto.json").read()
BASE="https://jjoeboy93.github.io/JJA-VIS/"
FPS=24; OUT="fotogrammi"
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
n=[0]
async def instrada(route):
    u=route.request.url
    if u.startswith(BASE) and not u.endswith(".json"): return await route.fulfill(body=PAGINA, content_type="text/html")
    if u.endswith("conto.json"): return await route.fulfill(body=CONTO, content_type="application/json")
    await route.fulfill(status=404, body="")
DIDA='''([t, piccola])=>{let d=document.getElementById('dida');
 if(!d){d=document.createElement('div');d.id='dida';document.body.appendChild(d);
  Object.assign(d.style,{position:'fixed',left:'6%',right:'6%',top:'17%',zIndex:99,padding:'14px 16px',
   background:'rgba(2,11,24,.82)',border:'1px solid rgba(0,180,216,.6)',color:'#E8F7FF',textAlign:'center',
   font:'800 25px/1.18 "DejaVu Sans", sans-serif',letterSpacing:'.01em',boxShadow:'0 0 24px rgba(0,180,216,.35)',
   transition:'opacity .25s',borderRadius:'4px'});}
 if(!t){d.style.opacity=0;return;} d.style.opacity=1; d.innerHTML=t+(piccola?'<div style="font:600 15px/1.3 DejaVu Sans Mono,monospace;margin-top:6px;color:#7FDBFF">'+piccola+'</div>':'');}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        ctx=await b.new_context(viewport={"width":432,"height":768}, device_scale_factor=2.5, has_touch=True, is_mobile=True)
        await ctx.route("**/*", instrada)
        pg=await ctx.new_page()
        await pg.clock.install()
        await pg.goto(BASE); await pg.clock.run_for(300)
        await pg.add_style_tag(content="#dida b{color:#FFD60A} ::-webkit-scrollbar{display:none}")
        async def scatta(secondi, prima=None):
            for i in range(int(secondi*FPS)):
                if prima: await prima(i)
                await pg.clock.run_for(1000//FPS)
                await pg.screenshot(path=f"{OUT}/{n[0]:05d}.png"); n[0]+=1
        dida=lambda t,s=None: pg.evaluate(DIDA,[t,s])
        # 1 — l'aggancio
        await dida("Un assistente che impara <b>il tuo</b> lavoro")
        await scatta(3.2)
        # 2 — il nome, lettera per lettera
        await dida("Gli dai un nome","il tuo, non il mio")
        await pg.click("#sigla")
        lettere="Nova"
        async def scrivi(i):
            if i%5==0 and i//5 < len(lettere): await pg.keyboard.type(lettere[i//5])
        await scatta(3.0, scrivi)
        await pg.click("#avanti-o1"); await pg.clock.run_for(600)
        # 3 — il colore
        await dida("…e il colore che vuoi")
        temi=["calmo","deciso","naturale","tech"]
        async def colora(i):
            if i%14==0 and i//14 < len(temi): await pg.click(f'#temi [data-tema="{temi[i//14]}"]')
        await scatta(3.4, colora)
        # 4 — la Bottega
        await pg.evaluate("location.hash='#bottega'"); await pg.clock.run_for(400)
        await dida("<b>Sopralluogo gratis</b> del tuo sito","e i lavori su misura, già adesso")
        await pg.evaluate("document.getElementById('sopralluogo').scrollIntoView({block:'start'}); window.scrollBy(0,-250)")
        async def scorri(i): await pg.evaluate("window.scrollBy(0,2)")
        await scatta(3.4, scorri)
        await dida("Per guide turistiche: <b>Clio</b>","parli una volta, ognuno ti legge nella sua lingua")
        await pg.evaluate("document.getElementById('clio').scrollIntoView({block:'start'}); window.scrollBy(0,-250)")
        await scatta(3.0, scorri)
        # 5 — la chiusura
        await pg.evaluate("location.hash='#inizia'"); await pg.clock.run_for(400); await pg.evaluate("window.scrollTo(0,0)")
        await pg.evaluate("document.getElementById('p-inizia').style.visibility='hidden'")
        await dida("Provalo:<br>è <b>gratis</b>","link in bio")
        await pg.evaluate("Object.assign(document.getElementById('dida').style,{top:'50%',fontSize:'34px',padding:'22px 16px'})")
        await scatta(3.5)
        await b.close()
    print("fotogrammi:", n[0])
asyncio.run(main())
