# Brandora AI Service (v3.1)

> **للباك إند:** دليل التكامل الكامل (شكل الـ request والـ response بأمثلة، التعامل مع `orderCandidate` و`requiresReview`، حفظ رد الـ AI، الـ FAQ، وتقرير الجاهزية) في [`docs/INTEGRATION_GUIDE.md`](docs/INTEGRATION_GUIDE.md).

خدمة الـ AI بتاعت Brandora: بتستقبل من الباك رسالة العميل + سياق البيزنس الحقيقي، وبترجّع رد على شكل **E0-3 Structured Order Candidate (Schema 1.0)** حرفيًا. شغالة على **Gemini الحقيقي** بمعمارية **Router + Generator**.

## التشغيل
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      |  Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # Windows: copy .env.example .env   ← حطي GEMINI_API_KEY
uvicorn main:app --port 8000
```
Swagger: http://localhost:8000/docs  |  من غير مفتاح: `AI_PROVIDER=rules` (محرك قواعد بدون شبكة).
لو `AI_PROVIDER=gemini` ومفيش `GEMINI_API_KEY` الخدمة **ترفض تشتغل** وبتقولك ليه (fail-fast).

## المعمارية (نفس فكرة Tamkeen)
```
request ─► context: يشيل أي منتج isActive=false قبل أي حاجة، ويحدد اللغة وحالة المحادثة
        ─► Hard Rules (كود): تحية / شكر / تأكيد / تراجع  → بدون أي نداء Gemini
        ─► Router (gemini flash-lite, Strict JSON): intent + product/color/size/quantity
        ─► enforce rules: الكود له الكلمة الأخيرة على ناتج الـ Router
        ─► Planner (كود): الكتالوج، المخزون، السياسات، المواعيد → رد "مُتحقق منه" + orderCandidate
        ─► Generator (gemini flash): يعيد صياغة الرد المتحقق منه بلغة العميل
        ─► Guard: أي مخالفة → يتبعت القالب المتحقق منه بدل كلام الموديل
        ─► E0-3: { intent, reply, requiresReview, orderCandidate }
