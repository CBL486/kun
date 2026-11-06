# G2 Production API Recovery - 2026-11-03

## Current state

- Candidate release: `0.1.0-g2-rc1`
- Release directory: `C:\AIWorld\releases\0.1.0-g2-rc1-20261102`
- `C:\AIWorld\current` exists and exposes the candidate release.
- `AIWorld-API` is registered with the expected script and arguments:
  `C:\AIWorld\releases\0.1.0-g2-rc1-20261102\deploy\windows\Start-AIWorldApi.ps1`
- The task returns exit code `1`; port `127.0.0.1:8080` is not listening.
- Therefore G2 is **not** live and must not be reported as complete.

## Production environment defect found and corrected

The server copy of `C:\AIWorld\config\production.env` had been flattened into one concatenated line. For example, adjacent assignments appeared as `productionAIWORLD_DATABASE_URL=...` rather than as separate lines.

This is incompatible with `Import-AIWorldEnvironment`, which expects one `NAME=value` assignment per line.

Recovery performed:

- Preserved the original file as `C:\AIWorld\config\production - 副本.env`.
- Rewrote the production file with a newline inserted before every `AIWORLD_` boundary.
- Verified that every non-empty line contains `=` and that the expected variable names appear in order.
- No secret values were written to this repository or log.

After the fix, manually triggering the task still produced exit code `1`, and no new API startup record appeared in `C:\AIWorld\logs\api.log`. The failure therefore occurs before the Python process's output redirection, or the task cannot start the script as configured.

A diagnostic `Start-Transcript` line was prepended to
`C:\AIWorld\current\deploy\windows\Start-AIWorldApi.ps1` to capture pre-Python errors on the next run. If the task never creates `C:\AIWorld\logs\api-task.log`, the failure is earlier than script execution.

## Next recovery sequence

1. Run the exact task action interactively from an elevated PowerShell in the release Windows directory:
   ```powershell
   .\Start-AIWorldApi.ps1 `
     -RootPath C:\AIWorld\current `
     -PythonPath C:\AIWorld\runtime\Python312\python.exe `
     -EnvironmentFile C:\AIWorld\config\production.env `
     -LogDirectory C:\AIWorld\logs
   ```
2. Capture and fix the first terminating error.
3. Trigger `AIWorld-API` again and require:
   - task result success,
   - `TcpTestSucceeded=True` for `127.0.0.1:8080`,
   - `/health`, `/ready`, `/world`, `/agent`, and `/metrics` responses.
4. Run the production DeepSeek smoke against the scheduler database and preserve the evidence JSON.
5. Only then proceed to reverse proxy/TLS, public exposure, and the 14-day G3 run.

## Boundaries

- Do not edit or delete `AIWorldPostgreSQL`.
- Do not remove the preserved environment backup.
- Do not expose `/metrics` through a public reverse proxy.
- Do not paste database passwords, API keys, or server credentials into repository files, logs, or chat.
- Real external content review is still `local`; `review=approved` does not mean an external review vendor is connected.
## Latest diagnostic update (2026-11-03)

- The environment file was normalized successfully. A Python line audit confirmed that every non-empty line contains `=`, and the expected 13 `AIWORLD_*` names appear in order.
- `AIWorld-API` was manually triggered again. It returned exit code `1`, and `127.0.0.1:8080` still does not listen.
- The task action points to the expected release script and absolute arguments.
- An interactive run of the release script revealed a PowerShell parser failure around the `param(...)` block after the diagnostic transcript edit. The diagnostic `Start-Transcript` line has been removed; the first 10 lines now read as a valid `param` block.
- The script file was rewritten through PowerShell/ASCII during recovery. If the parser failure persists, restore `Start-AIWorldApi.ps1` from the verified release archive instead of further in-place editing, then re-run the task with the task's absolute arguments.
- `C:\AIWorld\logs\api.log` has not received a new startup record, so the current failure is still before Python logging.

Do not mark G2 complete until the API is listening and health/readiness checks pass.

## Resolution (2026-11-06)

The production API and scheduler are live again. The root cause was not the
environment file or the release contents: Windows PowerShell 5.1 converts
native stderr output into `NativeCommandError` records while
`$ErrorActionPreference` is `Stop`. Uvicorn writes normal `INFO` records to
stderr, so the launcher terminated immediately after the server process started.

Recovery performed:

- Scoped `$ErrorActionPreference = "Continue"` to the native Python service
  invocation in the API, scheduler and backup launchers.
- Restored the `AIWorld-API` task to the official `Start-AIWorldApi.ps1` with
  explicit `-RootPath`, `-PythonPath`, `-EnvironmentFile` and `-LogDirectory`
  arguments.
- Re-ran the API task and confirmed it remains in the `Running` state with the
  Python process parented by the task's PowerShell process.
- Started the scheduler task and confirmed the same managed process structure.
- Ran the production DeepSeek smoke successfully.
- Built and verified a clean `0.1.0-g2-rc3` release directory from the patched
  source. The temporary `.fixed.ps1` recovery file is excluded.

Live verification:

- `AIWorld-API`: `Running`, last result `267009` (task still running).
- API listener: `127.0.0.1:8080`, PID `2892`.
- `/health`, `/ready`, `/world`, `/agent`, `/metrics`: HTTP `200`.
- Metrics: database ready `1`, scheduler configured `1`, pending/delayed/leased
  and expired-lease counts all `0`.
- `AIWorld-Scheduler`: `Running`, last result `267009`.
- `AIWorld-Backup`: manual run completed with result `0`; a new verified dump and
  manifest were created at `2026-11-06 17:02:06 +08:00`.
- DeepSeek smoke: `live=true`, `provider=deepseek`, `model=deepseek-flash`,
  `run_mode=model`, `status=succeeded`, `112` input / `81` output tokens,
  cost `0.00121824 CNY`.

Prepared release:

- `C:\AIWorldeleases\0.1.0-g2-rc3-20261106`
- `188` files, `rpg_deploy verify` returned no issues.
- Package checksum:
  `e44dc22142b8a7accdc2932a8b28b0ceaaf13b6648b00296fccaad1b8bd7f35c`

`C:\AIWorld\current` still points at the hot-fixed rc2 release; the clean rc3
directory is ready for the next maintenance-window cutover. Do not treat the rc2
manifest as immutable after the emergency script repair.
