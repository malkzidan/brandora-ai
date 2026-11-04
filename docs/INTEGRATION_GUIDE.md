# Brandora AI Service — Integration Guide & Status Report

> Historical **v1** guide. Current standalone read-only chatbot instructions are
> in [LOCAL_CHATBOT.md](LOCAL_CHATBOT.md); verified Backend main and missing
> contracts are in [BACKEND_HANDOFF.md](BACKEND_HANDOFF.md). Legacy order-candidate
> examples below do not enable Orders in the new conversational application.

| | |
|---|---|
| **Service version** | v3.1 (431 automated tests passing) |
| **Date** | 26 Oct 2026 |
| **Audience** | Backend team (NestJS: Yomna, Shrouk) and project leads |
| **AI owner** | Malak |
| **Contract** | E0-3 *Structured Order Candidate JSON Contract*, Schema 1.0 (implemented literally) |
| **Endpoint** | `POST /v1/ai/respond` |

> **Honesty note.** Everything in this document was checked against the code and the test-suite. The one thing that has **not**
> been verified is a *successful call to the live Gemini API* (the build sandbox has no route to Google). That is item #1 of the
> go-live checklist in §3.3.

---

## 0. At a glance

```
 WhatsApp ──► Backend webhook ──► ingestInboundMessage (store the customer message, status 200 to Meta immediately)
                                      │
                                      ▼
                         build ONE JSON payload (business, customer, conversation, catalog, knowledge, orders, message)
                                      │   POST /v1/ai/respond   + header  X-Internal-Token
                                      ▼
                              ┌──────────────────┐
                              │   AI Service     │  stateless: it keeps NOTHING between calls
                              └──────────────────┘
                                      │   { intent, reply, requiresReview, orderCandidate }
                                      ▼
   1. store `reply` VERBATIM as a Message(senderType = AI)      ◄── §1.4-C  (the AI reads its own reply back next turn)
   2. send `reply` to the customer on WhatsApp
   3. if intent == CONFIRMED_ORDER  → validate `orderCandidate`, create Order(PENDING_APPROVAL)   ◄── §1.4-A
   4. if requiresReview == true     → notify the business owner                                   ◄── §1.4-B
```

**The six rules for the backend** (details below):

