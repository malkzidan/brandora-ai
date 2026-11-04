# تسليم Backend: الموجود والناقص وعقد القبول

Audit 2026-11-04 ؛ repo `shrouqshaker/brandora-backend`. `main=83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b`. Conversations PR #1 مفتوح وغير مدموج، head `0e92d6b5d038aa6da87c76ee5f06d29aebe4127a`. دي قراءة كود، مش Backend test execution أو DB inspection. ما ظهرش Orders PR في قائمة PRs كلها.

**P0** blocker لأول integration read-only ، **P1** قبل customer-facing staging/release ، **Future** مش داخل نطاق النسخة الحالية. `No` يعني مش موجود في المصادر المتراجعة، مش حكم على شغل خاص بره الريبو. paths لأي internal controller/signing/outbox جديد **لسه مش محددة**؛ ما بنقدمهاش كملفات موجودة.

## 1. Products — نستخدم الخدمات الحالية

| Requirement | main ؟ | open PR فقط؟ | AI dependency | Priority | Acceptance criteria | Backend source الحالي |
|---|---|---|---|---|---|---|
| Scoped Product list/get | Yes | No | get_products/details | موجود؛ maintain | business-scoped ، details direct ، pagination | `src/products/products.controller.ts`, `products.service.ts:list/get/read` |
| Scoped Variant list/get | Yes | No | get_product_variants/details | موجود؛ maintain | variant تابع product والمحل، inactive واضح | `src/variants/variants.controller.ts`, `variants.service.ts:scoped` |
| Present prices/options correctly | Yes | No | typed Product/Variant | P0 verify mapping | Decimal strings2dp ، effectivePrice كما presenter ، null محفوظ | `src/products/product-presenter.ts:variantResponse/productResponse` |
| Read-only internal dispatcher | No | No | BackendClient target | P0 BLOCKER | whitelist أدوات فقط؛ schema args ؛ reject unknown/write/URL tools ؛ services الحالية تتستخدم | receiver جديد مقترح؛ `src/app.module.ts` مفيهوش module ليه |
| Envelope mapping | No internal envelope | No | ToolEnvelope | P0 BLOCKER | `{tool,data}`؛ details direct ؛ list items/pagination | services الحالية مصدر data ، مش envelope |
| Embedded variants completion | Yes metadata | No | bounded variant retrieval | P0 verify | embedded20 و variantsPagination ؛ V tool يكمل بنفس parent | `product-presenter.ts:productInclude/productResponse` |
| Inventory contract | Yes model/primitives | No | shortage/no-stock guards | P0 verify | tracked=>integer≥0 ، untracked=>null ؛ no parent stock inheritance | `prisma/schema.prisma:ProductVariant`, `src/inventory/inventory.service.ts` |
| isSellable semantics | Yes | No | product status | P0 verify | active + active priced variant ؛ مش stock guarantee | `products.service.ts:eligible`, `product-presenter.ts:productResponse` |
| Business info aggregate | No internal aggregate | No | foundation فقط؛ canonical لايسمح به | Optional | `{business:{id,name}}` minimal agreed DTO ؛ لا policies غير موجودة | `src/businesses/` موجود؛ internal aggregation جديد غير منفذ |

ما تعيدوش كتابة CRUD أو Prisma modeling للـ Products/Variants عشان integration. ناقص exposure آمن وإضافة contract tests ، مش بديل للخدمات الشغالة.

## 2. Conversations

