# GroqCloud → OpenRouter → deterministic Python

Latest compatibility correction: [Nemotron free capability policy](OPENROUTER_NEMOTRON_FIX.md).
Only the explicitly documented Gemma and Nemotron free IDs are now accepted;
unknown free IDs fail closed before HTTP. Nemotron omits `response_format`.

4 November 2026. The operator reports successful live Groq understanding and
reply generation, including the exact 275 / 285 / 10 EGP comparison in 2721 ms.
This correction made no live inference calls. Public official documentation was
consulted without credentials. Actual `.env` was not printed, edited or replaced.

## Selected models and documented capabilities

The standalone automatic chain defaults to:

1. GroqCloud: `openai/gpt-oss-120b`.
2. OpenRouter: **`google/gemma-4-31b-it:free`**.
3. Existing deterministic Python fallback.

The [official OpenRouter model page](https://openrouter.ai/google/gemma-4-31b-it:free)
lists the exact free variant, an active Google AI Studio provider, multilingual
support across 140+ languages, and JSON `response_format` support. This is Gemma,
a different model family from GPT-OSS; it is not the optional Gemini adapter.
Arabic/English suitability is a multilingual-model selection inference, not a
new live quality claim. Franco-Arabic quality requires operator review.

The same page explicitly distinguishes JSON output from native JSON Schema
enforcement: the selected free endpoint supports the former, not the latter.
Accordingly this adapter deliberately sends `response_format: {type: json_object}`
and the exact schema in the system instruction. It always applies existing strict
Pydantic parsing, semantic selectors and grounding/composition validation. It does
not silently downgrade a failed schema request or accept unvalidated prose.
Native schema-constrained decoding is not claimed for this endpoint.

[OpenRouter's structured-output documentation](https://openrouter.ai/docs/guides/features/structured-outputs)
states that native schema support depends on the endpoint. Older free model
pages alone were not treated as proof of availability. In particular, queried
Qwen free IDs were not corroborated in current model listings and Nemotron 3
Super's queried free endpoint metadata had no endpoints. They were not selected.

## Integration and safeguards

`OpenRouterClient` reuses GroqClient's bounded async HTTP lifecycle via small
request/configuration hooks. ProviderChain, circuit breakers, half-open recovery
probes, interpretation parser and NaturalResponder are reused. Both understanding
and reply can independently fail over on invalid JSON/schema/semantics, rejected
fact IDs, 429, 503, timeouts or transport failures. Exhaustion retains grounded
deterministic replies. Tenant-scoped Backend reads, Decimal facts and disabled
Orders remain unchanged.

Requests use a fixed HTTPS chat-completions endpoint, no redirects, no proxy
inheritance, no customer-supplied URLs or tools, and no extra SDK/dependency.
One attempt per configured model is bounded by the existing stage/provider
budgets. Shared state contains health/cooldowns only.

Free-only enforcement happens before HTTP and again while building requests:

* Only one to four distinct explicit `vendor/model:free` IDs are allowed.
* Paid variants, suffix chains, URLs and all `openrouter/*` routers are rejected.
* A stage's `models` argument cannot override the OpenRouter configuration.
* Each request names one model; no server-side model array, routing plugin or
  paid fallback is sent.
* Provider preferences set `require_parameters=true`, `allow_fallbacks=false`
  and `max_price={prompt:0, completion:0, request:0}`.

The [official provider-routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection)
documents parameter requirements, fallback controls and maximum prices. Zero-price
filters should fail closed if no compatible free provider remains. Availability,
account policy and free-tier quotas can change; the application never substitutes
a paid model to recover. Errors contain fixed categories/statuses, not provider
payloads, raw customer data or credentials. API keys are excluded from Settings repr.

## Configuration and compatibility

Optional `OPENROUTER_API_KEY` and comma-separated `OPENROUTER_MODELS` are loaded
through existing settings. `.env.example` contains blank credential placeholders,
`GROQ_MODELS=openai/gpt-oss-120b` and `CHAT_PROVIDER_ORDER=groq,openrouter`.
Missing provider keys omit that provider in auto mode; missing both safely uses
Python. Explicit `--mode openrouter` or `--mode groq` requires that provider's key.
Invalid OpenRouter model configuration stops before network use.

Gemini is instantiated only when explicitly selected by `CHAT_PROVIDER_ORDER` or
`--mode gemini`. Gemini mode puts it first and retains configured secondaries.
The interactive CLI remains offline rules mode unless a live mode is explicitly
selected. Existing v1 HTTP implementation and its separate `AI_PROVIDER` settings
are preserved; this task does not unify/activate the legacy and standalone paths.
Existing local environment overrides remain effective because `.env` was preserved.

## Exact operator verification commands

From the repository root in PowerShell, with keys already configured privately.
These commands use the **synthetic catalog only**. The live flags spend provider
quota. No real Backend, customer data or Orders are involved.

```powershell
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHONIOENCODING='utf-8'
$env:GROQ_MODELS='openai/gpt-oss-120b'
$env:OPENROUTER_MODELS='google/gemma-4-31b-it:free'
$env:CHAT_PROVIDER_ORDER='groq,openrouter'

# Each provider independently. OpenRouter-only cannot call Groq or Gemini.
.\venv\Scripts\python.exe -m app.chat.evaluate --mode groq --allow-live
.\venv\Scripts\python.exe -m app.chat.evaluate --mode openrouter --allow-live

# Normal chain: confirm Groq is primary and review any fallback diagnostics.
.\venv\Scripts\python.exe -m app.chat.evaluate --mode auto --allow-live

# Controlled failover: local synthetic Groq 503; real OpenRouter handles both stages.
# No real Groq outage, bad credentials or failing Groq generation is needed.
.\venv\Scripts\python.exe -m app.chat.evaluate --mode auto --allow-live --simulate-groq-failure

# Interactive synthetic conversation using the same automatic chain.
.\venv\Scripts\python.exe -m app.chat --mode auto
```

The evaluation prints parsed fields only for fixed synthetic scenarios. Confirm
`understandingProvider` and `replyProvider` are `openrouter` in the OpenRouter-only
and simulated-outage runs. The simulated outage records a Groq 503, followed by
circuit-open diagnostics; these are expected. A secondary failure must remain
visible rather than counting deterministic fallback as live acceptance. All
checks, including exact comparison prices/difference, should pass. Review Arabic,
English, Franco, clarifications and the original multi-turn selection changes.

Free endpoint latency may exceed the existing 3-second provider budget. If the
operator elects to allow more time, set bounded process-local values explicitly:

```powershell
$env:CHAT_PROVIDER_TIMEOUT_SECONDS='6'
$env:CHAT_TOTAL_TIMEOUT_SECONDS='8'
```

This is optional and does not change checked-in defaults. Full-stage and outer
understanding/reply deadlines remain enforced. No paid endpoint is enabled.

## Changes and offline verification

Files changed for this task (earlier uncommitted work is preserved):

* `app/providers/openrouter.py`: free-only adapter.
* `app/providers/groq.py`: reusable transport hooks; existing Groq schema behavior retained.
* `app/config.py`: optional OpenRouter config and free-first standalone defaults.
* `app/chat/__main__.py`: OpenRouter-only mode, automatic/optional Gemini selection.
* `app/chat/application.py`: correct OpenRouter reply diagnostics.
* `app/chat/evaluate.py`: OpenRouter acceptance and opt-in local outage simulation.
* `.env.example`: blank key example and public model/order values.
* `tests/test_openrouter.py`: 38 new offline cases.
* `tests/test_multi_provider_development.py`: expected primary updated to 120B;
  explicit two-model fixture preserves existing multi-model failure assertions.
* `docs/CHAT_ACCEPTANCE_RULES.jsonl`, `docs/CHAT_ACCEPTANCE_FAKE.jsonl`: refreshed captures.
* This document and `docs/MULTI_PROVIDER_DEVELOPMENT.md`: current configuration and operator steps.

With `AI_PROVIDER=rules`, `ENABLE_DEV_ENDPOINTS=false`:

* `python -m pytest -q`: **1,358 passed, 2 warnings**.
* Rules and fake evaluation: **all checks pass**, six scenarios / 17 turns each.
* New tests cover HTTP/auth/schema format, cost controls, rejected paid/router
  IDs, refusal/truncation, malformed output, 429/503/timeout/semantic failover,
  reply-only Guard failover, deterministic exhaustion, circuit recovery, settings
  defaults, optional Gemini, safe errors and the operator outage simulation.

Warnings remain the existing Starlette/httpx deprecation and Windows pytest cache
write permission. No real provider inference, Backend changes, production access,
Orders, commits, push, merge or deployment occurred. Live OpenRouter acceptance
and provider-side limits remain operator review work.
