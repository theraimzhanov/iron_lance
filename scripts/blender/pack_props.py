"""Pack each staged Poly Haven glTF (+ textures) into one self-contained GLB, and report its size.

Run:  blender -b -P scripts/blender/pack_props.py -- <staging_dir> <out_dir>
"""
import bpy, os, sys, glob
from mathutils import Vector

stage, out = sys.argv[sys.argv.index("--") + 1:][:2]
os.makedirs(out, exist_ok=True)
MAX_TRIS = 8000
for d in sorted(glob.glob(os.path.join(stage, "*"))):
    src = glob.glob(os.path.join(d, "*.gltf"))
    if not src: continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src[0])
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    if tris > MAX_TRIS:  # photoscans are dense; keep each prop within a browser budget
        for o in meshes:
            m = o.modifiers.new("dec", "DECIMATE"); m.ratio = MAX_TRIS / tris
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes: o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.convert(target="MESH")
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    name = os.path.basename(d)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_image_format="JPEG")
    print(f"PACKED {name} size={tuple(round(v, 2) for v in hi - lo)} tris={tris}")
