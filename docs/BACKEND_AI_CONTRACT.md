# Brandora Backend–AI contract: Phase 1 proposal

Current runnable conversational application: [local guide](LOCAL_CHATBOT.md).
For verified Backend main (commit 83a65e9) and the actionable dependency checklist,
use [Backend handoff](BACKEND_HANDOFF.md). The phase notes below remain an audit
trail; proposed routes, customer/history authorization, aggregate shape and Orders
must not be confused with implemented Backend APIs. Local conversational generation
now uses guarded speech acts; the Phase 7 presentation-only provider remains a
compatible baseline, not the only responder. The disabled order seam additionally
retains requested options, missing selections and confirmation-required metadata.

Status: proposed Backend contract with offline fixtures and a standalone typed
data layer. Phase 2 added request-local execution results to the legacy AI flow;
Phases 3–8 do not connect data access, history preparation, retrieval policy,
evidence planning or grounded presentation to the live flow. Phase 8 assembles
them only through an internal standalone coordinator for offline testing.
`/internal/ai/data` and the
versioned AI route below are **proposed, not implemented or enabled**. No token
verification, Backend adapter, variant-aware planner, or new orchestration is
implemented by Phase 1. Existing `/v1/ai/respond` behavior remains unchanged.

The product fields, effective-price formula, variant inventory ownership, and
EGP policy below are agreed inputs supplied by the project owner. They were not
verified against a live Backend or NestJS source in this workspace. The old
[integration guide](INTEGRATION_GUIDE.md) describes legacy behavior and does not
establish availability of Orders or knowledge APIs.

## Proposed Backend → AI transport

`POST /v2/ai/respond`, JSON body:

```json
{
  "schemaVersion": "2.0",
  "businessId": "10000000-0000-4000-8000-000000000001",
  "customerId": "20000000-0000-4000-8000-000000000001",
  "conversationId": "30000000-0000-4000-8000-000000000001",
  "messageId": "60000000-0000-4000-8000-000000000005",
  "message": {"text": "عايزة اتنين منه"}
}
```

All body keys and the route/version marker above are a proposal. Reuse the
existing nonempty, trimmed, maximum-2000-character message constraint. UUIDs use
canonical hyphenated syntax, case-insensitively, without client version/variant
restrictions; actual Backend acceptance remains its responsibility. The body
does not carry a complete catalog, orders, customer profile, or policies.

Proposed headers: `X-Internal-Token: <Backend-to-AI service credential>` and
`X-AI-Context: <signed opaque business-scoped context>`. Keep service identity
separate from request scope. Authenticate even requests resolved by hard rules.
The existing v1 service token is optional configuration; this is not sufficient
evidence that the future production route is securely configured.

Signing format, issuer, audience, allowed algorithms, key distribution/rotation,
expiry, clock handling, replay policy, and revocation are **unresolved**. No
signature algorithm, JWT claim schema, decoding-only validation, introspection
endpoint, or trusted-header bypass is prescribed or implemented here. Activation
is blocked until the trust/verification contract is agreed and tested. Candidate
scope semantics must bind business, customer, conversation, and current message;
their encoded names and whether Python verifies claims locally remain undecided.

Body IDs are selectors to check against authenticated scope, not authorization.
Backend must enforce conversation ownership within the customer and business,
current-message membership/sender, product business, and variant parent/business.
Python must reject known mismatches and never use a body or model-selected ID to
expand authorization. Backend must enforce scope even if Python errs. Do not put
credentials into prompts, traces, error text, fixtures with real data, or logs.
Do not retain tokens or customer plans on shared clients. No cross-customer
history or cached evidence may leak, including customers within one business.

## AI → Backend tools

Proposed endpoint: `POST /internal/ai/data`. Existing standalone BackendClient
headers: `Authorization: Bearer <AI-to-Backend service credential>` and
`X-AI-Context: <per-call context token>`. Credential provisioning and whether the
two service directions use distinct credentials must be agreed; do not assume
they are interchangeable. Origin comes from deployment configuration, never a
customer or Gemini. Client timeouts, redirect blocking, and sanitized errors stay.

Request envelope:

```json
{"tool":"get_products","arguments":{"limit":20,"offset":0}}
```

Success envelope (full envelope returned by BackendClient):

```json
{
  "tool": "get_products",
  "data": {
    "items": [],
    "pagination": {
      "limit":20,"offset":0,"totalCount":0,"hasMore":false,"nextOffset":null
    }
  }
}
```

Only these tools and argument keys are accepted:

| Tool / Python method | Wire arguments | Proposed `data` |
|---|---|---|
| `get_products(limit, offset)` | `limit`, `offset` | `items: CatalogItem[]`, `pagination` |
| `get_product_details(product_id)` | `productId` | CatalogItem object directly |
| `get_product_variants(product_id, limit, offset)` | `productId`, `limit`, `offset` | `items: ProductVariant[]`, `pagination` |
| `get_variant_details(product_id, variant_id)` | `productId`, `variantId` | ProductVariant object directly |
| `get_conversation_history(conversation_id, limit, offset)` | `conversationId`, `limit`, `offset` | `items: Message[]`, `pagination` |
| `get_business_info()` | none | `business: object` |

Every method also requires keyword-only `context_token`. `call_tool` takes the
camelCase wire keys directly. `businessId` is not a tool argument: authorization
comes from context. The confirmed ProductsService.get() convention returns a
product directly. The proposed internal envelope therefore uses
`{"tool":"get_product_details","data":<CatalogItem>}` and, consistently,
`{"tool":"get_variant_details","data":<ProductVariant>}` without extra
`data.product` or `data.variant` wrappers. The current client checks `data` is an
object; it does not validate domain fields. Passing transport tests do not prove
domain validation.

### Business-info aggregation is separate

`get_business_info` aggregates multiple services and does not inherit the
single-product detail convention. Its illustrative Phase 1 envelope remains
`{"tool":"get_business_info","data":{"business":{"id":"...","name":"..."}}}`.
This minimal aggregation fixture is a proposal, not confirmation of the full
Backend DTO. Exact settings, working-hours, contact, optional-section/nullability,
and partial-service-failure shapes still need agreement. No knowledge API is
assumed. A direct detail convention must not silently flatten this aggregate.

No search/filter tool, arbitrary URL, Orders API, reservation, mutation, WhatsApp
action, or unavailable business-knowledge API is allowed. Python selects and
executes tools under bounded retrieval policy; Gemini classifies/extracts only.

## CatalogItem and ProductVariant

CatalogItem fields: `id`, `businessId`, `name`, `description`, `basePrice`,
`options`, `attributes`, `isActive`, `isSellable`, `variants`, `variantsPagination`.
No parent inventory fields are introduced. ProductVariant fields: `id`,
`businessId`, `catalogItemId`, `optionValues`, `unitPrice`, `effectivePrice`,
`trackInventory`, `stockQuantity`, `isActive`.

Backend computes `effectivePrice = variant.unitPrice ?? product.basePrice`.
All non-null price fields follow Backend Decimal(12,2): decimal strings with
at most 10 integer digits and exactly two fractional digits, maximum
`9999999999.99`. Null remains unknown; `0.00` is a valid explicit price.
Python must use the supplied `effectivePrice`, not recompute or substitute a
price when it is absent. The fixture audit checks example arithmetic only; it is
not a production pricing engine. Explicit `0.00` is not null. All businesses use
EGP by agreed application policy; **no database or response currency field is
asserted to exist**. Use Decimal for future calculations, not binary float.

