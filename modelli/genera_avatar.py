"""
Genera l'avatar della città in Blender (bpy 5.0), e lo esporta in glTF (.glb).

    python modelli/genera_avatar.py uomo   -> modelli/avatar-uomo.glb
    python modelli/genera_avatar.py donna  -> modelli/avatar-donna.glb

Serve bpy (Blender come libreria Python, vuole Python 3.11): vedi Ardito-Vault/progetto/piano/blender.md.

SECONDA PROVA (4/10): un corpo solo col modificatore Skin di Blender. Si disegna lo scheletro come una fila di punti
con un raggio (caviglia, ginocchio, anca, vita, petto, collo; spalla, gomito, polso), Blender ne fa una pelle continua,
poi una suddivisione leggera: forme da persona, senza giunture a vista. Testa, capelli, occhi, naso, orecchie, scarpe e
mani sono pezzi a parte (non si piegano).

IL CONTRATTO con la città (citta.html), lo stesso degli omini fatti nel codice:
  - in piedi sull'origine, guarda verso +Z di three.js (in Blender: -Y), alto ~2,1 m
  - giunture: anca a 0,90 m (ossa gamba_s, gamba_d), ginocchio a 0,48 m (stinco_s, stinco_d, figli della gamba; sotto,
    piede_s e piede_d senza pesi, che servono solo a dire dov'è il piede), spalle a 1,55 m (braccio_s, braccio_d), busto,
    testa. Il ginocchio c'è dal 9/10: senza, da seduti la gamba restava dritta in avanti come un bastone (JJ, 6/10)
  - materiali coi nomi che la città ricolora: maglia, pantaloni, pelle, capelli, scarpe, occhi
"""
import sys, os, bpy, bmesh

CORPO = sys.argv[1] if len(sys.argv) > 1 else "uomo"
DONNA = CORPO == "donna"
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.path.join(QUI, f"avatar-{CORPO}.glb")
ANCA, SPALLA, GINOCCHIO = 0.90, 1.55, 0.48
k = 0.9 if DONNA else 1.0          # la donna un po' più sottile
gx = 0.12 if DONNA else 0.14        # gambe dal centro
bx = 0.31 if DONNA else 0.34        # spalle dal centro

bpy.ops.wm.read_factory_settings(use_empty=True)

def materiale(nome, colore):
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = (*colore, 1); b.inputs["Roughness"].default_value = 0.7
    return m
MAT = dict(maglia=materiale("maglia", (0.05, 0.05, 0.07)), pantaloni=materiale("pantaloni", (0.03, 0.04, 0.08)),
           pelle=materiale("pelle", (0.76, 0.52, 0.38)), capelli=materiale("capelli", (0.08, 0.05, 0.03)),
           scarpe=materiale("scarpe", (0.06, 0.06, 0.07)), occhi=materiale("occhi", (0.02, 0.02, 0.02)))

def pelle_da_scheletro(nome, punti, archi, materiali_per_z):
    """punti: [(x,y,z,raggio_x,raggio_y)], archi: [(i,j)] -> mesh continua (Skin + Subsurf), materiale a fasce d'altezza"""
    me = bpy.data.meshes.new(nome); o = bpy.data.objects.new(nome, me); bpy.context.collection.objects.link(o)
    me.from_pydata([(p[0], p[1], p[2]) for p in punti], archi, [])
    sk = o.modifiers.new("pelle", "SKIN"); sk.use_smooth_shade = True
    for v, p in zip(me.skin_vertices[0].data, punti): v.radius = (p[3], p[4])
    me.skin_vertices[0].data[0].use_root = True
    su = o.modifiers.new("morbido", "SUBSURF"); su.levels = 1; su.render_levels = 1
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="pelle"); bpy.ops.object.modifier_apply(modifier="morbido")
    for nm in materiali_per_z: o.data.materials.append(MAT[nm[1]])
    for f in o.data.polygons:   # il materiale secondo l'altezza: sotto la vita pantaloni, sopra maglia
        z = f.center.z
        for i, (zmin, nm) in enumerate(materiali_per_z):
            if z >= zmin: f.material_index = i
    bpy.ops.object.shade_smooth()
    return o

