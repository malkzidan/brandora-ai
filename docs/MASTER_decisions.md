# Brandora — Master Project Documentation
## Final Decisions, Implemented Backend, API Contracts, Data Model, Team Integration, Testing, Deployment Direction, and Remaining Roadmap

> **Document type:** Master Markdown Reference  
> **Project:** Brandora  
> **Checkpoint:** 9 October 2026  
> **Purpose:** This file consolidates the final agreed decisions and the verified current state of the Brandora project from the project discussions, implementation reports, verification outputs, API handoff material, and Jira checkpoint.  
> **Important rule:** Earlier ideas that were later replaced are not presented as current decisions. Where a historical implementation/prototype exists but is **not part of the current merged backend baseline**, it is explicitly marked as prototype / deferred / not yet merged.

---

# Table of Contents

1. Executive Summary  
2. Product Vision  
3. Core Product Principles  
4. Team Structure and Ownership  
5. Current Backend Technology Stack  
6. Repository and Local Development Context  
7. Current Implementation Status  
8. High-Level Architecture  
9. Multi-Business / Multi-Tenant Direction  
10. User / Business / Ownership Direction  
11. Database Source-of-Truth Policy  
12. Excel Import Scope  
13. Catalog Domain  
14. CatalogItem Data Model  
15. Catalog CRUD  
16. ImportJob Data Model  
17. Import Lifecycle  
18. Excel Analyze  
19. Header Detection  
20. Sheet Selection  
21. Mapping  
22. Normalization  
23. Validation  
24. Validation Snapshot  
25. Validation Results Pagination  
26. Preview / Planning  
27. Import Identity  
28. Import Update Semantics  
29. Import Duplicate Rules  
30. Import Execute  
31. Import Resume / Status  
32. Import History  
33. Import Error / Recovery Limitations  
34. Inventory Domain  
35. InventoryMovement  
36. InventoryService  
37. Inventory Rules During Import  
38. Manual Inventory Adjustment API  
39. Inventory History API  
40. Inventory Concurrency  
41. Business Profile  
42. Business Settings  
43. Working Hours  
44. Business Knowledge — Policies and FAQs  
45. Customer / Conversation / Message Direction  
46. WhatsApp Integration Direction  
47. AI Architecture  
48. AI Service Direction  
49. Orders Domain  
50. Order State Machine  
51. Order Stock Semantics  
52. OrderItem Snapshot  
53. Notifications  
54. Dashboard / Daily Brief  
55. Follow-Ups / Abandoned Intent  
56. Shared Error Contract  
57. Shared Pagination Contract  
58. API Surface — Current Implemented Endpoints  
59. Detailed API Contracts  
60. Prisma / Migration Rules  
61. Current Migration History  
62. Testing Strategy  
63. Latest Verification Results  
64. API Documentation Structure  
65. README Decision  
66. Mobile Handoff Rules  
67. Azure Production Direction  
68. Production Storage Direction  
69. Environment Variables  
70. Deployment Commands  
71. Security / Privacy / Data Isolation Principles  
72. Jira Status and Completed Tasks  
73. Current Known Limitations  
74. Explicitly Deferred Features  
75. Final Architectural Invariants  
76. Recommended Resume Sequence  
77. Definition of “Done” for Future Backend Tasks  
78. Current Resume Checklist  
79. Glossary  
80. Final Snapshot

---

# 1. Executive Summary

Brandora is a **generic multi-business platform** for business owners who need a single system to manage business data, customer communication, orders, inventory, and later AI-assisted customer handling.

The project is intentionally **not tied to one business vertical**. The backend must be reusable for examples such as:

- Fashion businesses
- Retail stores
- Restaurants
- Bakeries
- Salons
- Service businesses
- Home businesses
- Solo entrepreneurs
- SMEs

The current backend foundation has already progressed beyond the initial project skeleton.

The **verified current backend baseline** includes:

- PostgreSQL + Prisma foundation
- Business entity
- Catalog Item model
- Catalog CRUD
- Excel workbook analysis
- Automatic header detection
- Mapping suggestions and owner-confirmed mapping
- Row normalization
- Row validation
- Import validation result persistence
- Validation result pagination
- Import preview / plan
- Import execution
- Import status / resume
- Import history
- InventoryService
- InventoryMovement audit
- Manual stock adjustment API
- Per-item inventory history
- Whole-business inventory history
- Business profile API
- Business settings API
- Working-hours API
- Stable API error envelope
- Reusable pagination utilities
- API documentation for current domains
- Automated tests for the implemented domains

At the latest verified checkpoint:

- **15 / 15 test suites passed**
- **463 / 463 tests passed**
- Build passed
- Formatting passed
- `git diff --check` passed
- Prisma validate passed
- Prisma generate passed

---

# 2. Product Vision

Brandora is intended to become an owner-facing business platform that can eventually support:

- Business setup
- Catalog/product management
- Inventory
- Business policies and FAQs
- Working hours
- WhatsApp customer communication
- Customer and conversation history
- AI-assisted customer responses
- Structured order extraction
- Owner order approval
- Notifications
- Dashboard / analytics
- Follow-up on abandoned customer intent

The platform should make the owner’s business data usable by both the Mobile app and the AI layer without allowing AI to bypass backend business rules.

---

# 3. Core Product Principles

The project repeatedly converged on these principles.

## 3.1 Generic, not industry-specific

The core backend must not assume that every business is:

- fashion
- restaurant
- salon
- retail

Generic fields should be preferred.

Flexible metadata should use generic structures where appropriate.

## 3.2 Backend is authoritative

Business rules live in the backend.

Mobile does not decide business invariants.

AI does not decide business invariants.

## 3.3 PostgreSQL is authoritative after import

After imported data is accepted into Brandora:

**PostgreSQL is the source of truth.**

Excel is not the long-term authoritative database.

## 3.4 Audit important business mutations

Stock must be auditable.

Order-related stock mutations must later reuse the same inventory audit architecture.

## 3.5 Multi-business isolation

Every business-owned entity must be scoped by business.

A caller must never gain access to another business’s data through an object ID alone.

## 3.6 Stable API contracts for Mobile

Mobile must receive:

- predictable JSON
- stable error codes
- documented lifecycle rules
- consistent pagination

---

# 4. Team Structure and Ownership

Current team structure:

| Area | Owner |
|---|---|
| Backend 1 | Shrouq |
| Backend 2 | Second backend teammate |
| AI | Malak |
| Mobile | Yasmin |

## 4.1 Backend 1 — Shrouq

Primary responsibility:

- Business/data core
- Excel import
- Catalog
- Inventory
- Business profile
- Business settings
- Working hours
- Business Knowledge later

Current implemented work includes much of this area.

## 4.2 Backend 2

Primary direction:

- WhatsApp
- Customers
- Conversations
- Messages
- Orders
- Approval workflows
- Notifications
- Dashboard
- Follow-ups
- Backend-side AI integration

## 4.3 AI — Malak

AI responsibility is to handle language/intelligence tasks, not authoritative persistence.

Planned responsibilities:

