# Brandora AI

Canonical Backend integration: **POST /v2/ai/respond**. Authenticated, bounded,
read-only Products plus on-demand authorized conversation history tools, using GroqCloud
and deterministic Python. E0-3 responses retain `orderCandidate=null`.

The canonical request contains only businessId, customerId, conversationId,
messageId and message. Caller-supplied history/historyStatus are rejected.
Use the versioned conversation-tools-v1 context profile in the final handoff;
older supplied-context clients need the explicitly gated compatibility route.

- [Final Backend handoff](docs/FINAL_BACKEND_AI_HANDOFF.md): contracts, security,
  staging prerequisites, configuration and current release verdict.
- [Independent test plan](docs/AI_INDEPENDENT_TEST_PLAN.md): full HTTP tests,
  synthetic local FastAPI server and 10 Arabic conversation scenarios.
- [Products compatibility contract](docs/PRODUCTS_BACKEND_INTEGRATION.md): retained
  `/v2/ai/products/respond`; the 45 existing tests remain supported.
- [Historical v1 README](docs/LEGACY_README.md): legacy behavior only, not the
  release/deployment entry point. Other phase/provider reports are historical.

## Offline verification

```powershell
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHON_DOTENV_DISABLED='1'
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m app.offline_demo --evaluate
.\venv\Scripts\python.exe -m app.offline_demo
```

No Backend, real keys, database, Docker or external model calls are needed.
The demo explicitly uses MockTransport and ephemeral synthetic signing keys;
it cannot silently replace the real Backend in the release service.

## Release service

`railway.json` runs **python -m app.server**, binding `0.0.0.0` to runtime `PORT`.
The launcher requires explicit staging/production configuration, canonical-route
activation, separate credentials, the Backend public key and verified proxy
CIDRs. It disables legacy v1 and all developer endpoints. Only trusted socket
peers may assert HTTPS. `/health/live` is liveness; `/ready` checks configuration
without calling Backend or Groq. Neither proves live integration acceptance.

Integration is disabled by default. `.env.example` contains no credentials.
Do not overwrite a private `.env` with sample values. RS256 and the canonical
context profile remain proposed Backend agreements. Real authenticated staging
acceptance has not occurred; the complete system is **BLOCKED_BY_BACKEND**.