The fixture represents `options` as a name-to-values map and `optionValues` as a
name-to-selected-value map. Exact DTO shapes, attribute types, nullability, list
projections, and embedded-variant pagination remain to be confirmed. The keys are
agreed; nested option representations and the business aggregate remain proposals.

Inventory belongs exclusively to a variant:

| Evidence | Future response requirement |
|---|---|
| Active product + active variant, tracked stock > 0 | Recorded current quantity; no reservation or future guarantee |
| Tracked stock = 0 | No recorded stock remains, even with `isSellable=true` |
| `trackInventory=false`, `stockQuantity=null` | Quantity and availability unknown; neither zero nor guaranteed |
| Inactive parent or variant | Never offer as available to purchase |
| Null effective price | Say price unavailable; do not fabricate a price |
| Product options contain a value | Does not prove every combination exists |

Different color/size variants may have different prices and stock. Never combine
one variant's price with another's stock. `isSellable` means the product is
active and has at least one active variant with a non-null effective price
(including `0.00`). It is not an inventory guarantee and says nothing about the
requested variant's stock. False also does not prove an otherwise existing
product is absent. Complete fixtures follow this rule; partial embedded variant
pages cannot be used to recompute it. Tracked inventory requires an integer
quantity >= 0; untracked inventory requires null. Missing stock, null tracked
stock, and non-null untracked stock are INVALID evidence, never zero, positive,
or an ordinary unknown tracked-stock state. No inference of a
Cartesian product from options or independent color/size lists is permitted.

## Pagination and incomplete information

`limit` is a strict integer 1..100 (default 20). `offset` is a strict integer
0..9007199254740991 (default 0). Booleans, floats, and numeric strings are invalid.
Response `limit`/`offset` echo the request. `totalCount` is a nonnegative safe
integer; `hasMore` is a boolean; `nextOffset` is a safe integer strictly greater
than offset when `hasMore=true`, otherwise null. `items` is a list of objects no
larger than limit. All pagination fields are required by the existing client.

Counts, rows, and hasMore can observe separate database reads. A short or empty
page can coexist with a larger count; rows may outlive the counted snapshot.
Do not reject these solely for inconsistency, require full pages, or derive
hasMore/nextOffset from totalCount. Follow the supplied safe continuation with
future page/call/time/size budgets and deduplication. Offset pagination under
writes does not guarantee a complete snapshot, even after reaching a terminal
page. Embedded `variantsPagination` is a separate coverage boundary; current
BackendClient does not validate it.

Distinguish confirmed empty, partial, unavailable, and malformed data. No match
in bounded retrieval is not proof of global absence or the globally cheapest
price. No row-level missing field should acquire a factual default. Missing
policies mean unknown, not free delivery, cash accepted, or a return window.
Business-info fixture uses only `id` and `name`; settings/hours/contact/policy
coverage is unresolved, not an assumed new API.

## Conversation history

Rows use the keys already accepted by `ConversationMessage`: `id`, `senderType`
(`CUSTOMER`, `AI`, `OWNER`), `content`, `messageType`, `createdAt`. No extra Backend
history row fields are invented. Envelopes/pagination are proposed.

Newest-first retrieval is a fixture assumption requiring Backend confirmation.
Future normalization parses timestamps, keeps sender roles, excludes the current
message by message ID, and returns bounded chronological prior messages. Equal
text with different IDs must remain distinct. Owner/AI historical text is not
current product, stock, or policy authority. Missing/truncated history cannot
justify a product reference or an ambiguous confirmation. Arabic, English, and
Franco-Arabic examples are included.

History fixture `complete` and `expectedPriorIds` are **test metadata outside
Backend rows**, not new wire fields. Stable ordering/ties, timezone handling,
null timestamps, current-message inclusion, and before-current boundaries are
unresolved. The current tool has no `beforeMessageId` argument. Do not invent one.
The legacy context still uses phrase-based state, loses OWNER versus AI in its
Turn representation, and can remove same-text current-looking messages. Phase 1
does not fix those limitations or claim ID-only normalization is implemented.

## Errors, authorization, and unsupported work

Existing client behavior: 401/403 -> sanitized authentication error; timeout ->
sanitized timeout error; other non-2xx (including redirects) -> sanitized client
error; malformed JSON/envelope/pagination -> response error. No retries or
redirect following. Backend error body is not surfaced. Proposed error semantics:
400 invalid tool/arguments, 401 invalid credential/context, 403 forbidden scope,
404 missing accessible entity (or concealed forbidden entity), 429 throttled,
5xx temporarily unavailable. Exact statuses, error body, 404 concealment policy,
and not-found detail shape are unresolved; no error JSON shape is assumed.

Future behavior: fail closed on scope/auth errors, never switch tenants or use
stale cross-request data. For transient failure, say current facts cannot be
verified; retain escalation where appropriate and clarify missing information.
Do not silently return fabricated facts or reinterpret unavailable as empty.
Tests of BackendClient exceptions are not end-to-end fallback implementation.

## Response compatibility and Orders boundary

Keep `AiResponse` exactly: `intent`, `reply`, `requiresReview`, `orderCandidate`.
Proposed read-only responses set `orderCandidate=null` and never use
`CONFIRMED_ORDER`; that intent requires a candidate under the existing schema.
`PURCHASE_INTENT` can acknowledge interest without implying a transaction. Owner
review flags do not establish that notification, cancellation, or refund occurred.

Orders are unimplemented. Future agreement: AI identifies purchase intent,
product, variant, requested quantity; Backend validates price/stock and creates
orders; business owner approves; stock deduction uses existing InventoryService
transaction methods on approval; eventual cancellation lifecycle restores stock.
No lifecycle, Orders endpoint/model, inventory write, or order confirmation is
introduced here. Legacy order-related behavior stays unchanged on v1 and is not
activated on a new path; there is no new path in Phase 1.

## Offline evidence and coverage boundaries

Fixtures: [backend_contract_fixtures.py](../tests/backend_contract_fixtures.py).
All data is synthetic. `SCENARIOS` is a future acceptance backlog, not executable
pipeline coverage. No skipped/failing placeholder tests are used.

| Evidence | What passing establishes |
|---|---|
| `test_phase1_fixture_contract.py` | Fixture field/price/relationship consistency, six mock transport examples, client errors and per-call token separation, response-schema compatibility |
| `test_phase1_behavior_regression.py` | Current hard rules, routing/generation fallbacks, guard, language/matching, ambiguity, business facts, missing prices/policies, review flags, request-local outputs, limited injection defenses, current history behavior |
| Existing `test_backend_client.py` | Client argument/envelope validation, UUID syntax, concurrent-write-compatible pagination, timeouts, redirects, token isolation |
| Existing order/customer-service/handoff suites | Legacy behavior and schema safeguards remain unchanged |

Scripted Gemini tests prove deterministic enforcement for supplied model outputs,
not live model resistance to prompt injection. Description attacks currently do
not enter the router's catalog hint; history/customer text does. Structured
provenance, semantic grounding, tool authorization, signed-token verification,
variant planning, retrieval budgets, incomplete-catalog wording, and future
history normalization are **not implemented or proven** by these tests.

Future scenario IDs explicitly cover positive/zero/untracked stock, inactive
parent/variant, missing/zero price, missing option combination, partial catalog
and variants, Backend failure, business/customer isolation, Arabic/Franco
references, ambiguous confirmations, missing/incomplete history, repeated text,
missing policy, and injections in customer/history/description fields.