- intent classification
- inquiry answering
- structured order extraction
- clarifying questions
- language-aware response behavior
- guardrails

## 4.4 Mobile — Yasmin

Mobile is expected to consume documented APIs and stable DTO contracts.

Important integration need:

**Mobile must be able to continue building even when some backend screens are not yet connected live.**

This is why request/response contracts and sample JSON are part of the backend handoff.

---

# 5. Current Backend Technology Stack

Final backend stack:

- **NestJS**
- **TypeScript**
- **Prisma**
- **PostgreSQL**

Other relevant implementation pieces:

- ExcelJS for Excel workbook handling
- Jest / Supertest style automated testing
- Prisma-generated client
- Global validation
- Structured exception filter

Production direction:

- Backend hosting: **Azure**
- Managed PostgreSQL currently planned through **Neon PostgreSQL**
- Durable production file/artifact storage: **Azure Blob Storage**

---

# 6. Repository and Local Development Context

Repository:

```text
https://github.com/shrouqshaker/brandora-backend
```

Local development path used during implementation:

```text
C:\Users\A . ONE\Desktop\brandora-backend
```

The repository is private.

A ChatGPT GitHub connector previously returned 404 for this private repository, so code verification during the project often relied on:

- uploaded repository ZIP
- Codex diffs
- test output
- Git status
- Git diff stats
- generated documentation
- direct local implementation reports

---

# 7. Current Implementation Status

## 7.1 Implemented and verified

### Data / Catalog
- Business base model
- CatalogItem
- Catalog CRUD
- Soft deactivate
- Business scoping

### Excel Import
- Analyze
- Sheet discovery
- Header detection
- Mapping
- Normalize
- Validate
- Validation snapshot
- Validation results reader
- Preview
- Execute
- Status
- History

### Inventory
- InventoryService
- InventoryMovement
- Import stock integration
- Manual stock adjustment
- Item movement history
- Business movement history

### Business
- Business profile GET/PATCH
- Business settings GET/PATCH
- Working hours GET/PUT

### Cross-cutting
- Stable error envelope
- Shared pagination
- Documentation
- Automated regression tests

## 7.2 Not yet implemented in the verified current baseline

- Auth
- Register/login
- BusinessMember ownership enforcement
- Create Business flow for real authenticated users
- Policies API
- FAQs API
- WhatsApp production integration
- Customer/Conversation/Message persistence in current baseline
- AI production integration
- Orders
- Notifications
- Dashboard
- Follow-ups
- Variants
- Images
- Azure Blob implementation
- Azure deployment

---

# 8. High-Level Architecture

Current/final direction:

```text
Flutter Mobile
      |
      v
NestJS Backend
      |
      +---------------------+
      |                     |
      v                     v
PostgreSQL / Neon      Durable Object Storage
(source of truth)      (Azure Blob later)
      |
      v
Business Data / Catalog / Inventory / Orders / Conversations
      |
      v
AI Service / WhatsApp integrations consume backend contracts
```

The AI layer does not bypass NestJS to mutate PostgreSQL.

---

# 9. Multi-Business / Multi-Tenant Direction

Brandora is multi-business-ready.

Every business-owned resource should have business ownership or be reachable through a business-owned relation.

Examples:

- CatalogItem → businessId
- ImportJob → businessId
- InventoryMovement → businessId
- BusinessSettings → businessId
- WorkingHour → businessId
- future Customer → businessId
- future Conversation → businessId
- future Order → businessId

Cross-business behavior should generally return safe not-found semantics rather than exposing that another business owns a requested record.

---

# 10. User / Business / Ownership Direction

Final modeling direction:

- `User`
- `Business`
- `BusinessMember`

A User may exist without owning a Business.

A Business is not the same object as a User.

Ownership/role belongs in a relationship such as:

```text
BusinessMember
- userId
- businessId
- role
```

MVP starts with:

```text
OWNER
```

Future roles can be added without redesigning the Business entity.

No branch system is part of the MVP.

Auth and BusinessMember are not yet implemented in the current baseline.

---

# 11. Database Source-of-Truth Policy

The final rule:

> External files/services can feed Brandora, but PostgreSQL becomes authoritative after data is accepted into the platform.

Therefore:

## Excel can:
- create data
- update data

## Excel cannot:
- remain the master database
- delete missing Brandora records automatically
- force full replacement sync
- silently overwrite all fields

## Future Google Sheets / website adapters:
Should follow the same rule.

---

# 12. Excel Import Scope

Excel MVP imports:

- Catalog
- Inventory

It does not currently import:

- Customers
- Orders
- Policies
- FAQs
- Conversations
- Messages

Import is intentionally deterministic.

No AI is required to perform the MVP import pipeline.

---

# 13. Catalog Domain

Catalog is the generic item/product domain used by Brandora.

It must work across multiple business types.

The Catalog should contain universal fields directly and flexible business-specific metadata inside attributes where appropriate.

Variants/images/options are deferred.

---

# 14. CatalogItem Data Model

Current core shape:

```text
CatalogItem
- id: UUID
- businessId: UUID
- externalKey: nullable string
- name: string
- description: nullable string
- category: nullable string
- basePrice: nullable Decimal
- trackInventory: Boolean
- stockQuantity: nullable Int
- attributes: nullable JSONB
- isActive: Boolean
- createdAt
- updatedAt
```

Important database decisions:

- UUID IDs
- Decimal / NUMERIC for money
- JSONB for flexible attributes
- `isActive` for soft deactivation
- nullable stock
- nullable externalKey

Indexes/constraints include the business scope and lookup needs.

Important unique identity:

```text
unique(businessId, externalKey)
```

for non-null external keys.

---

# 15. Catalog CRUD

Current Catalog CRUD supports:

```text
POST   /catalog-items
GET    /catalog-items
GET    /catalog-items/:catalogItemId
PATCH  /catalog-items/:catalogItemId
DELETE /catalog-items/:catalogItemId
```

Business identity is supplied according to the existing Catalog API contract.

Key rules:

- business scoped
- missing/cross-business item → `CATALOG_ITEM_NOT_FOUND`
- DELETE = soft deactivate
- PATCH may reactivate using `isActive: true`
- omitted fields are preserved
- explicit null clears nullable metadata
- `externalKey` is trimmed
- blank externalKey becomes null
- duplicate non-null externalKey in same business → conflict
- attributes must be a JSON object
- direct Catalog CRUD cannot update stock
- direct Catalog CRUD cannot toggle tracking
- no Catalog update should bypass InventoryService for quantity changes

Excel attribute update semantics differ from direct Catalog PATCH:
- direct API may replace `attributes`
- Excel import merges mapped non-blank attributes into existing attributes

---

# 16. ImportJob Data Model

ImportJob stores the lifecycle of one import.

Current important fields/concepts:

- id
- businessId
- status
- sourceType
- fileName
- fileKey
- sheetName
- headerRow
- mapping JSON
- errors JSON
- totalRows
- validRows
- invalidRows
- skippedRows
- insertedCount
- updatedCount
- failedCount
- createdAt
- updatedAt

Source type is currently Excel-oriented.

