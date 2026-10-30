# Texture a set and review it

For a finished scene, texture visible furniture and props within the agreed scope, then provide lightweight review images. Final presentation renders are on request. A geometry-only or layout-only request does not authorize expanding the job to texturing. Newly modelled or substantially remodelled geometry still needs the user's approval before Retexture; review a coherent batch together rather than interrupting for each minor part.

## Preserve and resume

Keep a local run record with each unique asset's source revision, target/root, prepared checkpoint, UV layer, material bindings, brief, intended project id, job id, result ids, status and review outcome. Persist each transition and exact error before submitting another job. Save setup findings too; chat history is not a durable diagnostic record. Keep credentials out of logs.

Keep exact prompts and raw responses before parsing. A parser failure must not discard the evidence needed to reconcile a submission. Distinguish model/UV/export checks, image-reference acceptance and final PBR visual acceptance in the run record. Keep a conditional pilot separate from methods ready for bulk use; independent approved work may continue without propagating a known visual failure.

Prefer native batch orchestration when the loaded add-on exposes it. Older builds serialize the whole Retexture job and preparation; those need the individual-job fallback below. A source checkout does not establish installed capabilities. On resume, inspect saved batches/jobs first; a timeout or missing reply does not prove submission failed. Preserve failed attempts when retrying a diagnosed problem. Where the installed schema exposes `list_failures`, use it to recover individual-job failure details after a restart; batch stage histories are available through `batch_item`.

Verify the intended project before submission and retain its id. New batches capture the project explicitly, so later panel selection changes do not move their results. Older Retexture builds always export/upload; newer builds support `source: "auto"` for an unchanged recorded Studio source or `source: "upload"` for a fresh export. Record provenance and output ids separately. Verified newer revision guards include evaluated geometry, preparation transforms, UVs, shader constants, ramps/curves and image pixels. Materials with object-/scene-dependent or otherwise unverified inputs upload instead of reusing their cloud source. This is expected, not a reason to force reuse or remove material nodes. Preserve prepare warnings: some external inputs cannot be checked before apply, so keep pending targets, material graphs and their dependent scene inputs unchanged. Older builds may lack these guards.

## Native batch route

Discover `batch_submit`, `batch_status`, `batch_item`, `batch_control` and, if a review hold is requested, `batch_review`. Save the exact request with a new nonempty `request_id` before submission; reuse that id only for the identical uncertain submission, not changed work. Submit one item per approved unique texture target or style variant, with an explicit project id. The inspected limit is 1000 items per request; networking is bounded and Marso queues execution, so do not impose a four-job or single-cloud-job cap.

```json
{
  "request_id": "<new-stable-request-id>",
  "name": "Approved furniture finishes",
  "project_id": "<verified-project-id>",
  "items": [{
    "key": "table-oak-v01",
    "pipeline": "retexture",
    "object_name": "<explicit-texture-working-target>",
    "prompt": "<complete material brief>",
    "enhance": "",
    "reference_path": "",
    "auto_uv": false,
    "scope": "target",
    "source": "upload",
    "review": []
  }]
}
```

Prepare and approve geometry before submitting. Prefer the independent single-mesh authored-UV working target described in [preparation](preparation.md). `auto_uv: false` does not disable the batch's automatic multipart assembly preparation; an unprepared assembly can receive a new atlas. Inspect `assembly_state` and the exported UV route first. Make variant targets independent; the batch rejects simultaneous writers to the same claimed objects.

The chain is local prepare → cloud edit → cloud PBR → local apply. Local work is coordinated separately while independent cloud jobs remain outstanding. Do not additionally call `retexture`, PBR or preparation for batch-owned targets. The empty Retexture review list is the native default: geometry approval happens before submission and the final applied result still needs visual QA. If the user requires an edit/PBR review before advancement, configure supported review stages explicitly and inspect available evidence before approving. `review: []` is not a waiver for geometry approval on newly built assets.

Use `scope: "target"` by default. For an explicitly requested family-wide change, inspect the returned assembly/linked family and provide explicit member names where the schema supports them; do not assume a selection or matching names define the family. Builds with the corrected source-auto route retain a prepared export, retry transient source lookups and upload that export if the source stays unavailable. Verify this capability before relying on it; older batch builds lack that fallback. Use `source: "upload"` when the source or its equivalence is uncertain, as in the conservative example above. Preserve original/prepared baselines separately for variants.