## Decisions required before integration

1. Signed-context verification and provisioning; identity binding, expiry/replay,
   key rotation, and authorization/error behavior.
2. Final v2 request shape and business aggregation, null/not-found
   representation, options/optionValues DTOs, required fields and projections.
3. Inventory-null cases and effectivePrice consistency;
   expected behavior if a Backend record contradicts the agreed formula.
4. Business information coverage without an unavailable knowledge API.
5. History sorting, ties, missing dates, and a safe current-message boundary.
6. Embedded variant paging, catalog ordering under writes, retrieval budgets,
   and large-catalog discovery with only limit/offset (no search argument).

## Phase 2 execution ownership

`Orchestrator.respond` now returns an internal `ExecutionResult` with customer,
business and message identifiers, context, optional routing result, plan, response,
and trace. No conversation ID exists in v1, so none is synthesized. These are
payload identifiers, not verified security claims. A direct hard-rule decline has
no routing result. The orchestrator retains no last plan or execution result.
Request models and provider routing results are detached before mutable processing.
HTTP v1 and dev responses still expose only their existing body/trace shapes.

The result envelope is frozen; nested state is mutable and owned by its caller.
Gemini SDK client, schema capability, model health/cooldowns and counters remain
shared operational state. Health errors retain categories rather than raw
validation/SDK messages that could contain customer text. Settings contain service
configuration, not customer request state. Existing history semantics and the
future authorization/adapter boundaries remain unchanged.

Next work requires review. Do not enable or wire the Backend adapter in Phase 2.
Run tests offline with `AI_PROVIDER=rules` and `ENABLE_DEV_ENDPOINTS=false`.

## Phase 3 standalone typed data layer

`app/schemas/backend.py` defines Product, ProductVariant, Page/Pagination,
BusinessInformation, provisional HistoryMessage, ExpectedScope and typed
ToolEnvelope/RetrievalOutcome models. `app/data/backend.py` injects the existing
BackendClient and exposes its six methods. It is not imported by the Orchestrator,
has no application startup wiring or route, and performs one client call per
operation. Transport authentication, HTTP handling, redirects and timeouts remain
BackendClient responsibilities; no search, retry, cache or retrieval loop is added.

Each call receives `scope` and `context_token` separately. ExpectedScope is a
caller-established business ID with optional customer/conversation IDs, not a
verified token. History requires both customer and matching conversation scope
before network access. Product details check the returned ID against the requested
ID. Products and all embedded variants check business membership; variants also
check catalogItemId against the requested or enclosing product. Variant details
check their own requested ID. Business aggregate checks business.id. Any mismatch
discards the entire response, with no second tenant lookup or partial exposure.
Selectors originate from trusted caller code; this layer does not authorize
model-generated IDs. History rows have no documented ownership fields, so Python
cannot independently attest their business/customer ownership; Backend scope
authorization remains mandatory. Standalone variant data also cannot attest its
parent's active state: a future planner must obtain and check the parent before
offering anything. An AVAILABLE outcome means evidence retrieved, not stock
availability or purchase eligibility. Inactive records remain explicitly flagged.

Required product/variant fields do not get factual defaults. Missing required
data yields INVALID; explicit null price remains unknown. Price strings must be
nonnegative Decimal(12,2) strings with 1..10 integer digits and exactly two
fractional digits. Oversized strings (including more than 10 leading integer
digits), excess scale, floats, and numeric coercions are rejected. They become
exact Decimal values, serialize as decimal strings, and never use float or
quantization. The layer never fills effectivePrice from unitPrice/basePrice.
As an explicit safety policy pending Backend error-contract agreement, conflicting
non-null effectivePrice is rejected when the supplied unitPrice or enclosing
product basePrice disproves the agreed formula. A null effectivePrice is retained
as unknown even if inputs could derive a number. EGP is an application constant,
not a synthesized Backend field. No price rounding or inventory mutation occurs.

Inventory flags are strict booleans. For tracked inventory quantities must be
nonnegative JavaScript-safe integers; untracked inventory requires null.
Negative, float, bool, string, missing, or null tracked quantities are INVALID.
Non-null untracked quantities are contradictory and INVALID under the confirmed
Backend contract. No ordinary UNKNOWN tracked inventory state is exposed; invalid
evidence yields no typed envelope or customer-facing fact. Valid quantities are
recorded observations, never reservations. Options and
optionValues follow only the Phase 1 map representation; alternatives are rejected
until their DTO is agreed. No option combinations are generated. Product inventory
fields and other unknown extensions are ignored, not used as variant evidence.

Typed pagination models carry both outer and embedded variant metadata. They
validate types, safe bounds, page size and continuation progress, without requiring
item counts, totals and hasMore to share a database snapshot. Outer request echoes
remain checked by BackendClient. PARTIAL means hasMore on the outer or an embedded
variant page. EMPTY means an empty terminal response page, not global absence.
AVAILABLE/EMPTY/PARTIAL carry a full typed tool/data envelope; all failure outcomes
carry no evidence and only a fixed safe error category:

| Outcome | Meaning |
|---|---|
| INVALID | Malformed/missing data, invalid arguments, invalid JSON or response |
| UNAVAILABLE | Timeout or other Backend failure; distinct timeout/backend_error categories |
| AUTHORIZATION_FAILED | BackendClient rejected authentication/authorization (401/403) |
| SCOPE_MISMATCH | Returned identity/relationship mismatch or missing/mismatched history scope |

The current client does not expose structured status codes for other HTTP errors;
404, 429 and 5xx are backend_error here, not assumed empty or not-found facts.
No null detail representation is invented: non-object/null data is invalid under
the existing envelope. Backend error bodies and validation errors are neither
returned nor retained by the layer. Unexpected programming errors are not swallowed.

BusinessInformation currently accepts only the provisional aggregate
`data.business.{id,name}`; it ignores other fields rather than inventing settings,
contact or policy defaults. Those ignored sections are not evidence for future
planning until modeled. HistoryMessage accepts documented sender roles and optional
id/content/messageType/createdAt strings or null. Raw order/timestamps are preserved;
missing messageType stays unknown rather than defaulting to TEXT. No sorting,
current-message exclusion, reference resolution or history retrieval policy exists
in this phase.

Data-access instances retain only their injected client, never scope, tokens,
responses or outcomes. Responses are deep-copied before conversion so injected
fakes cannot create shared nested customer state. Frozen model fields do not imply
deep immutability: nested collections belong to the returned request-local result.
`test_backend_data.py` tests all operations with synthetic fixtures, scope checks,
price/inventory correctness, pagination, errors, and overlapping business/customer
calls, without live services. Phase 3 adds no production AI integration.

## Phase 4 standalone history preparation

`app/data/history.py` adds HistoryService over injected BackendDataAccess, with
explicit per-call ExpectedScope, context_token, conversation ID, current message
ID and current text. No production Orchestrator/context/provider/route is changed.
No new tool argument, product lookup, Orders action, token verification or global
history cache is introduced. The instance holds only data access, frozen limits
and a clock. Returned frozen records/tuples belong to that execution; repr omits
message content and reference details, and diagnostics use fixed issue codes.

