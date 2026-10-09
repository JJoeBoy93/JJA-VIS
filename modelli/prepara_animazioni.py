"""Le animazioni delle persone (JJ, 9/10: «camminare, correre, accovacciarsi, sedersi e saltare servono per ora»).

    /home/claude/blenderenv/bin/python modelli/prepara_skin.py animazioni-uomo|animazioni-donna
    (il file della libreria: variabile UAL, di base /home/claude/an/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb)

Prende la Universal Animation Library di Quaternius (CC0, release «animazioni» di JJA-VIS, la scarica la Action
.github/workflows/animazioni.yml) e passa le animazioni sullo scheletro delle nostre persone (MakeHuman «game_engine»,
braccia già abbassate, costruito da prepara_skin come quello delle persone). I nomi degli ossi sono gli stessi (pelvis, spine_01,
thigh_l…), ma le pose di riposo no (loro a T, noi con le braccia giù): si passa la ROTAZIONE NEL MONDO di ogni osso
rispetto al suo riposo, non la rotazione locale. Esce modelli/animazioni/persona-<corpo>.glb: solo lo scheletro e le clip.
"""
import sys, os, glob, bpy
from mathutils import Matrix
QUI = os.path.dirname(os.path.abspath(__file__))
# le dita no: pesano e da lontano non si vedono
# le clavicole no: hanno direzioni diverse nei tre scheletri, e copiarle alzava le spalle a gobba (JJ, 9/10: «doppia gobba
# sulle spalle», da fermi e da seduti). Restano come a riposo
OSSI = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "upperarm_l", "lowerarm_l", "hand_l",
        "upperarm_r", "lowerarm_r", "hand_r", "thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"]
# JJ, 9/10: Quaternius «si muove tipo Crash Bandicoot», le vuole come in Fortnite. Camminare, correre, stare fermi e saltare
# vengono da Human Basic Motions FREE di Kevin Iglesias (mocap; licenza nel PDF del pacchetto: Standard Asset Store EULA,
# gratis e commerciale, non si rivende il pacchetto). Accovacciarsi e sedersi non ci sono nella versione gratis: restano
# Quaternius (CC0). Il loro scheletro ha altri nomi: KEVIN dice quale osso nostro corrisponde a quale loro.
KEVIN = {"pelvis": "B-hips", "spine_01": "B-spine", "spine_03": "B-chest", "neck_01": "B-neck", "head": "B-head",
         **{f"{a}_{l}": f"B-{b}.{L}" for l, L in (("l", "L"), ("r", "R"))
            for a, b in (("clavicle", "shoulder"), ("upperarm", "upperArm"), ("lowerarm", "forearm"), ("hand", "hand"),
                         ("thigh", "thigh"), ("calf", "shin"), ("foot", "foot"), ("ball", "toe"))}}

def tutte(noi, corpo):
    """tutte le clip delle persone su `noi`. Le librerie stanno in /home/claude/an (Quaternius) e /home/claude/kev (Kevin)"""
    ual = os.environ.get("UAL", "/home/claude/an/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb")
    kev = os.environ.get("KEV", "/home/claude/kev/Animations")
    H = "HumanF" if corpo == "donna" else "HumanM"
    k = lambda nome: glob.glob(os.path.join(kev, "**", f"{H}@{nome}.fbx"), recursive=True)[0]
    for f, clip in ((k("Idle01"), "Idle_Loop"), (k("Walk01_Forward"), "Walk_Loop"), (k("Run01_Forward"), "Jog_Fwd_Loop"),
                    (k("Sprint01_Forward"), "Sprint_Loop"), (k("Jump01 - Begin"), "Jump_Start"), (k("Jump01"), "Jump_Loop"),
                    (k("Jump01 - Land"), "Jump_Land")):
        ritarghetta(noi, f, KEVIN, [(None, clip)])
    ritarghetta(noi, ual, None, [(c, c) for c in ("Crouch_Idle_Loop", "Crouch_Fwd_Loop")])
    # seduti: schiena, collo e testa restano dritti (quelli di Quaternius si piegavano in avanti: «non sembra seduto comodo», 9/10)
    ritarghetta(noi, ual, None, [(c, c) for c in ("Sitting_Enter", "Sitting_Idle_Loop", "Sitting_Exit")], salta={"spine_01", "spine_02", "spine_03", "neck_01", "head", "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r"})   # e le braccia lungo i fianchi: con la schiena dritta le loro mani finivano in aria davanti

def riposo(arm):
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)