Save a stable .blend before submitting and preserve recoverable checkpoints at safe boundaries. The add-on captures scene/file/target names and ownership tags: keep those identities and the target's geometry/materials stable mid-batch. Renaming or deleting the target holds its item; renaming an assembly part also counts as a change. Complete naming before submission. Newer revisions allow a harmless world translation, but that is not permission to alter parts or shader-dependent scene inputs. A target-change hold needs diagnosis: `retry` rechecks the original revision, so undo the change first. Where supported, explicit `reprepare` accepts the current target and reruns every stage, preserving attempt history; it still needs to locate the captured target, so restore a renamed target's identity first. Obtain geometry approval for substantial modelling changes before using it. To stop a held item, use `batch_control cancel` with its `item_ids`; `batch_review reject` only applies to `awaiting_review`. On older builds, reconcile the old item before submitting a separately approved replacement.

### Monitoring and recovery

- `batch_status {batch_id, since, limit, states}` gives compact progress. `batch_item {batch_id, item_id}` gives complete stages, warnings and outputs; the inspected implementation also accepts the submitted key as `item_id`. Save request keys and batch id locally. These ids are not `get_job` ids.
- `batch_wait {batch_id, since, timeout, until: "change"}` can return when state changes through an external bridge/connector. Use a host-compatible bounded timeout, normally at most 60 seconds. Never invoke blocking waits inside a Blender Python execution block: use short `batch_status` calls there. The add-on keeps scheduling while Blender runs; an agent need not poll to start the next item. No push notification that wakes a closed chat is verified.
- `settled` includes review/held states, not just success. Summary lists are capped. When `next_since` and `complete` are present, follow `since = next_since` until `complete`; do not jump to `version` while pages remain. Where exposed, `batch_items {batch_id, after, limit}` returns full records: follow `next_after` until `complete`. Use unfiltered results for the completion ledger; filtered views can change between calls. On older builds, reconcile omitted items through known-key `batch_item` calls. Counts and full outcomes must agree.
- `batch_review {batch_id, decisions: [{key, decision, note}]}` records the user's decision for the current waiting stage. `batch_control` supports pause/resume/cancel/retry, and newer builds add `reprepare`; retry/reprepare need explicit `item_ids`. Reprepare creates fresh runs for the changed target; it is not a status check. Pause stops new work but monitors existing cloud runs. Cancel cannot stop already-submitted cloud executions in the inspected API; it stops future advancement and retains their outcomes.
- Recover through `batch_list` and saved state before resubmitting. Keep held, failed and rejected results distinct. Use supported authorized routes: the remote Agent Connection allows monitoring and pause/cancel, but submission/review/resume/retry/reprepare may require the established Blender MCP route. Do not bypass a restricted connection.
- Newer builds hold uncertain non-PBR submissions after bounded execution-id rechecks. A missing id is not proof that nothing ran; inspect the saved node and service evidence before retrying. PBR resubmission may reuse its existing node execution under the verified API contract.
- `batches_restarting` means the previous engine is handing over its remaining work. Return control to Blender, wait briefly outside its main thread, then repeat the call. Existing batches resume automatically after handover. For a submission, keep the identical saved request and `request_id`; do not create a replacement batch or manually restart stages. If the condition persists, inspect saved state and diagnostics instead of looping rapidly or repeatedly reloading the add-on. Older builds without this handover fix should not be reloaded during active local work.

Inspect every applied result as below. Native status reports and persisted stage records are the completion ledger; `succeeded` is execution completion, not visual approval.

## Scheduling and time estimates