HistoryLimits bounds pages, examined rows, content characters and elapsed seconds,
with a Backend-compatible page size. Defaults are 3 pages, 60 rows, 12,000 content
characters, 5 seconds and page size 20. Requested limits shrink to the remaining
row budget. Duplicate/current/later rows count toward traversal budgets so they
cannot bypass bounds. Oversized content is not truncated into a different message:
the service stops and marks partial. Async calls are cancelled at the remaining
deadline; bounded synchronous processing checks the same deadline cooperatively.
This is not an HTTP response-byte limit or a preemptive CPU watchdog. Pagination
follows supplied continuation offsets, not inferred totals, and never loops past
the page cap. Empty nonterminal pages are also bounded.

PreparedHistory.coverage describes retrieval traversal:

- COMPLETE: a terminal page was observed within the budgets and no identity
  loss/conflict was detected. This is not proof of a complete database snapshot,
  reliable newest-first API ordering, or a before-current boundary.
- PARTIAL: page/row/character/time cap, conflicting/missing identities, or a later
  transient/invalid-data failure. Earlier validated evidence may remain.
- UNAVAILABLE: no usable retrieval after a Backend failure, or any authorization
  or scope failure. Authorization/scope failure discards all accumulated evidence,
  even after successful earlier pages; no tenant fallback occurs.

Failure preserves the typed layer's safe status, not Backend bodies or exceptions.
An empty terminal history differs from an unavailable API. Stable record identity
is a nonempty printable string of at most 128 characters without edge whitespace;
opaque string IDs remain supported because the documented schema does not require
UUID-only message IDs. Canonical UUID identities compare case-insensitively, while
the first original message ID is retained. Identical text never deduplicates IDs.
Exact duplicate IDs collapse; conflicting records for one ID are all removed and
marked partial. A conflicting current ID cannot establish a timestamp boundary.
Missing/unusable IDs are excluded, not synthesized. Invalid current ID fails
before network access. This identity policy is provisional pending the history DTO.

Normalization preserves ID, role (CUSTOMER/AI/OWNER), original content/type/date
and an aware UTC timestamp where parseable. ISO date-times with explicit offset or
Z and up to six fractional digits are parsed without rounding. Naive/date-only,
invalid dates, higher precision and unknown `-00:00` offsets remain undated.
Unknown/non-TEXT message types are excluded from text context with an issue code;
the service never assumes a missing type is TEXT.

Current-message exclusion uses ID only. The current message must be observed as
a CUSTOMER row with an unambiguous timestamp before it can supply even a
provisional timestamp boundary. Without it, other rows go to uncertain_messages
in first-seen retrieval order; no chronology is invented from page position.
With it, strictly earlier timestamp candidates go to messages sorted by UTC
timestamp then stable ID. Timestamp ties use ID only for deterministic presentation
and are explicitly flagged; this tie-break is not causal chronology. Equal-current
or undated rows go to uncertain_messages. Strictly later rows are excluded and
flagged. The current row itself is always excluded, including when undated.

**Chronology remains provisional.** chronology_uncertain is true whenever any
records were observed or retrieval was incomplete. Timestamp comparisons alone do
not prove logical order, clock correctness or a stable snapshot. messages therefore
contains earlier-timestamp candidates, not an attested before-current history.
No future planner may treat COMPLETE as a guarantee of prior context. An empty
terminal response has nothing to order but still reports current_boundary_unknown.
Backend sorting, tie-breaking, timestamp quality and a verified before-current
boundary remain unresolved; no unsupported beforeMessageId argument is added.

ReferenceHint reuses existing extract_entities, normalize and confirmation
utilities. It records source message/role, product terms, color/size and requested
quantity, plus UUID references only when explicitly labeled productId/variantId in
message text. Multiple different IDs for one label remain unresolved. IDs are never
invented from product names. All hints require Backend revalidation and contain no
authoritative price/stock/availability. They come only from earlier timestamp
candidates and remain uncertain with their source context. Customer, AI and owner
content is untrusted, including labeled identifiers and embedded instructions.

The latest timestamp group's outbound question IDs are clarification candidates,
not a persisted pending action or an assumption that a transaction is awaiting
confirmation. Bare confirmations, quantity-only replies and explicit references
such as منه, نفس المقاس and same size mark followup_requires_clarification.
This flag does not select a product, execute a tool, confirm/change an order or
authorize any action. No Gemini prompt or free-form content executes in this layer.

`tests/test_history_service.py` exercises traversal limits, normalization, identity
handling, provisional boundary flags, reference hints, injection as data, failures,
and overlapping customer/business calls using fakes and MockTransport. Passing
tests establish Python behavior for supplied records, not a new Backend ordering,
ownership or timestamp guarantee. Phase 4 stops before production integration.

## Phase 5 controlled retrieval policy

`app/data/retrieval.py` adds a standalone RetrievalCoordinator with a typed
RetrievalQuery and validated RetrievalLimits. It uses BackendDataAccess, existing
rule classification/entity extraction/product matching, and optionally consumes
PreparedHistory. It is not imported by production execution, has no Gemini calls,
and produces evidence rather than customer-facing replies or plans. History
preparation and policy share the same contextual-follow-up cue utility.

### Deterministic operation selection

| Inquiry | Policy |
|---|---|
| Pure greeting/thanks without explicit selectors | SKIP, zero calls |
| Ambiguous follow-up without usable prepared references | CLARIFY, no invented selection or order confirmation |
| Product discovery | Bounded get_products pages, local matching |
| One locally plausible named product | get_product_details to revalidate; search coverage remains explicit |
| Explicit product selector | get_product_details without catalog download |
| Price/options/availability for one active candidate | Use actual embedded variants; get_product_variants only for incomplete embedded coverage |
| Explicit variant selector or one matching requested option record | get_variant_details, with parent revalidation first |
| Multiple product candidates | Preserve ambiguity; no fan-out variant fetches |
| Business identity/name | get_business_info only |
| Order status/change/cancellation, payment dispute, returns/delivery/payment policies, unsupported operations | No unavailable tool; UNSUPPORTED or clarification |

The current BusinessInformation aggregate only models identity/name. Hours,
contact, delivery, payment and policy answers cannot be sourced from ignored or
unmodeled fields, so policy does not fetch an aggregate merely to imply those
facts are supported. Extend that policy only when the aggregate DTO is agreed.
Purchase-interest classification may retrieve read-only product evidence but marks
clarification; it never constructs an order candidate, confirms or performs an
action. Escalation/complaint intents do not cause product retrieval here; preserving
customer-service response behavior remains the future planner's responsibility.

RetrievalQuery may carry explicit product IDs and product/variant pairs from caller
code. They are candidate selectors, never authority. No IDs, scopes, credentials,
HTTP URLs or tool names are extracted from descriptions or executed from text.
Historical explicitly labeled IDs can be candidates only for a current contextual
follow-up. Each is revalidated through details under the unchanged ExpectedScope.
Prepared history must have an explicitly matching history_scope including customer
and conversation; this binding is a trusted-caller responsibility because the
existing PreparedHistory has no signed identity/current-turn attestation. Missing
or cross-customer binding fails closed. Supplied history authorization/scope failure
stops protected retrieval even for a self-contained question. History content never
chooses current facts. Chronology remains provisional and all contextual follow-ups
require clarification; this phase never upgrades them into confirmations.

The neutral matching projection reuses the tested NLU token scorer, material and
alias matching. It supplies no price or parent inventory for ranking, applies no
product base-price budget filter, and is never returned as business evidence.
Typed Product and ProductVariant records remain the only factual evidence. Arabic,
English and supported Franco-Arabic terms are retained; narrow Franco inquiry cues
permit bounded discovery when empty-catalog rule classification cannot identify a
product yet. Generic catalog wording does not trigger unnecessary product details.