1. Send the **active and inactive** catalog as-is; the AI strips `isActive=false` itself. Always send the real `isActive` value.
2. Always send `business.settings` and `business.workingHours` (rows). Omitting `settings` is read as *"delivery not available"*.
3. Always send `messageId` (the stored id of the customer's message). It becomes `orderCandidate.sourceMessageId`.
4. **Store the AI `reply` exactly as received** with `senderType: AI`, and include it in `conversation` next time (§1.4-C).
5. Create an order **only** when `intent == "CONFIRMED_ORDER"` **and** `orderCandidate != null`; status `PENDING_APPROVAL`; fill prices from the DB (§1.4-A).
6. `requiresReview == true` means **notify the owner**, even when there is no `orderCandidate` (§1.4-B).

---

## 1. Integration contract (for the Backend team)

### 1.1 Transport

| Item | Value |
|---|---|
| Method / path | `POST /v1/ai/respond` |
| Content type | `application/json; charset=utf-8` |
| Auth | Header `X-Internal-Token: <AI_SERVICE_TOKEN>` (constant-time comparison). **If the service has no token configured it is open** (it logs a warning). |
| Health | `GET /health` (no auth). `GET /health?probe=true` makes one tiny live call per model role. |
| Idempotency | The service is stateless and **not** idempotent about wording: the same `messageId` sent twice can produce differently-worded replies when Gemini is on. De-duplicate on **your** side (§1.4-E). |
| Message length | `message` ≤ 2000 characters, non-empty. |

**Status codes**

| Code | Body | Meaning / what to do |
|---|---|---|
| `200` | E0-3 `AiResponse` | Success. |
| `400` | `{"error":"VALIDATION_ERROR","details":[{"field":"messageId","message":"…"}]}` | Your payload is wrong. **Do not retry**; log `details`. |
| `401` | `{"detail":"invalid or missing X-Internal-Token"}` | Wrong/missing token. Do not retry. |
| `503` | `{"error":"AI_UNAVAILABLE",…}` + `Retry-After: 10` | Gemini is down **and** `AI_FALLBACK_TO_RULES=false`. Leave the message pending and retry later. (With the default `true` you never get this; you get a rule-engine answer instead.) |
| `500` | `{"error":"INTERNAL_ERROR"}` | Bug on our side (stack trace stays in our logs). Retry once, then fall back to a safe canned reply. |

**Timeouts.** Typical latency is a few hundred ms to a few seconds with Gemini *(not yet measured live; the rule engine answers in a few ms)*.
Worst case with the defaults is ≈ 74 s (router and generator each use their full budget). With
`GEMINI_TIMEOUT_SECONDS=8` and `GEMINI_TOTAL_TIMEOUT_SECONDS=10` it is ≈ 36 s. **Set your HTTP client timeout to 45 s** and acknowledge Meta's
webhook *before* calling the AI.

### 1.2 The request — `AIRespondRequest`

#### Full example

The payload below is the exact one used to generate every example in §1.3 (validated by the service on every run).

```json
{
  "business": {
    "id": "0bfc71e2-0728-4d39-8103-8410b644f945",
    "name": "Brandora Demo Store",
    "description": null,
    "category": "Retail",
    "phone": "01012345678",
    "address": "Cairo, Egypt",
    "settings": {
      "acceptsCash": true,
      "acceptsOnlinePayment": false,
      "deliveryEnabled": false,
      "pickupEnabled": true
    },
    "workingHours": [
      {
        "dayOfWeek": "MONDAY",
        "isOpen": true,
        "opensAt": "09:00",
        "closesAt": "21:00"
      },
      {
        "dayOfWeek": "TUESDAY",
        "isOpen": true,
        "opensAt": "09:00",
        "closesAt": "21:00"
      },
      {
        "dayOfWeek": "WEDNESDAY",
        "isOpen": true,
        "opensAt": "09:00",
        "closesAt": "21:00"
      },
      {
        "dayOfWeek": "THURSDAY",
        "isOpen": true,
        "opensAt": "09:00",
        "closesAt": "21:00"
      },
      {
        "dayOfWeek": "FRIDAY",
        "isOpen": false,
        "opensAt": null,
        "closesAt": null
      },
      {
        "dayOfWeek": "SATURDAY",
        "isOpen": true,
        "opensAt": "10:00",
        "closesAt": "22:00"
      },
      {
        "dayOfWeek": "SUNDAY",
        "isOpen": true,
        "opensAt": "09:00",
        "closesAt": "21:00"
      }
    ]
  },
  "customer": {
    "id": "7d3c1f0e-6a2b-4c58-9b1e-3f5a8d2c4e10",
    "phone": "201000000001",
    "name": "Malak"
  },
  "conversation": [
    {
      "id": "9f1d2c3b-4a5e-4f60-8a7b-1c2d3e4f5a6b",
      "senderType": "CUSTOMER",
      "content": "التيشيرت بكام؟",
      "messageType": "TEXT",
      "createdAt": "2026-10-26T09:30:00.000Z"
    }
  ],
  "catalog": [
    {
      "id": "fde347c5-dd42-4e1b-9322-d8b999ea50e2",
      "externalKey": "SKU-NEW-001",
      "name": "T-Shirt",
      "description": "New product",
      "category": "Shirts",
      "basePrice": "299.99",
      "trackInventory": true,
      "stockQuantity": 10,
      "attributes": {
        "Material": "Cotton",
        "Color": "Black, White",
        "Size": "S, M, L"
      },
      "isActive": true
    },
    {
      "id": "0efe3bf8-6dca-4101-9eb7-4ee6eb2ffce2",
      "externalKey": "SKU-EXISTING",
      "name": "Updated Hoodie",
      "description": null,
      "category": "Hoodies",
      "basePrice": "450",
      "trackInventory": true,
      "stockQuantity": 7,
      "attributes": {
        "Material": "Fleece"
      },
      "isActive": true
    },
    {
      "id": "d5e3608d-2f89-46c3-b94d-86beb0858738",
      "externalKey": "SKU-OLD",
      "name": "Old Cap",
      "description": null,
      "category": "Caps",
      "basePrice": "75.5",
      "trackInventory": false,
      "stockQuantity": null,
      "attributes": null,
      "isActive": false
    }
  ],
  "businessKnowledge": {
    "policies": {
      "returns": "الاستبدال والاسترجاع متاح خلال 14 يوم من الاستلام بشرط المنتج يكون بحالته ومعاه الفاتورة."
    },
    "faqs": [
      {
        "id": "a1b2c3d4-0000-4000-8000-000000000001",
        "question": "الباقة بكام؟",
        "answer": "الباقة الأساسية بـ 500 جنيه.",
        "isActive": true
      },
      {
        "id": "a1b2c3d4-0000-4000-8000-000000000002",
        "question": "فيه فرع في الاسكندرية؟",
        "answer": "أيوه، فرع سموحة.",
        "isActive": true
      }
    ]
  },
  "message": "التيشيرت بكام؟",
  "messageId": "9f1d2c3b-4a5e-4f60-8a7b-1c2d3e4f5a6b",
  "customerOrders": [
    {
      "id": "c0ffee00-0000-4000-8000-000000001002",
      "orderNumber": 1002,
      "status": "IN_PROGRESS",
      "createdAt": "2026-10-20T10:00:00.000Z",
      "items": [
        {
          "name": "Updated Hoodie",
          "quantity": 1
        }
      ]
    }
  ]
}
```

#### Field reference

**Top level**

| Field | Type | Required | Notes |
|---|---|---|---|
| `business` | object | **yes** | See below. |
| `customer` | object | **yes** | `id` (UUID) required; `phone`, `name` optional. |
| `conversation` | array | no | Earlier messages (§ below). Missing = no history. |
| `catalog` | array | no | `CatalogItem` rows. Missing = empty catalog. |
| `businessKnowledge` | object | no | `policies` + `faqs` (§ below). Currently empty in the DB. |
| `customerOrders` | array | no | **Send it whenever it exists** (even `[]`). Without the key the AI answers "I can't see order statuses right now". |
| `message` | string **or** `{ "id": uuid, "text": string }` | **yes** | The customer's new message. |
| `messageId` | UUID | **yes** (unless `message.id` is given) | Stored id of the customer's message → `orderCandidate.sourceMessageId`. Missing = `400`. |

Unknown extra fields anywhere are **ignored**, so you can forward database rows as they are.

**`business`**

| Field | Type | Required | Notes |
|---|---|---|---|
| `id`, `name` | UUID, string | **yes** | |
| `description`, `category`, `phone`, `address` | string \| null | no | `address` and `phone` are used verbatim for "where are you / what's your number". |
| `settings` | object | no, **but always send it** | `acceptsCash`, `acceptsOnlinePayment`, `deliveryEnabled`, `pickupEnabled` (booleans). **Defaults when omitted: cash `true`, online `false`, delivery `false`, pickup `true`.** |
| `workingHours` | **array of rows** | no | One row per day: `{ "dayOfWeek": "MONDAY"…"SUNDAY", "isOpen": bool, "opensAt": "09:00", "closesAt": "21:00" }` (24-hour `HH:MM`, `null` when closed). A closing time after midnight (`"02:00"`) is fine. Missing days are skipped. **No time-zone logic:** hours are spoken exactly as stored. A JSON object instead of a list is rejected with `400`. |

How the rows become a reply (Egyptian week, Saturday first, equal consecutive days merged):
`بنشتغل السبت من 10 الصبح لـ 10 بالليل، ومن الأحد للخميس من 9 الصبح لـ 9 بالليل، والجمعة إجازة.`
(English customers get: *We're open Saturday 10:00 AM–10:00 PM, Sunday to Thursday 9:00 AM–9:00 PM, and closed on Friday.*)

Delivery and payment answers come from `settings`:

| Condition | Reply |
|---|---|
| `deliveryEnabled=false`, `pickupEnabled=true` | التوصيل مش متاح حالياً، والاستلام من الفرع متاح. |
| `deliveryEnabled=false`, `pickupEnabled=false` | التوصيل مش متاح حالياً. |
| `deliveryEnabled=true` | التوصيل متاح، والأسعار هتتحدد من صاحب المحل. |
| cash only / online only / both / none | بنقبل الدفع كاش. / …أونلاين. / …كاش وأونلاين. / طرق الدفع مش متسجلة عندي دلوقتي. |

If `businessKnowledge.policies.delivery` (or `payment`) text exists it **overrides** the default sentence.

**`catalog[]` (one `CatalogItem` row each)**

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | UUID | **yes** | Becomes `orderCandidate.items[].catalogItemId`. |
| `name` | string | **yes** | Used verbatim in replies (never translated). Rows with an empty name are dropped. |
| `basePrice` | string \| number \| null | no | `"299.99"`. `null` → "the price isn't on file". **The AI never sends prices back in the candidate** (§1.3). |
| `trackInventory`, `stockQuantity` | bool, int \| null | no | `trackInventory=false` → always available. `true` + `stockQuantity=0` → "sold out". Quantity above stock → "only N available". |
| `category`, `description`, `externalKey` | string \| null | no | `category` is used to list sections and suggest alternatives. |
| `attributes` | **flat** object \| null | no | Owner-defined keys from the Excel import (see next table). |
| `isActive` | bool | no, **send the real value** | `false` → the item is **removed before any prompt is built** and can never be offered, priced or sold. Omitted = treated as `true`. |

What the AI reads from the flat `attributes` (keys are case/language-insensitive; values may be `"Black, White"`, `"S/M/L"`, `"أسود و أبيض"`, or a JSON list):

| Meaning | Accepted keys | Effect |
|---|---|---|
| Colour options | `Color`, `Colour`, `Colors`, `لون`, `اللون`, `الالوان` | **1 value** = fixed colour; **2+ values** = the customer must choose; **none** = the customer's colour is kept as typed and flagged for review. |
| Size options | `Size`, `Sizes`, `مقاس`, `المقاس`, `المقاسات`, `سايز` | Same rules as colour. |
| Material | `Material`, `material` | Only helps search ("cotton hoodie"). |
| Service | `Type: "Service"` (or `خدمة`) | The item is booked, not shipped; the AI asks for the time. |
| Anything else | e.g. `Brand`, `Fabric` | Ignored (kept for the future). |

Colour/size policy in one table:

| Catalog says | Customer says | Result |
|---|---|---|
| `Color: "Black, White"` | "أحمر" | AI asks again with the valid options. |
| `Color: "Black, White"` | "أسود" / "black" | Matched to `Black`, no review. |
| *no colour attribute* (today's real data) | "أحمر" | **Kept as typed** in `selectedAttributes.color`, `reviewReasons:["VARIANT_UNCLEAR"]`, `requiresReview:true`. |

**`businessKnowledge`** (owner-written knowledge, backend task SCRUM-33)

```json
{
  "policies": { "delivery": "…", "payment": "…", "returns": "…", "location": "…" },
  "faqs": [
    { "id": "…", "question": "الباقة بكام؟", "answer": "الباقة الأساسية بـ 500 جنيه.", "isActive": true }
  ]
}
```

| Part | Rules |
|---|---|
| `policies` | Free text, **sent to the customer verbatim**. Keys the AI reads: `delivery`, `payment`, `returns`, `location`. Unknown keys are ignored. |
| `faqs[]` | `question` and `answer` are **both required and non-empty**; `keywords` (array of strings) is **optional**; `isActive:false` rows are dropped; every other column is ignored. Max **40** are used (first 40 after cleaning). Order is irrelevant. See §2. |

**`customerOrders[]`** (this customer's orders)

| Field | Type | Notes |
|---|---|---|
| `orderNumber` | int \| string | Quoted to the customer (`#1002`) and used to match "طلب رقم 1002". |
| `status` | string | Active = `PENDING`, `PENDING_APPROVAL`, `IN_PROGRESS`. Anything else (`COMPLETED`, `CANCELLED`, …) is "not active". Known statuses are spoken as: مستني التأكيد / مستني موافقة صاحب المحل / قيد التنفيذ / اتسلم / اتلغى (English: pending / waiting for the owner's approval / in progress / delivered / cancelled). Unknown strings are echoed raw. |
| `items[]` | `{ "name", "quantity" }` | Shown as "(Updated Hoodie)". |
| `createdAt` | ISO string | Used to order orders newest-first. |

**`conversation[]`**

| Field | Notes |
|---|---|
| `senderType` | `CUSTOMER` → inbound. `AI` **and** `OWNER` → outbound (the AI must see what the owner typed by hand). |
| `content`, `messageType` | Only non-empty `TEXT` messages are used. Images/voice are ignored. |
| `createdAt` | Any order is accepted; the service sorts by it. The last 12 messages are used. |
| current message | May or may not be included; it is removed if its `id` equals `messageId` or its text is identical. |
| `content` of `AI` rows | **Must be the exact reply string the AI returned** (§1.4-C). |

### 1.3 The response — `AiResponse` (E0-3 Schema 1.0)

The body has **exactly four keys** (`additionalProperties:false`); every response is validated against the official JSON Schema in our tests.

```json
{ "intent": "INQUIRY | PURCHASE_INTENT | CONFIRMED_ORDER | OTHER",
  "reply": "string (never empty)",
  "requiresReview": false,
  "orderCandidate": null }
```

The AI **never** sends `unitPrice`, `total`, `stock`, `status`, `deliveryFee` or `deposit`. `orderCandidate` is non-null **only** when `intent == "CONFIRMED_ORDER"`.

**How the 16 internal intents map to E0-3** (the internal one is in the response header `X-AI-Detailed-Intent`):

| Internal intent | `intent` in body | `requiresReview` |
|---|---|---|
| `PRODUCT_INQUIRY`, `PRICE_INQUIRY`, `GENERAL_INFO`, `ORDER_STATUS`, `HELP`, `RETURNS_POLICY` | `INQUIRY` | `false` |
| `CREATE_ORDER` (summary / question to the customer) | `PURCHASE_INTENT` | `false` |
| `CREATE_ORDER` after the customer said *yes* | `CONFIRMED_ORDER` | `true` only if the candidate has `reviewReasons` |
| `ORDER_CANCEL`, `ORDER_MODIFY` (asking "are you sure?") | `OTHER` | `false` |
| `ORDER_CANCEL`, `ORDER_MODIFY` after the customer said *yes* | `OTHER` | **`true`** |
| `PAYMENT_DISPUTE`, `LEGAL_THREAT`, `CUSTOM_REQUEST` | `OTHER` | **`true`** |
| `COMPLAINT` | `OTHER` | `true` only after a dispute/threat in the last 3 customer messages (or if the model flagged it) |
| `GREETING`, `THANKYOU`, `UNKNOWN` | `OTHER` | `false` |

> **About the wording.** The examples below were produced by the real service with `AI_PROVIDER=rules` (deterministic text). With Gemini on, replies to
> *product / price / order* questions may be phrased a little differently (same facts, same confirmation question, filtered by the safety guard).
> Structure, `intent`, `requiresReview` and `orderCandidate` are identical in both modes, and FAQ / policy / hours / delivery / payment replies are verbatim in both.

#### Example 1 — `INQUIRY` (price question; read from the catalog)

Customer: **التيشيرت بكام؟**

```json
{
  "intent": "INQUIRY",
  "reply": "T-Shirt بـ 299.99 جنيه.",
  "requiresReview": false,
  "orderCandidate": null
}
```

#### Example 2 — `PURCHASE_INTENT` (order summary, **not confirmed yet** → no `orderCandidate`)

Customer: **عايز أطلب 2 تيشيرت أسود مقاس M**

```json
{
  "intent": "PURCHASE_INTENT",
  "reply": "تمام! T-Shirt Black مقاس M، كمية 2، الإجمالي 599.98 جنيه.\nتحب تأكد الطلب؟",
  "requiresReview": false,
  "orderCandidate": null
}
```

Nothing is created yet. The reply ends with the confirmation question the next turn depends on.

#### Example 3 — `CONFIRMED_ORDER` (customer replied "ايوه اكد" to that summary)

```json
{
  "intent": "CONFIRMED_ORDER",
  "reply": "تمام، هجهز طلبك للمراجعة: T-Shirt Black مقاس M، كمية 2.",
  "requiresReview": false,
  "orderCandidate": {
    "sourceMessageId": "9f1d2c3b-4a5e-4f60-8a7b-1c2d3e4f5a6b",
    "confidence": 0.9,
    "reviewReasons": [],
    "notes": null,
    "items": [
      {
        "catalogItemId": "fde347c5-dd42-4e1b-9322-d8b999ea50e2",
        "variantId": null,
        "rawText": "عايز أطلب 2 تيشيرت أسود مقاس M",
        "quantity": 2,
        "selectedAttributes": {
          "color": "Black",
          "size": "M"
        },
        "notes": null,
        "confidence": 0.9
      }
    ]
  }
}
```

#### Example 3b — `CONFIRMED_ORDER` with `requiresReview: true` (the colour/size the catalog cannot verify)

Customer asked for *"Updated Hoodie أحمر مقاس L"*; the hoodie has no colour/size options in the catalog:

```json
{
  "intent": "CONFIRMED_ORDER",
  "reply": "تمام، هجهز طلبك للمراجعة: Updated Hoodie أحمر مقاس L، كمية 1.",
  "requiresReview": true,
  "orderCandidate": {
    "sourceMessageId": "9f1d2c3b-4a5e-4f60-8a7b-1c2d3e4f5a6b",
    "confidence": 0.6,
    "reviewReasons": [
      "VARIANT_UNCLEAR"
    ],
    "notes": null,
    "items": [
      {
        "catalogItemId": "0efe3bf8-6dca-4101-9eb7-4ee6eb2ffce2",
        "variantId": null,
        "rawText": "هاخد 1 Updated Hoodie أحمر مقاس L",
        "quantity": 1,
        "selectedAttributes": {
          "color": "أحمر",
          "size": "L"
        },
        "notes": null,
        "confidence": 0.6
      }
    ]
  }
}
```

#### Example 4 — `OTHER` with `requiresReview: true` (cancellation confirmed by the customer)

Step 1: customer says **عايز ألغي الأوردر** → the AI asks (still `requiresReview:false`):

```json
{
  "intent": "OTHER",
  "reply": "عايز تلغي طلب رقم 1002 (Updated Hoodie)؟ اكتب (ايوه) لتأكيد الإلغاء.",
  "requiresReview": false,
  "orderCandidate": null
}
```

Step 2: customer says **ايوه** → the owner must act:

```json
{
  "intent": "OTHER",
  "reply": "تمام. إلغاء طلب رقم 1002 محتاج صاحب المحل يأكده بنفسه.",
  "requiresReview": true,
  "orderCandidate": null
}
```

The AI **cannot cancel or change orders** and never says it did. It only states that the owner must confirm.

#### Example 5 — `OTHER` with `requiresReview: true` (payment dispute)

Customer: **أنا دفعت ومحدش رد**

```json
{
  "intent": "OTHER",
  "reply": "آسف على اللي حصل. ممكن تبعتلي رقم الطلب وطريقة الدفع ووقت الدفع بالتقريب؟\nده بيساعد صاحب المحل يراجع الموضوع.",
  "requiresReview": true,
  "orderCandidate": null
}
```

#### Debug headers (not part of the contract, safe to log)

| Header | Values |
|---|---|
| `X-AI-Source` | `gemini` (router ran on Gemini), `rules` (rule engine: `AI_PROVIDER=rules` or Gemini failed), `hard-rule` (greeting/thanks/yes/no decided in code, no LLM call) |
| `X-AI-Detailed-Intent` | One of the 16 internal intents. **Use it to tell the owner *what kind* of review this is.** |
| `X-AI-Router-Model`, `X-AI-Generator-Model` | Present only when a Gemini call produced the answer. |
| `X-AI-Guard` | `fallback-to-template` when a Gemini rewrite was rejected by the safety guard and the verified template was sent instead. |
| `X-AI-Latency-Ms` | Server-side time. |

### 1.4 What the Backend must do with the response

#### A. `orderCandidate` → a real order

*Principle from E0-3: **AI suggests → Backend validates → Database stores → Owner approves.** The AI output is not trusted until it passes your validation.*

1. Trigger: `response.intent === "CONFIRMED_ORDER" && response.orderCandidate != null`. Do nothing order-related otherwise.
2. Validate (E0-3 rules V1–V11; the AI already enforces the ones marked ✓):

| Rule | Check | If it fails |
|---|---|---|
| V1/V2/V3 ✓ | Schema valid; candidate only with `CONFIRMED_ORDER`; `items` non-empty | reject whole output (`INVALID_ORDER_CANDIDATE`, 422 internally), send the customer a safe clarification, **create no order** |
| V4 | `catalogItemId` is a UUID of an **active** item **of this business** | flag the item `UNMATCHED_ITEM`, `requiresReview = true`; never guess by name |
| V5 | `variantId` (always `null` today) | n/a |
| V6/V7 ✓ | `quantity` integer 1–100; `confidence` within 0–1 | reject whole output |
| V8 | candidate/item `confidence` below **your** threshold (E0-3: 0.7, Backend config) | `requiresReview = true` + `LOW_ITEM_CONFIDENCE` (**the AI never sets this one**) |
| V9 | Never lower `requiresReview` | — |
| V10 ✓ | No forbidden fields (`unitPrice`, `total`, …) | reject whole output |
| V11 | Re-check stock and price **from the DB at creation time** | `OUT_OF_STOCK_RISK` + review. **Do not deduct stock here.** |

3. Create `Order` with status **`PENDING_APPROVAL`**. For each item take a **snapshot from the DB**: `productName`, `unitPrice` (database price, not anything the customer saw), `quantity`, `selectedAttributes` (as received; **never translated**).
4. Persist `sourceMessageId`, `confidence`, `reviewReasons` and `requiresReview` on the order; show them in the owner's "needs review" badge.
5. Notify the owner (§B). **Stock is deducted only when the owner approves** (E0-3 V11 / `ORDER_APPROVED` movement), never at creation.
6. The AI never says the order was *accepted*; its wording is "تمام، هجهز طلبك للمراجعة…". Keep it that way in any message you add.

What the AI guarantees about a candidate (all tested): one item per candidate today (the schema allows more); `catalogItemId` comes from the catalog **you** sent
(null only if your id is not a UUID); `selectedAttributes` keys are `color` / `size`; the value is the catalog's own string when it matched an option, otherwise
the customer's own words; `notes` carries a booking time for services; `rawText` ≤ 300 chars (the customer's messages that built the order, never a bare "yes");
`confidence` ≤ 0.97, `0.6` when options were kept unverified, `0.4` for a non-UUID id; `reviewReasons` the AI can emit: `VARIANT_UNCLEAR`, `UNMATCHED_ITEM`, `OUT_OF_STOCK_RISK`
(when the quantity equals the remaining stock).

Illustrative handler (NestJS-style; adapt to your services):

```ts
const ai = await this.aiClient.respond(payload);                       // POST /v1/ai/respond, 45 s timeout

await this.db.transaction(async (tx) => {
  await tx.message.create({ conversationId, senderType: 'AI', content: ai.reply });   // VERBATIM (§C)
  if (ai.intent === 'CONFIRMED_ORDER' && ai.orderCandidate) {
    const order = await this.orders.createFromCandidate(ai.orderCandidate, tx);       // validates V4/V8/V11, status PENDING_APPROVAL,
  }                                                                                   // unique index on sourceMessageId
});
await this.whatsapp.sendText(customerPhone, ai.reply);                 // send what you stored
if (ai.requiresReview) await this.notifications.notifyOwner(businessId, { kind: detailedIntent, conversationId });
```

#### B. `requiresReview: true` → notify the business owner

`requiresReview` can be `true` **without an `orderCandidate`**. In that case it means *"the owner must look at this conversation now"*:

| Trigger (`X-AI-Detailed-Intent`) | Customer example | What the owner should see |
|---|---|---|
| `PAYMENT_DISPUTE` | "أنا دفعت ومحدش رد" | Payment problem: check payment and order. |
| `LEGAL_THREAT` | "هشتكي عليكم" | Escalation: handle personally. |
| `CUSTOM_REQUEST` | "عايز تصميم خاص" | Custom work to negotiate. |
| `ORDER_CANCEL` | "ايوه" after the AI asked *"عايز تلغي طلب رقم 1002؟"* | Cancellation requested for order #1002 (the number is in the reply text). |
| `ORDER_MODIFY` | "ايوه" after *"عايز تعدّل طلب رقم 1002؟"* | Change requested; the customer was asked to describe it in the next message. |
| `COMPLAINT` | a complaint after a dispute/threat | Continuing escalation. |
| `CREATE_ORDER` (`CONFIRMED_ORDER`) | order with `reviewReasons` | Order needs a human check before approval. |

The body only says **that** a review is needed; use the `X-AI-Detailed-Intent` header (and the conversation) to say **what for**.
For cancel/modify the structured data (which order, what change) lives only in the reply text and the conversation today.

> ⚠ **To confirm with the backend team:** E0-3 defines `requiresReview` for *orders*. The AI also uses it on non-order replies. If the backend does not notify the owner in
> that case, payment disputes, legal threats and cancellations will be silently dropped.

#### C. Save the AI `reply` **exactly as received**

The service is **stateless**. It does not remember the conversation: it **re-reads your `conversation` array on every call**, including the last message it sent.
It decides what the customer means by looking for fixed phrases inside that last AI message:

| If the last AI message contains… | …the next customer message is interpreted as |
|---|---|
| `تحب تأكد الطلب؟` / `تحب تأكد الحجز؟` / `Would you like to confirm the order?` | an answer to the **order summary**: "ايوه" → `CONFIRMED_ORDER` + candidate; "لا" → nothing created |
| `…لتأكيد الإلغاء.` / `…to confirm the cancellation.` | an answer to the **cancel question** |
| `…لتأكيد التعديل.` / `…to confirm the change.` | an answer to the **modify question** |
| `تحب أنهي لون…`, `كام واحدة`, `الميعاد امتى`, `How many would you like?`, `Which color…` | a **short answer to an open question** ("أسود L اتنين", "two") that must be joined to the product discussed earlier |

If the backend does **not** store the reply, trims it, reformats it, translates it, or stores something else, then **"ايوه اكد" is just the word "yes"** to the AI: no order is created,
cancellations are not recognised, and "أسود L اتنين" loses its product. This is a silent failure, so please:

- store `reply` **byte-for-byte** (`senderType: AI`) **before** you send it, and send the same string;
- include it in `conversation` on the next call (and store the owner's manual replies as `senderType: OWNER`);
- if WhatsApp splits it into several parts, still store **one** message with the original string;
- never store `clarificationQuestion`-style text of your own in its place (there is none in this contract).

The service defends this on its side too: if Gemini rephrases a reply and drops one of these phrases, the safety guard discards the rewrite and sends the verified template.

#### D. A whole conversation, turn by turn

| # | Customer says | `intent` / detailed | `requiresReview` | Backend action |
|---|---|---|---|---|
| 1 | التيشيرت بكام؟ | `INQUIRY` / PRICE_INQUIRY | false | store + send reply |
| 2 | عايز أطلب 2 تيشيرت أسود مقاس M | `PURCHASE_INTENT` / CREATE_ORDER | false | store + send reply (ends with "تحب تأكد الطلب؟") |
| 3 | ايوه اكد | `CONFIRMED_ORDER` + `orderCandidate` | false (or true with reasons) | **create Order `PENDING_APPROVAL`**, store + send reply, notify owner (new order) |
| 4 | أنا دفعت ومحدش رد | `OTHER` / PAYMENT_DISPUTE | **true** | store + send reply, **notify owner** |

#### E. Errors, retries, idempotency

- Reply to Meta's webhook first; call the AI afterwards, asynchronously.
- `400`/`401`: configuration bug, never retry. `503`: retry later (message stays pending). `500`/timeout: retry once, then send your own safe canned reply.
- Create a **unique index on the order's `sourceMessageId`**: WhatsApp redelivery or your retry must not create two orders. Skip the AI call if you already stored an AI reply for that `messageId`.
- Only call the service for **text** messages. Images and voice notes are not handled yet (§3.4).

---

## 2. The dynamic FAQ mechanism

### 2.1 How it works

Every business has questions nobody can predict ("اللمبة الحمرا معلقة", "الباقة بكام", "الموز بيوصل امتى"). The owner writes them as FAQ rows; the AI never answers them from its own knowledge.

1. **Clean.** From `businessKnowledge.faqs` keep rows with a non-empty `question` **and** `answer` and `isActive != false`; keep the first 40. This ordered list is the *numbered list* for this request.
2. **Number.** The Router prompt receives the questions **numbered** (`1. الباقة بكام؟ [keywords: …]`). **Answers are never sent to the model.**
3. **Route.** The Router returns `{"intents":["GENERAL_INFO"],"faq_topic":"OTHER","faq_id": 2}`; it matches by *meaning*, so different wording and typos work.
4. **Resolve.** The pipeline reads `faqs[faq_id - 1].answer` **from your data** and sends it **verbatim**. A `faq_id` that is not in the list is discarded (never an out-of-range lookup).
5. **Safety nets in code** (they work with or without Gemini):
   - a question that matches an FAQ but was classified `PRICE_INQUIRY` / `PRODUCT_INQUIRY` / `UNKNOWN` is **re-routed to `GENERAL_INFO`**, as long as it names no catalog product;
   - a real catalog question ("التيشيرت بكام؟") is **never** hijacked by an FAQ with similar words: the catalog is the source of truth for prices and stock;
   - if nothing matches, the reply is *"معلش معنديش معلومة مؤكدة عن ده دلوقتي…"*. Nothing is invented.
6. **Verbatim.** FAQ, policy, hours, delivery and payment answers bypass the text generator completely, so owner-written text is never reworded.

Without Gemini (`AI_PROVIDER=rules`, or Gemini is down) step 3 is replaced by lexical matching: all content words of the FAQ question must appear in the message
(typos and Arabic prefixes tolerated), or the FAQ's optional `keywords` must.

### 2.2 `mock_data.py` is only a simulation

- `mock_data.py` is a **development fixture** (3 fake businesses, 46 products of which 2 are inactive, 10 customers). It is imported in exactly two places: `app/dev.py` (the `/v1/dev/*` playground, **off by default**:
  `ENABLE_DEV_ENDPOINTS=false`) and the tests.
- The production path never loads it. This is pinned by the test `test_production_path_never_imports_the_mock_fixture`, which starts the app in a fresh interpreter and asserts that `"mock_data" in sys.modules` is `False`.
- Its FAQ entries are just sample rows. The service contains **no FAQ text of its own**.

### 2.3 Proof that real PostgreSQL FAQ rows work with no code change

The test module `tests/test_handoff_hardening.py` uses a business that exists **nowhere in the codebase** (a gym), with FAQ rows shaped like a database table:
`{ id, businessId, question, answer, isActive, sortOrder, createdAt, updatedAt }`: **no `keywords` column**, no special formatting.

| What is proven | Test |
|---|---|
| Rows without `keywords` resolve to the right answer, in rules mode (no Gemini) | `test_faq_rows_without_keywords_resolve_in_rules_mode` (5 phrasings) |
| For **every** row, the number shown next to its question in the Router prompt is the number the pipeline resolves; the answer is read from the data and never appears in the prompt | `test_the_routers_faq_id_resolves_every_row_by_the_number_in_the_prompt` (one case per row) |
| Row order does not matter (numbering is relative to the list sent in *that* request) | `test_the_number_is_relative_to_the_list_of_this_request_so_row_order_does_not_matter` |
| Soft-deleted, blank and incomplete rows are dropped **before** numbering | `test_soft_deleted_blank_and_incomplete_rows_are_dropped_and_numbering_follows_the_clean_list` |
| An invalid `faq_id` is ignored; nothing is invented | `test_a_router_number_that_is_not_in_the_prompt_is_ignored_and_nothing_is_invented` |
| Only the first 40 are used | `test_only_the_first_forty_faqs_are_resolvable` |
| A FAQ never steals a catalog price question | `test_a_faq_never_steals_a_real_catalog_question` |
| FAQ/policy answers are verbatim (the generator is never called) | `test_owner_written_answers_are_sent_verbatim_the_generator_never_rephrases_them` |

Run it yourself:

```bash
pip install -r requirements-dev.txt
pytest tests/test_handoff_hardening.py -k "faq or verbatim or mock" -v
```

Therefore adding, editing or deleting FAQs in PostgreSQL requires **no deployment**: send the current rows in `businessKnowledge.faqs` with each request.

### 2.4 Requirements and limits

| Topic | Limit / requirement |
|---|---|
| Row shape | `question` + `answer` text. `keywords` optional (helps rules mode). `isActive:false` is honoured. |
| Size | First **40** FAQs per request. Send the most important ones first if a business has more. |
| Semantic matching | Done by Gemini (the numbered list). **Its accuracy on real FAQs has not been measured yet** (§3.5). |
| Rules mode | A message must contain *all* content words of a question (or a keyword). "الاشتراك بكام؟" does **not** match "الاشتراك الشهري بكام؟" without Gemini or a keyword. |
| Answers | Plain text, sent as written (no templating, no variables). |

---

## 3. Final status & missing pieces (AI side)

### 3.1 Verdict

**Feature-complete and contract-compliant; not yet "100 % production-ready".** The code, the contract and the safety nets are done and covered by 431 tests.
What is missing is operational: a live Gemini verification, deployment, monitoring, and the backend agreeing on §1.4. None of the remaining items needs new AI features.

### 3.2 Done and verified

| Area | Evidence |
|---|---|
| E0-3 Schema 1.0 compliance | every test response is validated against the official JSON Schema; the doc's 3 examples + 14 rejection cases + all forbidden fields tested |
| Real backend data shapes | Railway data (business, settings, hours rows, flat attributes, string prices) used in tests and in a live local run |
| Strict `isActive` filter | inactive products/FAQs never reach a prompt or a reply (tested) |
| Router + Generator + Guard | rewrite rejected on new numbers, changed product names, promises, "order accepted" claims, markdown/emoji/URLs, wrong language, **lost conversation-state phrases** |
| Failure handling | 503 / 429 / 404 / 403 / timeout / bad JSON on the Gemini client (scripted), real-SDK connection failure → rule fallback, no key in logs |
| Security | optional shared-secret token, prompt-injection delimiting, dev endpoints off by default, no stack traces in responses, customer text only at `DEBUG` |
| Config | fail-fast on missing key; `AI_PROVIDER=rules` for offline |
| Compatibility | source parses as Python 3.10; tests run on 3.12.3 (fastapi 0.156, pydantic 2.14, google-genai 2.31) |

### 3.3 Go-live checklist

**P0 — blocking**

| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Create a Gemini API key with billing/quota; run `GET /health?probe=true` **and** a 30-message smoke test on the Railway business | AI | The only unverified path. Check the router/generator model names in the probe result. |
| 2 | Set `AI_SERVICE_TOKEN`; backend sends the same value in `X-Internal-Token` | AI + Backend | Without it the endpoint is open. |
| 3 | Deploy (Railway) with the start command below, HTTPS, `ENABLE_DEV_ENDPOINTS=false` | AI + Backend | No Dockerfile exists yet (§3.4). |
| 4 | Agree the request shape (§1.2) and **store AI replies verbatim** (§1.4-C) | Backend | Silent failure if missed. |
| 5 | Backend handles `CONFIRMED_ORDER`, `requiresReview` and the idempotency index | Backend | §1.4-A/B/E. |
| 6 | Confirm that `requiresReview:true` on a non-order reply notifies the owner | Backend | §1.4-B warning. |

**P1 — before real customers**

| # | Task |
|---|---|
| 7 | Import a realistic catalog (Arabic names, `Color`/`Size` columns, real prices). The current Railway data is test data (`Duplicate Product A`, `Test`). |
| 8 | Log aggregation + alerts on: `X-AI-Source: rules` ratio (Gemini degraded), `X-AI-Guard` ratio (rewrites rejected), 5xx/503 rate, latency p95. |
| 9 | Evaluation set (SCRUM-44, ~50 real chats) run against live Gemini; tune prompts from failures. |
| 10 | Dockerfile + CI that runs `pytest` on Python 3.10/3.11/3.12. |
| 11 | Load test (the service is async and CPU-light; Gemini quota is the real limit). |

**Deployment reference**

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT        # Railway provides $PORT; the app itself does not read it
```

| Variable | Default | Production value |
|---|---|---|
| `AI_PROVIDER` | `gemini` | `gemini` (`rules` = offline engine, no key) |
| `GEMINI_API_KEY` | — | **required** when `AI_PROVIDER=gemini`; the service refuses to start without it |
| `AI_SERVICE_TOKEN` | — | **set it** (long random string) |
| `ENABLE_DEV_ENDPOINTS` | `false` | `false` |
| `AI_FALLBACK_TO_RULES` | `true` | `true` = customers always get an answer (lower quality) · `false` = `503` and you retry |
| `ROUTER_MODELS` | `gemini-flash-lite-latest,gemini-2.5-flash-lite` | check with `/health?probe=true`; rename here if Google renames a model |
| `GENERATOR_MODELS` | `gemini-flash-latest,gemini-3.5-flash,gemini-2.5-flash` | same |
| `GENERATOR_ENABLED` | `true` | `false` = router only, fixed templates (cheapest, fully deterministic) |
| `GEMINI_TIMEOUT_SECONDS` / `GEMINI_TOTAL_TIMEOUT_SECONDS` | `12` / `25` | `8` / `10` (worst case ≈ 36 s) |
| `GEMINI_MAX_RETRIES` / `GEMINI_RETRY_DELAY_SECONDS` / `GEMINI_COOLDOWN_SECONDS` | `2` / `3` / `60` | defaults |
| `ROUTER_TEMPERATURE` / `GENERATOR_TEMPERATURE` | `0` / `0.3` | defaults |
| `MIN_CONFIDENCE` | `0.4` | default (below it an intent becomes `UNKNOWN`) |
| `LOG_LEVEL` | `INFO` | `INFO` (`DEBUG` logs customer text: avoid in production) |

### 3.4 Technical debt and known limitations (document before handoff)

| # | Item | Impact | Mitigation / plan |
|---|---|---|---|
| 1 | **Conversation state lives in the wording of the AI's previous reply** (stateless design) | If the backend stores the reply differently, confirmations silently fail | §1.4-C; the guard protects rewrites; a future contract field (`pendingAction`) would be sturdier |
| 2 | `requiresReview` is used on non-order replies | Possibly ignored by the backend | Agree on semantics (P0 #6); long-term add a typed `reviewReason` to the contract |
| 3 | Cancel/modify details are **unstructured** (order number only inside `reply`, no "what to change") | Owner must read the conversation | Extend E0-3 later |
| 4 | **One product per order** (`items` is an array, but we emit one) | "A hoodie and a t-shirt" asks "which one?" | Multi-item parsing is a planned extension |
| 5 | Live Gemini never exercised; router/generator quality unmeasured | Unknown accuracy on messy real chats | P0 #1, P1 #9 |
| 6 | Single currency (EGP) hard-coded in templates | Other currencies print "جنيه"/"EGP" | Read `currency` when needed |
| 7 | No time-zone logic; "are you open now?" is answered with the full schedule | Less precise | Needs a business time-zone field |
| 8 | **Images, voice notes, stickers are not handled** (SCRUM E5-4 "image request" intent not built) | The backend must not call the AI for them | Handle non-text in the backend for now |
| 9 | Limits: first 40 FAQs, first 60 products in the Router's catalog hint (matching itself uses all products), last 12 messages | Very large catalogs/FAQ sets lose recall | Backend can pre-filter; raise constants if needed |
| 10 | Franco-Arabic ("3ayez tshirt") answered in Arabic by a heuristic; the rule engine's English coverage is lighter than its Arabic | Edge cases | Gemini handles them when available |
| 11 | No rate limiting, quotas per business, or usage/cost metrics | Abuse or cost spikes | Add at the gateway; log tokens when live |
| 12 | `/health` is unauthenticated and lists model names | Minor information exposure | Keep the service on a private network or protect `/health` |
| 13 | Model health/cooldown state is per process | Several instances learn about an overloaded model separately | Acceptable; shared cache later if needed |
| 14 | `Orchestrator.last_plan` is a debug attribute overwritten per request (used by tests) | Not request-safe, harmless in production | Replace with a context variable before heavy concurrency |
| 15 | No Dockerfile, CI, or dependency lock file (ranges only) | Reproducibility | P1 #10 |
| 16 | Replies are written in Egyptian-Arabic/English templates; no per-business tone settings | One voice for all businesses | `settings.tone` is available in the data model for later |

### 3.5 Not verified (so nobody assumes otherwise)

- A successful call to the live Gemini API (model names, structured-output acceptance, latency, cost).
- Python 3.10 / 3.11 *execution* (syntax only was checked) and Windows runtime.
- Behaviour under load and with catalogs of hundreds of products.
- Accuracy of the Router's semantic FAQ matching on real owner FAQs.

### 3.6 Open questions for the backend

1. Will the backend always send `messageId` (the stored id)? It is mandatory.
2. Does `requiresReview:true` on an `OTHER` reply notify the owner? (§1.4-B)
3. Final shape of `businessKnowledge` (SCRUM-33): are `policies` text and `faqs[{question, answer}]` acceptable?
4. Will `customerOrders` be sent once Orders exist? Which status strings will be used (we assume `PENDING`, `PENDING_APPROVAL`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)?
5. Are AI replies and owner replies stored as `senderType` `AI` / `OWNER` with verbatim `content`?

---

## Appendix A — changes since the v3 hand-off (found while preparing this guide)

| # | Problem found | Fix | Test |
|---|---|---|---|
| 1 | A Gemini rewrite of the order summary could drop "تحب تأكد الطلب؟", after which the customer's "ايوه" **no longer confirmed the order** | The guard now requires the conversation-state phrases to survive; the generator prompt says to keep them word for word | `test_a_reworded_summary_cannot_break_the_customers_confirmation` |
| 2 | English questions ("Which quantity?") carried no recognisable phrase, so "two" lost its product | English questions rewritten ("How many would you like?", "Which color and size would you like?") | `test_english_order_flow_end_to_end` |
| 3 | FAQ rows from a table (no `keywords`) did not resolve without Gemini; soft-deleted FAQs were not filtered | `isActive:false` dropped; keyword-less matching by question coverage | the FAQ tests in §2.3 |
| 4 | Owner-written replies could be reworded by the generator | FAQ, policy, hours, delivery, payment and returns replies are sent verbatim | `test_owner_written_answers_are_sent_verbatim…` |
| 5 | English fragments of "I'll take" were read as product words | added to the stop-word list | included in #2 |

## Appendix B — test inventory (431)

| File | Tests | Covers |
|---|---|---|
| `test_scenarios_rules.py` | 88 | intents, replies, business data, English, invariants |
| `test_context_nlu_router.py` | 78 | `Ctx` properties, budgets, FAQ matching, yes/no by context, Router prompt |
| `test_customer_service.py` | 58 | new intents, owner review, cancel/modify, budgets, dynamic FAQ, careful mode |
| `test_pipeline_gemini.py` | 35 | Router + Generator + Guard through the pipeline (scripted Gemini) |
| `test_handoff_hardening.py` | 34 | state-phrase guard, English flow, PostgreSQL-shaped FAQ proof, mock isolation, verbatim answers |
| `test_gemini_new_intents.py` | 31 | new fields through Gemini, schema sent to Gemini, guard additions |
| `test_request_and_contract.py` | 30 | request shapes, E0-3 examples and rejections |
| `test_orders_flow.py` | 23 | multi-turn orders, confirmation, candidate |
| `test_api_and_config.py` | 22 | HTTP layer, auth, headers, provider selection |
| `test_catalog_policy.py` | 17 | real Railway data, colour/size policy, `isActive` filter |
| `test_gemini_provider.py` | 15 | retry / fallback / cooldown policy |
