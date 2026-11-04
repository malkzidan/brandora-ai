# OpenRouter Nemotron free compatibility correction

## Verified incompatibility

The old adapter sent `response_format={type:json_object}` and
`provider.require_parameters=true` for every configured free model.
The [official Nemotron endpoint metadata](https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-lightning:free/endpoints)
lists temperature and max_tokens, but not response_format. The
[official model page](https://openrouter.ai/nvidia/nemotron-3.5-lightning:free)
explicitly states that JSON output is not enforced through response_format.
Requiring that unsupported parameter can exclude the endpoint during routing.
This confirms an adapter incompatibility, not proof that every observed HTTP 404
has that sole cause. No live inference was performed to confirm the corrected
request. Account access, capacity and endpoint availability remain external.

## Explicit policy and safeguards

The immutable policy registry in `app/providers/openrouter.py` supports exactly:

| Exact free model ID | response_format policy |
| --- | --- |
| `google/gemma-4-31b-it:free` | `{type:json_object}`, unchanged |
| `nvidia/nemotron-3.5-lightning:free` | Field omitted entirely |

Gemma's JSON-mode capability is documented on its
[official model page](https://openrouter.ai/google/gemma-4-31b-it:free).
Neither policy claims native JSON Schema enforcement. Both retain the exact
schema instructions in the system prompt, strict Pydantic parsing, semantic
selection validation and grounding/composition Guard. Invalid JSON, invented
selectors and unverified fact references fail validation and use the existing
bounded fallback paths. Nemotron's omission is predetermined configuration, not
a downgrade triggered by an HTTP error.

Unknown model IDs or invalid capability states raise the fixed
`unsupported_model_capabilities` category before HTTP. CLI configuration errors
expose that category without echoing configured values. Existing invalid or paid
ID restrictions remain. Adding a new free model now requires documenting and
testing an explicit capability entry; `:free` alone is insufficient.

Both policies preserve `require_parameters=true`, `allow_fallbacks=false` and
`max_price={prompt:0,completion:0,request:0}`. These are OpenRouter routing
preferences, not unsupported native model generation parameters. See the
[official provider-routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection).
No redirect, router, paid endpoint, arbitrary HTTP tool or order action is enabled.
The default model/order and all timeouts/circuit behavior remain unchanged.

## Offline verification

With `AI_PROVIDER=rules` and `ENABLE_DEV_ENDPOINTS=false`:

* Full suite: **1,380 passed, 2 warnings**.
* Rules and fake evaluations: **all checks pass**, six scenarios / 17 turns each.
* 22 additional parameterized cases cover both model request formats, schema
  instructions, safe HTTP failures including 404/429, invalid JSON, unknown
  capabilities, invalid policy states, and Nemotron → Gemma fallback after
  malformed semantics, JSON, 404 or 429. Verified 275/285/10 Decimal comparison
  assertions remain active during fallback.
* A mocked routing-filter regression reproduces 404 for the old unsupported
  required format and accepts the corrected Nemotron body. This is an offline
  simulation of documented filtering, not a real OpenRouter result.

Warnings are the existing Starlette/httpx deprecation and Windows pytest cache
permission. `git diff --check` also flags trailing whitespace / an extra final
blank line in `.env.example:50`, which this task did not edit; it was left intact.

Files changed in this correction:

* `app/providers/openrouter.py`: explicit immutable capabilities and safe rejection.
* `app/chat/__main__.py`: safe capability configuration diagnostic.
* `tests/test_openrouter.py`: new and expanded mocked regressions.
* `docs/CHAT_ACCEPTANCE_RULES.jsonl`, `docs/CHAT_ACCEPTANCE_FAKE.jsonl`: refreshed captures.
* This document and `docs/OPENROUTER_INTEGRATION.md`: findings and operator commands.

## Operator-initiated live verification

From the repository root, with the API key already configured privately:

```powershell
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHONIOENCODING='utf-8'
$env:OPENROUTER_MODELS='nvidia/nemotron-3.5-lightning:free'
.\venv\Scripts\python.exe -m app.chat.evaluate --mode openrouter --allow-live
```

This uses the synthetic catalog, does not modify `.env`, and spends OpenRouter
quota only when the operator runs it. Confirm `understandingProvider=openrouter`,
`replyProvider=openrouter`, all checks pass, and the named comparison produces
275 EGP, 285 EGP and the exact 10 EGP difference. Interactive equivalent:

```powershell
.\venv\Scripts\python.exe -m app.chat --mode openrouter
```

Optional controlled automatic failover, with both keys privately configured:

```powershell
$env:CHAT_PROVIDER_ORDER='groq,openrouter'
.\venv\Scripts\python.exe -m app.chat.evaluate --mode auto --allow-live --simulate-groq-failure
```

The last command simulates Groq 503 locally; only OpenRouter inference is live.
Nemotron may still time out, return invalid JSON/semantics, hit capacity/quotas or
be unavailable. None of these errors weakens validation or enables paid routing.
Native JSON-mode guarantees are unavailable for this endpoint, so retries/fallback
may occur more often. Real keys were not inspected or modified; no live inference,
production/Backend changes, Orders, commit, push or deployment occurred.