| Requirement | main ؟ | open PR فقط؟ | AI dependency | Priority | Acceptance criteria | Backend paths |
|---|---|---|---|---|---|---|
| Customer/Conversation/Message storage | No | Yes #1 | trustworthy IDs/history | P0 BLOCKER | merge بعد حل auth/schema conflicts ، scoped ownership | PR `prisma/schema.prisma`, migration `20261016040000_add_customer_conversation` |
| Ingest/dedup CUSTOMER message | No | Yes #1 | current message stored before AI | P0 BLOCKER | externalMessageId duplicate معروف؛ no duplicate processing ؛ owned customer | PR `src/conversations/conversations.service.ts:ingestInboundMessage/findDuplicate` |
| Public conversation list/get/messages | No | Yes #1 | UI foundation ؛ مش internal tool مباشرة | P0 secure merge | integrate main global guard + explicit policies ؛ no unauthenticated reads | PR `conversations.controller.ts`, `src/customers/customers.controller.ts` |
| Authenticated history dispatcher | No | No | get_conversation_history | P0 BLOCKER | service auth+claims ؛ lookup business/customer/conversation independently ؛ all matched | internal receiver لسه مقترح |
| Current-message cutoff | No canonical behavior | No | prepare_authorized | P0 BLOCKER | currentMessage belongs to conversation/customer/business ؛ جميع rows strictly older ؛ exclude current/future | PR `listMessages` لا يدعم cutoff الحالي |
| Stable history across pages | No canonical snapshot | No | snapshot/order/complete | P0 BLOCKER | snapshot+boundary+totalCount ثابتين لنفس signed message/context ؛ newest-first ؛ لا truncate وتدعي complete | PR `listMessages` count/findMany منفصلين؛ internal implementation مطلوب |
| History identity DTO | No | No | AuthorizedHistoryPage | P0 BLOCKER | metadata IDs و row conversationId/type/time مطابقة؛ reject nonscope | PR `messageSelect` مش كفاية metadata canonical |
| AI reply/review persistence | No current workflow | No complete AI workflow | response lifecycle | P1 BLOCKER لإرسالعملي | scoped stored AI reply ، review state ، correlation/message id ؛ dedup | models أساسها PR ؛ orchestration/review persistence مش موجودة |
| Ordering/duplicate handling end-to-end | No complete flow | Partial inbound dedup #1 | safe replay/retries | P1 | retries لا تكرر reply/action ؛ current/later/duplicate tests ؛ serialize/version conversation processing | PR ingest foundation فقط |

PR فيه scoped query لـ business (`getOne`) بالفعل؛ **مطلوب إضافة customer authorization و service trust ، مش الادعاء إن مفيش أي scope filter**. PR head قديم ومفيهوش main AuthModule ؛ بعد الدمج global main guard محتاج scope policies ، مش مجرد استخدام Controller القديم كماهو.

## 3. Orders — FUTURE DESIGN ، تفضل disabled دلوقتي

| Requirement | main ؟ | PR ؟ | AI dependency | Priority | Acceptance criteria | Backend paths |
|---|---|---|---|---|---|---|
| Order/OrderLine models/API/service | No | No | future write extension | Future | approved state machine/schema/auth قبل أي AI action | لا Orders paths/models في main/PR المتراجع |
| Stock deduction/restoration primitives | Yes | No | future Backend order transaction | maintain | stable orderLineId + caller transaction ، exactly-once movement | `src/inventory/inventory.service.ts:deductForOrder/restoreForOrder/orderChange` |
| Transactional purchase validation | No order workflow | No | fresh validation قبل write | Future | recheck active/parent/options/price/quantity/stock مع orderstate transaction | existing product/inventory services تتستخدم، workflow جديد |
| Confirmation/approval policy | No order workflow | No | UI/customer contract | Product-owner decision | مين يوافق وإمتى stock يتخصم؟ تغيرالسعر؟ reserve expiry ؟ cancellation state ؟ | مش متنفذ |
| Idempotent order creation/cancel | No order workflow | No | safe retries | Future BLOCKER للـ Orders | scoped action key ؛ repeated request لا doubleorder/deduct/restore | inventory primitives أساس، مش completed order idempotency |
| Explicit reviewed AI order extension | No active tool | No | DisabledOrderExtension | Future | design review + auth/scopes/Guard/tests جديدة؛ لا استخدام implicit confirmation | AI `app/pipeline/extensions.py` disabled |

وجود `ORDER_APPROVED` في InventoryMovement enum **مش Order table**. `PURCHASE_INTENT` و`orderCandidate=null` هي الحالة الحالية الصحيحة. ما تتعاملش مع `requiresReview=true` كأمر create/approve/reserve.

