"""Build a rigged, gallop-animated horse procedurally and export assets/horse.glb.

Run:  blender -b -P scripts/blender/build_horse.py -- <out_dir> [preview_dir]
Body = metaballs (organic blending) converted to mesh; skeleton + weights + gallop are generated here.
Units are metres, Blender axes: +Y forward, +Z up. Warhorse ~1.62 m at the withers.
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = argv[0] if argv else os.path.join(os.path.dirname(__file__), "..", "..", "assets")
PREVIEW_DIR = argv[1] if len(argv) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- body shape
VIS = 0.575  # visible radius / field radius for stiffness 2, threshold 0.6


def metaball(name, resolution=0.022):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = mb.render_resolution = resolution
    mb.threshold = 0.6
    ob = bpy.data.objects.new(name, mb)
    scene.collection.objects.link(ob)
    return ob, mb


def ellipsoid(mb, c, half):
    e = mb.elements.new(type="ELLIPSOID")
    e.co = c; e.radius = 1 / VIS; e.stiffness = 2
    e.size_x, e.size_y, e.size_z = half
    return e


def ball(mb, c, r):
    e = mb.elements.new(type="BALL")
    e.co = c; e.radius = r / VIS; e.stiffness = 2
    return e


def capsule(mb, a, b, r):
    a, b = Vector(a), Vector(b)
    e = mb.elements.new(type="CAPSULE")
    e.co = (a + b) / 2; e.radius = r / VIS; e.stiffness = 2
    e.size_x = (b - a).length / 2
    e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())
    return e


def taper(mb, a, b, r0, r1, n=4):
    """Chain of short capsules from radius r0 to r1 (metaball capsules can't taper on their own)."""
    a, b = Vector(a), Vector(b)
    for i in range(n):
        p, q = a.lerp(b, i / n), a.lerp(b, (i + 1) / n)
        capsule(mb, p, q, r0 + (r1 - r0) * (i + 0.5) / n)


body_ob, B = metaball("HorseBody")
# Trunk: barrel, chest/shoulders, hindquarters, withers, belly line
ellipsoid(B, (0, -0.05, 1.24), (0.3, 0.56, 0.33))
ellipsoid(B, (0, 0.42, 1.22), (0.29, 0.28, 0.35))
ellipsoid(B, (0, -0.55, 1.29), (0.31, 0.32, 0.31))
ellipsoid(B, (0, -0.05, 1.04), (0.22, 0.42, 0.14))          # belly underline
capsule(B, (0, 0.25, 1.47), (0, 0.55, 1.5), 0.12)          # withers
for s in (-1, 1):
    ellipsoid(B, (s * 0.1, -0.62, 1.35), (0.17, 0.24, 0.24))  # croup muscles
    ellipsoid(B, (s * 0.12, 0.47, 1.15), (0.14, 0.2, 0.24))   # shoulder muscles
    capsule(B, (s * 0.15, 0.52, 1.0), (s * 0.13, 0.3, 1.42), 0.07)  # shoulder blade, sloping back
    ellipsoid(B, (s * 0.1, 0.62, 1.1), (0.12, 0.1, 0.14))     # pectorals
    ellipsoid(B, (s * 0.16, 0.36, 1.02), (0.09, 0.11, 0.11))  # triceps
    ellipsoid(B, (s * 0.12, -0.1, 1.2), (0.17, 0.4, 0.27))    # ribcage
    ellipsoid(B, (s * 0.15, -0.45, 1.05), (0.12, 0.17, 0.2))  # stifle / thigh
    ellipsoid(B, (s * 0.11, -0.72, 1.12), (0.1, 0.12, 0.2))   # hamstring
    ellipsoid(B, (s * 0.17, -0.42, 0.8), (0.07, 0.09, 0.12))  # gaskin
    ellipsoid(B, (s * 0.16, 0.41, 0.82), (0.07, 0.08, 0.13))  # forearm
taper(B, (0, -0.8, 1.47), (0, -0.95, 1.28), 0.06, 0.045, 3)  # tail dock
# Neck: thick, arched, tapering to the poll
taper(B, (0, 0.55, 1.33), (0, 0.84, 1.8), 0.25, 0.18)
taper(B, (0, 0.84, 1.8), (0, 0.98, 2.0), 0.16, 0.12, 2)
capsule(B, (0, 0.6, 1.6), (0, 0.9, 1.95), 0.095)              # crest of the neck
# Head: wedge-shaped face, broad flat forehead, big round cheeks (masseter), flared nostrils, lips, pointed ears
taper(B, (0, 1.0, 2.02), (0, 1.36, 1.62), 0.095, 0.058, 6)       # nasal bone narrowing to the muzzle
ellipsoid(B, (0, 1.08, 2.0), (0.105, 0.09, 0.05))               # forehead
ellipsoid(B, (0, 1.38, 1.6), (0.07, 0.07, 0.065))               # muzzle
ellipsoid(B, (0, 1.4, 1.56), (0.055, 0.05, 0.035))              # upper lip
ellipsoid(B, (0, 1.34, 1.53), (0.045, 0.05, 0.035))             # chin
for s in (-1, 1):
    ellipsoid(B, (s * 0.065, 1.05, 1.87), (0.06, 0.12, 0.12))   # round cheek plate
    capsule(B, (s * 0.05, 1.0, 1.8), (s * 0.035, 1.3, 1.6), 0.04)  # lower jaw edge
    ball(B, (s * 0.045, 1.415, 1.625), 0.028)                   # flared nostrils
    taper(B, (s * 0.055, 0.99, 2.07), (s * 0.075, 0.95, 2.25), 0.03, 0.008, 4)  # pointed ears
    ball(B, (s * 0.075, 1.05, 1.995), 0.028)                    # brow ridge over the eye
    ball(B, (s * 0.095, 1.0, 2.04), 0.022).use_negative = True  # hollow above the eye
ball(B, (0, 0.97, 1.79), 0.045).use_negative = True             # throatlatch hollow between jaw and neck


def leg(mb, x, pts, radii):
    for (a, b), (r0, r1) in zip(zip(pts, pts[1:]), radii):
        taper(mb, (x, *a), (x, *b), r0, r1, 6)
    for p, r in zip(pts[1:-1], [rr[1] * 1.04 for rr in radii[:-1]]):
        ball(mb, (x, *p), r)  # joints slightly knobbly


FRONT = [(0.45, 1.18), (0.4, 0.95), (0.42, 0.5), (0.43, 0.19), (0.47, 0.035)]
HIND = [(-0.5, 1.22), (-0.32, 0.92), (-0.6, 0.56), (-0.57, 0.19), (-0.55, 0.035)]
for s in (-1, 1):
    leg(B, s * 0.16, FRONT, [(0.13, 0.095), (0.083, 0.053), (0.047, 0.045), (0.047, 0.05)])
    leg(B, s * 0.17, HIND, [(0.165, 0.105), (0.088, 0.059), (0.05, 0.045), (0.047, 0.05)])


def to_mesh(ob, name, target_faces):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.name = name
    new = bpy.data.objects.new(name, me)
    scene.collection.objects.link(new)
    bpy.data.objects.remove(ob)
    # smooth + decimate to a game budget
    for m, kw in (("SMOOTH", dict(factor=0.6, iterations=6)), ("DECIMATE", None)):
        mod = new.modifiers.new(m.lower(), m)
        if kw:
            for k, v in kw.items(): setattr(mod, k, v)
        else:
            mod.ratio = min(1.0, target_faces / max(1, len(me.polygons)))
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(new.evaluated_get(dg))
    new.modifiers.clear(); old = new.data; new.data = me2; bpy.data.meshes.remove(old)
    me2.name = name
    for p in me2.polygons: p.use_smooth = True
    return new


body = to_mesh(body_ob, "HorseBody", 18000)


def unwrap(ob):
    """UVs so the game can lay a fine hair-grain texture over the coat."""
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")


unwrap(body)


def material(name, colour, rough, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m


body.data.materials.append(material("HorseCoat", (0.05, 0.03, 0.02), 0.55))

# ---------------------------------------------------------------- skeleton
arm_data = bpy.data.armatures.new("HorseRig")
rig = bpy.data.objects.new("HorseRig", arm_data)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones
X = Vector((1, 0, 0))


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name); b.head = head; b.tail = tail
    b.align_roll(X.cross((Vector(tail) - Vector(head)).normalized()))  # local X = world X → pitch about X
    if parent: b.parent = eb[parent]; b.use_connect = (Vector(head) - eb[parent].tail).length < 1e-4
    b.use_deform = deform
    return b


bone("root", (0, 0, 0), (0, 0.3, 0), deform=False)
bone("hips", (0, -0.55, 1.3), (0, -0.1, 1.3), "root")
bone("back", (0, -0.1, 1.3), (0, 0.3, 1.33), "hips")
bone("chest", (0, 0.3, 1.33), (0, 0.6, 1.4), "back")
bone("neck1", (0, 0.6, 1.4), (0, 0.84, 1.8), "chest")
bone("neck2", (0, 0.84, 1.8), (0, 1.0, 2.02), "neck1")
bone("head", (0, 1.0, 2.02), (0, 1.38, 1.6), "neck2")
bone("tail1", (0, -0.8, 1.48), (0, -0.98, 1.22), "hips")
bone("tail2", (0, -0.98, 1.22), (0, -1.04, 0.62), "tail1")
LEGS = {}
for side, s in (("L", 1), ("R", -1)):
    for kind, pts, x, parent in (("f", FRONT, 0.16, "chest"), ("h", HIND, 0.17, "hips")):
        names = [f"{kind}{i}.{side}" for i in range(4)]
        prev = parent
        for i, n in enumerate(names):
            bone(n, (s * x, *pts[i]), (s * x, *pts[i + 1]), prev); prev = n
        LEGS[kind + side] = names
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------------------------------------------------------- weights (distance to bone segments)
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


deform = [b for b in arm_data.bones if b.use_deform]
segs = [(b.name, b.head_local.copy(), b.tail_local.copy()) for b in deform]


def skin(ob):
    """Blender's bone-heat automatic weights; falls back to distance weights if heat fails."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    if any(len(v.groups) for v in ob.data.vertices[:200]):
        return
    print("WARN heat weights failed on", ob.name, "- using distance weights")
    groups = {n: ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n) for n, _, _ in segs}
    for v in ob.data.vertices:
        p = v.co
        cand = [(seg_dist(p, a, b), n) for n, a, b in segs
                if not (n[0] in "fh" and n[1] == "0" and p.z > a.z - 0.2)]
        d = sorted(cand)[:3]
        d = [x for x in d if x[0] < d[0][0] * 2.2 + 0.02]
        w = [(1 / (dist + 0.015) ** 4, n) for dist, n in d]
        tot = sum(x for x, _ in w)
        for x, n in w: groups[n].add([v.index], x / tot, "REPLACE")


skin(body)

# ---------------------------------------------------------------- hair strands, eyes, hooves, star
import random
random.seed(7)


def mesh_from_curve(name, paths, r0):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = r0; cu.bevel_resolution = 0; cu.resolution_u = 3; cu.fill_mode = "FULL"
    for pts in paths:
        sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*p, 1); sp.points[i].radius = 1 - 0.6 * i / (len(pts) - 1)
        sp.use_endpoint_u = True; sp.order_u = 3
    tmp = bpy.data.objects.new(name + "Curve", cu); scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    return ob


def skin_to(ob, names):
    """Distance weights restricted to the given bones (hair and small parts follow the right bones)."""
    chosen = [(n, a, b) for n, a, b in segs if n in names]
    groups = {n: ob.vertex_groups.new(name=n) for n, _, _ in chosen}
    for v in ob.data.vertices:
        d = sorted((seg_dist(v.co, a, b), n) for n, a, b in chosen)[:2]
        w = [(1 / (dist + 0.02) ** 4, n) for dist, n in d]
        tot = sum(x for x, _ in w)
        for x, n in w: groups[n].add([v.index], x / tot, "REPLACE")
    ob.parent = rig
    mod = ob.modifiers.new("Armature", "ARMATURE"); mod.object = rig


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    return o


def surface(origin, direction):
    ok, loc, nrm, _ = body.ray_cast(Vector(origin), Vector(direction).normalized())
    assert ok, ("no surface hit", origin, direction)
    return loc, nrm


def side_x(y, z, sd):
    """Skin x on side sd (+1/-1) at height z and length y; steps down if the ray passes over the crest."""
    for k in range(8):
        ok, loc, _, _ = body.ray_cast(Vector((sd * 1.0, y, z - 0.025 * k)), Vector((-sd, 0, 0)))
        if ok:
            return loc.x
    return sd * 0.1


jit = lambda a: (random.random() - 0.5) * 2 * a
V = lambda *c: Vector(c)
hair_parts = []
# Mane: long, falling mostly to the right side of the neck (like a Friesian's)
paths = []
for i in range(64):
    t = i / 63
    y = 0.56 + 0.41 * t + jit(0.006)
    c = surface((0, y, 3), (0, 0, -1))[0] + V(0, 0, 0.005)
    sd = 1 if random.random() > 0.18 else -1
    L = 0.3 + 0.16 * random.random() * (1 - 0.5 * t)
    pts = [c, c + V(sd * 0.04, -0.02, 0.02)]
    for dz, dy in ((-0.05, -0.04), (-0.17, -0.07), (-L, -0.1 + jit(0.03))):
        z = c.z + dz
        pts.append(V(side_x(y + dy, z, sd) + sd * (0.022 + jit(0.008)), y + dy, z))
    paths.append(pts)
ob = mesh_from_curve("HorseMane", paths, 0.028); skin_to(ob, {"neck1", "neck2", "head", "chest"}); hair_parts.append(ob)
# Forelock over the forehead
paths = [[V(jit(0.02), 0.98, 2.1), V(jit(0.02), 1.04, 2.11), V(jit(0.025), 1.1, 2.03), V(jit(0.03), 1.13, 1.93)] for _ in range(8)]
ob = mesh_from_curve("HorseForelock", paths, 0.022); skin_to(ob, {"head"}); hair_parts.append(ob)
# Tail: full and long, falling to the hocks
paths = []
for i in range(64):
    j, r0 = jit(0.05), V(jit(0.02), -0.86 - 0.08 * random.random(), 1.45 - 0.12 * random.random())
    paths.append([r0, V(j * 0.5, -0.99, 1.3), V(j, -1.06 + jit(0.02), 1.0), V(j * 1.6, -1.14 + jit(0.03), 0.76),
                  V(j * 2.2, -1.18 + jit(0.06), 0.5 + 0.12 * random.random())])
ob = mesh_from_curve("HorseTail", paths, 0.034); skin_to(ob, {"tail1", "tail2"}); hair_parts.append(ob)
# Feathering: long hair over the fetlocks and hooves
for key, (y, x) in {"fL": (0.43, 0.16), "fR": (0.43, -0.16), "hL": (-0.57, 0.17), "hR": (-0.57, -0.17)}.items():
    paths = []
    for k in range(11):
        a = math.radians(70 + 220 * k / 10)  # round the sides and back of the leg
        out = V(math.sin(a) * (1 if x > 0 else -1), -math.cos(a), 0)
        root = V(x, y, 0.22) + out * 0.04
        paths.append([root, root + out * 0.03 + V(0, 0, -0.08), root + out * (0.05 + jit(0.01)) + V(0, -0.01, -0.19 + jit(0.01))])
    ob = mesh_from_curve("HorseFeather" + key, paths, 0.018); skin_to(ob, set(LEGS[key][2:])); hair_parts.append(ob)
hair = join(hair_parts, "HorseHair")
hair.data.materials.append(material("HorseHair", (0.015, 0.012, 0.01), 0.7))

# Eyes: dark and glossy, set into the head
eye_parts = []
for sx in (1, -1):
    hit, n = surface((sx * 1.0, 1.06, 1.97), (-sx, 0, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.026, location=hit - n * 0.012)
    eye_parts.append(bpy.context.active_object)
eyes = join(eye_parts, "HorseEyes")
eyes.data.materials.append(material("HorseEye", (0.01, 0.006, 0.004), 0.05))
for p in eyes.data.polygons: p.use_smooth = True
skin_to(eyes, {"head"})

# Hooves: horn-coloured, sloped walls
hoof_parts = []
for key, (y, x) in {"fL": (0.475, 0.16), "fR": (0.475, -0.16), "hL": (-0.545, 0.17), "hR": (-0.545, -0.17)}.items():
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.068, radius2=0.048, depth=0.085, location=(x, y, 0.0425))
    h = bpy.context.active_object; h.rotation_euler = (math.radians(-12), 0, 0); h.scale = (0.95, 1.1, 1)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    skin_to(h, {LEGS[key][3]}); hoof_parts.append(h)
hooves = join(hoof_parts, "HorseHooves")
hooves.data.materials.append(material("HorseHoof", (0.06, 0.055, 0.05), 0.45))
for p in hooves.data.polygons: p.use_smooth = True

# White star on the forehead (as on the black horses in the references)
hit, n = surface((0, 1.6, 2.45), (0, -0.62, -0.72))   # straight at the forehead
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=hit + n * 0.002)
star = bpy.context.active_object; star.name = "HorseStar"
star.scale = (0.034, 0.008, 0.05); star.rotation_euler = (math.atan2(n.z, n.y), 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
star.data.materials.append(material("HorseStar", (0.9, 0.88, 0.85), 0.6))
for p in star.data.polygons: p.use_smooth = True
skin_to(star, {"head"})

# ---------------------------------------------------------------- tack: bridle, reins, breastplate (peytral), chanfron
TACK_LEATHER = material("HorseTack", (0.06, 0.035, 0.02), 0.5)
TACK_METAL = material("HorseTackMetal", (0.86, 0.86, 0.9), 0.25, 1.0)
POLL, MUZZLE = Vector((0, 1.0, 2.02)), Vector((0, 1.36, 1.62))
HAX = (MUZZLE - POLL).normalized()
HU, HW = Vector((1, 0, 0)), HAX.cross(Vector((1, 0, 0)))  # HW points under the jaw; -HW over the face


def on_head(t, a, off=0.007):
    """Point on the head skin at fraction t from poll to muzzle, angle a round the head (0 = left side, 3pi/2 = face)."""
    c = POLL.lerp(MUZZLE, t); d = HU * math.cos(a) + HW * math.sin(a)
    ok, loc, n, _ = body.ray_cast(c + d * 0.6, -d)
    return (loc + n * off, n) if ok else (c + d * 0.1, d)


def tube(name, paths, radius, cyclic=False, mat=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = radius; cu.bevel_resolution = 0; cu.resolution_u = 2; cu.fill_mode = "FULL"
    for pts in paths:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for i, q in enumerate(pts): sp.points[i].co = (*q, 1)
        sp.use_cyclic_u = cyclic
    tmp = bpy.data.objects.new(name + "Curve", cu); scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    for f in me.polygons: f.use_smooth = True
    if mat: me.materials.append(mat)
    return ob


ring = lambda t, a0=0.0, a1=2 * math.pi, n=32: [on_head(t, a0 + (a1 - a0) * i / n)[0] for i in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-6 else 1))]
straps = []
straps.append(tube("Noseband", [ring(0.6)], 0.011, cyclic=True))
straps.append(tube("Crown", [ring(-0.04)], 0.011, cyclic=True))            # crownpiece + throatlatch behind the ears
straps.append(tube("Browband", [ring(0.07, math.pi, 2 * math.pi, 16)], 0.01))
for a in (0.0, math.pi):                                                     # cheekpieces down each side
    straps.append(tube("Cheek", [[on_head(-0.04 + 0.66 * i / 10, a)[0] for i in range(11)]], 0.011))
bridle = join(straps, "HorseBridle"); bridle.data.materials.append(TACK_LEATHER)
skin_to(bridle, {"head", "neck2"})

# Bit rings at the corners of the mouth, reins sagging back to the rider's left hand
bits, rein_paths = [], []
HAND = Vector((-0.22, 0.3, 2.12))
for a in (0.0, math.pi):
    q, n = on_head(0.84, a, 0.012)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.0055, location=q,
                                     rotation=Vector((0, 0, 1)).rotation_difference(n).to_euler())
    bits.append(bpy.context.active_object)
    rein_paths.append([q + (q - HAND) * 0.0 + n * 0.01] + [q.lerp(HAND, k / 6) + Vector((0, 0, -0.14 * math.sin(math.pi * k / 6))) for k in range(1, 7)])
bitm = join(bits, "HorseBit"); bitm.data.materials.append(TACK_METAL); skin_to(bitm, {"head"})
reins = tube("HorseReins", rein_paths, 0.008, mat=TACK_LEATHER); skin_to(reins, {"head", "neck2", "neck1", "chest"})

# Peytral: a strap round the front of the chest studded with silver discs
PC = Vector((0, 0.3, 1.24))
def on_chest(a, off=0.008):
    d = Vector((math.sin(a), math.cos(a), 0))
    ok, loc, n, _ = body.ray_cast(PC + d * 1.2, -d)
    return (loc + n * off, n)
peytral = tube("HorsePeytral", [[on_chest(math.radians(-85 + 170 * i / 24))[0] for i in range(25)]], 0.017)
discs = []
for deg in range(-60, 61, 20):
    q, n = on_chest(math.radians(deg), 0.02)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.042, depth=0.01, location=q,
                                        rotation=Vector((0, 0, 1)).rotation_difference(n).to_euler())
    discs.append(bpy.context.active_object)
discm = join(discs, "HorsePeytralDiscs"); discm.data.materials.append(TACK_METAL)
for f in discm.data.polygons: f.use_smooth = False
peytral.data.materials.append(TACK_LEATHER)
skin_to(peytral, {"chest", "neck1"}); skin_to(discm, {"chest", "neck1"})

# Chanfron: cloth face cover over the forehead and nose (eyes left free), coloured per team in the game
rows, cols = 12, 14
verts, faces = [], []
for i in range(rows):
    for j in range(cols):
        a = math.pi + 0.5 + (math.pi - 1.0) * j / (cols - 1)
        verts.append(on_head(-0.02 + 0.74 * i / (rows - 1), a, 0.013)[0])
for i in range(rows - 1):
    for j in range(cols - 1):
        faces.append((i * cols + j, i * cols + j + 1, (i + 1) * cols + j + 1, (i + 1) * cols + j))
me = bpy.data.meshes.new("HorseChanfron"); me.from_pydata(verts, [], faces); me.update()
chanfron = bpy.data.objects.new("HorseChanfron", me); scene.collection.objects.link(chanfron)
for f in me.polygons: f.use_smooth = True
sol = chanfron.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.006
dg = bpy.context.evaluated_depsgraph_get()
me2 = bpy.data.meshes.new_from_object(chanfron.evaluated_get(dg)); chanfron.modifiers.clear(); chanfron.data = me2
me2.materials.append(material("HorseChanfron", (0.6, 0.08, 0.06), 0.85))
unwrap(chanfron)
skin_to(chanfron, {"head"})
TACK_PARTS = [bridle, bitm, reins, peytral, discm, chanfron]
EXTRAS = [hair, eyes, hooves, star, *TACK_PARTS]

# ---------------------------------------------------------------- gallop cycle (transverse gallop, right lead)
FPS, N = 30, 20  # 0.67 s per stride at speedRatio 1
scene.render.fps = FPS; scene.frame_start = 0; scene.frame_end = N
OFFSETS = {"hL": 0.0, "hR": 0.12, "fL": 0.42, "fR": 0.54}
STANCE = 0.36
action = bpy.data.actions.new("Gallop")
rig.animation_data_create(); rig.animation_data.action = action
pb = rig.pose.bones
for p in pb: p.rotation_mode = "XYZ"


def leg_pose(t, offset, front):
    p = (t - offset) % 1.0
    if p < STANCE:   # hoof on the ground: leg sweeps backward, straight
        swing = 1 - 2 * (p / STANCE); flex = 0.0
    else:            # in the air: leg folds and reaches forward
        q = (p - STANCE) / (1 - STANCE)
        swing = -math.cos(math.pi * q); flex = math.sin(math.pi * q)
    if front:  # shoulder swing, knee (carpus) folds back, fetlock/pastern fold
        return [0.32 * swing + 0.05, 0.3 * swing - 1.4 * flex * (0.4 + 0.6 * max(0, -swing + 0.6)), 0.25 * flex, 0.9 * flex - 0.25 * (1 - flex) * (p < STANCE)]
    return [0.36 * swing, 0.2 * swing + 0.45 * flex, -1.1 * flex, 0.8 * flex - 0.25 * (1 - flex) * (p < STANCE)]


for f in range(N + 1):
    t = (f % N) / N
    w = 2 * math.pi * t
    pb["root"].location = (0, 0, 0.06 * math.sin(w - 1.2)); pb["root"].keyframe_insert("location", frame=f)
    rot = {
        "hips": 0.07 * math.sin(w + 0.4), "back": -0.03 * math.sin(w + 0.4), "chest": -0.05 * math.sin(w + 0.4),
        "neck1": 0.14 * math.sin(w + 1.6) - 0.05, "neck2": 0.06 * math.sin(w + 1.9), "head": -0.12 * math.sin(w + 1.6),
        "tail1": 0.25 + 0.12 * math.sin(w), "tail2": 0.1 * math.sin(w + 0.8),
    }
    for key, names in LEGS.items():
        for n, a in zip(names, leg_pose(t, OFFSETS[key], key[0] == "f")): rot[n] = a
    for n, a in rot.items():
        pb[n].rotation_euler = (a, 0, 0); pb[n].keyframe_insert("rotation_euler", frame=f)

for fc in action.fcurves if hasattr(action, "fcurves") else []:
    for k in fc.keyframe_points: k.interpolation = "LINEAR"

# ---------------------------------------------------------------- export
bpy.ops.object.select_all(action="DESELECT")
for ob in (rig, body, *EXTRAS): ob.select_set(True)
glb = os.path.join(OUT_DIR, "horse.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_animations=True,
                          export_apply=True, export_yup=True)
print("EXPORTED", glb, "faces", sum(len(o.data.polygons) for o in (body, *EXTRAS)))

# ---------------------------------------------------------------- preview renders (side view, 4 phases)
if PREVIEW_DIR:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
    cam.location = (4.3, 0.1, 1.0); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    cam.data.lens = 40; scene.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), 0, math.radians(60)); sun.data.energy = 4
    scene.world = bpy.data.worlds.new("w"); scene.world.color = (0.6, 0.65, 0.7)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x, scene.render.resolution_y = 640, 480
    bpy.ops.mesh.primitive_plane_add(size=6)
    for f in range(0, N, 4):
        scene.frame_set(f)
        scene.render.filepath = os.path.join(PREVIEW_DIR, f"horse_{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    print("PREVIEWS", PREVIEW_DIR)

if PREVIEW_DIR:
    cam.location = (1.6, 1.9, 2.2)
    cam.rotation_euler = (Vector((0, 1.05, 1.85)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.frame_set(8); scene.render.filepath = os.path.join(PREVIEW_DIR, "horse_head.png")
    bpy.ops.render.render(write_still=True)
    cam.location = (-3.0, -3.6, 1.8)
    cam.rotation_euler = (Vector((0, -0.2, 1.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(PREVIEW_DIR, "horse_rear.png")
    bpy.ops.render.render(write_still=True)