---

# 17. Import Lifecycle

Final mobile/backend workflow:

```text
Analyze
  ↓
Mapping
  ↓
Validate once
  ↓
Validation Results
  ↓
Preview
  ↓
Execute
  ↓
Status / Resume
  ↓
History
```

Import statuses include:

```text
UPLOADED
ANALYZING
MAPPING_REQUIRED
VALIDATING
READY
IMPORTING
COMPLETED
COMPLETED_WITH_ERRORS
FAILED
CANCELLED
```

---

# 18. Excel Analyze

Endpoint:

```http
POST /businesses/:businessId/imports/excel/analyze
```

Form-data:

```text
file       required
sheetName  optional
```

Final rules:

- `.xlsx`
- maximum 10 MiB
- verify workbook content
- do not trust MIME alone
- business must exist
- discover sheets
- select requested sheet or default
- detect header row
- return headers
- return up to sample rows
- calculate total rows
- persist workbook using storage abstraction
- create ImportJob
- do not modify Catalog

Successful analysis moves the workflow into mapping-required state.

---

# 19. Header Detection

Final decision:

**Backend detects header row automatically.**

Mobile does not manually choose header row in the current MVP.

The heuristic searches early workbook rows.

The returned `headerRow` is a one-based Excel row number.

This decision was confirmed after Mobile feedback.

---

# 20. Sheet Selection

A workbook can contain multiple sheets.

Analyze returns available sheet names.

One sheet is selected for an ImportJob.

If the owner later wants a different file/sheet after validation begins:

**Create a new ImportJob rather than reopening the existing validated job.**

---

# 21. Mapping

Endpoints:

```http
GET   /imports/:importId/mapping
PATCH /imports/:importId/mapping
```

Mapping is deterministic.

No AI fuzzy mapping in current MVP.

Supported conceptual mapping types:

```text
STANDARD
ATTRIBUTE
VARIANT_ATTRIBUTE
IGNORE
UNMAPPED
```

Important rules:

- `name` must be mapped as a standard field
- no duplicate standard target
- no duplicate source mapping
- safe custom attribute keys
- source-column index handles duplicate/blank Excel headers
- mapping can be edited only while job is `MAPPING_REQUIRED`
- after validation begins, mapping is locked

To change mapping later:
- analyze again
- create a new job

---

# 22. Normalization

Normalization converts Excel cells into the backend’s canonical values before validation/planning.

Examples of concerns handled:

- text cleanup
- decimal price representation
- integer stock
- empty/blank semantics
- attributes
- row number preservation

Important decisions:

- Formula cells use stored/cached result.
- Excel is not used to recalculate formulas.
- Empty rows are skipped.
- Embedded Excel images are unsupported.

---

# 23. Validation

Endpoint:

```http
POST /imports/:importId/validate
```

This is a state-changing action.

Final behavior:

1. Job must be in the correct mapping state.
2. Claim `VALIDATING`.
3. Read retained workbook.
4. Normalize full sheet.
5. Validate all rows.
6. Detect duplicate external keys globally.
7. Persist validation snapshot.
8. Persist counters/summary.
9. Transition to `READY`.

Success response is intentionally compact:

```json
{
  "importId": "e5b31599-e582-4a36-966b-dda8389e2fb0",
  "status": "READY",
  "summary": {
    "totalRows": 3,
    "validRows": 1,
    "invalidRows": 1,
    "skippedRows": 1
  }
}
```

`POST validate` does not paginate.

`limit` and `offset` are not part of the validation action.

---

# 24. Validation Snapshot

Validation results need to remain readable without rerunning validation.

Current checkpoint implementation uses a persisted snapshot.

Snapshot content concept:

```json
{
  "version": 1,
  "importId": "...",
  "result": {
    "summary": {},
    "validRows": [],
    "invalidRows": []
  }
}
```

Current persistence:

| Data | Filesystem | PostgreSQL |
|---|---:|---:|
| validRows | Yes | No |
| invalidRows | Yes | initially also stored in errors JSON |
| validation summary | Yes | counters/errors summary |

Current local path pattern:

```text
.storage/imports/<uuid>.validation.json
```

Snapshot is written before successful validation is finalized.

This allows later GET requests to read original validation results.

---

# 25. Validation Results Pagination

Endpoint:

```http
GET /imports/:importId/validation-results?limit=50&offset=0
```

Purpose:

- Browse validation results
- Do not rerun validation
- Do not mutate state

Response shape:

```json
{
  "importId": "...",
  "status": "READY",
  "summary": {
    "totalRows": 3,
    "validRows": 1,
    "invalidRows": 1,
    "skippedRows": 1
  },
  "pagination": {
    "limit": 50,
    "offset": 0,
    "totalCount": 2,
    "hasMore": false,
    "nextOffset": null
  },
  "validRows": [],
  "invalidRows": []
}
```

Important behavior:

- valid + invalid rows form one logical ordered result
- sort by Excel row number
- paginate the combined result
- then split returned page into `validRows` and `invalidRows`
- skipped rows consume no positions

GET validation-results does not:

- decode workbook again
- normalize workbook again
- revalidate
- mutate counters
- change ImportJob status
- write Catalog
- write Inventory
- write new snapshot

Current readable later statuses include relevant later lifecycle states when a valid snapshot exists.

---

# 26. Preview / Planning

Endpoint:

```http
GET /imports/:importId/preview?limit=50&offset=0
```

Preview categories:

```text
inserts
updates
unchanged
invalidRows
```

Preview is read-only.

Final rules:

- rebuild current plan against current Catalog
- plan entire workbook first
- produce global summary
- paginate combined planned rows afterward
- no writes
- repeatable while applicable
- current preview is not a frozen snapshot

Because Preview is recomputed, Catalog changes between two preview requests can change the plan.

Execution must therefore re-check authoritative DB state.

---

# 27. Import Identity

Stable matching rule:

```text
(businessId, externalKey)
```

External key usually represents:

- SKU
- product code
- owner-provided stable external identifier

Final decisions:

- never match by name
- matching is business-scoped
- null externalKey cannot match future rows
- unkeyed valid row is insert candidate

Names can change without creating a new item if externalKey remains the same.

---

# 28. Import Update Semantics

For an existing matched CatalogItem:

## Non-null mapped value
Update it if changed.

## Blank/null mapped value
Preserve existing value.

## Unmapped field
Preserve existing value.

## Attributes
Merge non-blank mapped attributes into existing attributes.

## isActive
Do not auto-reactivate an item just because it appears in Excel.

## Missing from new file
Do not delete/deactivate the existing CatalogItem.

This is UPSERT behavior, not replacement synchronization.

---

# 29. Import Duplicate Rules

Duplicate externalKey within the same file:

**All occurrences are invalid.**

The importer does not select first or last duplicate.

This avoids silent ambiguity.

---

# 30. Import Execute

Endpoint:

```http
POST /imports/:importId/execute
```

Final behavior:

- job must be READY
- claim IMPORTING
- reopen/rebuild current normalized rows
- revalidate authoritative conditions
- re-plan each operation against current DB
- use transaction for each safe row operation
- use InventoryService for stock
- continue past row-level failures where safe
- fail job for system-level failures