## 4. Service Authentication & Integration

| Requirement | main ؟ | PR ؟ | AI dependency | Priority | Acceptance criteria | Backend paths |
|---|---|---|---|---|---|---|
| OWNER/user JWT auth | Yes | PR head لا يحتويها | public CRUD security | maintain | active session+membership ، existing tests | `src/auth/auth.guard.ts`, `auth.module.ts` |
| AI-specific inbound S2S verifier | No | No | AI→Backend Bearer | P0 BLOCKER | dedicated service credential/policy ؛ no OWNER JWT reuse ؛ timing-safe compare/rotation/revocation | internal auth جديد؛ main AuthGuard مش ده |
| Backend→AI caller | No | No | canonical request delivery | P0 BLOCKER | persist current message ؛ derive trustedIDs ؛ bounded timeout ؛ classify403/503 ؛ no raw payload logs | AI caller service لسه مقترح |
| RS256 issuer/signing profile | No | No | X-AI-Context | P0 BLOCKER | privatekey Backend فقط؛ RSA≥2048 ؛ exactaud/scope/issuer ؛ ≤300sec ؛ key-rotation plan | issuer module لسه مقترح |
| Raw-body SHA256 binding | No | No | authenticate_conversation | P0 BLOCKER | sign hash bytes ثم ابعت **نفس bytes**؛ IDs الأربعة match ؛ no reserialization بعدالتوقيع | caller/signing implementation جديد |
| Reauthorize every tool | No internal endpoint | No | tenant isolation | P0 BLOCKER | service+context verification independently ؛ product parent/conversation/customer matches ؛ reject crossscope | reuse scoped services + new internal policies |
| Error/privacy policy | Public errors موجودة؛ internal flow No | No | sanitized retrieval status | P1 | 401/403 واضحين؛ no secret/customer dumps ؛ no redirects ؛ timeout budget ؛ audit IDs minimal | `src/common/errors/` existing ، internal mapping مطلوب |

## 5. Notifications / WhatsApp

| Requirement | main ؟ | PR ؟ | AI dependency | Priority | Acceptance criteria | Backend paths |
|---|---|---|---|---|---|---|
| Real WhatsApp inbound webhook | No | No ؛ dev simulator فقط | trusted message ingest | P1 BLOCKER للـ realchannel | verify platform signature ؛ ownbusiness/channel ؛ dedup externalID ؛ no arbitrary business from message | PR `src/conversations/dev-inbound.controller.ts` **مش webhook** |
| Owner shortage triage policy | No complete workflow | No | requiresReview | P1 | owner attention display مقابل consent-gated notification قرار موثق | review handling جديد غيرمنفذ |
| Persist review decision/lifecycle | No | No | reason/consent/status | P1 | trigger scoped message ، offer/accepted/declined/resolved state ، audit وحفظآمن | persistence schema/service غيرموجود |
| Notification/outbox + idempotency | No AI flow | No | truthful action status | P1 | scoped dedupkey ، retry policy ، delivery status ، no duplicate notify | outbox/delivery paths لسه مقترحة |
| Customer reply delivery | No complete AI flow | No | FastAPI reply | P1 | persist AI response قبل delivery حسب policy ؛ retry/receipts ؛ scopebound | WhatsApp sender لسه غيرمنفذ |
| Inventory disclosure approval | No runtimeAI policy service | No | tenant allowlist | P1 | storeowner/operator يعتمد business policy ؛ explicitquestion شرطثاني؛ defaultdeny | AI config موجود؛ Backend policy integration قرارمستقبلي |

AI يطلع review signal وسؤال «نراجع مع المسؤول؟» بس. إشعار المالك ممكن يبقى automatic triage أو يحتاج consent حسب قرار المنتج؛ **الاتنين مش receipt**. لحد ما Backend يؤكد action result حقيقي، ما فيش «المالك اتبلغ». موافقة العميل لوحدها مش proof of delivery. مفيش notification tool تمت إضافتها هنا.

## 6. Staging & Railway

