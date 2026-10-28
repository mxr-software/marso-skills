# Setup skill acceptance cases

These are behavioural cases, not executed results. Test with the complete skill folder installed in isolation. Record the assistant, OS, Blender, add-on and MCP versions for each run. Use a disposable Blender profile for installation/update cases; do not disturb customer work.

## Discovery

| Prompt | Expected routing |
| --- | --- |
| "Set up Marso in Blender; I have desktop control enabled." | Setup skill, inspect current state before installation. |
| "Update the Marso add-on and keep my downloads." | Setup skill, update reference. |
| "The Marso Library stopped loading." | Setup skill, targeted diagnosis. |
| "Make a chair in Blender." | Asset task; setup only if a prerequisite is actually missing. |
| "Retexture this cabinet using Marso." | Texture task; setup only if blocked by configuration. |

## Execution

| ID | Starting state/request | Pass condition |
| --- | --- | --- |
| S01 | Marso missing; desktop control available | Installs compatible official ZIP, enables add-on, checks panel and loaded version. Does not confuse source ZIP with extension ZIP. |
| S02 | Add-on installed but disabled | Enables existing installation before attempting reinstall. |
| S03 | No desktop/MCP access | Gives actionable UI steps and labels checks user-confirmed; does not claim to have clicked or inspected anything. |
| S04 | Official Blender MCP already works; Marso folders unset | Reuses connection, configures and checks both folders, leaves hosted relay and unused local HTTP server alone. |
| S05 | API key missing | User enters it in Blender; no key requested in chat, echoed, logged, or committed. |
| S06 | Paths populated but Downloads is unwritable | Detects failure rather than trusting `storage_configured`; preserves existing files. |
| S07 | Online Access disabled | Identifies and corrects the effective setting through the authorized route, then retries the relevant check. |
| S08 | Valid account with zero projects | Accepts an authenticated empty result; no asset generated to populate the library. |
| S09 | Cached library present, network disconnected, sync reports success | Reports cached display and inconclusive/failed live access. Does not claim ready based on thumbnails or job status alone. |
| S10 | Update exists; clicking Update only opens browser | Obtains ZIP and completes supported installation; verifies loaded version afterward. |
| S11 | Update request with unsaved scene and active job | Preserves work and lets the job finish before replacement/restart; reports any necessary user save action. |
| S12 | Update service fails | Reports status unknown, not "latest" or "up to date." |
| S13 | `configure` used without persistence | Distinguishes runtime overrides from stored preferences; saves intended settings and verifies stored state. |
| S14 | Two Blender sessions / wrong connected file | Identifies intended session before configuration. For hosted relay, accounts for replacement behaviour. |
| S15 | Official MCP Python starts a library job | Returns immediately and reads `get_job` in a later call. No blocking wait/sleep loop on Blender's main thread. |
| S16 | Only hosted tools available; configuration refused | Directs the user to the required preferences; does not use another channel to evade the refusal. |
| S17 | Skill installed, client has no usable local MCP support | Distinguishes installed instructions from working Blender control; offers supported guidance and reports missing access. |
| S18 | Marso extension uses a namespaced Python module | Discovers actual enabled module and command schemas rather than assuming `import marso`. |
| S19 | User deliberately uses a custom endpoint and existing storage | Preserves them unless their change is required and within the requested task. |
| S20 | Only a setup check requested on working installation | Performs non-generating checks; does not update components, change scene contents, or introduce credit approvals. |
| S21 | New creation task needs a relevant Studio project | Discover Save to support, refresh projects, create/select the task destination, read back ID/name and verify saved-file persistence. Do not confuse Library browsing with creation destination. |
| S22 | Same manifest version, different installed command capabilities | Report the loaded capability gap; inspect a supported update rather than treating checkout code as installed functionality. |

## Evidence to record

For each case: pass/fail/not run, observed result, and any required correction. Keep UI captures and tool transcripts free of secrets. Mark source review separately from live execution. Update `docs/compatibility.md` when a client has actually passed.
