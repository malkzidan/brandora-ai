# Local conversational Brandora

The current composer, automatic Gemini/GroqCloud failover, private key setup and
explicit development HTTP commands are documented in
[MULTI_PROVIDER_DEVELOPMENT.md](MULTI_PROVIDER_DEVELOPMENT.md).

For the latest real-provider corrections, sanitized diagnostics and explicit
discovery/live-test commands, see [GEMINI_REGRESSION_FIX.md](GEMINI_REGRESSION_FIX.md).
The previous offline delivery did not verify real Gemini. Legacy v1 remains
separate pending a successful reviewed live conversation.

The standalone read-only chatbot is runnable independently. Existing v1 HTTP
behavior remains unchanged; no v2 route is registered. The default uses synthetic
data through httpx.MockTransport, BackendClient and typed BackendDataAccess.
Explicit development mode now supports owner-authenticated loopback GETs;
actual HTTP testing and development-data-to-model transmission require operator
flags. Unauthenticated conversation APIs and production hosts remain blocked.

## Windows commands

From the repository root in PowerShell, Python 3.10+:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m app.chat --mode rules
.\venv\Scripts\python.exe -m app.chat --mode fake
```

Reuse an existing venv if present. No additional infrastructure/dependency or
async pytest plugin is needed. New tests use existing AnyIO with asyncio.
These commands do not print/overwrite `.env`. Some consoles need `chcp 65001`
for Arabic display.

Chat commands: `/catalog`, `/reset`, `/customer 1`, `/customer 2`, `/business 1`,
`/business 2`, `/quit`. Four independent business/customer sessions persist until
reset/process exit. EOF/Ctrl+C exits. Actual replies and safe intent/tool/candidate/
variant/clarification/fallback/source diagnostics are shown. No headers are logged.

Modes:

- `rules`: no model calls.
- `fake`: existing GeminiClient parsing/guard flow with SDK boundary replaced;
  deterministic semantic JSON and speech-act choices, not live quality evidence.
- `gemini`: explicitly enables existing GeminiClient/private local configuration
  and can spend quota. Backend and customer data remain synthetic.

Only when the operator deliberately wants live Gemini:

```powershell
.\venv\Scripts\python.exe -m app.chat --mode gemini
.\venv\Scripts\python.exe -m app.chat.evaluate --mode gemini --allow-live
```

No live mode was run during implementation. Existing `GEMINI_API_KEY`,
`ROUTER_MODELS`, `GENERATOR_MODELS` and timeouts are reused; enter keys privately,
never in shared commands. Missing configuration gets a sanitized error. Model
availability/key permissions remain unverified live.

## Manual scenarios

In a fresh rules/fake session:

1. `عندكم تيشيرت أسود؟` — actual black variants, focused size question.
2. `طب مقاس L بكام؟` — Black/L, 275.00 EGP, recorded stock 4.
3. `عايزة اتنين منه.` — quantity 2, provisional purchase, no order/reservation.
4. `طب غيرت رأيي عايزة الأبيض.` — freshly retrieved White/L, 285.00 EGP,
   stock 8; previous 275.00 must disappear.
5. `/customer 2`, `طب مقاس L بكام؟` — no inherited customer-1 selection.
6. `/reset`, `white tshirt size M price` — 225.00 EGP, untracked availability.
7. `blue tshirt size M price` — exact zero price AND zero stock.
8. `blue tshirt size L price` — inactive variant is not offered.
9. `cap price` — unknown price and untracked inventory, never invented zero.
10. `Can you guarantee delivery tomorrow?` — no unsupported promise.
11. `I have a complaint, my order is late` — requiresReview, no invented action.
12. `/reset`, `3andkom tshirt eswed`, `bekam size L`, `3ayez etneen meno` —
    Franco understanding, Arabic replies, quantity two, Orders disabled.

Batch chat accepts repeated `--message` arguments. Repeatable evaluation:

```powershell
.\venv\Scripts\python.exe -m app.chat.evaluate --mode rules
.\venv\Scripts\python.exe -m app.chat.evaluate --mode fake
```

Evaluation prints JSONL messages, actual replies, diagnostics and checks. Live
evaluation requires live understanding/generation sources, rather than counting
silent rules fallback as live success. Automated checks cover explicit scenario
prices, changed options, quantity, read-only status and review. Humans must rate
understanding fidelity, naturalness, focused clarification, localization and safe
refusal. Passing the harness alone is not a production/factuality certification.

## Architecture and safety

`ChatSession` owns one trusted scope/asyncio lock and serializes its turns. Other
sessions run concurrently. Bounded previous candidate metadata/options/quantity
are scoped hints. Raw historical AI prose is never price/stock authority. Follow-up
products/variants are read again; current changed options replace older choices.
New products/failures clear old selections; ambiguity is not silently collapsed.

`ConversationInterpreter` reuses multilingual NLU/routing for fallback. Gemini
receives current text and bounded prior candidate handles/names/options, never
tenant IDs, tokens, prior prices or stock. It extracts intent, search phrase,
handle, requested options/quantity and language. Strict schemas reject actions/
extra fields; handles map only to scoped candidates. Python builds Inquiry,
controls bounded tools and supplies scope/token. Hard rules, complaints, owner
review and known unsupported questions remain deterministic.
Gemini can additionally raise a review act for a novel complaint; it cannot
clear a review decision made by the deterministic rules. Pure confirmations
cannot become orders, and a decline clears provisional local selections.

RetrievalCoordinator/EvidencePlanner select actual typed evidence. A request-local
planner specialization retains interpreted language/quantity and removes redundant
generic purchase clarification when read-only facts are sufficient. Existing
evidence/authorization safeguards remain authoritative.

The historical `ConversationalResponder` implements EvidenceResponder. It validates the evidence
manifest, compiles mandatory localized acts (variant facts, focused questions,
unknowns, provisional purchase, quantity shortfall, freshness, partial search),
and asks Gemini to choose approved wording per fact ID and conversational tone.
Every act must appear once in order. Extra prose, missing facts, invented IDs or
invalid choices are rejected. Python inserts exact Decimal prices, quantities
and actual options. Arbitrary factual prose is never accepted by a keyword/
numeric scan. This goes beyond Phase 7 opening/spacing: Gemini interprets meaning
and chooses verbalizations for individual conversational/factual acts.

Generation is still a controlled bilingual phrase grammar. Free-form factual
prose is intentionally unavailable; wider approved phrasing can be added safely.
Live conversational quality remains pending acceptance. Product names/options
remain in their original catalog language. Descriptions/attributes cannot create
policy authority. Catalog strings are data, never instructions.

Existing Gemini parsing/retry/model-fallback/cooldown is reused. Understanding has
an 8-second outer cap; standalone retains 20 seconds/12 total Backend calls,
retrieval 5 seconds/8 calls, and reply-provider cap is 8 seconds. Normal product
turns use up to two model stages; hard rules use none. Shared provider health,
schema capability and SDK state are operational only; no shared customer cache.

Orders remain disabled: the seam holds provisional product/variant references,
requested options/quantity, missing/ambiguous selections and confirmation-required
metadata. All references require future revalidation. No order handler/config
switch, checkout, inventory mutation or reservation exists. AiResponse remains
`{intent,reply,requiresReview,orderCandidate:null}`. See the
[Backend handoff](BACKEND_HANDOFF.md) for fresh authorization/price/stock,
idempotency, owner approval and Backend state-machine responsibilities.

HistoryService remains available for bounded scoped Backend history. Local chat
uses trusted live session selections and disables unnecessary history reads; an
empty synthetic history is not a production conversation store. Durable/context
reconciliation, authenticated v2 ingress, business aggregation/policies and actual
Orders await external contracts.

## Verification and readiness

New conversation tests cover Arabic/English/Franco, Arabic dynamic options,
changed variants, fresh stock/price, zero/untracked/null/inactive states, similar
names, quantity shortfalls, reset/new nouns, auth/scope errors, timeout, concurrency,
adversarial model output, retries and CLI/evaluation. Existing Phase 1–8 suites
cover partial catalogs, pagination, uncertain history, injection, token isolation,
deadlines, grounding and v1 compatibility.

Ready for local demonstration and offline integration tests. Live Gemini and
Backend integration are unverified. Rules vocabulary cannot understand every
dialect/synonym/implicit reference; uncertainty clarifies rather than invents.
Fresh reads are observations, not future-stock guarantees. Production requires
authenticated ingress, durable scoped/versioned context, agreed dispatcher/
history/aggregate contracts, live-model acceptance and operational load checks.
