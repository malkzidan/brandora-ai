# Natural chat, provider failover and development Backend testing

Current provider order, model selection and commands:
[GroqCloud → OpenRouter integration](OPENROUTER_INTEGRATION.md).
The standalone default is now Groq `openai/gpt-oss-120b` → OpenRouter
`google/gemma-4-31b-it:free` → deterministic Python, with Gemini opt-in.
The historical Gemini-first examples below describe the previous delivery.

Latest correction: [named-product comparisons and Gemini reply diagnostics](NAMED_COMPARISON_PROVIDER_FIX.md).
The suite now passes 1,320 tests. The reported live reply HTTP 400 remains
unresolved pending operator verification; offline SDK serialization alone does
not prove server acceptance.

4 November 2026. The operator reports a successful real five-turn Gemini test
using `gemini-3.5-flash-lite` after the previous SDK fix. That configuration is
retained. This delivery's new composer, GroqCloud failover and development HTTP
adapter were tested offline. No real provider/Backend calls, production data,
Backend edits/migrations, Orders, public v2 activation, commit, push or deployment
occurred. Existing uncommitted work remains intact.

## One executable flow

The CLI runs scoped conversation → hard rules / structured understanding → bounded
read-only tools → typed evidence planning → natural composition → shared validation.
Both providers receive the same restricted understanding/composition tasks. Python
owns scope, HTTP execution, actual matches, prices, quantities and permissions.

`NaturalResponder` is used in every CLI mode. It dynamically builds clauses from
current variants and the current question. The model groups clauses into sentences
and chooses conjunctions, warmth and question style. Mandatory fact IDs must each
appear once, in order. Python renders verified price/options; stock qualifications
remain attached to their variant. The model cannot add prose, discounts, materials,
preferences, delivery claims or order actions. Invalid selections and composition
can trigger provider failover; invalid responses are never silently accepted.

This is a compositional grammar rather than more whole-reply templates. Human
option labels, shared-size references, Decimal money, questions and material
warnings combine independently. Routine price replies omit exact positive stock
and repeated reservation disclaimers. Stock questions report recorded quantities;
zero/insufficient stock is disclosed. Availability questions/purchases disclose
untracked availability. Quantity-only follow-ups avoid repeating unchanged prices;
changed options or fresh changed prices disclose the verified new price. Purchases
always state that no order/reservation was made. Partial-search warnings remain.
At most six variant clauses are shown, with a notice when more verified variants
exist. Arbitrary business-defined options remain literal; no attributes become
unverified policies or marketing claims.

Actual captured offline replies include:

```text
Customer: طب مقاس L بكام؟
AI: تمام، الأسود مقاس L بـ275 جنيه

Customer: أنا محتارة بين الأسود والأبيض، وعايزة مقاس L بس مش عارفة أنهي لون أحسن
AI: الأسود مقاس L بـ275 جنيه، والأبيض بنفس المقاس بـ285 جنيه. تميل لأنهي لون؟

Customer: bekam size L
AI: tamam, el eswed ma2as L b 275 geneh
```

Recognized Franco input keeps Franco script. Arabic/English labels and currency
are localized; original catalog names/options are not arbitrarily translated.
Comparison clears inherited purchase quantity/intent. Cancellation clears only
local provisional choices. Historical observations can flag a changed price but
never supply the current quoted value. Orders stay disabled and `orderCandidate=null`.

## Gemini → GroqCloud → deterministic

