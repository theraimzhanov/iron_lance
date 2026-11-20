"""Download CC0 photoscanned props from Poly Haven (glTF + textures) into a staging folder.

Run:  python scripts/fetch_props.py <staging_dir> [resolution]
Then pack them into GLBs with:  blender -b -P scripts/blender/pack_props.py -- <staging_dir> assets/props
"""
import json, os, sys, urllib.request

PROPS = ["wooden_barrels_01", "wine_barrel_01", "wooden_crate_01", "wooden_crate_02", "wooden_bucket_01",
         "wooden_ladder", "painted_wooden_bench",
         "shrub_03", "grass_medium_01", "tree_stump_01", "boulder_01", "wooden_lantern_01",
         "modular_fort_01"]
UA = {"User-Agent": "iron-lance-asset-fetch"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def main(stage, res="1k"):
    for pid in PROPS:
        files = json.loads(get(f"https://api.polyhaven.com/files/{pid}"))
        g = files["gltf"].get(res) or next(iter(files["gltf"].values()))
        g = g["gltf"]
        out = os.path.join(stage, pid)
        os.makedirs(out, exist_ok=True)
        main_path = os.path.join(out, os.path.basename(g["url"]))
        with open(main_path, "wb") as f: f.write(get(g["url"]))
        for rel, inc in g.get("include", {}).items():
            dst = os.path.normpath(os.path.join(out, rel))
            assert dst.startswith(os.path.normpath(out)), rel   # never write outside the staging folder
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f: f.write(get(inc["url"]))
        print("fetched", pid)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "1k")