Variants are never generated from the Cartesian product of options. Only active
actual records under an active parent become variant candidates; recorded zero
and untracked inventory remain distinct and never imply guaranteed availability.
Null effectivePrice stays unknown. Requested colors/sizes filter actual records
using existing normalization; one match can trigger detail revalidation. A detail
whose active state or options changed is not silently substituted for the requested
combination. This is evidence selection, not pricing calculations, final offer
eligibility, variant-aware response planning, or order handling. A selection that
cannot be verified remains empty/partial with fixed issue codes.

### Budgets, evidence and coverage

Defaults per execution: 8 calls, 3 product-list pages, 100 admitted records, 4 total
product/variant detail lookups, 5 seconds elapsed, and page size 10. Counts are
strict positive integers, page size <=100, deadline positive and finite. Every
network attempt consumes a call and, where applicable, a page/detail budget.
Identical (method, arguments) requests are deduplicated inside one execution only;
cache hits consume no additional Backend calls or records. No per-customer cache,
token, scope or evidence is retained on the shared coordinator.

Record admission counts products, embedded variants, standalone variants and the
business summary. A response that exceeds the remaining record budget is not
exposed as evidence and ends retrieval conservatively. This budget limits policy
inspection/admission, not the preceding mandatory typed validation or raw HTTP
bytes. The contract cannot cap embedded variants through get_products arguments;
Backend response-size/projection guarantees remain a dependency. Outer list limits
shrink to remaining records. Variant paging is bounded by total calls/records/time,
including empty nonterminal pages. There is no unbounded full-catalog scan.

The remaining deadline bounds each await; processing is bounded and checked
cooperatively. This is not a preemptive CPU watchdog. Calls execute serially in a
request-local execution object, so scope is fixed throughout. Returned outcomes
are copied so injected fakes cannot share nested mutable customer evidence.

RetrievalResult contains the decision, aggregate status, optional underlying safe
failure, typed full-envelope evidence, active product/variant candidates,
clarification flag, coverage, fixed issue codes, and budget counters. Repr omits
protected evidence and identifiers. Inactive records can remain in typed evidence
with flags intact but are not active candidates. No generated reply asserts facts.

Catalog and per-product variant coverage distinguish NOT_SEARCHED, PARTIAL,
EXHAUSTED and UNAVAILABLE. EXHAUSTED means traversal from the start reached a
terminal page; it is **not** a stable database snapshot or global completeness
guarantee under concurrent writes. Details alone never prove catalog or variant
list completeness. Discovery stops after useful candidates, preserving PARTIAL
when more pages exist. Therefore one candidate need not be globally unique. Empty
terminal results/no matches are distinct from a bounded partial search via status,
coverage and actual envelopes. No global absence, cheapest-product, stock guarantee
or missing-combination claim is generated from a partial search.

Timeout/invalid/missing detail ends further retrieval conservatively and preserves
only earlier verified evidence as PARTIAL, with a distinct underlying failure.
No retry, cross-tenant fallback or invented empty response is introduced. Any
authentication or scope failure clears candidates, variants, envelopes and the
execution cache, then stops. Budget limits return explicit partial issues instead
of bypassing data validation. The typed Backend layer remains responsible for
business/product/variant relationship validation and safe transport outcomes.

### Backend dependencies and test boundary

There is no Backend search API in the six-tool contract. Local matching has bounded
recall: a matching product outside the visited pages can be missed. Large catalogs
would benefit from a separately agreed business-scoped search endpoint with
documented query/filter semantics, stable pagination and authorization. No such
endpoint or undocumented query argument is implemented or assumed here.

Other dependencies remain: actual internal endpoint implementation, signed-scope
verification at a future route, history identity/order/before-current guarantees,
final business-info/options DTOs, response-size bounds, not-found semantics and
concurrent-write pagination behavior. `tests/test_retrieval_policy.py` checks actual
tool counts, offsets, request-local scopes/tokens, budgets/deduplication, multilingual
matching, ambiguity, actual variants/inventory, failures, injection as data and
overlapping customers/businesses using fakes and MockTransport. It proves Python
policy for synthetic evidence, not a live Backend or Gemini guarantee. Phase 5
stops before variant-aware planning and production orchestration integration.

## Phase 6 standalone variant-aware evidence planning

`app/pipeline/evidence_planner.py` adds a stateless EvidencePlanner. It accepts a
current string or validated PlanningInquiry/RetrievalQuery, a RetrievalResult, and
optional PreparedHistory. It executes no Backend or Gemini calls, changes no
authenticated scope, and is not wired to v1 or a v2 route. Legacy Planner, Guard,
Orchestrator, schemas and response behavior remain unchanged.

### Plan structures and provenance

EvidencePlan separates ProductFact and VariantFact records, CandidateReference
selectors, matching/selected variant IDs, missing facts, ambiguity codes, coverage,
confidence limitations, clarification/review flags and GroundedStatement material.
No numeric certainty is invented. Requested quantity is labeled as a current
customer request, never a reserved amount or a Backend inventory fact. All
collections/facts are request-local frozen records with immutable value tuples.
No customer-specific state is retained on the shared planner.

Only recognized typed tool/data envelopes introduce Backend facts. Retrieval
candidates alone, historical text, and model output do not. The planner validates
typed records again through their JSON representation to reject mutated invalid
evidence without correcting facts. Product/variant business and parent identity
conflicts fail closed; a variant without product evidence cannot establish parent
activity or support an offer. Mixed businesses cannot be combined into one plan.
The upstream scoped data layer remains the authorization boundary: this planner
does not independently authenticate a RetrievalResult or decode context tokens.

Every factual group carries EvidenceSource(tool, envelope_index, path), including
the enclosing product source for a variant. This lets a future grounding step
locate name/activity/price/quantity fields at their exact envelope record. Later
whole-record observations replace earlier ones; fields from different observations
are not merged. Price and inventory in one draft statement always come from the
same variant observation. EGP has a separate application_policy source; it is
never represented as an existing database currency field. Product basePrice is
identified separately and is never substituted for null effectivePrice.

Descriptions and arbitrary attributes are not included in plan facts or draft
material. Backend names/option labels/values remain data labels, never tool
instructions; later Gemini/Guard work must continue treating free-form fields as
untrusted text. Historical messages do not establish current prices, stock,
availability or policies. Reference IDs are recorded as provisional and marked
revalidated only when current Backend evidence supports the same identity/parent.
Even a revalidated ID does not resolve uncertain chronology or a bare confirmation.

### Dynamic option keys

The Backend permits business-defined keys. The shared pure matcher in
`app/data/options.py` reads Product.options and actual ProductVariant.optionValues.
Phase 5 now delegates to it; this is a focused compatibility improvement, not a
retrieval rewrite. Existing tool selection/budgets/scope checks remain intact.

- Case-insensitive/normalized keys preserve the original Backend key and value
  in facts. Known color/colour/لون and size/مقاس families reuse existing NLU value
  normalization. Multiple plausible semantic keys remain ambiguous.
- Material, Configuration and arbitrary other keys use exact normalized values,
  without invented translation or fuzzy key aliases. A value mentioned in the
  message is assigned only when its key is unambiguous or explicitly labeled.
  Comma-separated `Key: Value` labels and PlanningInquiry.option_values support
  explicit selections; these are local customer requests, not new tool arguments.
