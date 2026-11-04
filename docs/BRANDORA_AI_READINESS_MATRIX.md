# Brandora: الحالة المختصرة بعد المراجعة

2026-11-04 — AI branch: `feature/backend-ai-integration`، والـworking tree فيه شغل غير committed وملفات untracked. المراجعة شملت الشغل ده. Backend main متحقق منه عند `83a65e9`؛ Conversations PR #1 مفتوح وغير merged عند `0e92d6b`. Railway account/deployment ما اتفتحوش.

**الحكم الحالي: AI read-only flow IMPLEMENTED وMOCK-TESTED؛ real integration BLOCKED بمتطلبات Backend؛ Production readiness مش مثبتة.** Orders تفضل مقفولة عمدًا.

| Component | AI Code | AI Offline Tested | Backend Main | Backend PR | Real Integration Tested | Deployment Status | Remaining Work |
|---|---|---|---|---|---|---|---|
| Product discovery | IMPLEMENTED | MOCK-TESTED | IMPLEMENTED public CRUD؛ internal PROPOSED | NOT IMPLEMENTED internal | BLOCKED | UNVERIFIED | secure dispatcher + DTO + staging reads |
| Variant retrieval | IMPLEMENTED | MOCK-TESTED | IMPLEMENTED scoped list/get | NOT IMPLEMENTED internal | BLOCKED | UNVERIFIED | expose existing services بأمان؛ fresh evidence |
| Conversation history | IMPLEMENTED | MOCK-TESTED | NOT IMPLEMENTED | PARTIALLY IMPLEMENTED #1، غير merged | BLOCKED | UNVERIFIED | secure merge + scoped snapshot/boundary contract |
| Context restoration | IMPLEMENTED request-local | MOCK-TESTED | NOT IMPLEMENTED canonical support | PARTIALLY IMPLEMENTED history foundation | BLOCKED | UNVERIFIED | current-message storage + stable authorized history |
| Groq Understanding | IMPLEMENTED | MOCK-TESTED structured/semantic paths | NOT IMPLEMENTED AI caller | NOT IMPLEMENTED AI caller | UNVERIFIED في audit؛ نجاح سابق operator-reported | UNVERIFIED | operator live/staging quality، quota وlatency |
| Natural Generation | IMPLEMENTED constrained composition | MOCK-TESTED + fallback | NOT IMPLEMENTED orchestration | NOT IMPLEMENTED full flow | UNVERIFIED في audit | UNVERIFIED | human language review + live acceptance |
| Stock shortage policy | IMPLEMENTED | MOCK-TESTED | IMPLEMENTED inventory؛ AI review handling NOT IMPLEMENTED | NOT IMPLEMENTED review flow | BLOCKED | UNVERIFIED | approve disclosure/triage policy + real stock evidence |
| Owner review | IMPLEMENTED flag/offer فقط | MOCK-TESTED no action claims | NOT IMPLEMENTED AI review lifecycle | NOT IMPLEMENTED notification | BLOCKED | UNVERIFIED | consent policy، persistence، owner display/notification |
| Orders | NOT IMPLEMENTED active tools؛ disabled extension | MOCK-TESTED safety فقط | PARTIALLY IMPLEMENTED inventory primitives؛ Orders NOT IMPLEMENTED | NOT IMPLEMENTED | BLOCKED عمدًا | UNVERIFIED | future approved models/state/auth/transactions/idempotency |
| S2S Authentication | IMPLEMENTED AI verification + outbound headers | MOCK-TESTED | NOT IMPLEMENTED AI profile؛ OWNER auth IMPLEMENTED | NOT IMPLEMENTED | BLOCKED | UNVERIFIED | Backend issuer/verifier/caller + ownership checks |
| WhatsApp delivery | NOT IMPLEMENTED | NOT IMPLEMENTED real channel test | NOT IMPLEMENTED real webhook/sender | PARTIALLY IMPLEMENTED dev ingest فقط | BLOCKED | UNVERIFIED | platform signature، outbox، persistence، retries/receipts |
| Railway deployment | IMPLEMENTED config/launcher | MOCK-TESTED startup/proxy/PORT | UNVERIFIED actual infrastructure | UNVERIFIED actual infrastructure | UNVERIFIED | UNVERIFIED | account/service proof، clean build، verified proxy، staging gates |

