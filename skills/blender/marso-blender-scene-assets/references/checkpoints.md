# Review checkpoints

Retain approval of unchanged decisions. Consolidate plan, library and scene-budget review rather than asking the same questions twice. An explicit waiver permits the covered work; otherwise pause at the applicable checkpoints defined below until the user answers. Continue independent approved items. Record agent decisions as such, never as user approval.

## Plan and library selection

Show the verified Studio project, routes, unique assets and instance counts, resolved options and scene budget, exclusions/flags and useful library thumbnails. Review new choices only. A candidate score alone is not approval; an already selected asset or explicitly delegated reuse decision needs no repeated permission.

Record decisions with `manifest.py choose`. An asset with no useful candidate can be made within the approved plan. Revise plan/references as needed; reinitialise with `--force` only before any jobs exist. After submission, preserve the active record and plan revised work separately.

## Native batch route

Use image and mesh review gates by default; omit a gate only when explicitly waived. Review each ready item without waiting for every reference. Open its review artifact and compare it with its crop and brief. Approve through `batch_review`; reconcile local records as described in [batches](batches.md). A local manifest decision does not advance the batch.

Inspect image isolation/framing/proportions before mesh generation. Normally inspect geometry from useful views before advancing downstream PBR; an inadequate thumbnail is not a passed review. Some add-on builds expose only a small thumbnail at this gate and cannot import the raw mesh. If the user has delegated generated-asset review and has not required a pre-PBR geometry checkpoint, record that inspection as deferred, advance the existing item through its normal PBR stage, then inspect the imported geometry before accepting or placing it. Do not start another mesh run or record the thumbnail as a successful geometry review. If a pre-PBR checkpoint is explicitly required, hold the item and report the missing inspection capability. This exception never authorizes texturing newly modelled geometry. Rejecting a review stops that item. Held scene-generation items are different: reconcile the cause and use supported cancel or authorized retry; they cannot be review-rejected. Retexture reprepare does not apply to this pipeline.

## Individual-command fallback

Review completed reference images beside source crops with stable asset ids. Check wrong/merged subjects, cut-off parts, neighbours, pose, materials and proportions. Record with `manifest.py review <assets.json> --approve a001 a004 --reject a002 --note "..."`. Approved references can progress while others are revised. Preserve completed attempts when retrying.

The inspected legacy `scene_mesh` bundles mesh and PBR; it cannot pause between them. For generated assets on this fallback, the default is image approval, combined mesh/PBR, then inspection of the returned geometry. Disclose that sequence before submission; no extra generated-mesh waiver is required unless the user already required a pre-PBR geometry checkpoint. This exception does not apply to agent-modelled assets. If the user requires a pre-PBR mesh gate, use a verified staged/native route or report the capability gap. Do not promise a checkpoint the command cannot provide. Review returned geometry before placement; minted status is not visual approval.

## Modelled and reused assets

Newly modelled/substantially remodelled geometry needs a recorded visual form/construction check, then user approval before Retexture/PBR unless explicitly waived. A failed form check stays partial even when its UVs pass; repair it before final texture preparation, or report the remaining work without submitting it. Continue independent accepted assets and retain their approvals. Unchanged existing assets requested for retexture need no redundant model gate. Place complete assets and finish the requested scene; report unresolved or rejected ones.