- Unsupported keys/values and conflicting requests remain unresolved. A bare
  value shared by multiple keys is not applied to both automatically. A product
  with option keys but no resolved selection requires clarification even if only
  one record was retrieved.
- Variant keys must agree with declared keys after normalization and values must
  belong to the corresponding declared choices. Missing/ambiguous metadata is
  incomplete evidence, not proof that a requested combination is absent. Whether
  partial optionValues maps are valid Backend projections remains a DTO question.
- Only actual variant records establish combinations. No Cartesian product,
  missing variant ID, synthetic stock, or inferred price is generated. Default
  variants with empty option maps work when the parent declares no options.

Standalone retrieval uses the same matcher for capitalized, Arabic and arbitrary
keys, so a valid dynamic-option request is not lost before planning. Requests with
unsupported dynamic values do not silently select some other variant. Known
existing fixed-key matching behavior remains covered by the original tests.

### Safe facts, coverage and response material

Resolutions distinguish single/multiple variants, multiple products, inactive
records, missing details, exhausted no-match versus partial no-verified-match,
unsupported operations, invalid/unavailable data and authorization/scope rejection.
Incomplete metadata is not an exhausted negative. A single record found during a
partial catalog/variant search is not promoted to globally unique. EXHAUSTED still
means terminal offset traversal, not a concurrent-write snapshot.

Active parent and active variant are required for active matching. Inactive
records can be retained as flagged facts but are never rendered as purchase
offers. isSellable remains metadata, not stock availability. Non-null
effectivePrice is preserved exactly, including 0.00; null means price unknown.
Tracked positive stock is a recorded observation, zero explicitly means no
recorded stock remains, and untracked stock means availability/quantity unconfirmed.
No product-level inventory is used. Missing/unavailable facts remain explicit.

selected_variant_id is a conservative current reference, not an order or an
availability guarantee: it requires one active matching record, priced positive
recorded inventory, metadata eligibility, no unresolved clarification/failure, and
sufficient coverage (or an explicit variant ID). A zero/untracked/unpriced variant
can still be an actual matching record, but is never promoted to that selection.
All material states observations and warns that stock can change and no reservation
is made. No total, alternative price, globally cheapest product, delivery promise
or unsupported business policy is invented.

GroundedStatement contains a deterministic kind, text, subjects and source links;
the joined draft is safe material for later generation and validation. It is not
a free-form Gemini response or proof of semantic grounding by the existing Guard.
Focused product/option clarification is separated from missing Backend-information
wording. Complaint/escalation protections reuse calm existing templates; complaints
conservatively request owner review without claiming notification/refund/action.
An English delayed-order cue is handled locally to avoid misclassifying it as a
purchase. Help wording reflects read-only capabilities rather than promising order
creation. Greetings/thanks remain deterministic. Business identity can use the
minimal aggregate; policy facts cannot be synthesized from it.

EvidencePlan.to_response validates the deterministic draft against existing
AiResponse. It always supplies orderCandidate=null, never CONFIRMED_ORDER, and can
use PURCHASE_INTENT for current purchase interest. No order is created, confirmed,
modified or reserved. No inventory mutation occurs. This conversion helper does
not activate a route or persist anything.

### Tests and remaining dependencies

`tests/test_evidence_planner.py` asserts concrete prices, quantities, omissions,
sources, dynamic/default options, missing combinations, active states, coverage,
history ambiguity, complaints/escalation, schema compatibility, concurrent callers
and zero Backend/Gemini calls. Additional Phase 5 tests exercise dynamic options
through the existing mocked transport. Its timeout cancellation test uses the
injected clock to isolate the actual await timeout from incidental routing CPU
time; its cancellation/call-count assertions are unchanged.

Remaining Backend questions include final options/projection shape and key
uniqueness, partial optionValues semantics, snapshot/freshness guarantees, and the
already documented search/history/business aggregate/authentication dependencies.
Free-form text rendering, Gemini grounding, structured Guard integration and
production execution remain later phases. Phase 6 stops here for review.

## Phase 7 standalone grounded presentation and evidence guard

`app/providers/evidence.py` adds GroundedGenerator over an **injected existing
GeminiClient** and Settings. There is no second SDK client, provider-factory wiring,
v2 route, Backend lookup or live execution change. The existing client supplies
structured-schema/plain-JSON fallback, parse retries, model fallback, cooldowns
and sanitized operational health. A remaining-time wait_for additionally bounds
the whole new provider call, including its retries/delays. Caller cancellation is
propagated. No plan, prompt, response or token is saved on the generator instance.

### Deliberately closed response format

An open-ended factual paraphrase cannot be reliably proved correct by numeric
sets, keywords or another model assertion. This phase therefore uses the explicitly
restricted presentation contract, not arbitrary generated reply text:

```json
{"opening":"acknowledge","layout":"compact","statement_ids":["s0","s1","s2"]}
```

opening is none/acknowledge/helpful; layout is compact/spaced. Python supplies
localized nonfactual opening strings. statement_ids must equal the request-local
manifest **exactly once in the original order**, including every clarification,
missing-information and safety block. Unknown IDs, omission, duplication and
permutation are rejected. No reply prose, price, option selection, product ID,
action, policy, intent, review flag or orderCandidate can be supplied by Gemini.
All unknown JSON keys and duplicate object keys are invalid. Correct free-text
paraphrases are also unsupported rather than receiving a false grounding approval.

Python renders the immutable approved statement blocks byte-for-byte, with only
an allowlisted opening and line spacing selected by Gemini. This supports Arabic,
English and Franco-Arabic-derived Arabic plans while sacrificing open-ended
rewriting freedom. It preserves different variants' price/stock associations,
null-price and untracked-stock wording, zero stock, EGP, partial-search limitations,
questions and read-only restrictions. Recorded stock never becomes a reservation
or guarantee. Arithmetic, discounts, delivery/refund/payment policies and order
actions cannot be added through this contract. More natural factual paraphrasing
would require a separately reviewed deterministic renderer or equally verifiable
format, not relaxing the guard to keyword checks.

### Prompt and plan boundary

`app/prompts/evidence.py` builds a bounded JSON payload with approved statement
IDs/text, only factual groups referenced by those statements, record provenance,
required guidance and application policies. Local pN/vN labels replace UUIDs.
Names/option labels are explicitly untrusted data labels. Raw current messages,
product descriptions, history content, historical claims, request identifiers,
customer/business scope IDs, service credentials and context tokens are absent.
The generator accepts a plan rather than a raw authenticated request and therefore
has no reason to accept credentials or customer authorization material.

Defaults: <=32 statements, <=16,000 combined system/user prompt characters,
<=4,096 proposal characters, <=20,000 reply characters and <=25 seconds per
generation call (also capped by the configured Gemini total timeout). Excessive
plans/prompts fall back without truncating required facts or questions. Reply
limits must leave >=128 characters for an irreducible safe generic fallback. The
prompt contains no raw Backend envelopes or unrelated candidate facts. A generated
opening/spacing choice that exceeds the output bound is rejected.

`app/pipeline/evidence_guard.py` validates the read-only plan/schema shape, allowed
provenance paths, factual subject/parent/source links, active verified variant
requirements, and required clarification block before compiling a frozen manifest.
Its guard then proves that model presentation cannot add/remove/change/reorder
approved blocks. This is a structural invariant, not a keyword/numeric heuristic.

