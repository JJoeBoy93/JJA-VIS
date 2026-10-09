"""Una persona di MakeHuman vestita da lavoro: la skin base di JJA-VIS (JJ, 9/10: «le make human devono diventare le skin
base, non voglio omini finti ... la skin base è una persona con i suoi vestiti da lavoro»).

    /home/claude/blenderenv/bin/python modelli/prepara_skin.py persona-<mestiere>-<uomo|donna>   (il modo normale)
    /home/claude/blenderenv/bin/python modelli/genera_persona.py <mestiere> uomo|donna <uscita.glb>  (prova, braccia aperte)

La libreria è nella variabile MAKEHUMAN_LIB (di base /home/claude/mh/lib).

<libreria>: i pacchetti CC0 di MakeHuman scompattati insieme (release «makehuman» di JJA-VIS, li porta la Action
.github/workflows/makehuman.yml). Prima: MPFB2 fra le estensioni di Blender come «mpfb» (vedi genera_mpfb.py).
Ogni vestito usato è CC0: la licenza si legge nell'intestazione del suo .mhclo, e VESTE controlla che ci sia.
"""
import sys, os, glob, importlib, bpy

LIB = os.environ.get("MAKEHUMAN_LIB", "/home/claude/mh/lib")
MESTIERE, CORPO = sys.argv[1:3]; USCITA = sys.argv[3] if len(sys.argv) > 3 else None
donna = CORPO == "donna"
# i vestiti per mestiere (le chiavi sono quelle di VESTITI in citta.html, più «classica»: maglietta, pantaloni e scarpe
# semplici). JJ, 9/10: la skin base è la persona, e sotto «Base JJA-VIS» si sceglie il mestiere; la Classica è la stessa
# persona vestita normale. Ogni .mhclo è CC0 (lo controlla trova()).
TEE = {"uomo": "elvs_crude_t-shirt_male", "donna": "joepal_crude_t-shirt_female"}
STIVALI = {"uomo": "toigo_ankle_boots_male", "donna": "toigo_ankle_boots_female"}
def veste(maglia, pantaloni, scarpe):
    return {c: [x[c] if isinstance(x, dict) else x for x in (maglia, pantaloni, scarpe) if x] for c in ("uomo", "donna")}
VESTE = {
    "corriere":  veste("namuhekam_male_polo_shirt", "cortu_cargo_pants", STIVALI),
    "negozio":   veste("toigo_basic_tucked_t-shirt", "toigo_wool_pants", {"uomo": "shoes01", "donna": "toigo_flats"}),
    "artigiano": veste("male_worksuit01", None, STIVALI),
    "sanita":    veste("toigo_basic_tucked_t-shirt", "toigo_wool_pants", {"uomo": "shoes02", "donna": "toigo_flats"}),
    "ufficio":   veste({"uomo": "toigo_male_suit_tie_and_jacket", "donna": "toigo_female_suit"}, None, {"uomo": "shoes01", "donna": "toigo_flats"}),
    "studio":    veste("toigo_fisherman_sweater", "cortu_cargo_pants", {"uomo": "shoes03", "donna": "toigo_mj_cloth_shoes"}),
    "guida":     veste("namuhekam_male_polo_shirt", "toigo_wool_pants", STIVALI),
    "creator":   veste(TEE, "toigo_wool_pants", {"uomo": "shoes04", "donna": "toigo_mj_cloth_shoes"}),
    "altro":     veste(TEE, "cortu_cargo_pants", {"uomo": "shoes05", "donna": "toigo_flats"}),
    "jjavis":    veste("toigo_fisherman_sweater", "toigo_wool_pants", {"uomo": "shoes01", "donna": "toigo_flats"}),
    "classica":  veste(TEE, "toigo_wool_pants", {"uomo": "shoes01", "donna": "toigo_flats"}),
}
# il ruolo di ogni pezzo decide il nome del suo materiale, ed è col nome che la città lo colora (maglia, pantaloni, pelle,
# capelli: avatarDaSkin). Maglia e pantaloni sono a tinta piena; scarpe e abiti (giacca e cravatta) tengono la loro texture
def ruolo(nome):
    n = nome.lower()
    if any(k in n for k in ("shirt", "sweater", "polo", "worksuit", "tee")): return "maglia"
    if "pants" in n: return "pantaloni"
    if "suit" in n: return "abito"
    return "scarpe"
CAPELLI = {"uomo": "short02", "donna": "ponytail01"}

def trova(nome):
    f = glob.glob(os.path.join(LIB, "**", nome + ".mhclo"), recursive=True)
    if not f: raise SystemExit(f"non trovo {nome}.mhclo in {LIB}")
    testa = open(f[0], encoding="utf-8", errors="replace").read(1500).lower()
    if "agpl" in testa or not ("cc0" in testa or "cc-0" in testa or "creative commons zero" in testa):
        raise SystemExit(f"{nome}: la licenza nell'intestazione non è CC0, non lo uso")
    return f[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
M = lambda n: importlib.import_module("bl_ext.user_default.mpfb.services." + n)
HS, TS = M("humanservice").HumanService, M("targetservice").TargetService
h = HS.create_human(scale=0.1, macro_detail_dict={"gender": 0.0 if donna else 1.0, "age": 0.5, "muscle": 0.55, "weight": 0.5,
    "height": 0.6, "proportions": 0.7, "cupsize": 0.5, "firmness": 0.5, "race": {"african": 0.33, "asian": 0.33, "caucasian": 0.34}})
TS.bake_targets(h)
arm = HS.add_builtin_rig(h, "game_engine")
pezzi = []
def metti(file, tipo):
    o = HS.add_mhclo_asset(file, h, asset_type=tipo, subdiv_levels=0, material_type="GAMEENGINE"); pezzi.append(o); return o
occhi = metti(glob.glob(os.path.join(LIB, "eyes", "low-poly", "*.mhclo"))[0], "Eyes")
# gli occhi con la loro iride (senza, sono palline grigie)
mo = bpy.data.materials.new("occhi"); mo.use_nodes = True; nt = mo.node_tree
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(LIB, "eyes", "materials", "brown_eye.png"))
nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"]); occhi.data.materials.clear(); occhi.data.materials.append(mo)
metti(trova("eyebrow001"), "Eyebrows")