# il corpo: un tronco (bacino, vita, petto, collo) con due gambe e due braccia, tutto attaccato
P = [(0, 0, ANCA + 0.02, 0.21 * k, 0.13 * k),           # 0 bacino
     (0, 0, 1.12, 0.19 * k, 0.12 * k),                   # 1 vita
     (0, 0, 1.38, 0.24 * k, 0.14 * k),                   # 2 petto
     (0, 0, 1.56, 0.25 * k, 0.13 * k),                   # 3 spalle (centro)
     (0, 0, 1.70, 0.065, 0.065)]                         # 4 collo
A = [(0, 1), (1, 2), (2, 3), (3, 4)]
for s in (-1, 1):
    b = len(P)
    P += [(gx * s, 0, ANCA - 0.04, 0.10 * k, 0.10 * k),  # coscia
          (gx * s, -0.01, 0.48, 0.075 * k, 0.075 * k),   # ginocchio
          (gx * s, 0, 0.09, 0.055, 0.055)]               # caviglia
    A += [(0, b), (b, b + 1), (b + 1, b + 2)]
    c = len(P)
    P += [(bx * s, 0, SPALLA, 0.075 * k, 0.075 * k),     # spalla
          (bx * s + 0.01 * s, 0, 1.24, 0.058 * k, 0.058 * k),   # gomito
          (bx * s + 0.015 * s, 0, 0.96, 0.045, 0.045)]    # polso
    A += [(3, c), (c, c + 1), (c + 1, c + 2)]
corpo = pelle_da_scheletro("corpo", P, A, [(-1, "pantaloni"), (ANCA + 0.08, "maglia"), (1.66, "pelle")])

def pezzo(nome, tipo, loc, scala, mat, rot=(0, 0, 0)):
    if tipo == "sfera": bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=loc, rotation=rot, segments=16, ring_count=10)
    else: bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = nome; o.scale = scala; bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(MAT[mat]); bpy.ops.object.shade_smooth(); return o

T = 0.21 if DONNA else 0.22
testa = pezzo("testa", "sfera", (0, 0, 1.90), (T * 1.9, T * 2.0, T * 2.2), "pelle")
altri = {"testa": [testa], "stinco_s": [], "stinco_d": [], "braccio_s": [], "braccio_d": []}
for s in (-1, 1):
    altri["testa"] += [pezzo(f"occhio{s}", "sfera", (0.072 * s, -T * 0.9, 1.92), (0.05, 0.03, 0.06), "occhi"),
                       pezzo(f"orecchio{s}", "sfera", (T * 0.95 * s, 0, 1.89), (0.05, 0.08, 0.09), "pelle")]
    lato = "s" if s < 0 else "d"
    sc = pezzo(f"scarpa{s}", "cubo", (gx * s, -0.05, 0.05), (0.13, 0.28, 0.1), "scarpe")
    bev = sc.modifiers.new("smusso", "BEVEL"); bev.width = 0.03; bev.segments = 2; bpy.context.view_layer.objects.active = sc; bpy.ops.object.modifier_apply(modifier="smusso")
    altri[f"stinco_{lato}"].append(sc)   # la scarpa va con lo stinco: piegando il ginocchio il piede scende con lui
    altri[f"braccio_{lato}"].append(pezzo(f"mano{s}", "sfera", (bx * s + 0.015 * s, 0, 0.90), (0.1, 0.09, 0.13), "pelle"))