- Count unique texture targets and requested style variants, not placed instances. Reuse an accepted textured master for intended identical instances. Do not combine unrelated assets into one texture target just to reduce job count.
- Before a long batch, state the count, installed execution route and an approximate completion range when comparable measurements exist. Otherwise say the estimate is provisional and update it after the first few completions. Include preparation, queueing, application and review; keep possible rework separate. Do not switch creation routes or reduce quality merely because another route is faster.
- With native batches, observe aggregate progress and review holds; the scheduler owns cloud polling and advancement. For the legacy individual-job fallback, roughly 30–60 seconds between status checks is a starting cadence, not an API requirement; honour service backoff and host limits. Avoid tight polling and predicted whole-job sleeps. Return control between calls, record completion and advance when the add-on is ready.
- Write later briefs or inspect source photos while cloud work runs. Let native batches own their local preparation/application lane; on legacy builds finish the busy Retexture before the next preparation. Independent work must not mutate active targets/materials or obstruct the local work needed to finish them.
- Keep `submitted_at`, last observation, observed stage, job `started_at`/`finished_at` when returned, and `recorded_at` distinct. Add-on job time can include preparation and queueing; it is not pure model inference time. If no actual finish time exists, submission-to-recording is an upper bound, inflated by polling gaps. Never manufacture stage timings from a progress phrase or mix clocks without their timezone/source.
- Estimate legacy serial work from comparable job durations; estimate native batches from observed aggregate throughput and remaining stages, without assuming linear speedup. If only observed wall-clock intervals exist, label the estimate accordingly. Recalculate when queueing or hardware conditions change. Report completed, current stage, remaining, failures and items awaiting visual review at meaningful transitions and at the host's required progress cadence.

Unrestricted outstanding submissions do not imply unrestricted execution throughput. Marso queues cloud work; local Blender work retains its coordination requirements. A serial batch's duration divided by four is not evidence of a fourfold speedup.

Follow observed service rejections as well as installed schemas. If a response explicitly reports a capacity limit and confirms nothing started, retain that evidence and submit normally when accepted work clears. Do not turn one observed account/route limit into a universal fixed cap. If the outcome is uncertain, reconcile instead of treating an absent immediate execution id as a rejected submission.

## Review the applied result

- Inspect materials under neutral lighting at the intended viewing distance and close enough to see UV seams, stretches and protected small regions. Deliberate material colours help describe regions but do not provide an exact generation mask.
- Specify restrained wear with physical locations and scale. Rich detail does not mean uniform grime or damage across every face; do not ask texture to invent missing geometry.
- Check the [transparent-part handoff](preparation.md#transparent-parts) after map application. Marso supplies no transparency; restore excluded clear parts or apply a local transparent material/mask only to verified regions, keeping labels opaque. Do not change every instance or break prepared-state bindings.
- Recheck shared-material users before propagating a finished master to instances. Preserve alternatives and independent styles.
- Retain warnings and disclose remaining visible defects. Do not count an uninspected or failed material as complete.

Quality warnings identify checks to perform; they neither prove failure nor certify unflagged results:

| Returned warning | Targeted inspection |
| --- | --- |
| Visible seams | Inspect atlas boundaries and adjacent surfaces under neutral light, at delivery distance and close range. Check colour/roughness discontinuities and stretches; a room-wide image may hide them. |
| Some views could not be edited | Turn the asset around and inspect backs, undersides, recesses and all relevant exposed regions for unchanged, blank or inconsistent appearance. Do not assume which view failed unless the result identifies it. |

For every result, including one without warnings, verify intended part colours, wear strength, glass and protected features against the brief. Record the views actually checked and any inaccessible/unreviewed regions. Accept a warned result only when inspection supports its intended use, retaining the warning and limitations. Retry only for a visible, relevant defect with a diagnosed correction and within existing retry authorization; do not automatically rerun every warning or silently discard it. Geometry/UV changes return to preparation and correspondence checks; appearance retries branch from the preserved baseline.

## Lightweight reviews

Use a few modest-resolution material/rendered views, without overlapping GPU renders, texture baking and other heavy work. A solid/colour viewport proves form or base colour only, not PBR quality. Use appropriate material shading for the check being claimed. Save work before expensive operations; use a separate review copy/process when useful. Texture limits for a review must not destructively downsample source maps.

After textures are applied, test one representative shot before committing to a full render set. Earlier untextured render timings may no longer apply: map count, resolution and a rendered viewport can change memory pressure substantially. If memory pressure or contention is observed, defer competing task-owned GPU work and use an appropriate render-only texture limit or smaller review workload, then inspect detail again. A 2K limit is an option to test, not a universal requirement or a substitute for checking the requested delivery quality. Do not promise a fixed render time from another machine's sample count or GPU.

Do not change an artist's active viewport or render preferences merely to free resources. Track any background process you start, its command, output and PID; on Windows launch it hidden. If the user stops rendering, stop only the verified task-owned process and report what remains. Never terminate every Blender process. Compare source and destination file hashes when handing assets between machines; filenames alone do not prove a fresh transfer.
