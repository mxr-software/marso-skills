# Diagnose the observed failure

Use the exact error and current state to select a repair. Verify after each meaningful change; stop repeating an action when its cause has not changed.

| Symptom | Check | Repair or next step |
| --- | --- | --- |
| No Marso tab | Installed/enabled state; Blender compatibility; active editor. | Enable Marso, then open the `N` sidebar in a 3D Viewport. Install only if missing. |
| "Set your API key" | Key-presence status in effective configuration. | User enters the key in Marso preferences. Never request its value in chat. |
| Authentication failure | Endpoint and current non-generating request. | Preserve an intentional environment. Have the user correct the credential for that environment; re-test once. |
| "Set storage paths" | Both Cache and Downloads fields. | Set both, persist preferences, and verify write access. |
| Paths filled but files fail to write | Actual resolved locations, permissions, available drive and space. | Use a writable location or restore drive access. Changing Downloads does not move old assets. |
| Offline/network failure | Effective Online Access, launch mode, endpoint and network error. | Enable the requested online workflow through supported settings; report policy or network blocks rather than changing unrelated security settings. |
| Library appears populated while offline | Cached project data and request/job evidence. | Distinguish cached display from a fresh service response. Sync success can include a cache fallback. |
| Empty Library | Request success versus authentication/network errors. | An empty account is valid; do not generate a test asset. |
| Official MCP cannot inspect Blender | Correct MCP provider, running Blender-side component, actual client configuration. | Follow current Blender Lab setup and verify scene identity; do not assume Marso's relay fixes this connection. |
| Agent is inspecting the wrong scene | Session/file identity and which Blender instance is connected. | Select/reconnect the intended session. For Marso's hosted relay, a second Blender replaces the first. |
| Local Control Server unreachable | Enabled versus running state, actual port, token, and caller location. | Start the configured server and correct the local caller. A remote cloud connector cannot reach the user's `127.0.0.1`. |
| Hosted agent refuses configuration | Command is outside the hosted allowlist. | Explain the specific preference the user must set in Blender. Respect the refusal. |
| Settings revert | Session overrides, stored preferences, preference saving. | Persist intended settings and save preferences. Report overriding setting names without secrets. |
| Check for Updates fails | Job error, Online Access, credential presence and endpoint. | Report update status as unknown; use the official download page if available. |
| Update downloaded but version unchanged | Loaded version, installation result, reload requirement. | Complete installation/reload, then verify the loaded version. |
| Job appears stuck after Python invocation | Whether a main-thread call is blocking while a worker waits for it. | Return control to Blender, then inspect the same job in a later call. Avoid blocking waits inside Blender Python. |

For a partial setup, report what works and the exact remaining blocker. With no desktop or MCP access, guide the user through the relevant UI and label the resulting evidence as user-confirmed.
