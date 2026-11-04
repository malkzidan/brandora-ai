# Real-provider diagnostics and conversation regression — 4 November 2026

Subsequent operator report: all five real Gemini turns succeeded using
`gemini-3.5-flash-lite`. This corrective report remains the historical offline
record. The current natural composer, GroqCloud failover and distinct pending
live/development tests are in [MULTI_PROVIDER_DEVELOPMENT.md](MULTI_PROVIDER_DEVELOPMENT.md).

This is a corrective delivery, not v1/v2 unification. No live model discovery,
Gemini generation, Backend call, production data access or Backend modification
was performed. No credentials or `.env` were printed/modified. No Orders,
deployment, commit, push or merge occurred. Legacy v1 remains present.

## Confirmed findings versus unresolved causes

1. **Reproduced local SDK schema bug.** Installed `google-genai` is 2.33.0.
   Before this fix, `GeminiClient._generate` supplied the Pydantic `Meaning`
   class as `response_schema`. `Meaning.options` generates JSON Schema
   `additionalProperties: {type: string}`. The installed SDK's
   `_transformers.t_schema` / `_raise_for_unsupported_mldev_properties` rejects
   that schema in Developer API mode with ValueError, **before any HTTP request**.
   An offline reproduction using the actual SDK converter confirmed it.
2. **Confirmed misleading exception handling.** The previous client used one
   `except ValueError` for SDK conversion AND response parsing, recording both as
   invalid model output. This explains why the observed understanding log did
   not establish that Gemini returned malformed JSON. Fake SDK tests previously
   replaced `_generate` entirely, so they missed the converter defect.