| Requirement | main ؟ | PR ؟ | AI dependency | Priority | Acceptance criteria | Paths/الدليل |
|---|---|---|---|---|---|---|
| Deploy Backend internal contract | No endpoint | No | all live reads | P0 BLOCKER | staging synthetic tenant ، real authenticated tools +negativecases | internal implementation لسه مطلوب |
| AI deployment actual existence | Unverified | مش PR claim | HTTP reachability | P1 | operator يحدد account/project/service URL ؛ inspectdeployment logs بلا secrets | AI `railway.json` config فقط |
| TLS/proxy trust | Backend auth proxy work موجود؛ AI edge unverified | No | HTTPS checks | P1 | verify actual peerCIDRs ؛ spoofheaders rejected ؛ no wildcard | AI `app/ingress.py`, Backend `docs/railway-proxy-security.md` |
| AI start/build | مش Backendmain feature | No | app.server | P1 | clean install/runtime3.13 ؛ PORT ؛/ready ؛ restart ، legacydisabled | AI `.python-version`, `requirements.txt`, `app/server.py`, `railway.json` |
| Accepted staging transcript | No evidence executed هنا | No | release gate | P1 | realGroq semanticquality +authorized tools +persist/delivery/idempotency ؛ ownerreview/noOrders | runbook في Railway doc |

## 7. العقود المستهدفة — PROPOSED Backend contracts

### 7.1 Backend ينادي AI

AI receiver **IMPLEMENTED**، Backend caller/issuer **NOT IMPLEMENTED** في المصدر المتراجع:

```http
POST /v2/ai/respond
Content-Type: application/json
X-Internal-Token: <Backend-to-AI credential>
X-AI-Context: <RS256 context JWT>
```

```json
{
  "businessId":"00000001-0000-4000-8000-000000000001",
  "customerId":"00000002-0000-4000-8000-000000000001",
  "conversationId":"00000003-0000-4000-8000-000000000011",
  "messageId":"00000009-0000-4000-8000-000000000001",
  "message":"طب مقاس L بكام؟"
}
```

الـ IDs دي أمثلة synthetic. canonical extra fields مرفوضة. claims المطلوبة من `app/products_api.py:ConversationClaims`: `iss=brandora-backend`, `aud=brandora-ai-tools-v1`, `scope=products:read conversations:read`, IDs الأربعة، `requestHash` lowercase64hex للـ rawbody ، `iat`, `exp`، optional `nbf`. `exp<=iat+300` ومش expired ، no clockskew. AI publickey validator واحد؛ توافق issuer/verifier والـ rotation مطلوب قبل staging.

response exactkeys:

```json
{"intent":"PURCHASE_INTENT","reply":"رد من حقائق متحققة","requiresReview":false,"orderCandidate":null}
```

`requiresReview` يتحدد بالحقائق والسياسة؛ المثال false مش default لكل shortage. لا order creation confirmation. HTTP auth failures401/403 ؛ malformed request400 ؛ global deadline503 ؛ بعض availability failures بتطلع response آمن 200 بدل fabricatedfacts. caller لازم يتعامل مع status وال body ، مش يفترض 200=نجاح retrieval/liveLLM.

### 7.2 AI يقرأ Backend

**كل الجزء المستقبل ده PROPOSED على Backend**، client موجود في AI:

```http
POST /internal/ai/data
Authorization: Bearer <AI-to-Backend credential>
X-AI-Context: <same per-request signed context>
Content-Type: application/json
```

```json
{"tool":"get_products","arguments":{"limit":20,"offset":0}}
```

```json
{"tool":"get_products","data":{"items":[],"pagination":{"limit":20,"offset":0,"totalCount":0,"hasMore":false,"nextOffset":null}}}
```

| tool | arguments بالضبط | data |
|---|---|---|
| get_products | limit,offset | items + pagination |
| get_product_details | productId | product object مباشرة |
| get_product_variants | productId,limit,offset | variant items +pagination |
| get_variant_details | productId,variantId | variant object مباشرة |
| get_conversation_history | conversationId,limit,offset | AuthorizedHistoryPage تحت |
| get_business_info | `{}` | `{business:{id,name}}` minimal proposed aggregate ؛ **مش enabled canonical** |

