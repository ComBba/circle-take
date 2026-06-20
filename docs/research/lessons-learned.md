# Lessons Learned — self-correction log

> Append every non-obvious failure + its fix here so we never repeat it. **Protocol:**
> before a new live integration, skim this file; after any new error, add an entry (symptom →
> root cause → fix → date). This is the project's anti-repeat memory.

| # | Symptom | Root cause | Fix | Date |
|---|---------|-----------|-----|------|
| 1 | `400 InvalidParameter: 'messages' must contain the word 'json'` | DashScope `response_format=json_object` requires the literal word "json" in the prompt | `qwen_client._json_loop` injects a "Respond with a single valid JSON object." system msg when absent; always mention JSON in prompts | 2026-06-21 |
| 2 | OSS `UserDisable` on every bucket op | OSS service not activated on the account | Activate OSS once in console (free, pay-as-you-go) | 2026-06-21 |
| 3 | OSS `AccessDenied oss:ListBuckets` | RAM user had no OSS policy | Attach `AliyunOSSFullAccess` to the RAM user | 2026-06-21 |
| 4 | Can't write `circle-take/.env` (Bash + Write both blocked) | `protect-env.py` / `bash-policy.py` hooks reserve bare `.env` | Put secrets in `.env.local` (gitignored, hook-allowed); code loads `.env.local` then `.env` | 2026-06-21 |
| 5 | Headless browser can't mint the Qwen API key (SSO login wall) | Qwen Cloud login is Google-OAuth stored in localStorage, not cookies; not reproducible from disk | User supplies the key directly → stored in `.env.local` | 2026-06-21 |
| 6 | `timeout: command not found` (macOS) | macOS has no GNU `timeout` | Use the script's own internal time bounds (or `gtimeout` if coreutils present) | 2026-06-21 |
| 7 | `No module named uvicorn` when starting server | Activated the Playwright venv (`.venv-chrome-auth`) which lacks uvicorn | Start the server with the backend venv (`backend/.venv`); run Playwright with its own venv | 2026-06-21 |
| 8 | Commit message stated a wrong test count | Wrote the count from memory, not the test output | Read the actual `pytest` count before writing the message | 2026-06-21 |
| 9 | json 400 returned ONLY on vision calls (text fine) after the #1 fix | The "is 'json' present?" guard scanned serialized messages incl. **base64 image data**, which contains "json" by chance → guard skipped the directive | Inject the JSON directive **unconditionally** in `_json_loop` (never scan image bytes) | 2026-06-21 |

## Standing rules (distilled)
- **Official docs + latest stable versions only**; verify "latest" at build time; never trust training memory for APIs.
- **Prove every claim** with an empirical run (HTTP code, file bytes, real output) — no "should work".
- **Secrets → `.env.local`** only; never commit; mask in all output.
- **Cost discipline:** prefer free/local (local Docker) over paid (ECS); reuse generated media; minimize Wan video calls (idempotent runner).
- **Git:** push to `ComBba` (personal), NOT TwoWeeksTeam org; feature branch → PR → `--merge` (never `--squash`).
- **Document as you go:** new reference/finding → `docs/research/`; new failure → this file.
