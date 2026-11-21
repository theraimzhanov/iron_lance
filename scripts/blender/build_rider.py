"""Pose the Sketchfab "Armored Guard Knight Rig" (DM-913, CC BY 4.0) as a mounted jouster and export assets/rider.glb.

Run:  blender -b -P scripts/blender/build_rider.py -- <knight scene.gltf> <out.glb> [preview_dir]
Output matches the game's knight contract: origin at the seat, facing +Y (Blender), right arm couched under the
lance grip at about (0.30, 0.10, 0.45), left forearm forward to the shield. Spear and helper sphere removed,
pose baked into a static mesh, war saddle added.
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[:2]
preview = argv[2] if len(argv) > 2 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):  # the spear (Object_88: tall and thin) and the IK helper sphere
    if o.type == "MESH" and (o.name == "Icosphere" or o.name == "Object_88"):
        bpy.data.objects.remove(o)
if rig.animation_data: rig.animation_data.action = None
# Armour paint is bronze; turn it into steel by keeping only its brightness (scratches, straps stay dark)
import numpy as np
for img in bpy.data.images:
    if "Guard_Material_baseColor" in img.name and img.size[0]:
        px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
        lum = px[:, :3] @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
        px[:, :3] = np.clip(lum[:, None] * np.array([1.15, 1.18, 1.25], dtype=np.float32), 0, 1)
        img.pixels[:] = px.ravel()
        img.pack()
pb = {b.name.rsplit("_", 1)[0]: b for b in rig.pose.bones}   # "Thigh.L_60" -> "Thigh.L"
for b in rig.pose.bones:
    for c in list(b.constraints): b.constraints.remove(c)      # drop IK so pose rotations apply directly
    b.rotation_mode = "QUATERNION"
bpy.context.view_layer.update()

# Which way does the model face? right = left shoulder -> right shoulder; forward = up x right
right = rig.matrix_world @ pb["Shoulder.R"].head - rig.matrix_world @ pb["Shoulder.L"].head
right.z = 0; right.normalize()
fwd = Vector((0, 0, 1)).cross(right)


def aim(name, direction):
    """Rotate a pose bone so it points along a world direction (expressed as fwd/right/up mix)."""
    b = pb[name]
    bpy.context.view_layer.update()
    cur = (rig.matrix_world.to_3x3() @ (b.tail - b.head)).normalized()
    want = Vector(direction).normalized()
    q = cur.rotation_difference(want)
    world = rig.matrix_world @ b.matrix
    loc = world.to_translation()
    new = Matrix.Translation(loc) @ q.to_matrix().to_4x4() @ Matrix.Translation(-loc) @ world
    b.matrix = rig.matrix_world.inverted() @ new
    bpy.context.view_layer.update()


D = lambda f=0.0, r=0.0, u=0.0: fwd * f + right * r + Vector((0, 0, u))
for s, R in (("L", -1), ("R", 1)):          # astride: thighs down the horse's sides, knees bent, feet in stirrups
    aim("Thigh." + s, D(0.5, 0.55 * R, -0.65))
    aim("LowerLeg." + s, D(-0.1, 0.12 * R, -1))
    aim("Foot." + s, D(1, 0.1 * R, -0.25))
aim("Upperarm.R", D(-0.25, 0.55, -1))      # lance arm couched against the side
aim("Forearm.R", D(1, 0.35, -0.05))
aim("Hand.R", D(1, 0.15, 0))
aim("Upperarm.L", D(0.2, -0.45, -1))       # shield arm: elbow out to the left side
aim("Forearm.L", D(0.5, -0.9, 0.3))
aim("Hand.L", D(1, -0.2, 0.2))

PELVIS = rig.matrix_world @ pb["Pelvis"].head
HAND_R = rig.matrix_world @ pb["Hand.R"].tail
HAND_L = rig.matrix_world @ pb["Hand.L"].tail
HELM = rig.matrix_world @ pb["Head"].tail   # top of the helmet, where the crest goes
# Bake the pose into static meshes, drop the rig
dg = bpy.context.evaluated_depsgraph_get()
meshes = []
for o in [o for o in sc.objects if o.type == "MESH"]:   # posed, world-space copies; then drop the originals
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    n = bpy.data.objects.new(o.name + "Posed", me); sc.collection.objects.link(n); meshes.append(n)
for o in list(sc.objects):
    if o not in meshes: bpy.data.objects.remove(o)

# Move so the seat (just below the pelvis) is the origin and the knight faces +Y
bpy.ops.object.select_all(action="DESELECT")
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
knight = bpy.context.active_object; knight.name = "Rider"
turn = math.atan2(fwd.x, fwd.y)           # rotate fwd onto +Y
knight.rotation_euler = (0, 0, turn)
bpy.ops.object.transform_apply(rotation=True)
seat = Matrix.Rotation(turn, 3, "Z") @ PELVIS + Vector((0, 0, -0.1))   # seat sits just under the pelvis joint
for v in knight.data.vertices: v.co -= seat
print("HAND_R", tuple(round(c, 3) for c in Matrix.Rotation(turn, 3, "Z") @ HAND_R - seat))   # game lance grip should sit here
print("HAND_L", tuple(round(c, 3) for c in Matrix.Rotation(turn, 3, "Z") @ HAND_L - seat))   # shield sits here
knight.data.update()

# War saddle with high cantle and pommel
def box(name, loc, size, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.scale = size; o.name = name
    m = o.modifiers.new("bev", "BEVEL"); m.width = min(size) * 0.3; m.segments = 2
    return o
leather = bpy.data.materials.new("Leather"); leather.use_nodes = True
leather.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.26, 0.14, 0.07, 1)
parts = [box("saddle", (0, -0.02, -0.06), (0.38, 0.62, 0.08)), box("cantle", (0, -0.3, 0.1), (0.42, 0.07, 0.32), (math.radians(-12), 0, 0)),
         box("pommel", (0, 0.26, 0.03), (0.3, 0.07, 0.18), (math.radians(15), 0, 0))]
for p in parts: p.data.materials.append(leather)
bpy.ops.object.select_all(action="DESELECT")
for p in parts + [knight]: p.select_set(True)
bpy.context.view_layer.objects.active = knight
bpy.ops.object.convert(target="MESH"); bpy.ops.object.join()
# Marker nodes at the fists: the game reads these for the lance grip and shield, so no axis guessing there
for name, p in (("GripR", HAND_R), ("GripL", HAND_L), ("Crest", HELM)):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.location = Matrix.Rotation(turn, 3, "Z") @ p - seat; e.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG")
print("EXPORTED", out, "tris", sum(len(p.vertices) - 2 for p in knight.data.polygons), "fwd", tuple(round(c, 2) for c in fwd))

if preview:
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_x, sc.render.resolution_y = 480, 600
    for name, loc in (("side", (2.8, 0.2, 0.5)), ("front", (1.2, 2.4, 0.6))):
        cam.location = loc; cam.rotation_euler = (Vector((0, 0, 0.35)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(preview, f"rider_{name}.png"); bpy.ops.render.render(write_still=True)