GroqCloud uses **api.groq.com**, not xAI Grok. Its adapter uses existing async
httpx, a fixed HTTPS chat-completions endpoint, no redirects/proxies, no SDK
addition and no vendor-controlled tools. Defaults `openai/gpt-oss-20b` and
`openai/gpt-oss-120b` were verified against official
[models](https://console.groq.com/docs/models) and
[structured-output documentation](https://console.groq.com/docs/structured-outputs).
Account access/quota, actual server acceptance and live Arabic quality remain
operator acceptance work; documented compatibility plus MockTransport is not live testing.

Closed composition schemas use Groq strict JSON Schema. Understanding contains
dynamic business-defined option maps, incompatible with strict mode's requirement
for closed objects/all required fields. It therefore uses documented best-effort
JSON Schema followed by the **identical strict application parser**. No schema
failure switches to unrestricted prose. Gemini keeps its verified SDK
`response_json_schema` path.

Default multi-provider budgets: 3 seconds per provider, 8 seconds total per stage,
one Gemini attempt per configured model, at most four Groq priorities. Exhaustion
opens the provider circuit for 30 seconds. One half-open recovery probe runs;
other requests use the secondary. A successful probe closes the circuit. New-chat
Gemini model cooldown aligns with this setting. A single configured provider
receives the whole stage budget; missing Groq does not reserve time away from
Gemini. Existing retrieval/execution deadlines still apply. These are caps, not
live latency guarantees.

Failures include malformed JSON/selectors, guard rejection, unavailable models,
429/503 and timeout. Health/cooldown state contains no customer content. Results
and diagnostics are call-local, including across async task boundaries. Diagnostics
show `understandingProvider`, `replyProvider`, actual source/model and categorized
per-provider failures. Fake mode's Gemini tags identify the simulated SDK; the
CLI header/providerMode labels it fake. Missing all keys in auto mode produces
explicit missing-configuration diagnostics and deterministic replies.

## Private setup and commands

Reuse the existing `.env` and venv. **Do not overwrite `.env` from an example.**
No real Groq key was configured or tested during implementation. The operator
may add `GROQ_API_KEY` privately in the local editor; never paste it into chat,
shell history, shared output or screenshots. Settings loads it as optional
`groq_api_key`. Other non-secret options are in `.env.example`:

```dotenv
GROQ_MODELS=openai/gpt-oss-20b,openai/gpt-oss-120b
CHAT_PROVIDER_ORDER=gemini,groq
CHAT_PROVIDER_TIMEOUT_SECONDS=3
CHAT_TOTAL_TIMEOUT_SECONDS=8
CHAT_CIRCUIT_SECONDS=30
```

Keep the already working private Gemini key and router/generator model lists.
`AI_PROVIDER` retains its legacy v1 rules/gemini meaning. New CLI modes select
the new conversational provider flow independently.

PowerShell, from repository root:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONIOENCODING='utf-8'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:AI_PROVIDER='rules'
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m app.chat --mode rules
.\venv\Scripts\python.exe -m app.chat --mode fake
.\venv\Scripts\python.exe -m app.chat.evaluate --mode rules
.\venv\Scripts\python.exe -m app.chat.evaluate --mode fake
```

When the operator explicitly wants live generation against synthetic data:

```powershell
.\venv\Scripts\python.exe -m app.chat --mode auto
.\venv\Scripts\python.exe -m app.chat.evaluate --mode auto --allow-live
.\venv\Scripts\python.exe -m app.chat.evaluate --mode groq --allow-live
```

These commands can spend quota. Auto tries Gemini then configured Groq without
changing commands after failures. `--mode gemini` also enables the configured
secondary while requiring a Gemini key. `--mode groq` explicitly tests Groq only.
Rules/fake never call providers. Live evaluation requires real-provider success
for eligible understanding/reply stages, rather than counting fallback as success.
Review actual naturalness and grounding manually. Optional Gemini model metadata
discovery remains explicit: `python -m app.chat.diagnose --discover --allow-live`.

## Backend inspection and exact conversation blocker

Latest accessible main remains
[`83a65e9`](https://github.com/shrouqshaker/brandora-backend/commit/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b).
It implements owner-authenticated Products/Variants/Business APIs, fixed
Decimal(12,2) prices, embedded variant pagination and variant-only stock. The
development adapter maps those existing GET DTOs into existing full tool envelopes.
Shared BackendClient validation and typed BackendDataAccess are reused.

[PR #1](https://github.com/shrouqshaker/brandora-backend/pull/1),
`feature/customers-conversations`, is **open and unmerged**, inspected at
`0e92d6b5d038aa6da87c76ee5f06d29aebe4127a`. Its
[documentation](https://github.com/shrouqshaker/brandora-backend/blob/0e92d6b5d038aa6da87c76ee5f06d29aebe4127a/docs/conversations-api.md)
explicitly states that it has no authentication. Its controller/app module
predates current owner auth and Products/Variants modules. Tenant database
filters do not authorize a caller; switching to that branch is not a safe
combined integration environment.

PR reads are `/businesses/:businessId/conversations/:conversationId` and nested
`/messages`, with newest-first messages, CUSTOMER/AI/OWNER roles and conversationId.
The offline response mapper verifies business/customer/conversation ownership and
every row's conversationId, retaining typed pagination/envelopes. Runtime
`get_conversation_history` is blocked before HTTP. There is no auth-bypass toggle.
This is a prepared mapper/contract test, **not completed real conversation integration**.

Backend work: reconcile/rebase PR #1 with authenticated main, add reviewed
Customers/Conversations/Messages auth policies, enforce membership/resource
ownership and test cross-tenant denial. Preserve pagination, chronology, roles
and current-turn cutoff guarantees. Only then can a separately reviewed AI
revision enable that history transport. No Backend files/migrations were changed.

## Operator-authorized development HTTP reads

Use an already configured local/development Backend with authorized development
data. The AI performs no migration, seed, login/refresh, inbound-message POST,
inventory or order mutation. Production Railway/Neon use is prohibited. Only
loopback origins are accepted. Remote development requires an operator-managed
tunnel explicitly known to terminate at development; never tunnel production.

Private `.env` fields, filled by the operator:

```dotenv
DEV_BACKEND_URL=http://127.0.0.1:3000
DEV_BACKEND_OWNER_TOKEN=
DEV_BACKEND_BUSINESS_ID=
DEV_BACKEND_REVISION=83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b
```

Supply the private token from an authorized development login and the actual
owned business UUID. Revision is an operator assertion, not cryptographic server
attestation. The adapter first verifies `GET /auth/me` and OWNER membership in
that business. Each catalog GET still passes NestJS authentication/authorization.
Missing auth capability, another membership, expired credentials and tenant
mismatches fail closed. There is no automatic login/refresh. Obtain a fresh
development token privately and restart after expiry. Owner JWTs stay inside
the local adapter, never in prompts, public requests, AI-context headers or logs.

Explicit operator-initiated reads:

```powershell
.\venv\Scripts\python.exe -m app.chat --mode rules --backend development --allow-development-backend
.\venv\Scripts\python.exe -m app.chat --mode fake --backend development --allow-development-backend
```

Use `/catalog` and product questions. Output is labeled `backendSource=development-http`;
default fixture runs stay synthetic. Business scope is pinned; synthetic switch
commands cannot change it. History here is **local session history**, with local
identifiers and no Backend writes/persistence. Those are not fabricated Backend
customers/messages or production S2S credentials.

Transmitting selected development facts to external models needs explicit action:

```powershell
.\venv\Scripts\python.exe -m app.chat --mode auto --backend development --allow-development-backend --allow-development-data-to-models
```

This spends quota and sends the selected authorized development facts. It was
not run here. No safe development URL/token/data authorization and live-access
approval was provided in this task; actual development integration remains
**unverified**, not represented as a completed real test.

## Tests, file changes and remaining milestones

New: `app/providers/groq.py`, `app/providers/failover.py`, `app/chat/natural.py`,
`app/clients/development_backend.py`, `tests/test_multi_provider_development.py`
and this guide. Updated: Settings/.env.example; shared BackendClient pure
validators; provider diagnostics; chat build/CLI, interpreter, planner, fake SDK
and evaluation; related dialogue expectations and captured transcripts. No files
removed. Only assertions affected by requested presentation/localization changed;
equivalent price, inventory, intent, scope and order-safety assertions remain.

Offline coverage includes Arabic/English/Franco dialogue quality, comparison,
changed prices, quantity shortfalls, untracked stock, strict grounding attacks,
Gemini→Groq completion shapes through MockTransport, 429/503/timeout/missing-key
failover, circuit recovery/half-open concurrency, authenticated dev GET contracts,
tenant checks, redirects, production-host rejection and pending history mapping.
The existing Phase 1–8 and v1 regression suites remain enabled. Captured
`CHAT_ACCEPTANCE_*.jsonl` files are synthetic/fake evaluation, not live evidence.

Final verification: **1,288 passed, 2 warnings in 10.23 seconds**, with
`AI_PROVIDER=rules` and `ENABLE_DEV_ENDPOINTS=false`. This includes 51 new cases
in `test_multi_provider_development.py`. Rules and fake conversation evaluations
both passed with no failed checks, and their actual replies were inspected.
The existing warnings are Starlette/httpx deprecation and Windows pytest-cache
permissions. `git diff --check` passed. No new dependency installation was needed.

Remaining: live acceptance of the new composer and Groq account; authorized
development catalog testing; authenticated integrated conversation APIs/history;
then production S2S signed scope/audience/expiry/replay rules, customer-resource
authorization, durable context and operational checks. The owner JWT adapter must
never become public/customer-facing ingress. Orders/WhatsApp remain disabled/out
of scope. Legacy v1 remains separate; no production readiness or unification is claimed.