altri["testa"].append(pezzo("naso", "sfera", (0, -T * 0.97, 1.87), (0.045, 0.045, 0.055), "pelle"))
cap = pezzo("capelli", "sfera", (0, 0.015, 1.97), (T * 2.06, T * 2.1, T * 1.75), "capelli")
for v in cap.data.vertices:   # la calotta finisce sopra la fronte e scende dietro
    lim = 1.95 + 0.05 * (-v.co.y / T)
    if v.co.z < lim: v.co.z = lim
altri["testa"].append(cap)
if DONNA:
    d = pezzo("capelli_dietro", "cubo", (0, 0.16, 1.74), (0.4, 0.1, 0.48), "capelli")
    bev = d.modifiers.new("smusso", "BEVEL"); bev.width = 0.04; bev.segments = 3; bpy.context.view_layer.objects.active = d; bpy.ops.object.modifier_apply(modifier="smusso")
    altri["testa"].append(d)

# lo scheletro
bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = "scheletro"
bpy.ops.object.mode_set(mode="EDIT"); eb = arm.data.edit_bones; eb.remove(eb[0])
def osso(nome, h, t, padre=None):
    b = eb.new(nome); b.head = h; b.tail = t
    if padre: b.parent = eb[padre]
osso("busto", (0, 0, ANCA), (0, 0, 1.6)); osso("testa", (0, 0, 1.68), (0, 0, 2.1), "busto")
for s, lato in ((-1, "s"), (1, "d")):
    osso(f"gamba_{lato}", (gx * s, 0, ANCA), (gx * s, -0.01, GINOCCHIO), "busto")
    osso(f"stinco_{lato}", (gx * s, -0.01, GINOCCHIO), (gx * s, 0, 0.06), f"gamba_{lato}")
    osso(f"piede_{lato}", (gx * s, 0, 0.06), (gx * s, -0.14, 0.03), f"stinco_{lato}")
    osso(f"braccio_{lato}", (bx * s, 0, SPALLA), (bx * s, 0, SPALLA - 0.6), "busto")
bpy.ops.object.mode_set(mode="OBJECT")

# i pesi del corpo continuo: ogni punto va all'osso più vicino per zona (gambe sotto l'anca, braccia fuori dalle spalle)
# al ginocchio coscia e stinco si dividono il punto in una fascia di 12 cm, così piegando non si spezza
gruppi = {n: corpo.vertex_groups.new(name=n) for n in ("busto", "gamba_s", "gamba_d", "stinco_s", "stinco_d", "braccio_s", "braccio_d")}
for v in corpo.data.vertices:
    x, z = v.co.x, v.co.z
    if abs(x) > bx - 0.06 and z < SPALLA + 0.06 and z > 0.85: gruppi["braccio_s" if x < 0 else "braccio_d"].add([v.index], 1.0, "REPLACE")
    elif z < ANCA - 0.02:
        lato = "s" if x < 0 else "d"; t = min(1.0, max(0.0, (z - (GINOCCHIO - 0.06)) / 0.12))
        if t > 0: gruppi[f"gamba_{lato}"].add([v.index], t, "REPLACE")
        if t < 1: gruppi[f"stinco_{lato}"].add([v.index], 1 - t, "REPLACE")
    else: gruppi["busto"].add([v.index], 1.0, "REPLACE")
oggetti = [corpo]
for n, lista in altri.items():
    for o in lista:
        o.vertex_groups.new(name=n).add(list(range(len(o.data.vertices))), 1.0, "REPLACE"); oggetti.append(o)
bpy.ops.object.select_all(action="DESELECT")
for o in oggetti: o.select_set(True)
bpy.context.view_layer.objects.active = corpo; bpy.ops.object.join(); corpo = bpy.context.active_object; corpo.name = f"avatar_{CORPO}"
corpo.modifiers.new("scheletro", "ARMATURE").object = arm; corpo.parent = arm
bpy.ops.export_scene.gltf(filepath=FUORI, export_format="GLB", export_yup=True, export_skins=True, export_animations=False)
print("scritto", FUORI, round(os.path.getsize(FUORI) / 1024), "kB", "vertici", len(corpo.data.vertices))