def ritarghetta(noi, file, mappa, clip, salta=()):
    """noi: lo scheletro di una persona appena costruita (stesso giro di prepara_skin, così il riposo è identico a quello
    dei file delle persone: un glb reimportato in Blender cambia l'orientamento degli ossi e le clip non combacerebbero).
    mappa: osso nostro -> osso loro (None = stessi nomi). clip: [(azione loro o None per l'unica del file, nome nostro)]"""
    prima, azioni_prima = set(bpy.context.scene.objects), set(bpy.data.actions)
    if file.lower().endswith(".fbx"): bpy.ops.import_scene.fbx(filepath=file)
    else: bpy.ops.import_scene.gltf(filepath=file)
    loro = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o not in prima)
    nuove = [a for a in bpy.data.actions if a not in azioni_prima]
    for o in list(bpy.context.scene.objects):
        if o not in prima and o.type != "ARMATURE": bpy.data.objects.remove(o)
    nome = lambda arm, n: next((b for b in arm.pose.bones if b.name.lower() == n.lower()), None)
    coppie = [(nome(noi, n), nome(loro, (mappa or {}).get(n, n))) for n in OSSI]
    coppie = [(a, b) for a, b in coppie if a and b and a.name not in salta]
    print("ossi in comune", len(coppie), "su", len(OSSI))
    # riposo nel mondo
    Rn = {a.name: noi.matrix_world @ a.bone.matrix_local for a, _ in coppie}
    Rl = {b.name: loro.matrix_world @ b.bone.matrix_local for _, b in coppie}
    # braccia e gambe si passano per DIREZIONE: ogni nostro osso punta dove punta il loro adesso, partendo dal nostro riposo,
    # e la torsione resta la nostra. Passare la rotazione intera portava con sé le differenze dei riposi e del «roll» degli
    # ossi: JJ (9/10) le ha viste — gambe divaricate (noi a riposo coi piedi più larghi) e palmi aperti verso l'alto
    from mathutils import Vector
    Y = Vector((0, 1, 0))
    per_direzione = {a.name for a, _ in coppie if any(k in a.name.lower() for k in ("clavicle", "upperarm", "lowerarm", "hand", "thigh", "calf", "foot", "ball"))}
    # altezza dell'anca: lo spostamento del bacino si scala sulle nostre gambe
    hn = Rn[coppie[0][0].name].to_translation().z; hl = Rl[coppie[0][1].name].to_translation().z
    scala = hn / hl if hl else 1
    # gli ossi di MPFB girano in Eulero: le chiavi in quaternione restavano lettera morta e l'esportazione campionava una posa
    # ferma (9/10: la persona camminava a gambe dritte, con le mani avanti)
    for a, _ in coppie: a.rotation_mode = "QUATERNION"
    loro.animation_data_create(); noi.animation_data_create()
    for loro_nome, clip in clip:
        act = nuove[0] if loro_nome is None else next((a for a in nuove if a.name == loro_nome), None)
        if not act: print("manca", clip); continue
        loro.animation_data.action = act
        f0, f1 = (int(x) for x in act.frame_range)
        riposo(noi)   # gli ossi senza chiavi (clavicole, schiena da seduti) devono stare a riposo, non dove li ha lasciati la clip prima
        nuova = bpy.data.actions.new(clip); noi.animation_data.action = nuova
        for f in range(f0, f1 + 1):
            bpy.context.scene.frame_set(f)
            for a, b in coppie:
                Wl = loro.matrix_world @ b.matrix                          # dove sta il loro osso adesso, nel mondo
                if a.name in per_direzione:
                    dl = (Wl.to_3x3() @ Y).normalized(); dn = (Rn[a.name].to_3x3() @ Y).normalized()
                    Wn = dn.rotation_difference(dl).to_matrix().to_4x4() @ Rn[a.name].to_3x3().normalized().to_4x4()
                else:
                    rot = (Wl.to_quaternion() @ Rl[b.name].to_quaternion().inverted())   # quanto ha girato dal riposo, nel mondo
                    Wn = rot.to_matrix().to_4x4() @ Rn[a.name].to_3x3().to_4x4()
                pos = (noi.matrix_world @ a.matrix).to_translation()   # la testa dell'osso dove la porta il padre, già mosso
                if a.name.lower() == "pelvis":
                    d = (Wl.to_translation() - Rl[b.name].to_translation()) * scala; pos = Rn[a.name].to_translation() + d
                M = Matrix.Translation(pos) @ Wn
                a.matrix = noi.matrix_world.inverted() @ M
                if a.name.lower() != "pelvis": a.location = (0, 0, 0)
                bpy.context.view_layer.update()
                a.keyframe_insert("rotation_quaternion", frame=f - f0)
                if a.name.lower() == "pelvis": a.keyframe_insert("location", frame=f - f0)
        tr = noi.animation_data.nla_tracks.new(); tr.name = clip; tr.strips.new(clip, 0, nuova)
        noi.animation_data.action = None
        print("clip", clip, f1 - f0 + 1, "fotogrammi")
    riposo(noi)
    bpy.data.objects.remove(loro)
    for a in nuove: bpy.data.actions.remove(a)