Final statuses:

```text
COMPLETED
COMPLETED_WITH_ERRORS
FAILED
```

Counters include:

- insertedCount
- updatedCount
- failedCount
- validation counters

---

# 31. Import Resume / Status

Endpoint:

```http
GET /imports/:importId
```

Purpose:

- Mobile restart
- timeout recovery
- user returns later
- poll current state

Public response exposes safe fields such as:

- id
- businessId
- status
- fileName
- sheetName
- headerRow
- counters
- createdAt
- updatedAt

It must not expose:

- internal file path
- internal fileKey
- filesystem structure
- secret/internal error data

---

# 32. Import History

Endpoint:

```http
GET /businesses/:businessId/imports?limit=20&offset=0
```

Response:

```json
{
  "pagination": {
    "limit": 20,
    "offset": 0,
    "totalCount": 0,
    "hasMore": false,
    "nextOffset": null
  },
  "items": []
}
```

Rules:

- business scoped
- newest first
- deterministic ordering
- total count through Prisma `count`
- request page only
- do not load all imports into memory

---

# 33. Import Error / Recovery Limitations

Known current limitations:

## 33.1 Local snapshot storage
Validation snapshot relies on retained filesystem.

If production container filesystem is ephemeral, it can be lost.

## 33.2 Stuck states
Crash during validation may leave `VALIDATING`.

Crash during execution may leave `IMPORTING`.

Automatic recovery worker/state repair is not implemented yet.

## 33.3 Preview not frozen
Preview is recomputed rather than persisted.

---

# 34. Inventory Domain

Inventory is deliberately separated from Catalog metadata.

Core invariant:

> Catalog owns item metadata. InventoryService owns quantity mutation.

This prevents stock changes from bypassing audit.

---

# 35. InventoryMovement

Current movement types:

```text
INITIAL_IMPORT
IMPORT_UPDATE
MANUAL_ADJUSTMENT
ORDER_APPROVED
ORDER_CANCELLED
```

The Order movement types exist to support future order integration; their existence does not mean Orders are implemented yet.

Movement fields include:

- id
- businessId
- catalogItemId
- type
- quantityBefore
- quantityAfter
- quantityDelta
- referenceType
- referenceId
- createdAt

References are optional opaque audit references.

For import:

```text
referenceType = IMPORT_JOB
referenceId = importJobId
```

where applicable.

---

# 36. InventoryService

InventoryService uses absolute target quantity semantics.

Concept:

```text
setQuantity(item scope, target quantity, movement type, reference?, transaction?)
```

The service:

1. reads current quantity using business + item scope
2. checks whether the quantity changes
3. if unchanged → no stock write, no movement
4. performs conditional update
5. writes movement in same transaction
6. throws conflict on concurrency mismatch

Caller-owned transactions are supported.

This is important for:
- Excel import
- future order approval
- future order cancellation

---

# 37. Inventory Rules During Import

If normalized mapped stock is non-null:

- zero is a real value
- enable tracking
- route quantity through InventoryService
- create audit movement

New import stock:

```text
INITIAL_IMPORT
```

Updated import stock:

```text
IMPORT_UPDATE
```

If stock is blank or unmapped:

- preserve stockQuantity
- preserve trackInventory

---

# 38. Manual Inventory Adjustment API

Endpoint:

```http
POST /businesses/:businessId/catalog-items/:catalogItemId/inventory/adjust
```

Request:

```json
{
  "quantity": 15
}
```

Semantics:

**Set final quantity to 15.**

It does not mean “add 15”.

Example:

```text
Before = 10
Request = 15
After = 15
Delta = +5
```

Success:

```json
{
  "changed": true,
  "quantityBefore": 10,
  "quantityAfter": 15,
  "quantityDelta": 5,
  "movementId": "..."
}
```

No-op:

```json
{
  "changed": false,
  "quantityBefore": 15,
  "quantityAfter": 15,
  "quantityDelta": 0,
  "movementId": null
}
```

Validation:

- integer only
- min 0
- max PostgreSQL Int-safe bound used by implementation
- no negative
- no fraction
- no numeric string
- no null
- no unknown request fields

No `reason` or `note` field is currently modeled.

Important:

Manual adjustment preserves:
- `trackInventory`
- `isActive`

It does not enable tracking automatically.

---

# 39. Inventory History API

Per item:

```http
GET /businesses/:businessId/catalog-items/:catalogItemId/inventory/movements
```

Whole business:

```http
GET /businesses/:businessId/inventory/movements
```

Pagination:

```text
limit default 20
limit max 100
offset default 0
```

Response:

```json
{
  "pagination": {
    "limit": 20,
    "offset": 0,
    "totalCount": 1,
    "hasMore": false,
    "nextOffset": null
  },
  "items": [
    {
      "id": "...",
      "catalogItemId": "...",
      "type": "MANUAL_ADJUSTMENT",
      "quantityBefore": 10,
      "quantityAfter": 15,
      "quantityDelta": 5,
      "referenceType": null,
      "referenceId": null,
      "createdAt": "..."
    }
  ]
}
```

Ordering:

```text
createdAt DESC
id DESC
```

Inactive items still retain movement history.

---

# 40. Inventory Concurrency

Inventory quantity mutation is concurrency-aware.

The service does not blindly overwrite a stale quantity.

If another request changes stock between read and update:

```text
INVENTORY_CONFLICT
```

The mutation and audit movement remain atomic.

If movement creation fails:
- stock write rolls back

---

# 41. Business Profile

Endpoints:

```http
GET   /businesses/:businessId
PATCH /businesses/:businessId
```

Current profile fields:

```text
id
name
description
category
phone
address
createdAt
updatedAt
```

PATCH validation:

| Field | Rule |
|---|---|
| name | string, trimmed, 1–200, non-null |
| description | nullable string, max 5000 |
| category | nullable string, max 200 |
| phone | nullable string, max 50 |
| address | nullable string, max 1000 |

Semantics:

- omitted → preserve
- explicit null → clear nullable
- at least one editable field
- unknown fields rejected
- owner language preserved
- Arabic content preserved
- phone is not country-normalized yet

Operational settings do not belong in Business profile.

---

# 42. Business Settings

Endpoints:

```http
GET   /businesses/:businessId/settings
PATCH /businesses/:businessId/settings
```

Current fields:

```text
businessId
acceptsCash
acceptsOnlinePayment
deliveryEnabled
pickupEnabled
```

Defaults:

```json
{
  "acceptsCash": true,
  "acceptsOnlinePayment": false,
  "deliveryEnabled": false,
  "pickupEnabled": true
}
```

Final behavior:

- GET returns stored settings if present
- otherwise GET returns defaults without DB write
- PATCH upserts one settings row
- partial PATCH
- omitted fields preserved/defaulted
- strict Boolean validation
- unknown fields rejected

One row per business is guaranteed through the model key/constraint.

Current settings are preferences, not complete payment/delivery/order workflow implementations.