The trusted input remains an EvidencePlanner-produced plan over scoped retrieval.
This guard does **not** independently prove Backend truth, freshness, scope-token
authenticity or the correctness of arbitrary manually forged plan prose. It is not
a semantic verifier for unrestricted natural language. Plan construction and
future authenticated orchestration remain responsible for those boundaries. No
untrusted JSON plan endpoint is introduced. The live legacy Guard is unchanged.

### Fallback and response invariants

Malformed output uses the existing parser retry policy; a syntactically valid
proposal that fails the manifest guard immediately returns the deterministic plan
draft. Timeout, exhausted provider attempts, unexpected provider error, disabled
generation, and prompt bounds also return that draft. Review/escalation, hard-rule,
unsupported, invalid/unavailable and authorization-rejected plans bypass Gemini.
Their fixed safety wording does not need stylistic model intervention.

An invalid/unbounded caller plan cannot bless its own draft: use a short fixed
information-unverified fallback instead, retaining requiresReview. All final paths
are validated by AiResponse, always orderCandidate=null, never CONFIRMED_ORDER.
PURCHASE_INTENT is preserved only as intent. Gemini cannot downgrade review or
clarification. Diagnostics contain fixed fallback/violation categories and model
names, never raw prompt/model/customer/exception text. Existing shared health
retains categories rather than raw parse errors, including repeated invalid output.

### Historical Phase 5/6 structured-option checkpoint (superseded by Phase 8)

**At Phase 7 the mismatch was real:** PlanningInquiry.option_values was a local structured
selection map; RetrievalQuery has no corresponding field. Retrieval currently
uses text and explicit product/variant references. There is no proof in
RetrievalResult that a later planning inquiry used those same selections or even
the same turn. Do not silently claim a shared selection contract exists.

The offline end-to-end regression deliberately retrieves a partial product plus
Black/M detail, then asks planning for White/M through option_values. Actual calls
show that White/M was never requested or observed. Planning returns
NO_MATCH_PARTIAL with no selected variant, and a model proposal asserting an
invented White/M statement ID is rejected. Final output does not quote White/M's
unobserved price or claim the combination is resolved. This demonstrates both the
retrieval recall risk and the present fail-closed evidence boundary.

This regression is not full cross-layer alignment: other mismatched inquiries may
encounter an actual variant incidentally present in embedded evidence, and the
current structures do not attest inquiry/option provenance end-to-end. Phase 8
must review one shared selection/turn binding, query preservation and retrieval
coverage before production integration. This phase introduces no parallel tool
contract or new option argument, and does not treat the gap as harmless.

### Offline verification and remaining work

`tests/test_evidence_generation.py` asserts final schema-validated replies for
languages, prices/quantities, dynamic options, zero/null/untracked states, partial
coverage, multiple candidates, injection as data, fabricated discounts/actions/
combinations/arithmetic, parser/guard rejection, retries/model/schema fallback,
timeouts/cancellation, review/purchase invariants, prompt bounds, sanitized health,
request isolation and the structured-option gap. FakeGemini replaces only the
network method so real provider retry logic is exercised. MockTransport covers
the checkpoint's Backend calls. No live service is used.

Signed-context verification, the internal endpoint, final business/history/options
DTOs, stable snapshot guarantees, unified selection provenance and actual request
orchestration remain unresolved integration dependencies. Phase 7 stops before
v2 or live orchestration; no Orders, WhatsApp or inventory writes are implemented.

## Phase 8 standalone end-to-end assembly

`app/pipeline/standalone.py` adds StandalonePipeline. It composes the existing
HistoryService, RetrievalCoordinator, EvidencePlanner and GroundedGenerator using
an injected BackendDataAccess and existing injected GeminiClient-backed generator.
No SDK client is duplicated. It is not imported by main.py, provider factories,
the live Orchestrator or existing v1 routes; no v2 HTTP endpoint is activated.

### One inquiry across retrieval and planning

`app/schemas/inquiry.py` is now the single validated internal Inquiry definition:
text, product_ids, product/variant references and option_values. RetrievalQuery
and PlanningInquiry remain import-compatible aliases of this **same class**, not
parallel contracts. Text/ref constraints remain; structured values are strict
strings with nonblank keys/values. Options are copied into a read-only mapping,
references are frozen tuples/models, and JSON serialization remains supported.
Use model_dump(mode="json") plus model_validate for a detached validated snapshot;
mapping immutability is intentional rather than exposing a mutable options dict.

Execution makes one fresh validated snapshot before its first await. The exact
same object is passed to retrieval and planning. Retrieval now uses the shared
structured options for dynamic matching/detail selection and records that inquiry
in RetrievalResult. Planning compares the inquiry against that snapshot **before
using facts**: any change in text, product refs, variant refs or options produces
MISSING_DETAIL with inquiry_selection_mismatch, no factual selection and a safe
clarification. The assembled flow also rejects retrieval results missing the exact
binding. This resolves the Phase 7 checkpoint without adding Backend tool arguments.

For compatibility, earlier isolated component fixtures may still construct
RetrievalResult(inquiry=None); the standalone planner labels those with
unbound_retrieval_inquiry. This legacy testing mode cannot pass assembled execution's
binding check and is not an authenticated or publicly accepted evidence format.

`app/data/routing.py` consolidates the existing standalone delayed-order complaint
and Franco-Arabic overrides around the tested rule classifier. Retrieval and
planning therefore agree, and an English delayed-order complaint does not trigger
unnecessary catalog retrieval. The live NLU/RulesRouter/Gemini Router are unchanged.
Historical variant references now trigger current detail revalidation where
appropriate, even when the current follow-up names no option. Unrelated records'
embedded variants no longer mislabel a partial product no-match as missing detail.

### Scope, turn and prepared-history binding

execute accepts the validated Inquiry, caller-established ExpectedScope, current
message_id and an explicit context_token. TurnBinding requires business, customer,
conversation and message identifiers. **This is a provisional internal binding,
not cryptographic authentication, identity ownership verification or a signed token.**
No public entry point for arbitrary unsigned tenant IDs is introduced.

An execution-local data-access gate checks that every history/retrieval call uses
the same scope and per-call token. Selectors and historical IDs confer no authority;
the actual Backend must enforce business/customer/conversation/product ownership.
The token is never put in the query, plan, prompt, returned result or diagnostics.
It is held only while the call is executing and forwarded unchanged to Backend
methods. Service credentials remain BackendClient configuration.

History is prepared automatically only for context-dependent follow-ups when
enabled. Self-contained inquiries and hard rules avoid unnecessary history calls.
Callers can disable preparation and receive conservative clarification, or supply
BoundHistory carrying the same complete TurnBinding. Any business/customer/
conversation/message mismatch fails closed before Backend or Gemini access.
Supplied history is copied for ownership and must respect configured message,
content-character and reference-hint bounds; oversized context is rejected rather
than silently truncated or allowed to bypass preparation limits.

The internal caller must bind supplied prepared history correctly; a dataclass
wrapper cannot prove a signature or establish ordering/ownership. Current Backend
timestamps/order/before-current limitations remain explicit. Missing current rows
do not become a fabricated before-current boundary. Historical text is not current
price/stock authority, and follow-ups never become confirmed transactions.

### Total budgets, failure and cancellation

ExecutionLimits defaults to 20 total elapsed seconds and 12 actual Backend data
operations across **both** history and retrieval. It is validated independently
of, and does not relax, individual history/retrieval/generation limits. The local
gate refuses further calls at the total cap. Existing per-execution retrieval
deduplication remains intact; no global customer-specific cache is added.

