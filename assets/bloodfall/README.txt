BLOODFALL ARENA

A dark medieval tournament environment based on the user's arena layout.
The scene includes two jousting lanes, stepped spectator stands, a ruined
royal box, portcullis gates, curtain walls, towers, a castle backdrop,
wet churned earth, standing water, blood pools and drag marks, discarded
weapons, shattered timber, braziers, and 16 fallen armored fighters.
The fighters are intact static bodies, with no dismemberment.

FILES
Bloodfall_Arena.glb - portable 3D scene with embedded material textures.
Bloodfall_Arena.blend - editable source, lighting, atmosphere and cameras.
Bloodfall_Hero.png - human-height view rendered after re-importing the GLB.
Bloodfall_Overview.png - elevated layout view.
Overcast_Sky.hdr - environment lighting map for your game engine.
asset_stats.json - measured final mesh counts and verification results.

SCALE AND STRUCTURE
Units: metres. The arena floor is 34 x 62 metres; the stands and castle
extend beyond it. Blender is Z-up; GLB uses standard glTF axis conversion.
The source separates architecture, terrain, props, fallen fighters,
practical lights and presentation effects into named collections.
The portable export groups static scenery into spatial sections.
Materials use 1K-2K texture maps, with base color, roughness and normals.
The verified GLB contains 32 embedded images, 27 materials, and 114 mesh
objects after spatial grouping (924,060 triangles including instances).
The GLB includes the point lights at the braziers and directional lighting.

IMPORT
Use your engine's glTF importer, or open the Blender file and export your
preferred engine format. Set the included HDRI as your environment light.
Match the Blender scene's atmosphere using your engine's fog settings.
For reference, the Blender world uses HDRI strength 0.14 with a blue tint
(0.40, 0.58, 0.90), volume density 0.003, and AgX exposure +0.25.
These are Blender values; translate them to your engine's lighting units.
GLB does not carry a light's soft-shadow radius. The final imported preview
restores 0.45 m source radius for torch point lights and 0.18 rad angular
size for the sun; set equivalent source sizes in your engine for soft shadows.
Blender's volume cube, cameras and world nodes are intentionally not in GLB.
Lighting, tone mapping and normal-map handling can differ between engines.
No engine was specified, so no engine-specific project is included.

VALIDATION AND LIMITS
This is a static environment asset, not a complete playable game level.
There is no player controller, navigation mesh, collision configuration,
ragdoll setup, animated fire, sound, LOD chain or baked lightmap UV set.
The bodies reuse simplified armored geometry; close-up character fidelity
is lower than the environment's scanned surface detail.
No target-engine integration or frame-rate test has been performed.
Refer to asset_stats.json for the completed export validation.
No paid generation credits were spent.

MATERIAL CREDITS
Scanned textures and environment lighting supplied by Poly Haven (CC0):
https://polyhaven.com/license
https://polyhaven.com/a/muddy_tracks
https://polyhaven.com/a/medieval_blocks_02
https://polyhaven.com/a/medieval_wood
https://polyhaven.com/a/rusty_metal_03
https://polyhaven.com/a/brown_leather
https://polyhaven.com/a/fabric_pattern_07
https://polyhaven.com/a/kloofendal_overcast_puresky
Detailed prop models, also CC0, supplied by Poly Haven:
https://polyhaven.com/a/wooden_barrels_01
https://polyhaven.com/a/wooden_crate_02
https://polyhaven.com/a/ornate_medieval_mace
The original architectural layout, assemblies, stains and scene dressing
were created for this request. The user's supplied image guided the layout.