```
**ليه الـ Generator بيصيغ "مسودة متحقق منها" ومش بيكتب من الصفر؟** الأسعار والمخزون والإجمالي والمواعيد بتتحسب بالكود من داتا الباك. الـ Guard بيرفض أي رد فيه رقم جديد، أو اسم منتج اتغير، أو وعد ("هراجع مع الفريق")، أو ادعاء إن الطلب اتقبل، أو ماركداون/إيموجي، أو لغة غلط. فمفيش سعر مخترع، حتى لو الموديل هلوس.

## `POST /v1/ai/respond`
Header: `X-Internal-Token` (لو `AI_SERVICE_TOKEN` متحدد). الأخطاء: `400` payload غلط، `401`، `503` (Gemini وقع و`AI_FALLBACK_TO_RULES=false`)، `500` من غير تفاصيل.

### الـ Request (مقترح، لازم Yomna توافق عليه)
الداتا بالشكل اللي الباك بيرجّعه فعلًا، من غير تحويل:
```json
{
  "business":  { "id": "uuid", "name": "...", "description": null, "category": "Retail", "phone": "...", "address": "...",
                 "settings": { "acceptsCash": true, "acceptsOnlinePayment": false, "deliveryEnabled": false, "pickupEnabled": true },
                 "workingHours": [ { "dayOfWeek": "MONDAY", "isOpen": true, "opensAt": "09:00", "closesAt": "21:00" } ] },
  "customer":  { "id": "uuid", "phone": "2010...", "name": "..." },
  "conversation": [ { "id": "uuid", "senderType": "CUSTOMER|AI|OWNER", "content": "...", "messageType": "TEXT", "createdAt": "ISO" } ],
  "catalog":   [ { "id": "uuid", "name": "T-Shirt", "basePrice": "299.99", "trackInventory": true, "stockQuantity": 10,
                   "attributes": { "material": "Cotton" }, "isActive": true } ],
  "businessKnowledge": { "policies": { "delivery": "...", "returns": "..." }, "faqs": [ { "question": "...", "answer": "...", "keywords": ["..."] } ] },
  "customerOrders": [ { "orderNumber": 1002, "status": "PENDING_APPROVAL", "items": [ { "name": "...", "quantity": 1 } ] } ],
  "message": "عايز تيشيرت",
  "messageId": "uuid"
}
```
- **`messageId` إجباري**: هو `orderCandidate.sourceMessageId`.
- `catalog` يشمل المنتجات غير النشطة عادي (الـ AI بيشيلها). `conversation` بأي ترتيب (بيترتب بـ `createdAt`)، ولو الرسالة الحالية جواه بتتشال.
- `businessKnowledge` و`customerOrders` اختياريين (لسه مش موجودين في الباك: SCRUM-33 والـ Orders). من غير `customerOrders` سؤال "طلبي وصل فين؟" بيتجاوب بـ "معنديش وصول لحالة الطلبات".
- `attributes` مسطحة: مفاتيح مرنة (`Color`/`لون`، `Size`/`مقاس`) وقيم زي `"Black, Gray"` أو `"S/M/L"`.

### الـ Response (E0-3 حرفيًا)
```json
{ "intent": "INQUIRY|PURCHASE_INTENT|CONFIRMED_ORDER|OTHER", "reply": "...", "requiresReview": false, "orderCandidate": null }
```
- `orderCandidate` **بيتبعت بس لما العميل يأكد** (`CONFIRMED_ORDER`): `sourceMessageId`, `confidence`, `reviewReasons`, `items[{catalogItemId, variantId:null, rawText, quantity, selectedAttributes, notes, confidence}]`. **مفيش** أسعار ولا إجمالي ولا مخزون ولا status أبدًا (الـ Schema مقفول).
- الـ Router بيفهم 9 نيات أدق وبيتحوّلوا لـ 4: الاستفسارات ← `INQUIRY`، الطلب ← `PURCHASE_INTENT` (ويبقى `CONFIRMED_ORDER` بس بعد "أيوه")، والباقي (تحية/شكر/شكوى/غير مفهوم) ← `OTHER`.
- معلومات للتشخيص بتيجي في **headers** عشان الـ body يفضل مطابق للـ Schema: `X-AI-Source`, `X-AI-Detailed-Intent`, `X-AI-Router-Model`, `X-AI-Generator-Model`, `X-AI-Guard`, `X-AI-Latency-Ms`.

## النوايا (16) وإزاي بتتحوّل لـ E0-3
الـ Router بيفهم 16 نية أدق، والرد للباك دايمًا واحدة من 4 (`INQUIRY` / `PURCHASE_INTENT` / `CONFIRMED_ORDER` / `OTHER`). التفاصيل في header `X-AI-Detailed-Intent`.

| النية | مثال | E0-3 | `requiresReview` | الرد |
|---|---|---|---|---|
| `PRODUCT_INQUIRY` / `PRICE_INQUIRY` | "عايز تيشيرت" / "بكام؟" | INQUIRY | لا | من الكتالوج |
| `CREATE_ORDER` | "هاخد 2 تيشيرت" | PURCHASE_INTENT، ثم CONFIRMED_ORDER بعد "أيوه" | حسب الـ candidate | ملخص ثم candidate |
| `GENERAL_INFO` | "بتفتحوا امتى؟" + **أي سؤال في الـ FAQ** | INQUIRY | لا | من الإعدادات أو الـ FAQ |
| `HELP` | "إزاي أطلب؟" | INQUIRY | لا | شرح ثابت |
| `ORDER_STATUS` (كانت FOLLOW_UP) | "طلبي وصل فين؟" | INQUIRY | لا | حالة الطلب من `customerOrders` |
| `RETURNS_POLICY` | "إزاي أرجع المنتج؟" | INQUIRY | لا | `policies.returns` أو "معنديش معلومة مؤكدة" |
| `ORDER_CANCEL` / `ORDER_MODIFY` | "عايز ألغي الأوردر" | OTHER | **لا في السؤال، آه بعد "ايوه"** | خطوتين، شوف تحت |
| `PAYMENT_DISPUTE` | "أنا دفعت ومحدش رد" | OTHER | **آه** | رد هادي يطلب التفاصيل |
| `LEGAL_THREAT` | "هشتكي عليكم" | OTHER | **آه** | رد هادي يطلب التفاصيل |
| `CUSTOM_REQUEST` | "عايز تصميم خاص" | OTHER | **آه** | "بتتفق مع صاحب المحل" |
| `COMPLAINT` / `GREETING` / `THANKYOU` / `UNKNOWN` | | OTHER | `COMPLAINT` بعد نزاع/تهديد بس | قوالب ثابتة |

> **لازم Yomna تأكد:** E0-3 بيشرح `requiresReview` للـ orders بس. هنا بنرجّعه `true` على رد `OTHER` من غير `orderCandidate` ليعني "صاحب المحل لازم يشوف الرسالة دي". لو الباك مش بيعمل إشعار في الحالة دي، نفس الـ flag هيتجاهل.

### الإلغاء والتعديل (الـ AI مبيلغيش ولا بيعدّل حاجة)
1. العميل: "عايز ألغي الأوردر" ← الـ AI: "عايز تلغي طلب رقم 1002 (…)؟ اكتب (ايوه) لتأكيد الإلغاء."
2. "ايوه" / "ايوه الغي" ← "إلغاء طلب رقم 1002 محتاج صاحب المحل يأكده بنفسه." مع `requiresReview: true` (مفيش "اتلغى" أبدًا، والـ Guard بيمنعها).
3. "لا" / "متلغيش" / "don't cancel" ← "تمام، الطلب زي ما هو."
كلمات الرد بتتفهم حسب السؤال: في سياق الإلغاء "الغي" = **نعم**، وفي ملخص الطلب "لا خلاص الغي" = **رفض**.
لو العميل في نص طلب جديد وكتب "غير المقاس لـ L" ده تعديل على الملخص الجاري مش على طلب قديم.

### أسئلة البيزنس الديناميكية (FAQ)
`businessKnowledge.faqs = [{question, answer, keywords?}]`. الـ Router بيشوف الأسئلة **مرقّمة** (من غير الإجابات) ويرجّع `faq_id`، والإجابة بتتقرا من الداتا بالرقم. الكود كمان بيصحّح لو الـ Router قال PRICE/UNKNOWN على سؤال موجود في الـ FAQ. لو مفيش إجابة: "معنديش معلومة مؤكدة"، ومفيش اختراع.

### الميزانية
"تحت 200 جنيه" / "أرخص من 500" / "ميزانيتي ميتين" / "under 300" بتتحوّل لـ `max_price` وبتفلتر المنتجات (المنتج من غير سعر مش بيدخل). "عندكم حاجة تحت 130؟" بيعرض كل اللي يناسب من الأرخص، ولو مفيش بيقول أرخص حاجة موجودة.

### وضع الحذر (`is_angry_customer`)
لو في الرسالة أو آخر 3 رسايل نزاع دفع/تهديد: ردود القوالب بس (من غير Generator) ومن غير جملة "تحب تطلبه؟"، وأي شكوى بعدها بتتحوّل لصاحب البيزنس.

### سياسة اللون والمقاس
| الكتالوج | اللي بيحصل |
|---|---|
| بيعرّف خيارات (`Color: "Black, White"`) | الـ AI بيسأل لو ناقص، ويرفض اللي مش موجود |
| مفيهوش خيارات (زي الداتا الحقيقية دلوقتي) | **مبيسألش**، وبيحط اللي العميل قاله في `selectedAttributes` زي ما هو + `reviewReasons:["VARIANT_UNCLEAR"]` + `requiresReview:true`، والعميل بيتقاله إن صاحب المحل هيأكده |

> الدوكيومنت كان بيقول "يحطهم في `variant`"، بس في E0-3 مفيش حقل ده (`variantId` لازم UUID والـ Schema مقفول)، فاستخدمت `selectedAttributes` (الافتراض A1).

### ردود التوصيل (حسب `settings`)
`deliveryEnabled=false` → "التوصيل مش متاح حالياً، والاستلام من الفرع متاح." | `true` → "التوصيل متاح، والأسعار هتتحدد من صاحب المحل." | ممنوع أي وعد زي "هراجع مع الفريق".

## اللغة
أي حرف عربي (أو فرانكو زي `3ayez tshirt`) = رد عربي مصري. لاتيني = إنجليزي. القوالب والـ Generator بيلتزموا بكده، والـ Guard بيرفض لغة غلط.

## الاختبارات
```bash
pytest -q   # 431 اختبار
```
بتغطي: الداتا الحقيقية من Railway، المواعيد كصفوف، الـ attributes المسطحة، فلترة `isActive`، سياسة اللون/المقاس، الطلبات متعددة الخطوات، **كل رد بيتحقق منه ضد الـ JSON Schema الرسمي لـ E0-3** (+ أمثلة الدوكيومنت التلاتة)، الـ Router+Generator+Guard بموديل وهمي (503/429/404/403/timeout/JSON بايظ)، والـ HTTP.
الاختبارات مش بتكلم الإنترنت. **ما اتجرّبش نداء Gemini ناجح فعليًا**: جرّبيه بمفتاحك (`GET /health?probe=true` بيعمل نداء صغير لكل Role).

## الملفات
```
main.py                       السيرفر + /v1/ai/respond + /health
app/config.py                 الإعدادات + fail-fast
app/schemas/request.py        شكل الـ request الحقيقي
app/schemas/response.py       E0-3 Schema 1.0 (extra=forbid)
app/schemas/internal.py       ناتج الـ Router + الـ Plan
app/pipeline/context.py       فلتر isActive الصارم، اللغة، حالة المحادثة، الطلبات، الإلغاء/التعديل المعلّق، FAQ، وضع الحذر
app/pipeline/orchestrator.py  Hard rules → Router → Planner → Generator → Guard
app/pipeline/planner.py       قواعد البيزنس (كتالوج، مخزون، مواعيد، توصيل، candidate)
app/pipeline/guard.py         التحقق من كلام الـ Generator
app/providers/__init__.py     اختيار الـ provider من AI_PROVIDER
app/providers/gemini.py       GeminiClient (retry/fallback/cooldown) + Router + Generator
app/providers/rules.py        الـ Router بالقواعد (fallback ومحرك offline)
app/prompts/                  prompt الـ Router/Generator + القوالب (عربي/إنجليزي)
app/nlu.py                    عربي مصري/فرانكو/إنجليزي: typos، كمية/لون/مقاس
app/dev.py + mock_data.py     ملعب الـ mock (مقفول افتراضيًا، مش في مسار التشغيل)
```

## أسئلة مفتوحة للفريق
1. شكل الـ request (فوق) مع Yomna، ومعاه `messageId`. 2. شكل `businessKnowledge` لما SCRUM-33 يخلص. 3. `customerOrders` لما الـ Orders تتبني. 4. مفيش نية CANCEL: "لا خلاص" بترجع `OTHER` برد مهذب من غير طلب.