One outer wait_for bounds cumulative async execution; deadline checks between
stages prevent starting a later stage after time is exhausted. Nested limits may
finish sooner. Synchronous validation/planning and fallback are cooperative,
bounded processing rather than a preemptive CPU watchdog. A timeout cancels the
current await. If no complete plan exists, incomplete stage evidence/history is
discarded and an unavailable plan is built. If a verified plan already exists when
generation expires, reuse GroundedGenerator.fallback and the existing deterministic
evidence guard without starting another model attempt. User CancelledError is not
caught or converted into a response.

Authorization/scope failure stops retrieval and clears prepared history, retrieved
envelopes and factual selections before generation. The existing generator is
still invoked on the protected rejection plan and bypasses Gemini according to
its established policy. Invalid/missing/transient data keeps existing conservative
typed outcome semantics and explicit partial coverage. No cross-tenant fallback,
order action, inventory mutation or new search API is introduced.

GroundedGenerator exposes its existing deterministic fallback as a reusable method
for execution-budget exhaustion; normal execution always uses its generate/guard
path. Final AiResponse validation enforces the plan intent and review flag, no
CONFIRMED_ORDER and orderCandidate=null. A mismatching generator result falls
back rather than changing those requirements.

### Request-local result and diagnostics

StandaloneExecutionResult contains the response, turn binding, immutable inquiry,
optional bound history, typed retrieval result, EvidencePlan, generation metadata
and ExecutionDiagnostics. Protected fields are excluded from repr. Diagnostics
contain operation counts, elapsed milliseconds, completed/stopped stage names,
fixed issue codes and safe generation/fallback categories, not raw customer
records, identifiers, prompts, credentials or exception text. They describe this
call only and are not stored on the pipeline instance.

The shared objects are injected dependencies and frozen limits. Gemini operational
health/cooldowns/schema capability remain shared as before, without customer
content. History, query selections, evidence, deduplication state and budgets are
execution-local. No last_plan/last_result or customer cache is reintroduced.

### Offline integration evidence and remaining boundaries

`tests/test_standalone_pipeline.py` runs the actual composed stack with synthetic
records, MockTransport and a FakeGemini network override. It checks hard-rule zero
calls, discovery/detail counts, Arabic/English/Franco and dynamic keys, shared
structured selection, changed-selection rejection, zero/null/untracked stock,
inactive/missing combinations, partial searches, ambiguity, history boundaries,
scope/turn mismatches, injection omission, authorization/transient failures,
provider fallback, owner review/purchase invariants, cumulative budgets, timeout,
cancellation, concurrent customers/businesses, and unchanged v1/no-v2 routing.
Header/scope assertions in the mock Backend are **test placeholders**, not proof of
actual signed-context authentication. The Phase 7 checkpoint regression now asserts
the shared type and explicit rejection of a changed planning inquiry.

Before any live integration, agree and implement the authenticated v2 trust boundary
(service authentication, signed scope/turn verification, key lifecycle and replay
policy), the still-proposed internal Backend endpoint, final business/history/
options DTOs, ordering/freshness guarantees, error contracts and payload-size bounds.
The caller must verify message membership/content, customer/conversation ownership
and supplied-context provenance before constructing internal bindings. No weak
unsigned-ID or token-decoding-only substitute is implemented here. Phase 8 stops
for review and does not activate live services.

### Phase 8 extension boundaries: future conversation and Orders

Presentation-only Gemini is the current safe baseline, **not the final product
goal**. Future natural Arabic, English and Franco-Arabic-aware conversation can
evolve behind the injected EvidenceResponder boundary in app/providers/evidence.py.
That small interface consumes EvidencePlan and returns GroundedGeneration, with a
deterministic fallback. It exposes no Backend client, scope selector, token or tool
authority. GroundedGenerator remains the only supplied implementation; its strict
presentation schema, manifest guard, protected-plan bypasses and fallback behavior
are unchanged. No unrestricted generation mode or switch is added.

A future conversational implementation must preserve the same separation between
Backend observations, customer requests, provisional references, unknowns and
application policy. It may improve conversational phrasing and focused multilingual
clarification only behind a separately reviewed, verifiable grounding/guard design.
Do not approve arbitrary factual prose using numeric sets, keywords or the model's
own assertion. If a claim cannot be checked reliably, retain deterministic factual
rendering or a narrower verifiable format. Prices/stock must remain associated with
their actual variant; unknown inventory/prices, partial coverage, required review,
authorization rejection and cancellation/fallback constraints remain mandatory.
No future stylistic change may select business/customer identities, authorize tools,
create policies, imply an action occurred or weaken AiResponse read-only invariants.
New adversarial multilingual regression coverage and explicit review are prerequisites
before replacing the baseline implementation or wiring production execution.

`app/pipeline/extensions.py` reserves a minimal **disabled, data-only** Orders seam.
StandaloneExecutionResult.order_extension always has enabled=false, with no
constructor enable switch, handler, dispatch method, callback or order API client.
For purchase intent it may contain only provisional CandidateReference records and
the current requested quantity. References are deduplicated and deliberately marked
not revalidated for order processing, even if a read-only lookup checked them earlier.
This does not erase their existing read provenance in EvidencePlan: order validation
requires a new, stronger boundary. Auth/scope rejection, invalid/unavailable or
unsupported evidence and changed-inquiry failures produce no purchase handoff.

The seam contains no prices, stock, reservation, order ID, transaction status or
credentials. It is internal request-local metadata, not an AiResponse field or a
new Backend contract. Its presence, a selected variant, a requested quantity or
PURCHASE_INTENT must never trigger an order. orderCandidate remains null; no
CONFIRMED_ORDER, inventory deduction, reservation or order confirmation is enabled.

Any later Backend-owned order extension needs a separately agreed contract covering:

1. Authentication and authorization: verify service identity and signed business,
   customer, conversation and current-message scope/ownership at the real boundary;
   define expiry, replay, key rotation and authorized operations. Provisional Python
   bindings and historical references are not sufficient authority.
2. Fresh validation: Backend re-fetches current product/variant relationships,
   active/sellable state, actual option combination, effective Decimal(12,2) EGP
   price, inventory policy/quantity and requested quantity constraints. Read-only
   observations and AI arithmetic cannot authorize a reservation or charge. Check
   race-sensitive conditions within the Backend transaction that performs the action.
3. Idempotency: Backend defines a stable authorized operation key and durable atomic
   duplicate handling across retries/concurrent requests. Repeated payloads must not
   create duplicate orders or deduct stock twice; changed payload/key conflicts and
   replay behavior require explicit semantics. No key scheme or endpoint is invented
   or implemented in this phase.
4. Backend state ownership: Backend alone validates and creates orders and enforces
   allowed state transitions; the business owner approves. Stock deduction uses the
   Backend InventoryService transaction methods on approval; cancellation/restoration
   follows the eventual lifecycle. Approval, cancellation and restoration also need
   transactional/idempotent handling. AI reads only authorized Backend state and
   never treats a chat confirmation, old AI reply or generated sentence as order state.
5. Execution and response review: define explicit customer/owner confirmations,
   operation-specific permissions, concurrency/version checks, safe error handling
   and the agreed response contract before enabling any handler. The current schema's
   legacy CONFIRMED_ORDER path is not silently repurposed for this extension.

These are future requirements, not implemented authentication or an Orders design
activation. No live Backend endpoint, Gemini redesign, v2 route, v1 behavior change
or inventory mutation is part of this Phase 8 addition.