Deposit rules were discussed conceptually but are not part of the currently implemented settings fields.

---

# 43. Working Hours

Endpoints:

```http
GET /businesses/:businessId/working-hours
PUT /businesses/:businessId/working-hours
```

Current model:

```text
WorkingHour
- id UUID
- businessId
- dayOfWeek
- isOpen
- opensAt nullable varchar(5)
- closesAt nullable varchar(5)
- createdAt
- updatedAt
```

Unique:

```text
(businessId, dayOfWeek)
```

PUT requires the full seven-day schedule.

Example:

```json
{
  "days": [
    {
      "dayOfWeek": "MONDAY",
      "isOpen": true,
      "opensAt": "09:00",
      "closesAt": "17:30"
    },
    {
      "dayOfWeek": "TUESDAY",
      "isOpen": false
    }
  ]
}
```

Final validation:

- exactly seven unique weekdays
- `isOpen` required
- HH:mm format
- open day requires both times
- close must be later than open
- closed day has null/omitted times
- unknown fields rejected
- overnight hours unsupported

GET:
- empty array if no schedule
- otherwise ordered weekly schedule

PUT:
- upserts all seven days
- one transaction
- preserves existing row IDs where rows already exist

Current limitations:

- no split shifts
- no overnight
- no holiday exceptions
- no timezone model

---

# 44. Business Knowledge — Policies and FAQs

This is the next intended backend domain after the current pause.

It is **not implemented yet**.

Final direction:

## Policy

Conceptual fields:

```text
id
businessId
type/category
title? 
content
isActive
createdAt
updatedAt
```

## FAQ

Conceptual fields:

```text
id
businessId
question
answer
isActive
createdAt
updatedAt
```

Final decisions:

- business scoped
- generic
- soft-deactivate where appropriate
- owner-authored text preserved as written
- do not create separate Arabic/English DB columns solely for AI
- AI can respond in customer language using the stored source text

Planned routes:

```text
GET/POST/PATCH/DELETE policies
GET/POST/PATCH/DELETE faqs
```

Exact API should be finalized when implementation resumes.

---

# 45. Customer / Conversation / Message Direction

Planned domain, not yet in current backend baseline.

## Customer

Business scoped.

Expected to be created/resolved from a customer channel identity such as WhatsApp number.

## Conversation

Concept:

- business
- customer
- channel
- conversation state

One active/ongoing conversation per logical business/customer/channel context where appropriate.

## Message

Source role should support:

```text
CUSTOMER
AI
OWNER
```

Conversation history must remain persisted and auditable.

---

# 46. WhatsApp Integration Direction

WhatsApp belongs primarily to Backend 2.

Final production direction:

**WhatsApp Business Cloud API**

Planned flow:

```text
WhatsApp webhook
   ↓
Backend verifies request
   ↓
Resolve Business
   ↓
Resolve/Create Customer
   ↓
Resolve Conversation
   ↓
Persist CUSTOMER message
   ↓
Invoke AI/backend decision flow
   ↓
Persist AI/OWNER response
   ↓
Send via WhatsApp
```

Important distinction:

During earlier work, a separate WhatsApp patch/prototype was produced and tested independently with in-memory/mock behavior.

That work should **not be described as part of the verified current Brandora backend baseline unless it is actually merged into the repository**.

The final architectural direction remains useful:
- webhook verification
- deduplication
- business-number binding
- persistence
- backend-authoritative flow

---

# 47. AI Architecture

AI is not the authoritative business system.

Final rules:

AI must never:

- directly edit PostgreSQL
- directly change stock
- approve orders
- invent price
- invent stock availability
- invent policies
- invent product images
- silently perform business actions

AI may:

- classify intent
- extract structured data
- answer using trusted backend context
- ask clarifying questions
- produce candidate actions

Backend validates and executes actions.

---

# 48. AI Service Direction

Discussed/planned service direction:

- FastAPI
- independent AI service
- provider abstraction
- Mock provider during development
- Backend API provider later

Conceptual route:

```http
POST /v1/ai/respond
```

Language support:

- Arabic
- English
- mixed Arabic/English

A previous standalone AI prototype was produced with deterministic/rule-backed behavior and tests, but it should be treated as **prototype work unless adopted/merged by the team**.

Final preferred principle from that work remains valuable:

> LLM can understand/classify/extract, while prices, totals, stock, and business facts should be derived from trusted backend data/code rather than free-form hallucination.

---

# 49. Orders Domain

Orders are planned, not yet implemented in the current baseline.

Final principles:

- No Order just because customer asks a question.
- No Order just because purchase intent is detected.
- Create Order only after explicit customer confirmation and backend validation.
- Owner approval remains required.

---

# 50. Order State Machine

Final direction:

```text
PENDING_APPROVAL
      ↓ owner approves
IN_PROGRESS
      ↓
COMPLETED

Cancellation:
PENDING_APPROVAL → CANCELLED
IN_PROGRESS → CANCELLED
```

Earlier wording such as REJECTED was discussed, but the final operational model centers around pending approval, progress, completion, and cancellation.

---

# 51. Order Stock Semantics

Final rule:

> Stock is deducted when owner approves the order and it enters IN_PROGRESS.

Do not deduct stock when:

- customer asks a question
- purchase intent detected
- AI extracts candidate
- PENDING_APPROVAL merely created

Approval transaction should:

1. re-check stock
2. deduct quantity
3. create InventoryMovement with `ORDER_APPROVED`
4. update Order state

Cancellation:

If stock had been deducted:
- restore via InventoryService
- create `ORDER_CANCELLED`

If stock had not been deducted:
- do not restore

---

# 52. OrderItem Snapshot

OrderItem must snapshot the commercial meaning at order time.

Reason:

A future Catalog edit must not rewrite historical orders.

Snapshot may include:

- product name
- price
- quantity
- selected options/variant details later

---

# 53. Notifications

Planned future domain.

Use cases:

- New PENDING_APPROVAL order
- Owner action required
- Important business alerts

Direction:

- persist notification
- FCM push
- notification center
- deep links in Mobile

Not implemented yet.

---

# 54. Dashboard / Daily Brief

Planned later:

- Daily Business Brief
- Tasks & Alerts
- Revenue
- Order breakdown
- Best sellers
- New customers

Not implemented.

---

# 55. Follow-Ups / Abandoned Intent

Planned later.

Concept:

- detect purchase intent
- detect drop-off / abandoned progress
- expose owner follow-up list

Actions:

```text
View Chat
Follow Up
Dismiss
```

Not implemented.

---

# 56. Shared Error Contract

Brandora uses:

```json
{
  "statusCode": 409,
  "code": "IMPORT_NOT_READY",
  "message": "The import job must be READY before execution",
  "error": "Conflict"
}
```

Meaning:

## statusCode
HTTP status.

## code
Stable Mobile-readable/machine-readable code.

## message
English debug/developer detail.

## error
HTTP error label.

Mobile should localize by `code`.

Unexpected internal errors are sanitized.

Never expose:

- SQL
- password
- DB internals
- local path
- storage secret
- stack trace

Important current codes include:

