"""Le animazioni delle persone (JJ, 9/10: «camminare, correre, accovacciarsi, sedersi e saltare servono per ora»).

    /home/claude/blenderenv/bin/python modelli/prepara_skin.py animazioni-uomo|animazioni-donna
    (il file della libreria: variabile UAL, di base /home/claude/an/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb)

Prende la Universal Animation Library di Quaternius (CC0, release «animazioni» di JJA-VIS, la scarica la Action
.github/workflows/animazioni.yml) e passa le animazioni sullo scheletro delle nostre persone (MakeHuman «game_engine»,
braccia già abbassate, costruito da prepara_skin come quello delle persone). I nomi degli ossi sono gli stessi (pelvis, spine_01,
thigh_l…), ma le pose di riposo no (loro a T, noi con le braccia giù): si passa la ROTAZIONE NEL MONDO di ogni osso
rispetto al suo riposo, non la rotazione locale. Esce modelli/animazioni/persona-<corpo>.glb: solo lo scheletro e le clip.
"""
import sys, os, bpy
from mathutils import Matrix
QUI = os.path.dirname(os.path.abspath(__file__))
CLIP = ["Idle_Loop", "Walk_Loop", "Jog_Fwd_Loop", "Sprint_Loop", "Crouch_Idle_Loop", "Crouch_Fwd_Loop",
        "Sitting_Enter", "Sitting_Idle_Loop", "Sitting_Exit", "Jump_Start", "Jump_Loop", "Jump_Land"]
# le dita no: pesano e da lontano non si vedono
OSSI = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
        "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"]

def ritarghetta(noi, UAL):
    """noi: lo scheletro di una persona appena costruita (stesso giro di prepara_skin, così il riposo è identico a quello
    dei file delle persone: un glb reimportato in Blender cambia l'orientamento degli ossi e le clip non combacerebbero)"""
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    prima = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=UAL)
    loro = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o not in prima)
    for o in list(bpy.context.scene.objects):
        if o not in prima and o.type == "MESH": bpy.data.objects.remove(o)
    nome = lambda arm, n: next((b for b in arm.pose.bones if b.name.lower() == n.lower()), None)
    coppie = [(nome(noi, n), nome(loro, n)) for n in OSSI]
    coppie = [(a, b) for a, b in coppie if a and b]
    print("ossi in comune", len(coppie), "su", len(OSSI))
    # riposo nel mondo
    Rn = {a.name: noi.matrix_world @ a.bone.matrix_local for a, _ in coppie}
    Rl = {b.name: loro.matrix_world @ b.bone.matrix_local for _, b in coppie}
    # i riposi non sono la stessa posa (loro a T, noi con le braccia giù): prima di passare le rotazioni si porta ogni nostro
    # osso a puntare dove punta il loro a riposo (9/10: con il riposo nostro così com'era, le braccia andavano in alto e avanti)
    from mathutils import Vector
    for a, b in coppie:
        if not any(k in a.name.lower() for k in ("clavicle", "upperarm", "lowerarm", "hand")): continue   # solo le braccia: su schiena e gambe allineare piegava in avanti il busto
        dn = (Rn[a.name].to_3x3() @ Vector((0, 1, 0))).normalized(); dl = (Rl[b.name].to_3x3() @ Vector((0, 1, 0))).normalized()
        q = dn.rotation_difference(dl)
        Rn[a.name] = Matrix.Translation(Rn[a.name].to_translation()) @ (q.to_matrix() @ Rn[a.name].to_3x3()).to_4x4()
    # altezza dell'anca: lo spostamento del bacino si scala sulle nostre gambe
    hn = Rn[coppie[0][0].name].to_translation().z; hl = Rl[coppie[0][1].name].to_translation().z
    scala = hn / hl if hl else 1
    # gli ossi di MPFB girano in Eulero: le chiavi in quaternione restavano lettera morta e l'esportazione campionava una posa
    # ferma (9/10: la persona camminava a gambe dritte, con le mani avanti)
    for a, _ in coppie: a.rotation_mode = "QUATERNION"
    loro.animation_data_create(); noi.animation_data_create()
    for clip in CLIP:
        act = bpy.data.actions.get(clip)
        if not act: print("manca", clip); continue
        loro.animation_data.action = act
        f0, f1 = (int(x) for x in act.frame_range)
        nuova = bpy.data.actions.new(clip); noi.animation_data.action = nuova
        for f in range(f0, f1 + 1):
            bpy.context.scene.frame_set(f)
            for a, b in coppie:
                Wl = loro.matrix_world @ b.matrix                          # dove sta il loro osso adesso, nel mondo
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
    bpy.data.objects.remove(loro)