`IMPLEMENTED` = فيه كود؛ `MOCK-TESTED` = اتجرّب ببيانات/HTTP محاكاة؛ `PARTIALLY IMPLEMENTED` = جزء من المطلوب موجود؛ `NOT IMPLEMENTED` = مش موجود في المصادر المتراجعة؛ `PROPOSED` = عقد مستهدف لسه مش endpoint فعلي؛ `UNVERIFIED` = مفيش دليل تنفيذ في المراجعة؛ `BLOCKED` = فيه prerequisite يمنع قبول الربط. passing tests مش deployment ولا Production acceptance.

## الأدلة والنتائج الفعلية

- full offline suite: **1580 passed، 0 failed، 0 skipped، 1 warning** باستخدام `-p no:cacheprovider` مع AI_PROVIDER=rules وENABLE_DEV_ENDPOINTS=false وdotenv disabled. warning تخص Starlette/httpx، مش failure.
- independent canonical HTTP evaluation: **12 سيناريو / 23 رسالة، 0 failed**.
- rules وfake evaluations: **17 رسالة لكل واحد، 0 failed checks**.
- interactive demo: الأربع رسائل اتعادت فعلًا؛ آخر اختيار White/L، quantity3، price285، review=false، orderCandidate=null؛ shortage10 عرض review من غير إظهار stock4.
- Backend tests وlive Groq/WhatsApp/DB/Railway build/deploy: **not run** هنا. نجاح Groq اللي اتبلغ عنه سابقًا historical report فقط.

أهم code evidence: [build_products_router](../app/products_api.py)، [execute_conversation](../app/conversation_api.py)، [HistoryService](../app/data/history.py)، [RetrievalCoordinator](../app/data/retrieval.py)، [ConversationPlanner](../app/chat/application.py)، [NaturalResponder](../app/chat/natural.py)، [DisabledOrderExtension](../app/pipeline/extensions.py)، [release launcher](../app/server.py).

Backend evidence: [Products main](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/src/products/products.service.ts)، [Prisma main](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/prisma/schema.prisma)، [Inventory order primitives](https://github.com/shrouqshaker/brandora-backend/blob/83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b/src/inventory/inventory.service.ts#L323)، [Conversations PR #1](https://github.com/shrouqshaker/brandora-backend/pull/1). الـPR مش merged وmain مفيهوش internal dispatcher أو Orders models.

## مخاطر وملاحظات ما اتصلحتش في audit

1. history `before_message_id` بيُستخدم للتحقق في Python، مش wire argument؛ Backend لازم يستنتج الحد من signed messageId ويضمن snapshot ثابت عبر الصفحات. آلية التنفيذ لسه محتاجة اتفاق واختبار.
2. `/ready` ممكن يرجع200 مع rules fallback أو Backend غير reachable؛ هو config readiness فقط.
3. public OWNER auth الحالية مش S2S؛ PR القديم محتاج دمج ومراجعة auth policy، مش تفعيل مباشر.
4. cancellation الآمنة عملت Product read زيادة في demo؛ الرد الأول فيه تكرار availability caveat لكل variant. ملاحظات جودة/كفاءة، مش Orders اتنفذت.
5. core files untracked وrequirements ranges: نشر commit قديم أو clean install مختلف ممكن ما يطابقش الاختبارات هنا.
6. NaturalReply حاليًا presentation مقيد، مش free-form sales agent؛ provider health/circuit state shared لكن customer execution state request-local.

للقراءة بالتدريج: [الشرح الكامل](BRANDORA_AI_COMPLETE_WALKTHROUGH.md) → [دليل التجربة](BRANDORA_AI_TESTING_HANDBOOK.md) → [Backend checklist](BRANDORA_BACKEND_IMPLEMENTATION_CHECKLIST.md) → [Railway readiness](BRANDORA_RAILWAY_READINESS.md).

المراجعة دي كتبت خمس مستندات بس؛ لا application/test changes، ولا قراءة credentials، ولا live APIs، ولا commit/push/deployment. مفيش مرحلة implementation جديدة بدأت.