```text
VALIDATION_ERROR
BUSINESS_NOT_FOUND
CATALOG_ITEM_NOT_FOUND
CATALOG_EXTERNAL_KEY_CONFLICT
CATALOG_ATTRIBUTES_INVALID
IMPORT_JOB_NOT_FOUND
IMPORT_NOT_READY
IMPORT_VALIDATION_RESULTS_UNAVAILABLE
INVENTORY_CONFLICT
INTERNAL_SERVER_ERROR
```

---

# 57. Shared Pagination Contract

Canonical shape:

```json
{
  "limit": 20,
  "offset": 0,
  "totalCount": 45,
  "hasMore": true,
  "nextOffset": 20
}
```

Validation:

```text
limit >= 1
limit <= 100
offset >= 0
offset must be a safe integer
unknown query fields rejected
```

Final page:

```text
nextOffset = null
```

Beyond final page:

- empty items/result collections
- global totalCount preserved
- hasMore false
- nextOffset null

Shared helper was introduced under common pagination code.

---

# 58. API Surface — Current Implemented Endpoints

## 58.1 Imports

```http
POST  /businesses/:businessId/imports/excel/analyze
GET   /imports/:importId/mapping
PATCH /imports/:importId/mapping
POST  /imports/:importId/validate
GET   /imports/:importId/validation-results
GET   /imports/:importId/preview
POST  /imports/:importId/execute
GET   /imports/:importId
GET   /businesses/:businessId/imports
```

## 58.2 Catalog

```http
POST   /catalog-items
GET    /catalog-items
GET    /catalog-items/:catalogItemId
PATCH  /catalog-items/:catalogItemId
DELETE /catalog-items/:catalogItemId
```

## 58.3 Inventory

```http
POST /businesses/:businessId/catalog-items/:catalogItemId/inventory/adjust
GET  /businesses/:businessId/catalog-items/:catalogItemId/inventory/movements
GET  /businesses/:businessId/inventory/movements
```

## 58.4 Business Profile

```http
GET   /businesses/:businessId
PATCH /businesses/:businessId
```

## 58.5 Business Settings

```http
GET   /businesses/:businessId/settings
PATCH /businesses/:businessId/settings
```

## 58.6 Working Hours

```http
GET /businesses/:businessId/working-hours
PUT /businesses/:businessId/working-hours
```

---

# 59. Detailed API Contracts

This section summarizes current contract expectations. The dedicated API docs remain the implementation-level source for exact fields.

## 59.1 Analyze Excel

```http
POST /businesses/:businessId/imports/excel/analyze
Content-Type: multipart/form-data
```

Request:

```text
file: required .xlsx
sheetName: optional
```

Response concept:

```json
{
  "importJobId": "...",
  "status": "MAPPING_REQUIRED",
  "sheetNames": ["Products"],
  "selectedSheetName": "Products",
  "headerRow": 3,
  "headers": ["SKU", "Name", "Price", "Stock"],
  "sampleRows": [
    {
      "rowNumber": 4,
      "values": ["P-1", "Coffee", 49.9, 10]
    }
  ],
  "totalRows": 1
}
```

## 59.2 Validate

```http
POST /imports/:importId/validate
```

No pagination query.

Response:

```json
{
  "importId": "...",
  "status": "READY",
  "summary": {
    "totalRows": 100,
    "validRows": 95,
    "invalidRows": 3,
    "skippedRows": 2
  }
}
```

## 59.3 Validation Results

```http
GET /imports/:importId/validation-results?limit=50&offset=0
```

Response contains:
- summary
- pagination
- validRows
- invalidRows

## 59.4 Preview

```http
GET /imports/:importId/preview?limit=50&offset=0
```

Response contains global summary and page subsets of:
- inserts
- updates
- unchanged
- invalidRows

## 59.5 Execute

```http
POST /imports/:importId/execute
```

No file re-upload from Mobile.

## 59.6 Import Status

```http
GET /imports/:importId
```

Used for resume/polling.

## 59.7 Import History

```http
GET /businesses/:businessId/imports?limit=20&offset=0
```

Uses standard pagination envelope.

## 59.8 Manual Inventory

```http
POST /businesses/:businessId/catalog-items/:catalogItemId/inventory/adjust
```

```json
{
  "quantity": 15
}
```

## 59.9 Business Profile PATCH

```http
PATCH /businesses/:businessId
```

Example:

```json
{
  "description": "Fresh bread and pastries",
  "category": "Bakery",
  "address": null
}
```

## 59.10 Business Settings PATCH

```http
PATCH /businesses/:businessId/settings
```

Example:

```json
{
  "acceptsCash": false,
  "deliveryEnabled": true
}
```

## 59.11 Working Hours PUT

```http
PUT /businesses/:businessId/working-hours
```

Requires all seven weekdays.

---

# 60. Prisma / Migration Rules

Project rules:

- UUID primary keys where applicable
- Decimal for money
- JSONB for flexible structured metadata
- indexes for business-scoped reads
- forward-only migrations
- never edit old applied migrations
- no production reset
- descriptive migration names

Production uses:

```bash
npx prisma migrate deploy
```

Not:

```bash
prisma migrate dev
```

on production.

---

# 61. Current Migration History

Known migration history:

```text
20261005000000_init
20261005200111_init
20261005202258_add_import_job_file_key
20261006075041_add_inventory_movement
20261009125310_add_business_profile_settings_working_hours
```

The latest Business migration added:

- Business nullable metadata fields
- BusinessSettings
- DayOfWeek
- WorkingHour
- indexes/constraints

Prompt 1 Inventory API required no schema migration.

Old migrations were not modified during the verified Business work.

---

# 62. Testing Strategy

Testing covers business rules, not only happy-path controllers.

Important areas:

## Imports
- validation
- snapshot
- validation result paging
- duplicate behavior
- preview paging
- import history
- lifecycle
- safe fields

## Catalog
- CRUD
- business scoping
- externalKey conflict
- attributes
- stock rejection

## Inventory
- adjustment
- zero
- no-op
- null → zero
- invalid quantity
- unknown fields
- movement creation
- rollback
- concurrency
- history pagination
- cross-business isolation

## Business
- GET
- PATCH
- nullable clears
- default settings
- settings upsert
- full working week
- invalid schedule
- transaction rollback
- missing business

---

# 63. Latest Verification Results

Latest combined verification:

```text
Test suites: 15 / 15 passed
Tests:       463 / 463 passed
Build:       passed
Format:      passed
Format check: passed
Prisma validate: passed
Prisma generate: passed
git diff --check: passed
```

Prisma Client version at verification:

```text
7.10.0
```

Important caveat:

Several HTTP/domain tests use mocked Prisma state.

The latest verification did not represent a complete real-database E2E run for every new endpoint.

Earlier import flows were manually tested against a real/local database during development, but that does not replace future production integration verification.

---

# 64. API Documentation Structure

Current documentation direction:

```text
README.md
docs/
  imports-api.md
  catalog-api.md
  inventory-api.md
  business-api.md
  api-errors.md
```

