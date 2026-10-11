"""Gli dèi dell'Olimpo: le skin degli agenti (JJ, 11/10: «gli agenti devono avere la loro skin, non devono essere come gli altri
avatar»). Una libreria CC0 di dèi che camminino e si siedano non esiste (cercata l'11/10: ci sono solo statue scansionate, ferme e
da centinaia di migliaia di poligoni). Quindi: una persona di MakeHuman (CC0, la stessa catena di genera_persona.py) con la veste
del suo dio (vestiti MakeHuman CC0: la tunica lunga di Donitz, gli abiti a pieghe di Toigo) e i suoi attributi, fatti qui in
Blender e legati all'osso che li porta (la testa, la mano). Non sono skin in vendita: sono degli agenti.

    /home/claude/blenderenv/bin/python modelli/genera_dio.py <dio> [<dio> ...]     ->  modelli/dei/<dio>.glb
    /home/claude/blenderenv/bin/python modelli/genera_dio.py tutti

La libreria MakeHuman deve avere anche dress01 e suits02 (release «makehuman» di JJA-VIS). La licenza di ogni vestito la
controlla genera_persona.trova (CC0, mai AGPL: la tunica micenea di WDG è AGPL e non si usa).
"""
import sys, os, math, json, runpy, bpy, bmesh
from mathutils import Vector, Matrix
QUI = os.path.dirname(os.path.abspath(__file__)); FUORI = os.path.join(QUI, "dei"); os.makedirs(FUORI, exist_ok=True)

ORO, ARGENTO, BRONZO, LEGNO, SCURO = (0.85, 0.65, 0.18), (0.78, 0.8, 0.84), (0.55, 0.36, 0.17), (0.36, 0.24, 0.14), (0.12, 0.11, 0.13)
TUNICA, PEPLO, CORTO = "donitz_monk_robe", "toigo_halter_dress_with_fluted_skirt", "toigo_halter_dress_midi"
SANDALI = {"uomo": "toigo_ankle_boots_male", "donna": "toigo_flats"}
# il dio: corpo, età, veste, colore della veste, capelli (colore in Blender, fisso), attributi
DEI = {
  "zeus":      dict(corpo="uomo",  eta=0.85, veste=TUNICA, colore=(0.93, 0.92, 0.88), capelli=(0.85, 0.85, 0.85), cose=["alloro_oro", "fulmine"]),
  "hera":      dict(corpo="donna", eta=0.6,  veste=PEPLO,  colore=(0.42, 0.2, 0.5),   capelli=(0.18, 0.1, 0.06),  cose=["diadema", "scettro"]),
  "athena":    dict(corpo="donna", eta=0.5,  veste=PEPLO,  colore=(0.85, 0.86, 0.9),  capelli=(0.16, 0.1, 0.06),  cose=["elmo", "lancia", "scudo"]),
  "ares":      dict(corpo="uomo",  eta=0.5,  veste=TUNICA, colore=(0.5, 0.08, 0.06),  capelli=(0.1, 0.07, 0.05),  cose=["elmo_rosso", "lancia", "scudo_bronzo"]),
  "poseidone": dict(corpo="uomo",  eta=0.8,  veste=TUNICA, colore=(0.1, 0.42, 0.5),   capelli=(0.75, 0.78, 0.8),  cose=["corona", "tridente"]),
  "apollo":    dict(corpo="uomo",  eta=0.5,  veste=TUNICA, colore=(0.95, 0.85, 0.5),  capelli=(0.75, 0.55, 0.2),  cose=["alloro", "lira"]),
  "artemide":  dict(corpo="donna", eta=0.5,  veste=CORTO,  colore=(0.3, 0.45, 0.25),  capelli=(0.35, 0.2, 0.1),   cose=["luna", "arco"]),
  "efesto":    dict(corpo="uomo",  eta=0.7,  veste=TUNICA, colore=(0.35, 0.22, 0.14), capelli=(0.12, 0.08, 0.06), cose=["martello"]),
  "afrodite":  dict(corpo="donna", eta=0.5,  veste=PEPLO,  colore=(0.92, 0.55, 0.62), capelli=(0.8, 0.6, 0.3),   cose=["diadema", "specchio"]),
  "hestia":    dict(corpo="donna", eta=0.65, veste=PEPLO,  colore=(0.85, 0.42, 0.15), capelli=(0.25, 0.14, 0.08), cose=["fiamma"]),
  "demetra":   dict(corpo="donna", eta=0.65, veste=PEPLO,  colore=(0.82, 0.68, 0.25), capelli=(0.55, 0.38, 0.18), cose=["spighe", "covone"]),
  "hermes":    dict(corpo="uomo",  eta=0.5,  veste=TUNICA, colore=(0.45, 0.65, 0.85), capelli=(0.3, 0.18, 0.08),  cose=["petaso", "caduceo"]),
  "ade":       dict(corpo="uomo",  eta=0.75, veste=TUNICA, colore=(0.09, 0.08, 0.1),  capelli=(0.05, 0.05, 0.05), cose=["corona_scura", "bidente"]),
  "persefone": dict(corpo="donna", eta=0.5,  veste=PEPLO,  colore=(0.3, 0.12, 0.3),   capelli=(0.1, 0.06, 0.05),  cose=["fiori", "pianta"]),
  "dioniso":   dict(corpo="uomo",  eta=0.5, veste=TUNICA, colore=(0.38, 0.12, 0.4),  capelli=(0.18, 0.1, 0.06),  cose=["edera", "coppa"]),
}