metti(trova(CAPELLI[CORPO]), "Hair")
for n in VESTE[MESTIERE][CORPO]: metti(trova(n), "Clothes").__setitem__("ruolo", ruolo(n))
# il corpo è quello pieno di MakeHuman, SENZA decimate (il decimate rompe le coordinate della texture: bocca e mani a
# macchie rosse, 9/10) e senza il corpo leggero (proxy): il proxy non sa dei vestiti, e i piedi nudi bucavano gli scarponi.
# Le parti coperte le toglie la maschera che ogni vestito mette sul corpo (delete group), applicata qui sotto.
pelle = glob.glob(os.path.join(LIB, "skins", f"young_caucasian_{'female' if donna else 'male'}", "*.mhmat"))[0]
HS.set_character_skin(pelle, h, skin_type="GAMEENGINE")
# maglia e pantaloni: tinta piena chiara, il colore vero lo dà la città (quello del mestiere, o quello scelto allo specchio)
for o in pezzi:
    r = o.get("ruolo")
    if r in ("maglia", "pantaloni"):
        m = bpy.data.materials.new(r); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
        o.data.materials.clear(); o.data.materials.append(m)
# la maglia un filo fuori (9 mm; con 6 restava un segnetto dietro lungo le normali): alla vita i pantaloni la bucavano, e dietro si vedeva una macchia scura
# a stella sopra la cintura (foto di JJ, 9/10). Prima di montarla sullo scheletro: si sposta la forma di riposo
for o in pezzi:
    if o.get("ruolo") in ("maglia", "abito"):
        for v in o.data.vertices: v.co += v.normal * 0.009
# pelle e capelli col nome che la città riconosce. I capelli (e le sopracciglia) diventano grigi chiari, così il colore
# scelto li tinge davvero: una texture castana moltiplicata per il biondo resta castana
for m in list(h.data.materials):
    if m: m.name = "pelle"
for o in pezzi:
    if any(k in o.name.lower() for k in ("eyebrow", "short", "ponytail")):
        for m in o.data.materials:
            m.name = "capelli"
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and n.image.pixels:
                    px = list(n.image.pixels); lum = [0.3 * px[k] + 0.59 * px[k + 1] + 0.11 * px[k + 2] for k in range(0, len(px), 4)]
                    mx = max(lum) or 1
                    for q, L in enumerate(lum):
                        g = 0.45 + 0.55 * L / mx; px[4 * q:4 * q + 3] = (g, g, g)
                    n.image.pixels[:] = px
# le maschere sul corpo (geometrie d'aiuto e parti coperte dai vestiti) si applicano: restano solo testa, braccia e mani
bpy.context.view_layer.objects.active = h
for m in list(h.modifiers):
    if m.type == "MASK": bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0); bpy.ops.object.modifier_apply(modifier=m.name)
# le scarpe troppo fitte sì: le ballerine «toigo_flats» hanno 30.000 punti e da sole facevano pesare una persona 3,5 MB
# (9/10). Sulle scarpe la texture si sporca poco e da lontano non si vede
for o in pezzi:
    if o.get("ruolo") == "scarpe" and len(o.data.vertices) > 5000:
        bpy.context.view_layer.objects.active = o; d = o.modifiers.new("leggero", "DECIMATE"); d.ratio = 4000 / len(o.data.vertices)
        bpy.ops.object.modifier_move_to_index(modifier="leggero", index=0); bpy.ops.object.modifier_apply(modifier="leggero")
# niente decimate su maglie e pantaloni: sul Corriere del 9/10 apriva buchi nella maglia e faceva uscire la pelle dai pantaloni
# trasparenze: MPFB mette tutto in «blend» e a due facce, e three.js disegnava l'interno della bocca sopra la faccia (le
# macchie rosse del 9/10). Pelle, occhi e vestiti diventano opachi e a una faccia; capelli e sopracciglia restano ritagliati
for m in bpy.data.materials:
    if not m.use_nodes: continue
    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf: continue
    ritaglio = any(k in m.name.lower() for k in ("capelli", "eyebrow", "short", "ponytail", "long", "bob", "braid", "afro", "eyelash"))
    if ritaglio:
        m.surface_render_method = "DITHERED"; m.use_backface_culling = False
    else:
        for l in list(bsdf.inputs["Alpha"].links): m.node_tree.links.remove(l)
        bsdf.inputs["Alpha"].default_value = 1.0; m.surface_render_method = "DITHERED"; m.use_backface_culling = True
# texture piccole: 512 al massimo
for im in bpy.data.images:
    if im.size[0] > 512: im.scale(512, int(512 * im.size[1] / im.size[0]))
corpo = h
if USCITA:
    bpy.ops.object.select_all(action="DESELECT")
    for o in [corpo, arm] + pezzi: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=USCITA, export_format="GLB", export_yup=True, export_skins=True, export_animations=False,
                              use_selection=True, export_image_format="JPEG", export_jpeg_quality=80)
    print("scritto", USCITA, round(os.path.getsize(USCITA) / 1024), "kB", sum(len(o.data.vertices) for o in [corpo] + pezzi), "punti")