A Mobile/Yasmin handoff document is also maintained.

Rule:

> If request/response/error details are long, they belong in `docs/`, not in the README.

---

# 65. README Decision

The README became too large when detailed API examples were repeatedly added.

Final preferred README role:

- What is Brandora
- Current MVP scope
- Stack
- Modules/architecture
- Setup
- `.env`
- Prisma
- Run
- Tests
- Links to API docs
- Known limitations
- Status

The README should **not** duplicate every endpoint’s:
- body
- response
- errors
- workflow detail

Those belong in dedicated API documents.

---

# 66. Mobile Handoff Rules

Backend → Mobile handoff should contain:

- endpoint
- method
- path parameters
- query parameters
- request body
- response body
- error codes
- lifecycle
- pagination
- field semantics
- known limitations

Critical Mobile-specific decisions:

- no manual Excel header selection
- mapping locks after validation
- re-upload/new job if mapping must change later
- validation is one POST
- result pages come from GET validation-results
- preview is paginated
- import can be resumed using import status/history
- Manual stock adjustment uses absolute target quantity
- stable errors localized by `code`

---

# 67. Azure Production Direction

Final hosting decision:

**Azure**

Earlier alternatives such as Render/Koyeb were considered but are not the current chosen direction.

Planned architecture:

```text
Flutter Mobile
      ↓
Azure-hosted NestJS
      ↓
Neon PostgreSQL
      +
Azure Blob Storage
```

Azure student/university benefit was the reason for choosing this direction.

Actual deployment is deferred until after the paused backend checkpoint.

---

# 68. Production Storage Direction

Current local Import storage uses filesystem.

This is fine for local development.

It is **not acceptable as the final production durability solution**.

Production storage should use the existing abstraction.

Direction:

```text
ImportFileStorage
  ├── LocalImportFileStorage
  └── AzureBlobImportFileStorage
```

Durable production storage should cover:

- source workbook
- validation result snapshot
- future durable import artifacts as required

Backend returns opaque IDs/status, not direct local/blob paths.

---

# 69. Environment Variables

Current/planned important variables:

```text
NODE_ENV
DATABASE_URL
PORT
CORS_ORIGINS

IMPORT_STORAGE_DRIVER
AZURE_STORAGE_CONNECTION_STRING
AZURE_STORAGE_CONTAINER
```

Rules:

- `.env` not committed
- `.env.example` placeholders only
- no secrets in README
- no secrets hardcoded
- production configuration from environment

---

# 70. Deployment Commands

Expected production flow:

```bash
npm ci
npx prisma generate
npm run build
npx prisma migrate deploy
npm run start:prod
```

A production health endpoint is planned:

```http
GET /health
```

Minimum response concept:

```json
{
  "status": "ok"
}
```

Health should remain lightweight and read-only.

---

# 71. Security / Privacy / Data Isolation Principles

Current/final security direction:

- strict DTO validation
- reject unknown body/query fields
- business-scoped reads/writes
- sanitized unexpected errors
- no storage path leakage
- no SQL leakage
- no password/secret leakage
- no AI direct DB access
- no client-controlled movement type
- no client-controlled business ownership through body when path already defines it

Auth is still pending and will later add identity/authorization on top of these domain constraints.

---

# 72. Jira Status and Completed Tasks

Relevant backend tasks already marked Done include:

```text
SCRUM-23  Excel analyze endpoint
SCRUM-24  Suggest and save column mapping
SCRUM-25  Normalize & validate imported rows
SCRUM-26  Execute import
SCRUM-28  Catalog Item CRUD
SCRUM-70  Generate import preview / plan
SCRUM-22  Edit business profile
SCRUM-30  Inventory adjustments + movement history
SCRUM-32  Business settings API
SCRUM-16  Share sample JSON request + response
```

Current important open item:

```text
SCRUM-15 — Agree on DB schema (ERD)
```

It remains In Progress intentionally.

Reason:

The full MVP ERD is not fully finalized until these areas are settled:

- Auth / User / BusinessMember
- Policies / FAQ
- Customer / Conversation / Message
- Orders

Next relevant backend task:

```text
SCRUM-33 — Policies and FAQs API
```

---

# 73. Current Known Limitations

## Imports
- local filesystem dependency
- no automatic stuck-job recovery
- preview not frozen
- offset pagination
- older jobs without snapshot may not support result reading

## Catalog
- no variants
- no images
- unkeyed imports cannot reliably match later
- no direct stock edit by design

## Inventory
- no manual adjustment reason
- manual quantity change does not toggle trackInventory
- no DB CHECK for non-negative stock
- offset pages can shift under concurrent writes

## Business
- no Auth yet
- no BusinessMember enforcement
- Business creation currently outside proper authenticated flow
- settings only four booleans
- no deposit configuration yet

## Working Hours
- no overnight
- no multiple intervals
- no holidays
- no timezone

## Production
- Azure not deployed
- Blob storage not implemented
- local snapshots not production durable

---

# 74. Explicitly Deferred Features

Deferred intentionally:

- Auth until current data core was stable
- Catalog variants
- Catalog images
- Options/add-ons
- Two-way Google Sheets sync
- Fuzzy AI Excel mapping
- AI-generated database writes
- Full ERP behavior
- Branches
- Holiday schedule
- split working shifts
- overnight working hours
- Azure deploy during current coding checkpoint
- Orders until Customer/AI/approval flow is ready

---

# 75. Final Architectural Invariants

These should not change accidentally.

1. PostgreSQL is the authoritative database after import.
2. Excel is import/update input, not live sync.
3. Never match product import by name.
4. `(businessId, externalKey)` is import identity when key exists.
5. externalKey is optional for insert.
6. Missing file rows never auto-delete DB products.
7. Blank mapped existing values preserve old values.
8. Duplicate file externalKey invalidates all duplicates.
9. Catalog cannot directly mutate stock.
10. All real stock mutation goes through InventoryService.
11. Every real stock change should have InventoryMovement audit.
12. Business-scoped access is mandatory.
13. Cross-business data must not leak.
14. Mobile relies on stable error codes.
15. Error messages are not localization keys.
16. AI cannot directly mutate authoritative business data.
17. AI cannot approve Orders.
18. Order stock deduction happens on owner approval.
19. Order cancellation restores only previously deducted stock.
20. OrderItems snapshot commercial data.
21. README remains concise.
22. API details belong in docs.
23. Production import files/snapshots use durable storage.
24. Old migrations are never rewritten.
25. Production uses `prisma migrate deploy`.
26. Core remains generic, not vertical-specific.
27. User and Business remain separate.
28. Ownership goes through BusinessMember.
29. No branches in MVP.
30. No hidden write on GET settings.

---

# 76. Recommended Resume Sequence

When development resumes:

## Step 1
Open current code and verify checkpoint.

## Step 2
Implement:

```text
SCRUM-33 — Policies + FAQs
```

## Step 3
Finalize Business Knowledge docs and handoff.

## Step 4
Finalize User/Auth/BusinessMember model.

## Step 5
Close full ERD / SCRUM-15 once major domains are agreed.