3. **Confirmed model configuration problem in the reported IDs.** Google's
   [deprecation page](https://ai.google.dev/gemini-api/docs/deprecations) lists
   `gemini-2.0-flash` shutdown on 1 June 2026. It lists 2.5 Flash as restricted
   to existing users, with a migration scheduled for December 2026; 2.5 Flash-Lite
   has no shutdown date announced in the page inspected. Availability for a
   particular key/project is still unverified. No replacement IDs were chosen
   automatically and no default model list or `.env` was rewritten.
4. **Original reply ClientError remains unproven.** Existing logs discarded the
   status/category, so authentication, permissions, quota, invalid request/schema
   and model/API availability cannot be distinguished retrospectively. The
   reply schema passes local SDK serialization; that does not prove server
   acceptance or successful generation. No claim of a successful real fix/test
   is made without the next explicit operator-initiated run.
5. **Latency explanation is bounded, not a benchmark claim.** The former local
   conversion failure was retried against multiple models, and later generic
   request failures could sleep/retry until the 8-second outer stage cap. No
   live timings were collected here. Deterministic SDK configuration failures
   now fail immediately; deterministic 4xx requests do not incur delayed retries.
   Live generation naturally has network/model latency and can still time out.

## Provider correction and diagnostics

`GeminiJSONModel` marks the two conversational schemas for the SDK's documented
`response_json_schema` path. The
[official SDK documentation](https://googleapis.github.io/python-genai/genai.html)
recommends this alternative when `response_schema` cannot process a schema.
Only its documented JSON Schema subset is sent. `maxLength`/`maxProperties`
remain enforced by strict local Pydantic validation; unsupported wire keywords
are omitted. Required fields, types, enums, nullability, numeric/array bounds,
references and `additionalProperties` restrictions are retained as applicable.
Other providers/legacy schemas retain their existing response-schema path.

Application parsing rejects missing fields, wrong types/enums, extra fields,
duplicate keys, oversized/empty output and malformed JSON. A single complete
JSON code fence can be decoded, then receives the identical strict validation.
No heuristic repair, coercion, arbitrary prose or invalid guard response is
accepted. Conversational schema errors do not silently disable the schema.
Blocked/truncated SDK responses are classified without exposing their contents.

Call-local `ProviderDiagnostic` records contain fixed category, operation and
integer HTTP status only. No payload, customer text, authorization, provider
message, model-supplied field name or key is retained. Shared health retains
operational categories, not request data. Diagnostics distinguish:

| Category | Meaning / safe next check |
| --- | --- |
| sdk_schema_error | Local conversion problem; run offline schema check |
| sdk_configuration_error | Local SDK/config validation, not model output |
| api_schema_error | HTTP 400 mentioning schema; inspect version/model support |
| api_request_error | Other non-authentication 4xx; exact payload cause not exposed |
| model_unavailable | HTTP 404; check accessible model IDs/API endpoint/version |
| authentication | HTTP 401 or known invalid-key 400 marker; check key privately |
| permission_denied | HTTP 403; check project/service/key restrictions and model access |
| rate_limit_or_quota | HTTP 429; inspect project/model limits and billing privately |
| api_unavailable | Other server failures, e.g. 503 |
| timeout | Stage deadline, asyncio/httpx timeout, HTTP 408/504 |
| malformed_json / missing_fields / validation_error | Model output failed strict parsing/validation |
| empty_output / output_truncated / output_blocked | No usable complete response; never invent success |
| grounding_guard_rejected | Schema parsed, but required factual acts/IDs were altered or omitted |

HTTP status alone does not prove billing versus transient rate limits, or why a
403/404 occurred. Those distinctions deliberately remain operator checks.

Chat diagnostics now separately expose `understandingFailure`, `replyFailure`
and `providerFailures.understanding/reply`, so a first-stage fallback cannot mask
the second-stage error. `understandingMs`, `executionMs` and combined `elapsedMs`
replace the misleading execution-only timing as the turn duration estimate.

## Conversation correction

The reported final message contains an explicit comparison/preference question,
two colors and size L. The old fallback treated comparison words as an unrelated
product query, and purchase wording won over the comparison. It could not safely
represent two alternative values with its single-value options map.

The interpreter now recognizes `compare`, keeps a uniquely scoped previous
product when the message contains comparison language/options rather than a new
product noun, and resets inherited purchase quantity. Gemini can express the
same act with `option_alternatives`; deterministic comparison cannot be changed
into purchase by an invalid model proposal.

The immutable internal Inquiry adds a bounded OR selector: at most two option
keys, each with two to four distinct requested values. Normal shared options
still use the single-value map. Both retrieval and planning resolve these against
the product's current declared definitions and filter **actual typed variants**.
Different option keys combine with AND. No Cartesian combinations or new tools
are synthesized. Backend wire arguments and six read-only operations are unchanged.

For the exact five-turn Arabic regression, both offline modes now retain the
product, return INQUIRY, quote current Black/L 275.00 EGP and White/L 285.00 EGP,
and clear requested quantity. The reply explains that color preference is the
customer's and asks a focused color question. It never declares a color better
or invents material/style differences. Missing/inactive/unpriced alternatives
are explicitly unverified; partial searches never prove global absence.

Cancellation/decline clears provisional local selections only. Changing one's
mind revalidates changed options; a new unrelated product does not inherit the
previous selection or quantity. A new explicit purchase sets its current quantity.
Orders remain disabled and `orderCandidate=null` throughout.

## Files and regression verification

New: `app/providers/structured.py`, `app/chat/diagnose.py`,
`tests/test_chat_provider_regressions.py`, this document.

Updated: provider `base.py`, `gemini.py`, `evidence.py`; chat `__main__.py`,
`understanding.py`, `responding.py`, `application.py`, `evaluate.py`;
`app/schemas/inquiry.py`, `app/data/options.py`, `app/data/retrieval.py`,
`app/pipeline/evidence_planner.py`; local guide/README and captured evaluation
transcripts. No files removed. Earlier uncommitted phase work remains intact.

Forty-one new regression cases cover exact Meaning/ConversationReply schema
serialization through the installed SDK's actual request converter and mocked
real `_generate` path, strict valid/invalid outputs, sanitized HTTP categories,
SDK conversion errors, blocking/truncation/timeouts, stage-separated fallbacks,
model-discovery/preflight gates and the conversation/stock/selection regressions.
This supplements the existing fake-boundary, grounding, history, isolation and
legacy v1 suites; unrelated tests were not changed.

Full offline suite with `AI_PROVIDER=rules`, `ENABLE_DEV_ENDPOINTS=false`:
`1237 passed, 2 warnings`. Warnings remain Starlette/httpx deprecation and Windows
pytest-cache access. Rules and fake evaluation include the exact five-turn
regression; captured replies/checks are in `CHAT_ACCEPTANCE_RULES.jsonl` and
`CHAT_ACCEPTANCE_FAKE.jsonl`. No live success is inferred from these tests.

## Exact operator-initiated checks

PowerShell from repository root; keep the existing key private:

```powershell
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe -m app.chat.diagnose
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m app.chat.evaluate --mode rules
.\venv\Scripts\python.exe -m app.chat.evaluate --mode fake
```

`diagnose` without flags only serializes synthetic schemas locally; it prints
SDK version and pass/fail. It never initializes an API client or discovers models.

When the operator deliberately authorizes model-metadata access:

```powershell
.\venv\Scripts\python.exe -m app.chat.diagnose --discover --allow-live
```

This uses existing private configuration and prints only accessible
generateContent model IDs, capped at 500 metadata records. It performs no
generation and changes no configuration. Listing a model does not establish
generation quota or successful structured output. If discovery fails, use the
fixed category/status above; check the same key's project, Gemini API enablement,
key/API restrictions, region/model permissions, rate limits and billing privately
in Google AI Studio/Google Cloud. Never paste a key, raw exception or auth header.

Choose active text-generation IDs from the successful discovery and current
documentation; set the process environment explicitly. The placeholders below
must be replaced with the operator-selected IDs, not copied literally:

```powershell
$env:ROUTER_MODELS='<accessible-active-generateContent-id>'
$env:GENERATOR_MODELS='<accessible-active-generateContent-id>'
.\venv\Scripts\python.exe -m app.chat.evaluate --mode gemini --allow-live
.\venv\Scripts\python.exe -m app.chat --mode gemini
```

These final commands spend generation quota. Synthetic Backend only; no live
customer data is sent. The local chat preflight refuses known-retired Gemini 2.0
IDs rather than blindly replacing them or spending requests on them. Live
evaluation must show successful Gemini understanding AND reply sources for
eligible turns, correct comparison prices/intent and no guard failures. Review
naturalness and understanding manually; do not count deterministic fallback as
successful real-Gemini acceptance. Review safe stage diagnostics before retrying
if the run fails. Avoid repeated quota-spending loops.

## Remaining limits / next milestone

The SDK defect and offline conversation regressions are fixed and tested. The
original reply API failure, key/project permissions/quota, model availability for
this operator and subjective live-model quality remain unverified. This is not
yet a successful reviewed real-Gemini conversation. Rules comparison vocabulary
is finite; unknown synonyms, multiple products, undeclared alternatives or
uncertain scope require clarification. Comparisons are evidence summaries, not
recommendations about unverified style, quality or customer preferences. Generation
remains the guarded bilingual phrase grammar. No legacy v1 removal or unification
should proceed until explicit live acceptance succeeds and is reviewed.