defaults20/0 ، limit1..100 ، offset0..9007199254740991 ، strictinteger مش bool/float. UUID canonical بلا v4-onlypolicy. مفيش businessId في arguments ؛ authority من verifiedclaims مش الموديل. no arbitrary URL/tool dispatch ولا paid/providerchoice من message.

ProductDTO في `app/schemas/backend.py:Product`: id/businessId/name/description/basePrice/options/attributes/isActive/isSellable/variants/variantsPagination. VariantDTO: id/businessId/catalogItemId/optionValues/unitPrice/effectivePrice/trackInventory/stockQuantity/isActive. أسعار nonnull string Decimal(12,2)، ليس JSONfloat ؛ defaults/null ما تتخمنش. Unknown extra productfields مش authority. historyDTO strict extras forbidden ؛ اعمل mapping صريح.

### 7.3 history envelope مثال كامل — synthetic ، مش response حقيقية

```json
{
  "tool":"get_conversation_history",
  "data":{
    "businessId":"00000001-0000-4000-8000-000000000001",
    "customerId":"00000002-0000-4000-8000-000000000001",
    "conversationId":"00000003-0000-4000-8000-000000000011",
    "beforeMessageId":"00000009-0000-4000-8000-000000000001",
    "beforeMessageCreatedAt":"2026-11-04T12:00:00Z",
    "snapshot":"opaque-bound-snapshot",
    "order":"createdAt_desc_id_desc",
    "complete":true,
    "pagination":{"limit":20,"offset":0,"totalCount":1,"hasMore":false,"nextOffset":null},
    "items":[{
      "id":"00000009-0000-4000-8000-000000000002",
      "conversationId":"00000003-0000-4000-8000-000000000011",
      "senderType":"CUSTOMER",
      "content":"عندكم تيشيرت أسود؟",
      "messageType":"TEXT",
      "createdAt":"2026-11-04T11:59:00Z",
      "externalMessageId":null
    }]
  }
}
```

الحد مستنتج من `messageId` في signedclaims ، **مش beforeMessageId argument مبعوت من AI**. `before_message_id` الحالي Python check للـ response. الـ snapshot opaque identity مش timestamp نخمنه. نفس token/currentmessage عبر pages لازم يرجع نفس snapshot/boundary/count. implementation storage/expiry/isolation strategy **لسه قرارمفتوح**. `complete=true` مش معناها window صغيرةواعتبرالباقي irrelevant ؛ AI بيرفض history أكبرمن budget60 أو incomplete ، ومشبيستخدم partialselectors. حد text/chronology المدعوم متوثق في`HistoryService.prepare_authorized`؛ راجع timestamp ties وملفات nontext قبل staging.

### 7.4 acceptance gate موحد

- [ ] main/PR distinction اتحسمت بعد code review ؛ publicauth ما اتضعفتش لإرضاء AI.
- [ ] goldenfixtures تطابق existing serviceJSON مع typedAI ، including directdetails/Decimal/null/pagination.
- [ ] service auth/signature/audience/scope/expiry/hash والـ IDsnegativecases ناجحين داخل Backend و AI.
- [ ] crossbusiness/customer/conversation و variantparent rejects منغير leak ؛ لا secrets/rawcustomerlogs.
- [ ] realhistorysnapshot مع concurrentwrites و duplicates/current/future/messagesoverbudget بيتعامل safe.
- [ ] canonical transcript صحيحبقراءاتحالية؛ provider failure مايخترعش facts ؛ allordersdisabled.
- [ ] review flag مش notificationreceipt ؛ consent/persistence/delivery/idempotency مصممين قبل customeruse.
- [ ] stagingedge/TLS/proxytimeouts/health/config والـ rollback اتراجعوا؛ offline pass مش productionreadiness.

تفاصيل الفهم في [Walkthrough](BRANDORA_AI_COMPLETE_WALKTHROUGH.md)، والتشغيل الآمن في [Railway readiness](BRANDORA_RAILWAY_READINESS.md).