## Step 6
Coordinate Backend 2 / AI contracts:

- Customer
- Conversation
- Message
- Order Candidate
- Orders

## Step 7
Prepare production infrastructure:

- Azure App hosting
- Azure Blob storage
- health
- CORS/env
- migration deploy

## Step 8
Deploy backend.

---

# 77. Definition of “Done” for Future Backend Tasks

For Brandora backend, a task should not be called complete just because code compiles.

Recommended Done criteria:

- implementation complete
- business scoping
- DTO validation
- unknown fields rejected
- stable error contract
- docs updated
- Mobile examples added
- tests added
- regression tests pass
- format passes
- build passes
- Prisma validate/generate if schema changed
- migration created if required
- old migrations untouched
- `git diff --check` passes
- no secrets added

---

# 78. Current Resume Checklist

After the pause:

```text
[ ] git pull / inspect latest branch
[ ] git status
[ ] npm install / npm ci if needed
[ ] npx prisma generate
[ ] npx prisma migrate status
[ ] npm test
[ ] npm run build
[ ] review Jira current state
[ ] confirm Mobile handoff still matches backend
[ ] begin Policies/FAQs
```

Before Azure:

```text
[ ] health endpoint
[ ] production PORT
[ ] CORS config
[ ] Azure storage adapter
[ ] durable validation snapshots
[ ] secrets/env review
[ ] Neon production DATABASE_URL
[ ] prisma migrate deploy
[ ] production smoke test
```

---

# 79. Glossary

## Business-scoped
A query/action must be constrained to the owning business.

## externalKey
Owner/external-system stable Catalog identifier, typically SKU/product code.

## ImportJob
Persistent lifecycle record for one Excel import flow.

## Mapping
Defines how Excel columns map to Brandora standard fields/attributes.

## Validation snapshot
Persisted validation result used for page reads without re-running validation.

## Preview
Read-only current plan showing what execution would insert/update/leave unchanged.

## InventoryMovement
Audit record of a stock quantity transition.

## Source of truth
The authoritative persisted business state. For Brandora, PostgreSQL after import.

## PENDING_APPROVAL
Order waiting for owner review.

## IN_PROGRESS
Approved operational order; stock has been deducted according to the final rule.

## Business Knowledge
Owner-configured facts such as policies and FAQs used by Mobile/AI.

---

# 80. Final Snapshot

At the current pause, the Brandora backend is no longer just a project skeleton.

It has a verified core covering:

```text
Business
Catalog
Excel Analyze
Mapping
Normalization
Validation
Validation Results
Preview
Execute
Import Resume
Import History
InventoryService
InventoryMovement
Manual Inventory
Inventory History
Business Profile
Business Settings
Working Hours
Shared Error Contract
Shared Pagination
Documentation
Tests
```

Latest verified quality checkpoint:

```text
15 test suites passed
463 tests passed
Build passed
Prisma validate passed
Prisma generate passed
Format passed
Diff check passed
```

The next clean product-domain task is:

```text
Policies + FAQs / Business Knowledge
```

The next major architecture checkpoint after that is:

```text
Auth + User + BusinessMember + remaining full MVP ERD
```

The next production checkpoint is:

```text
Azure hosting + Azure Blob durable import storage + Neon PostgreSQL
```

---

# Appendix A — Final Decision Matrix

| Topic | Final Decision |
|---|---|
| Backend | NestJS + TypeScript |
| ORM | Prisma |
| Database | PostgreSQL |
| Cloud DB | Neon direction |
| Production hosting | Azure |
| Production file storage | Azure Blob |
| Mobile | Flutter |
| Excel role | Input/update only |
| DB source of truth | PostgreSQL |
| Product identity | businessId + externalKey |
| Name matching | Never |
| Missing file rows | Preserve DB items |
| Blank existing values | Preserve |
| Duplicate SKU in file | All invalid |
| Stock mutation | InventoryService only |
| Stock audit | InventoryMovement |
| Manual stock API | Absolute target quantity |
| Auth | Deferred at current checkpoint |
| User vs Business | Separate |
| Ownership | BusinessMember |
| Branches | Not MVP |
| AI direct DB writes | Forbidden |
| AI order approval | Forbidden |
| Order stock deduction | Owner approval |
| README | Concise |
| API detail | docs/ |
| Working-hours timezone | Deferred |
| Overnight hours | Unsupported MVP |
| Validation snapshot production | Durable storage required |
| Prisma production migration | migrate deploy |

---

# Appendix B — Current API Error Reference

Common codes:

```text
VALIDATION_ERROR
BUSINESS_NOT_FOUND
CATALOG_ITEM_NOT_FOUND
CATALOG_EXTERNAL_KEY_CONFLICT
CATALOG_ATTRIBUTES_INVALID
IMPORT_JOB_NOT_FOUND
IMPORT_NOT_READY
IMPORT_VALIDATION_RESULTS_UNAVAILABLE
INVENTORY_CONFLICT
INTERNAL_SERVER_ERROR
```

Standard response:

```json
{
  "statusCode": 400,
  "code": "VALIDATION_ERROR",
  "message": "Human/developer-readable English message",
  "error": "Bad Request"
}
```

Mobile should use `code` for localization and user-facing messaging.

---

# Appendix C — Current Business Defaults

```json
{
  "acceptsCash": true,
  "acceptsOnlinePayment": false,
  "deliveryEnabled": false,
  "pickupEnabled": true
}
```

---

# Appendix D — Current Pagination Defaults

| Endpoint family | Default |
|---|---:|
| Validation Results | 50 |
| Preview | 50 |
| Import History | 20 |
| Inventory History | 20 |

All paginated APIs cap limit at 100.

---

# Appendix E — Current Working-Hours Rules

```text
7 unique weekdays required
HH:mm
same-day only
opensAt < closesAt
closed day => null/omitted times
no overnight
no split shifts
no timezone
no holiday exceptions
```

---

# Appendix F — Current Import Storage Limitation

Local development:

```text
.storage/imports/
```

Validation snapshot:

```text
<uuid>.validation.json
```

Production requirement:

```text
Do not depend on ephemeral local disk.
Move source workbook + validation artifacts to durable Azure Blob-backed storage.
```

---

# Appendix G — Jira Checkpoint

Done:

```text
SCRUM-16
SCRUM-22
SCRUM-23
SCRUM-24
SCRUM-25
SCRUM-26
SCRUM-28
SCRUM-30
SCRUM-32
SCRUM-70
```

Still intentionally open:

```text
SCRUM-15 — Full ERD agreement
SCRUM-33 — Policies and FAQs
```

---

# Appendix H — Historical / Prototype Clarification

Some work was produced during exploration for WhatsApp and AI as separate prototype/patch artifacts.

Those artifacts are useful for:

- validating concepts
- reusing test ideas
- defining integration contracts
- accelerating future implementation

But they must **not be confused with the verified current merged backend** unless the team explicitly merges/adopts them.

This Master document therefore distinguishes:

- **Implemented baseline**
- **Final planned architecture**
- **Prototype / deferred work**

That distinction should be preserved in every future handoff.