def materiale(nome, colore, luce=0.0, metallo=0.0):
    m = bpy.data.materials.get(nome)
    if m: return m
    m = bpy.data.materials.new(nome); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colore, 1); b.inputs["Roughness"].default_value = 0.45 if metallo else 0.8
    b.inputs["Metallic"].default_value = metallo
    if luce: b.inputs["Emission Color"].default_value = (*colore, 1); b.inputs["Emission Strength"].default_value = luce
    return m

class Pezzo:
    """un attributo fatto di forme semplici, in metri, nel sistema della persona (Z in alto, -Y davanti)"""
    def __init__(s): s.bm = bmesh.new(); s.mat = []; s.idx = {}
    def _m(s, mat):
        if mat.name not in s.idx: s.idx[mat.name] = len(s.mat); s.mat.append(mat)
        return s.idx[mat.name]
    def _metti(s, geo_fn, mat, M):
        t = bmesh.new(); geo_fn(t); bmesh.ops.transform(t, matrix=M, verts=t.verts)
        k = s._m(mat)
        for f in t.faces: f.material_index = k
        me = bpy.data.meshes.new("t"); t.to_mesh(me); s.bm.from_mesh(me); bpy.data.meshes.remove(me); t.free()
    def cil(s, a, b, r1, r2, mat, seg=10):
        a, b = Vector(a), Vector(b); d = b - a; L = d.length
        R = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        s._metti(lambda t: bmesh.ops.create_cone(t, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=L), mat, Matrix.Translation((a + b) / 2) @ R)
    def scatola(s, c, dim, mat, rot=Matrix()):
        s._metti(lambda t: bmesh.ops.create_cube(t, size=1), mat, Matrix.Translation(c) @ rot.to_4x4() @ Matrix.Diagonal((*dim, 1)))
    def palla(s, c, r, mat, sc=(1, 1, 1), seg=10):
        s._metti(lambda t: bmesh.ops.create_uvsphere(t, u_segments=seg, v_segments=max(5, seg // 2), radius=r), mat, Matrix.Translation(c) @ Matrix.Diagonal((*sc, 1)))
    def anello(s, c, R, r, mat, da=0, a=2 * math.pi, n=24, asse=Matrix()):
        for k in range(n):
            t0 = da + (a - da) * k / n; t1 = da + (a - da) * (k + 1) / n
            p0 = Vector(c) + asse @ Vector((math.cos(t0) * R, math.sin(t0) * R, 0)); p1 = Vector(c) + asse @ Vector((math.cos(t1) * R, math.sin(t1) * R, 0))
            s.cil(p0, p1, r, r, mat, seg=6)
    def oggetto(s, nome, arm, osso):
        me = bpy.data.meshes.new(nome); s.bm.to_mesh(me)
        for m in s.mat: me.materials.append(m)
        o = bpy.data.objects.new(nome, me); bpy.context.scene.collection.objects.link(o)
        g = o.vertex_groups.new(name=osso); g.add(list(range(len(me.vertices))), 1.0, "REPLACE")
        mo = o.modifiers.new("Armature", "ARMATURE"); mo.object = arm; o.parent = arm
        return o

def attributi(nome, arm, corpo):
    B = {b.name: b for b in arm.data.bones}
    W = arm.matrix_world
    testa_c = W @ B["head"].head_local; testa_t = W @ B["head"].tail_local
    # l'osso della testa va dal collo alla cima del capo: la fascia di una corona sta a due terzi (prima l'11/10 l'elmo galleggiava
    # una spanna sopra la testa: la cima era stimata oltre la punta dell'osso)
    Lt = (testa_t - testa_c).length
    fronte = Vector((testa_c.x, testa_c.y, testa_c.z + Lt * 0.8))
    print("testa", round(testa_c.z, 3), round(testa_t.z, 3), "fascia", round(fronte.z, 3))
    mano = {l: (W @ B[f"hand_{l}"].head_local).lerp(W @ B[f"hand_{l}"].tail_local, 0.6) for l in ("r", "l")}
    oro, arg, bro, leg, scu = materiale("oro", ORO, metallo=1), materiale("argento", ARGENTO, metallo=1), materiale("bronzo", BRONZO, metallo=1), materiale("legno", LEGNO), materiale("scuro", SCURO, metallo=0.5)
    verde = materiale("foglie", (0.2, 0.42, 0.16)); rosso = materiale("pennacchio", (0.6, 0.05, 0.04))
    luce = materiale("luce", (1.0, 0.55, 0.1), luce=4.0); fulm = materiale("lampo", (1.0, 0.9, 0.4), luce=3.0)
    T, M = Pezzo(), Pezzo()   # T sulla testa, M nelle mani (due pezzi: mano destra e sinistra)
    Ms = Pezzo()
    rt = 0.105   # raggio della testa
    hz = fronte.z
    def corona(mat, foglie=None, punte=0):
        T.anello((fronte.x, fronte.y + 0.01, hz), rt + 0.012, 0.009, mat)
        if foglie:
            for k in range(22):
                a = k / 22 * 2 * math.pi
                if abs(math.sin(a)) > 0.92 and math.sin(a) < 0: continue   # davanti al centro, la fronte libera
                p = (fronte.x + math.cos(a) * (rt + 0.02), fronte.y + 0.01 + math.sin(a) * (rt + 0.02), hz + 0.012 * (k % 2))
                T.palla(p, 0.022, foglie, sc=(0.6, 1.4, 0.35), seg=6)
        for k in range(punte):
            a = k / punte * 2 * math.pi
            b = Vector((fronte.x + math.cos(a) * (rt + 0.012), fronte.y + 0.01 + math.sin(a) * (rt + 0.012), hz))
            T.cil(b, b + Vector((0, 0, 0.07)), 0.014, 0.001, mat, seg=4)
    asta = lambda mano_, giu, su, r=0.017, mat=leg: M.cil(mano_ + Vector((0, 0, -giu)), mano_ + Vector((0, 0, su)), r, r, mat)
    R, L = mano["r"], mano["l"]
    for c in DEI[nome]["cose"]:
        if c == "alloro_oro": corona(oro, foglie=oro)
        elif c == "alloro": corona(verde, foglie=verde)
        elif c == "edera": corona(verde, foglie=verde); [T.palla((fronte.x + s * 0.09, fronte.y - 0.02, hz - 0.03), 0.025, materiale("uva", (0.3, 0.08, 0.35))) for s in (-1, 1)]
        elif c == "spighe": corona(oro, foglie=materiale("grano", (0.85, 0.7, 0.3)))
        elif c == "corona": corona(oro, punte=7)
        elif c == "corona_scura": corona(scu, punte=9)
        elif c == "diadema":
            T.anello((fronte.x, fronte.y + 0.01, hz), rt + 0.01, 0.007, oro, da=math.pi * 1.15, a=math.pi * 1.85)
            T.palla((fronte.x, fronte.y - rt - 0.012, hz + 0.03), 0.02, oro, sc=(1, 0.4, 1.4))
        elif c == "luna":
            T.anello((fronte.x, fronte.y + 0.01, hz), rt + 0.01, 0.006, arg, da=math.pi * 1.15, a=math.pi * 1.85)
            T.anello((fronte.x, fronte.y - rt - 0.015, hz + 0.05), 0.04, 0.008, arg, da=math.pi * 1.1, a=math.pi * 1.9, n=10, asse=Matrix.Rotation(math.pi / 2, 3, "X"))
        elif c in ("elmo", "elmo_rosso"):
            met = bro if c == "elmo_rosso" else oro
            T.palla((testa_c.x, testa_c.y + 0.035, hz + 0.01), rt + 0.02, met, sc=(1, 1.05, 0.9), seg=14)
            T.scatola((testa_c.x, testa_c.y + 0.03, hz + rt + 0.05), (0.03, 0.26, 0.1), rosso if c == "elmo_rosso" else materiale("criniera", (0.1, 0.25, 0.5)))
        elif c == "petaso":
            T.cil((fronte.x, fronte.y + 0.01, hz + 0.03), (fronte.x, fronte.y + 0.01, hz + 0.045), rt + 0.09, rt + 0.09, materiale("feltro", (0.55, 0.45, 0.3)), seg=16)
            T.palla((fronte.x, fronte.y + 0.01, hz + 0.06), rt * 0.95, materiale("feltro", (0.55, 0.45, 0.3)), sc=(1, 1, 0.55), seg=12)
            for s in (-1, 1): T.palla((fronte.x + s * (rt + 0.04), fronte.y + 0.04, hz + 0.1), 0.05, materiale("piume", (0.95, 0.95, 0.95)), sc=(0.25, 1.4, 0.8), seg=6)
        elif c == "lancia": asta(R, 0.9, 1.25); M.cil(R + Vector((0, 0, 1.25)), R + Vector((0, 0, 1.45)), 0.035, 0.001, bro, seg=6)
        elif c in ("scudo", "scudo_bronzo"):
            fuori = Vector((1 if L.x > 0 else -1, 0, 0))
            c0 = L + fuori * 0.07 + Vector((0, 0, 0.12))
            Ms.cil(c0, c0 + fuori * 0.03, 0.34, 0.34, bro if c == "scudo_bronzo" else oro, seg=20)
            Ms.cil(c0 + fuori * 0.03, c0 + fuori * 0.06, 0.12, 0.08, oro if c == "scudo_bronzo" else materiale("civetta", (0.3, 0.3, 0.32)), seg=12)
        elif c == "tridente":
            asta(R, 0.9, 1.25, mat=oro); y0 = R + Vector((0, 0, 1.25)); M.cil(y0 + Vector((-0.12, 0, 0)), y0 + Vector((0.12, 0, 0)), 0.015, 0.015, oro)
            for dx in (-0.12, 0, 0.12): M.cil(y0 + Vector((dx, 0, 0)), y0 + Vector((dx, 0, 0.25)), 0.014, 0.002, oro, seg=6)
        elif c == "fulmine":
            punti = [Vector(p) for p in ((0, 0, -0.35), (0.06, 0, -0.12), (-0.04, 0, -0.04), (0.05, 0, 0.16), (-0.03, 0, 0.24), (0.03, 0, 0.45))]
            for a, b in zip(punti, punti[1:]): M.cil(R + a, R + b, 0.022, 0.016, fulm, seg=6)
        elif c == "scettro": asta(R, 0.85, 0.75, mat=oro, r=0.014); M.palla(R + Vector((0, 0, 0.78)), 0.05, materiale("gemma", (0.35, 0.1, 0.5), luce=1.0))
        elif c == "bidente":
            asta(R, 0.9, 1.2, mat=scu); y0 = R + Vector((0, 0, 1.2)); M.cil(y0 + Vector((-0.07, 0, 0)), y0 + Vector((0.07, 0, 0)), 0.014, 0.014, scu)
            for dx in (-0.07, 0.07): M.cil(y0 + Vector((dx, 0, 0)), y0 + Vector((dx, 0, 0.22)), 0.013, 0.002, scu, seg=6)
        elif c == "caduceo":
            asta(R, 0.35, 0.6, mat=oro, r=0.012); top = R + Vector((0, 0, 0.6)); M.palla(top, 0.035, oro)
            for s in (-1, 1): M.palla(top + Vector((s * 0.07, 0, -0.03)), 0.05, materiale("piume", (0.95, 0.95, 0.95)), sc=(1.4, 0.25, 0.7), seg=6)
            for k in range(6): M.palla(R + Vector((0.025 * math.cos(k * 1.6), 0.025 * math.sin(k * 1.6), 0.05 + k * 0.08)), 0.018, materiale("serpenti", (0.2, 0.4, 0.2)), seg=6)
        elif c == "lira":
            b0 = L + Vector((0, -0.08, 0.05)); Ms.cil(b0 + Vector((-0.1, 0, 0)), b0 + Vector((0.1, 0, 0)), 0.02, 0.02, oro)
            for s in (-1, 1): Ms.cil(b0 + Vector((s * 0.1, 0, 0)), b0 + Vector((s * 0.13, 0, 0.3)), 0.016, 0.012, oro)
            Ms.cil(b0 + Vector((-0.13, 0, 0.3)), b0 + Vector((0.13, 0, 0.3)), 0.012, 0.012, oro)
            for k in range(5): x = -0.07 + k * 0.035; Ms.cil(b0 + Vector((x, 0, 0)), b0 + Vector((x, 0, 0.3)), 0.002, 0.002, materiale("corde", (0.95, 0.92, 0.8)), seg=3)
        elif c == "arco":
            Ms.anello(L + Vector((0, -0.12, 0.1)), 0.55, 0.012, leg, da=-1.1, a=1.1, n=14, asse=Matrix.Rotation(math.pi / 2, 3, "Y") @ Matrix.Rotation(math.pi / 2, 3, "Z"))
            Ms.cil(L + Vector((0, -0.12 + math.cos(1.1) * 0.55 - 0.55, 0.1 - math.sin(1.1) * 0.55)), L + Vector((0, -0.12 + math.cos(1.1) * 0.55 - 0.55, 0.1 + math.sin(1.1) * 0.55)), 0.002, 0.002, materiale("corde", (0.95, 0.92, 0.8)), seg=3)
        elif c == "martello":
            asta(R, 0.05, 0.42, r=0.016); M.scatola(R + Vector((0, 0, 0.45)), (0.08, 0.2, 0.08), scu)
        elif c == "specchio":
            asta(R, 0.0, 0.14, mat=oro, r=0.01); M.cil(R + Vector((0, 0, 0.22)), R + Vector((0, -0.01, 0.22)), 0.08, 0.08, arg, seg=16)
            M.anello(R + Vector((0, -0.005, 0.22)), 0.085, 0.008, oro, asse=Matrix.Rotation(math.pi / 2, 3, "X"))
        elif c == "fiamma":
            c0 = R + Vector((0, -0.05, 0.08)); M.cil(c0, c0 + Vector((0, 0, 0.07)), 0.03, 0.09, bro, seg=12); M.cil(c0 + Vector((0, 0, 0.07)), c0 + Vector((0, 0, 0.3)), 0.07, 0.0, luce, seg=8)
        elif c == "covone":
            c0 = L + Vector((0, -0.08, 0.1)); gr = materiale("grano", (0.85, 0.7, 0.3))
            for k in range(9): a = k * 0.7; d = Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0)); M.cil(c0 + d + Vector((0, 0, -0.25)), c0 + d * 3 + Vector((0, 0, 0.3)), 0.008, 0.008, gr, seg=4); M.palla(c0 + d * 3.2 + Vector((0, 0, 0.34)), 0.02, gr, sc=(0.6, 0.6, 1.8), seg=5)
        elif c == "coppa":
            c0 = R + Vector((0, -0.06, 0.06)); M.cil(c0, c0 + Vector((0, 0, 0.08)), 0.03, 0.03, oro, seg=8); M.cil(c0 + Vector((0, 0, 0.08)), c0 + Vector((0, 0, 0.16)), 0.03, 0.09, oro, seg=14)
            M.cil(c0 + Vector((0, 0, 0.155)), c0 + Vector((0, 0, 0.165)), 0.08, 0.08, materiale("vino", (0.4, 0.04, 0.1)), seg=14)
        elif c in ("fiori", "pianta"):
            pass
    if "pianta" in DEI[nome]["cose"]:   # la pianta carnivora di Persefone: il suo simbolo nell'Olimpo di JARVIS
        c0 = R + Vector((0, -0.06, 0.1)); M.cil(c0 + Vector((0, 0, -0.1)), c0 + Vector((0, 0, 0.12)), 0.008, 0.008, verde, seg=5)
        for s in (-1, 1): M.palla(c0 + Vector((s * 0.03, 0, 0.16)), 0.05, materiale("trappola", (0.45, 0.6, 0.15)), sc=(0.45, 1, 0.8), seg=8)
        for k in range(7): a = k / 7 * 2 * math.pi; T.palla((fronte.x + math.cos(a) * (rt + 0.015), fronte.y + 0.01 + math.sin(a) * (rt + 0.015), hz), 0.024, materiale("melograno", (0.55, 0.05, 0.12)), seg=6)
    fuori = []
    if T.bm.verts: fuori.append(T.oggetto("attributi_testa", arm, "head"))
    if M.bm.verts: fuori.append(M.oggetto("attributi_destra", arm, "hand_r"))
    if Ms.bm.verts: fuori.append(Ms.oggetto("attributi_sinistra", arm, "hand_l"))
    return fuori

def braccia_giu(corpi, arm, gradi=30):
    """come prepara_skin: si abbassano le braccia e la posa diventa quella di riposo (le persone sono fatte così)"""
    bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for lato, s_ in (("l", 1), ("r", -1)):
        pb = arm.pose.bones[f"upperarm_{lato}"]; m = pb.matrix.copy(); t = m.to_translation()
        pb.matrix = Matrix.Translation(t) @ Matrix.Rotation(math.radians(gradi) * s_, 4, "Y") @ Matrix.Translation(-t) @ m
    bpy.context.view_layer.update(); bpy.ops.object.mode_set(mode="OBJECT")
    for h in corpi:
        mods = [m for m in h.modifiers if m.type == "ARMATURE"]
        if not mods: continue
        bpy.ops.object.select_all(action="DESELECT"); h.select_set(True); bpy.context.view_layer.objects.active = h
        bpy.ops.object.modifier_copy(modifier=mods[0].name); bpy.ops.object.modifier_apply(modifier=mods[0].name)
    bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE"); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode="OBJECT")

def fai(nome):
    d = DEI[nome]
    os.environ["DIO"] = json.dumps({"vesti": [d["veste"], SANDALI[d["corpo"]]], "eta": d["eta"]})
    sys.argv = [sys.argv[0], "classica", d["corpo"]]
    g = runpy.run_path(os.path.join(QUI, "genera_persona.py"))
    corpi = [g["corpo"]] + g["pezzi"]
    braccia_giu(corpi, g["arm"])
    # la veste del colore del dio, a tinta piena con la sua trama di pieghe sotto (il colore moltiplica la texture)
    for o in g["pezzi"]:
        if o.get("ruolo") == "veste":
            for m in o.data.materials:
                if not m: continue
                m.name = "veste"
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image and n.image.pixels:
                        px = list(n.image.pixels); c = d["colore"]
                        for q in range(0, len(px), 4):
                            L = 0.35 + 0.65 * (0.3 * px[q] + 0.59 * px[q + 1] + 0.11 * px[q + 2])
                            px[q:q + 3] = (min(1, c[0] * L * 1.3), min(1, c[1] * L * 1.3), min(1, c[2] * L * 1.3))
                        n.image.pixels[:] = px; n.image.name = "veste-" + nome
                b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                if b and not b.inputs["Base Color"].links: b.inputs["Base Color"].default_value = (*d["colore"], 1)
        # i capelli del colore del dio: genera_persona li ha resi grigi chiari, qui si tingono nella texture stessa
        if any(k in o.name.lower() for k in ("short", "ponytail")):
            for m in o.data.materials:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image and n.image.pixels:
                        px = list(n.image.pixels); c = d["capelli"]
                        for q in range(0, len(px), 4): px[q:q + 3] = (px[q] * c[0] * 1.6, px[q + 1] * c[1] * 1.6, px[q + 2] * c[2] * 1.6)
                        n.image.pixels[:] = px; n.image.name = "capelli-" + nome
                m.name = "chioma"   # non «capelli»: la città non li ricolora, il colore è del dio
    att = attributi(nome, g["arm"], d["corpo"])
    out = os.path.join(FUORI, nome + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    for o in [g["arm"]] + corpi + att: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_yup=True, export_skins=True, export_animations=False,
                              use_selection=True, export_image_format="JPEG", export_jpeg_quality=80)
    print("scritto", out, os.path.getsize(out) // 1024, "kB")

if __name__ == "__main__":
    quali = list(DEI) if sys.argv[1:] == ["tutti"] else sys.argv[1:]
    for q in quali: fai(q)
