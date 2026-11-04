# Backend handoff — read-only conversational AI

4 November update: main remains `83a65e9`. The new opt-in authenticated loopback
catalog adapter and exact operator test commands are in
[MULTI_PROVIDER_DEVELOPMENT.md](MULTI_PROVIDER_DEVELOPMENT.md). Actual development
HTTP testing was not performed. PR #1 is open/unmerged at
`0e92d6b5d038aa6da87c76ee5f06d29aebe4127a`; its conversation endpoints explicitly
lack authentication and its branch predates current auth/products modules.
History transport remains blocked; only its response mapper/contract is prepared.
Reconcile the branch with authenticated main and review ownership/chronology
guarantees before enabling it. The development owner JWT is not a production
S2S design and is never exposed to customer-facing AI requests or models.

Reviewed 3 November 2026 against accessible `shrouqshaker/brandora-backend/main`,
commit [`83a65e9`](https://github.com/shrouqshaker/brandora-backend/commit/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b)
(30 October). Repository reads only; no running Backend, database or production
data was accessed. Other branches were not treated as implemented on main.

## A. Verified on main

- [ProductsService](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/src/products/products.service.ts)
  and VariantsService provide tenant-scoped CRUD under
  `/businesses/:businessId/products` and nested `/:productId/variants`.
  Detail responses are **direct objects**. Lists use `{items,pagination}`.
  Products embed the first 20 variants plus `variantsPagination`.
- [Presenter](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/src/products/product-presenter.ts):
  non-null response prices are fixed two-decimal strings; Decimal(12,2) allows
  at most 10 integer digits. Inputs may have fewer decimals; AI validates the
  **response** format. `effectivePrice = unitPrice ?? basePrice`, including zero.
  `isSellable` is active/priced metadata eligibility, not stock availability.
- Dynamic options are case-sensitive definitions/selections, not a Cartesian
  catalog. AI resolves aliases only when unique against actual declared values.
  Lists include inactive records. UUID path pipes do not specify a UUID version.
  Pagination limits are 1..100; offsets 0..Number.MAX_SAFE_INTEGER. Each list
  uses repeatable-read; separate tool calls are not one snapshot.
- [Variant-only inventory migration](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/prisma/migrations/20261030000000_variant_only_inventory/migration.sql)
  enforces tracked integer quantity >=0 or untracked/null. InventoryService has
  transaction-taking `deductForOrder` / `restoreForOrder` primitives with stable
  order-line movement identities. These are **not an implemented Orders API**.
- BusinessesService has profile, separate settings (cash/online/delivery/pickup)
  and working-hour services. Hours prohibit overnight ranges. These can supply
  a future aggregate; no AI aggregate route was found.
- [AuthGuard](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/src/auth/auth.guard.ts)
  validates owner access JWT/session/authVersion and active OWNER membership.
  Resource-scope denials can be hidden as 404. This is **not** customer-context
  authentication for AI.
- Existing errors use `{statusCode,code,message,error}` with sanitized unexpected
  500s. Inspected Prisma schema and registered modules contain no Customer,
  Conversation, Message or Order service/model. Catalog, Imports, Inventory,
  Business, Products, Variants and Auth modules exist. `/internal/ai/data` was
  not found in inspected main code/documentation.

## B. Required Backend work

- [ ] Implement a separately authorized internal read-only dispatcher for exactly
  `get_products`, `get_product_details`, `get_product_variants`,
  `get_variant_details`, `get_conversation_history`, `get_business_info`.
  Reuse existing presenters/services and tenant/parent checks.
- [ ] Agree service identity + signed per-request customer context: bind
  business/customer/conversation/current-message, issuer, audience, expiry and
  replay policy; define revocation/key rotation. Authorized business must come
  from verified context, never Gemini or arbitrary body fields. Do not give AI
  an owner's access token or unrestricted CRUD access.
- [ ] Implement scoped conversation storage/history. Attest conversation AND
  current-message ownership; preserve CUSTOMER/AI/OWNER roles, stable IDs,
  timezone-bearing timestamps and reliable current-turn cutoff. Define edits,
  deletions, same-timestamp ordering, pagination and replay.
- [ ] Agree business-info aggregate shape and permitted fields. AI currently
  consumes only `data.business.{id,name}`; profile/settings/hours exist in
  separate services. No returns-policy/FAQ API was verified.
- [ ] Define bounded payload sizes, timeout, 400/401/403/404/429/5xx semantics,
  rate limits and audit redaction. Decide whether hidden 404 scope denials need
  a distinct internal machine category. AI never echoes raw Backend errors.
- [ ] Future Orders: finalize permissions, ownership, owner approval/state
  machine, stable idempotency keys, retries, conflicts and cancellation. Revalidate
  scope, actual variant/options, current price and stock transactionally before
  deductions; use inventory primitives inside Backend order transactions.
  No AI-generated price, approval or status is authoritative.

## C. AI integration waiting for contracts

- [ ] Configure existing BackendClient/BackendDataAccess for the implemented
  endpoint with deployment-managed credentials and verified context; run shared
  contract tests, including scoped 404 and authorization failures.
- [ ] Add authenticated ingress and bounded durable/versioned context storage
  before any customer-facing v2 route. Local ChatSession is not authentication.
- [ ] Connect HistoryService to attested turn boundaries and reconcile persisted
  semantic selections; reject stale/concurrent context writes.
- [ ] Map the agreed business aggregate with scope/optional-data validation.
  Do not claim settings, hours or policies until supported by that contract.
- [ ] Run explicit live Gemini acceptance and authorized Backend integration.
  Enable Orders only after separately reviewed response/action contracts.

## D. Proposed protocol — not an existing endpoint

`POST /internal/ai/data` with `Authorization: Bearer <service-token>` and
`X-AI-Context: <per-call-context-token>`. Neither credential is a model input.

```json
{"tool":"get_product_details","arguments":{"productId":"00000004-0000-4000-8000-000000000010"}}
```

```json
{"tool":"get_product_details","data":{"id":"00000004-0000-4000-8000-000000000010","businessId":"00000001-0000-4000-8000-000000000001","name":"Synthetic T-Shirt","description":null,"basePrice":"200.00","options":{},"attributes":{},"isActive":true,"isSellable":false,"variants":[],"variantsPagination":{"limit":20,"offset":0,"totalCount":0,"hasMore":false,"nextOffset":null}}}
```

Variant details also use direct `data: <variant object>`. Collection tools use
`data: {items: [...], pagination: {...}}`. Wire selectors are `productId`,
`variantId`, `conversationId`, `limit`, `offset`; Python methods stay snake_case.
Full envelopes are retained. No businessId tool argument is accepted. Proposed
business aggregate minimum:
`{"tool":"get_business_info","data":{"business":{"id":"<uuid>","name":"Example"}}}`.
Extensions require agreement; existing service fields do not imply an AI API.

Proposed errors should reuse the existing envelope: 401/403 stop retrieval and
discard evidence, 404 yields unverified information, timeout/5xx yield safe
unavailable replies. No redirects or automatic tool retries. Counts may change
between pages; bounded traversal never proves durable absence, global uniqueness
or reservations. EGP remains an application convention pending agreement.
