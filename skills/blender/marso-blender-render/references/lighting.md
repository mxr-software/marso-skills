# Realistic lighting and scene presentation

First identify the visible problem: wrong proportions/contact, weak material response, unsuitable camera, noisy sampling or lighting. Do not cure incorrect normals with grading or regenerate a good asset to fix light direction. Keep accepted Marso maps and their source relationships intact. Finish new required material appearances through the texture workflow; use library masters when they already meet the brief.

Lock a useful comparison view before changing lighting. Build from plausible sources: sky/window, practical fixtures, sun or a deliberate studio setup. Source size/distance controls highlight shape and shadow softness; strength alone cannot fix flat form. Keep the shadow side readable without filling away all contrast. Identify the subject's focal separation from the background; a bright opening can steal attention from it.

For a lighting-only change, save the baseline and note its mesh/material assignments and source images. Keep edits scoped to lights/world and requested output controls; compare those assignments and the affected shader inputs afterward. Investigate unexpected changes instead of rebuilding accepted assets. A complete geometry/pixel hash audit is not required for every light adjustment.

Inspect neutral/clay form only when geometry versus material is uncertain. For material presentation use real PBR under the intended light and a complementary changed-light view. Look for believable scale of roughness/detail, reflections, contact shadows, bevel highlights and undersides. Clean realism is not mandatory grime, haze or exaggerated surface noise. Textures cannot create missing silhouette or structural depth.

Start with a small number of named light roles and change the failing group. Keep world contribution appropriate to the setting; an excessively bright environment can wash out an interior. Diagnose light leaks and geometry thickness before multiplying fill lights. Renderer-specific indirect lighting, glass and shadow settings must be checked against the installed version.

For a sequence, preserve coherent direction, colour and exposure intent across coverage. Compare contact sheets and a moving segment; a good still does not establish temporal stability. Where repeated balance changes justify it, Cycles light groups let the compositor rebalance existing contributions without a full rerender. They cannot reproduce changing geometry or moving a light. Do not require extra passes for a simple review frame.

Use low-cost previews to resolve composition and light, then a final-quality crop/full frame appropriate to the deliverable. More samples reduce noise, not bad art direction. Compare the same camera and resolution when judging a change; preserve a clean baseline and report actual render time. Do not claim an objective photorealism score from brightness statistics.
