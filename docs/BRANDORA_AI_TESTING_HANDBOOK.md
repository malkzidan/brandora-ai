# دليل تجربة Brandora AI على Windows PowerShell

## 1. ابدأ بالتجربة الآمنة

من root المشروع:

```powershell
.\venv\Scripts\python.exe -m app.offline_demo
```

الأمر ده موجود فعلًا في `app/offline_demo.py:main`. بيستخدم **synthetic Backend + Groq-compatible HTTP stub**. يعني بيعدي من FastAPI canonical/auth/history/typed data/Guard الحقيقيين، لكن Backend وGroq requests بيترد عليهم بـ `httpx.MockTransport` داخل الجهاز. مش بيانات محل حقيقي، ومش live inference، ومش دليل مفتاح Groq شغال. الموديول بيقفل dotenv loading قبل config؛ مفيش احتياج لقراءة `.env`.

`You>` مكان كتابة رسالتك. `AI>` dictionary بالـ E0-3 response، مش نص الرد لوحده. `Tools>` actual Backend reads في الطلب ده؛ ممكن تشمل reads لاسترجاع selectors من التاريخ. `synthetic Groq-compatible stub` معناها استجابة برمجية مطابقة لصيغة API، مش نموذج بيستنتج اللغة بنفسه.

الأوامر المتاحة هنا فقط: `/reset` يبدأ synthetic harness/history جديد، و`/quit` يخرج. `/catalog` و`/mode` **مش أوامر للديمو ده**؛ موجودين في CLI آخر `app.chat`، اللي مش نفس تجربة canonical history. الإدخال العادي مش command لتغيير stock أو إطلاق failure.

لو venv مش موجودة أو import dependency ناقصة، توقف وراجع setup؛ الدليل مش بيطلب تنزيل packages أو مفاتيح. أثناء audit استخدمنا venv الموجودة، Python 3.13.7.

## 2. الأربع رسائل: نتيجة اتعادت فعلًا

اكتبهم في **نفس الجلسة** من غير `/reset` بينهم:

```text
عندكم تيشيرت أسود؟
طب مقاس L بكام؟
طب عايزة 10 قطع من مقاس L
طب خلاص، خليهم 3 قطع من الأبيض مقاس L بدل الأسود
```

| الدور | intent | Tools بالترتيب في التشغيل الفعلي هنا | المتوقع |
|---|---|---|---|
| 1 | INQUIRY | get_products → get_product_details | Black/M250 وBlack/L275، ويسأل المقاس |
| 2 | INQUIRY | get_conversation_history → get_products → get_product_details → get_variant_details | Black/L275 |
| 3 | PURCHASE_INTENT | نفس الدور2 | quantity10، shortage، review=true، يخفي stock4 |
| 4 | PURCHASE_INTENT | history → products → product_details → variant_details → variant_details | White/L285، quantity3، review=false |

آخر ردين بالضبط في إعادة التشغيل التفاعلي:

```text
تمام، بالنسبة للـ10 قطع من الأسود مقاس L بـ275 جنيه للقطعة، والكمية دي مش متاحة بالكامل حاليًا. نراجع إمكانية توفير الكمية مع المسؤول؟

تمام، بالنسبة للـ3 قطع من الأبيض مقاس L بـ285 جنيه للقطعة، والتوافر النهائي محتاج تأكيد
```

في الاتنين `orderCandidate=None` في Python print، وده نفسه JSON `null`. مفيش حجز ولا طلب شراء. `requiresReview=True` معناه owner attention signal، مش notification حصلت. stock الفعلي من fixture بيبقى داخلي؛ مش رسالة لازم تظهر للمستخدم.

قراءة variant مرتين في الدور4 مش duplicate order؛ replay لاختيار سابق ثم قراءة White/L الحالي. ترتيب/عدد calls ممكن يختلف مع catalog أو history مختلفة، لكن أدوات write مستحيل تكون نتيجة متوقعة.

## 3. جهز جلسة الاختبارات من غير live services

```powershell
Set-Location -LiteralPath 'C:\Users\ELTANANY 01062856027\Desktop\brandora-ai'
$env:AI_PROVIDER = 'rules'
$env:ENABLE_DEV_ENDPOINTS = 'false'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

دي process variables للجلسة، مش تعديل `.env`. `AI_PROVIDER=rules` يوقف legacy Gemini؛ الاختبارات اللي بتحتاج structured provider behavior بتحقنه كمحاكاة، مش live calls. ما تشغلش `--mode groq/auto/gemini/openrouter` في audit offline.

اختبار الكل، بنفس اختيار cache اللي استخدمناه عشان Windows permissions:

```powershell
.\venv\Scripts\python.exe -m pytest -q --tb=short -p no:cacheprovider
```

**اللي اتشغل هنا فعلًا:** 1580 passed، 0 failed، 0 skipped، 1 warning، 31.56 ثانية. warning هي `StarletteDeprecationWarning` لاستخدام httpx مع TestClient. مش failure، ومش network call. من غير `-p no:cacheprovider` ممكن يظهر كمان Windows pytest-cache access warning المعروف؛ ما عدلناش permissions أو dependencies عشان نخفيه.

كل أوامر الاختبارات الجزئية تحت verified إن filenames والـ selectors موجودين. **ما أعدناش كل command جزئي كتشغيل منفصل**؛ نفس الاختبارات اتنفذت ضمن full suite أعلاه. ما تجمعش أعداد suites متداخلة وتقول إنها tests مختلفة.

## 4. أوامر موجودة فعلًا

| المطلوب | PowerShell command بعد إعداد البيئة | الدليل |
|---|---|---|
| Independent canonical HTTP evaluation | `.\venv\Scripts\python.exe -m app.offline_demo --evaluate` | اتعاد هنا: 12 scenarios / 23 turns، failed=[] |
| Canonical HTTP + auth/history/proxy | `.\venv\Scripts\python.exe -m pytest tests/test_canonical_integration.py -q -p no:cacheprovider` | نفس canonical /v2 path، signed synthetic context |
| Products compatibility | `.\venv\Scripts\python.exe -m pytest tests/test_products_integration.py -q -p no:cacheprovider` | 45 cases موجودة ضمن full run؛ الأربع tools فقط |
| Context + stock customer copy | `.\venv\Scripts\python.exe -m pytest tests/test_customer_stock_regression.py -q -p no:cacheprovider` | 33 cases ضمن full suite |
| History foundation + canonical | `.\venv\Scripts\python.exe -m pytest tests/test_history_service.py tests/test_canonical_integration.py -q -p no:cacheprovider` | legacy prepare وstrict prepare_authorized مش نفس guarantees |
| Typed Backend/HTTP contract | `.\venv\Scripts\python.exe -m pytest tests/test_backend_client.py tests/test_backend_data.py -q -p no:cacheprovider` | UUID/Decimal/envelopes/isolation/errors |
| Retrieval/planning | `.\venv\Scripts\python.exe -m pytest tests/test_retrieval_policy.py tests/test_evidence_planner.py -q -p no:cacheprovider` | limits، actual variants، missing evidence |
| Groq + Guard/fallback | `.\venv\Scripts\python.exe -m pytest tests/test_multi_provider_development.py tests/test_evidence_generation.py tests/test_chat_provider_regressions.py -q -p no:cacheprovider` | controlled provider HTTP/semantic failures، مش live |
| Orders safety فقط | `.\venv\Scripts\python.exe -m pytest tests/test_standalone_pipeline.py tests/test_customer_stock_regression.py -k 'order or purchase or shortage or stock or correction or cancel' -q -p no:cacheprovider` | منع writes/confirmation، مش تنفيذ order |
| Auth/scope negatives | `.\venv\Scripts\python.exe -m pytest tests/test_canonical_integration.py tests/test_products_integration.py -k 'auth or scope or signed or token or context or binding or proxy' -q -p no:cacheprovider` | forged IDs/body/signature/tenant/proxy |
| Concurrency/isolation | `.\venv\Scripts\python.exe -m pytest tests/test_canonical_integration.py tests/test_retrieval_policy.py tests/test_standalone_pipeline.py -k 'concurrent or scope or isolated' -q -p no:cacheprovider` | request-local state بين العملاء والمحلات |
| Rules evaluation | `.\venv\Scripts\python.exe -m app.chat.evaluate --mode rules` | اتعاد هنا: 17 turns، failedChecks=[] |
| Fake-model evaluation | `.\venv\Scripts\python.exe -m app.chat.evaluate --mode fake` | اتعاد هنا: 17 turns، failedChecks=[] |

rules/fake evaluations بتستخدم `ChatSession` synthetic local session، مش canonical signed HTTP history. عشان تختبر المسار ده استخدم offline_demo/canonical tests. الاتنين مفيدين لكن مش interchangeable. ملفات JSONL القديمة في docs historical captures؛ المراجعة دي قرت النتائج من stdout وما عدلتش captures القديمة.

## 5. Products: جرّب إيه بإيدك وإيه محتاج test؟

اعمل `/reset` قبل الحالات المستقلة، واحتفظ بنفس الجلسة للفولو-أب. أسماء الأدوات في الجدول abbreviations: P=`get_products`، D=`get_product_details`، V=`get_product_variants`، VD=`get_variant_details`، H=`get_conversation_history`.

| Scenario | Input / fixture | Expected intent | Expected tools | Expected behavior | Test command/location / النوع |
|---|---|---|---|---|---|
| Discovery | `عندكم تيشيرت أسود؟` | INQUIRY | P,D | مقاسين فعليين، سؤال اختيار | Interactive demo؛ test_canonical_integration.py |
| Product details | `black tshirt size L price` | INQUIRY | P,D,VD | 275، مش base200 | Interactive؛ test_products_integration.py:test_success_current_effective_price_and_exact_e03_contract |
| Variants pagination | fixture أكتر من embedded20 | INQUIRY | P,D,V؛ VD لو اختيار محدد | استكمال bounded، مش اختلاق variants | Automated؛ test_products_integration.py:test_product_and_embedded_variant_pagination_are_retrieved؛ Requires custom fixture لو يدوي |
| Sizes/colors | `عندكم تيشيرت أبيض مقاس L؟` | INQUIRY | P,D,VD | White/L285 | Interactive؛ customer_stock_regression / chat_application |
| Price follow-up | بعد Black inquiry: `طب مقاس L بكام؟` | INQUIRY | H,P,D,VD | fresh275 | Interactive؛ selection_correction scenario |
| Missing price | `عندكم كاب بكام؟` | INQUIRY | P,D | سعر غير مؤكد، مش صفر | Interactive؛ app.offline_demo missing_price |
| Zero stock | `عندكم تيشيرت أزرق مقاس M؟` | INQUIRY | P,D,VD | unavailable؛ سعر0 هنا صحيح في fixture | Interactive؛ test_customer_stock_regression.py:test_inventory_customer_policy |
| Insufficient stock | `عايزة 10 تيشيرت أسود مقاس L` | PURCHASE_INTENT | P,D,VD | review offer، no count4، order=null | Interactive؛ same test + internal_shortage_facts |
| Within stock | `عايزة 3 تيشيرت أسود مقاس L` | PURCHASE_INTENT | P,D,VD | confirmation caveat، review=false | Interactive؛ same policy test |
| Untracked | `عندكم تيشيرت أبيض مقاس M؟` | INQUIRY | P,D,VD | price225، availability needs confirmation | Interactive؛ untracked scenario |
| Inactive variant | `blue tshirt size L price` | INQUIRY | P,D؛ VD حسب selectors | لا205، لا substitution بـBlue/M | Interactive؛ test_chat_application.py:test_inventory_and_clarification |
| Inactive product | `isActive=false` على parent fixture | INQUIRY | scoped reads، بلا active offer | ما يعرضش withdrawn price | Automated؛ test_products_integration.py:test_inactive_records_do_not_quote_withdrawn_price؛ Requires custom fixture لو يدوي |
| Multiple matching products | duplicate matching product fixture | INQUIRY | catalog، بدون fan-out أعمى | يسأل أي منتج | Automated؛ test_retrieval_policy.py:test_ambiguous_products_are_not_silently_resolved_or_fanned_out_into_variants |
| Unknown product | `hoodie price` | INQUIRY | P أو clarification حسب selector | لا275 من تيشيرت قديم | Interactive؛ test_canonical_integration.py:test_new_unrelated_product_clears_previous_purchase_context |
| Price comparison | `قصدي التيشيرت القطن الأسود والأبيض مقاس L أنهي أرخص؟` | INQUIRY | P,D ثم variants موثقة | 275/285، Black أرخص10 بـDecimal | Interactive؛ named_comparison scenario/test_named_comparison_regression.py |
| Changed options | بعد Black/L: `غيرت رأيي، عايزة الأبيض مقاس M` | PURCHASE_INTENT | H + fresh reads | White/M225، untracked، مفيش inherited stock4 | Interactive؛ test_customer_stock_regression.py:test_contextual_changes_refresh_data |
| Wrong tenant/malformed DTO | controlled invalid Backend response | inquiry/purchase أو HTTP403 | يتوقف عند الرفض | لا facts محمية ولا سعر مخترع | Automated؛ test_backend_data.py، test_products_integration.py |
| Provider outage | `h.model_failure=503`/timeout/json/guard | نفس semantics الآمنة | نفس read-only policy | Python fallback بنفس الحقائق | Automated؛ test_customer_stock_regression.py:test_exact_four_turn_http_correction_with_model_and_fallback |
| Exact stock policy | explicit count question + tenant allowlist | INQUIRY | H/VD حسب context | count فقط لو الشرطين متحققين | Automated؛ test_exact_count_requires_both_explicit_question_and_tenant_policy |

الديمو مفيهوش command يغير stock أو يحقن401 أو يضيف catalog rows؛ متقولش «اكتب 503» عشان تحاكي outage. الاختبارات فوق فيها fixtures دي فعلًا. `OfflineHarness.backend_failure`, `.model_failure`, `.history_patch`, `.history_chunk_size` seams برمجية في tests، مش customer API أو أوامر interactive. ما نضيفش production flags عشان الاختبار.

## 6. History/Context: مصفوفة الاختبارات

| Scenario | Input / setup | Expected intent | Expected tools | Expected behavior | Test location / النوع |
|---|---|---|---|---|---|
| First named message | أول رسالة Black tee | INQUIRY | P,D؛ noH | skip history | Interactive + canonical independent scenarios |
| Size follow-up | `طب مقاس L بكام؟` | INQUIRY | H + products | Black/L restored، fresh price | Interactive + exact_four_turn test |
| Changed color | `خليهم 3 من الأبيض بدل الأسود` | PURCHASE_INTENT | H + products/variants | oldBlack مش alternative | Interactive + contextual_changes_refresh_data |
| Changed quantity | بعد purchase: `طب خليهم 12` ثم `طب خليهم 2` | PURCHASE_INTENT | H + fresh reads | 12 review/shortage؛2 cautious، noorder | Interactive + contextual_changes_refresh_data |
| Color + size | `غيرت رأيي، عايزة الأبيض مقاس M` | PURCHASE_INTENT | H + fresh reads | White/M؛ evidence جديد | Interactive + same test |
| Inactive correction | `طب خليها الأزرق بدل الأسود` بعدBlack/L | INQUIRY | H + product reads | حافظ علىL، اسأل بديل؛ لا205 | Interactive + blue_correction_preserves_product_and_size |
| New product | `بدل الأسود عايزة الكاب` | PURCHASE_INTENT | P,D؛ noH | Cap مش T-shirt؛ السعر غيرمؤكد | Interactive + unrelated_named_product test |
| Comparison after purchase | `الأسود ولا الأبيض مقاس L أنهي أرخص؟` | INQUIRY | H + fresh data | لا inherited purchaseqty، difference10 | Interactive + comparison_after_purchase_and_cancel |
| Cancellation | `خلاص مش عايزة` | OTHER | observed P إضافية؛ noH | clear provisional selection، لا cancel-order action | Interactive؛ ملاحظة read زيادة، مش إصلاح في audit |
| Missing/partial history | history_status unavailable/partial | clarification | H فقط؛ no catalog guess | يسأل المنتج | Automated؛ correction_with_untrusted_history؛ interactive بعدreset فيه empty history لكن ده مش timeout/partial simulation |
| Pagination | history_chunk_size fixture | حسب الرسالة | H مكرر bounded | نفس snapshot/order/cutoff | Automated؛ test_canonical_integration.py وtest_history_service.py |
| Old/duplicate/current/future | injected rows/metadata | clarification أو normal identical dedup | H ثم reads لو context complete | لا replay لcurrent/future؛ conflict partial | Automated؛ canonical history boundary/duplicate tests |
| Wrong conversation/customer/business | signed/scoped mismatches | HTTP403 أورفض قبلread | no leaked facts | IDs تتطابق كلها | Automated؛ canonical signed_context/history scope tests |
| Backend401/403/timeout | controlled responses | auth rejection أوclarification | bounded H/reads | لا stale authority | Automated؛ test_canonical_integration.py/test_history_service.py |
| Concurrent customers | ThreadPoolExecutor/async fixtures | independent | scoped reads لكلطلب | لا shared Selection/token/cache | Automated؛ canonical/retrieval/standalone concurrency tests |

الـ Demo يمسك تاريخ synthetic داخل harness ويستدعي canonical route برسالة وخمس IDs، **مش بيبعت body.history**. `/reset` يبدأ التخزين من جديد؛ مش بيمثل DB deletion حقيقية. AI ما بيحفظش reply في Backend؛ demo يحاكي رحلة الاختبار، مش delivery system.

## 7. Orders safety: إيه الإثبات وإيه مش إثبات؟

* اختبر `عايزة 3 تيشيرت أسود مقاس L`: intent purchase، quantity3، `orderCandidate=null`؛ العبارة مش order confirmation.
* اختبر shortage10،zeroBlue/M،untrackedWhite/M: لا stock guarantee ولا notify/reservation claims.
* غير اللون/الكمية قبل التأكيد، وبعدها cancellation: ده selector state بس. `cancel` مش استدعاء Backend order-cancel؛ مفيش الأداة أصلًا.
* `test_standalone_pipeline.py:test_order_extension_has_no_enable_switch_or_execution_handler` يثبت extension disabled؛ tests منع generator تغيير intent/review مكملة له.
* duplicate message tests تثبت history/IDs/safety، **مش exactly-once reply delivery**؛ AI مفيهوش persistent response-idempotency store. محتاج Backend outbox/dedup لاحقًا.
* `requiresReview=true` مش database row ولا owner notification receipt. عدم وجود write tools والكود الحالي هو دليل عدم الإرسال؛ مش نتيجة اتصال notification حقيقي.

**Orders readiness:** incomplete عمدًا. tests pass لأنها تمنع action، مش لأنها نفذت approved order. أي future order integration محتاجة schema/state/auth/transactions/idempotency واختبارات مستقلة.

## 8. إزاي تقرأ النتائج؟

`passed` معناها assertion نجحت في البيئة دي. `failedChecks=[]` معناها automatic checks بتاعة evaluator نجحت؛ تقييم اللغة والأسئلة لسه محتاج إنسان. `failed=[]` في offline_demo مش معناه Groq شغّال live. `requiresReview` إشارة owner attention، و`orderCandidate=null` عدم وجود order handoff قابل للتنفيذ. `Tools=[]` طبيعي مع greeting/clarification، لكنه regression لو رسالة محتاجة context اتفهمت غلط؛ راجع expected case.

لو حصل failure، احتفظ بـ test name وsanitized diagnostics وtool names، مش المفاتيح/raw customer payload. في demo البيانات synthetic وممكن تعرضها؛ في production ما تنسخش نفس transcript logging.

## 9. اللي لازم staging حقيقية عشان نثبته

| Verification | ليه offline مش كفاية؟ | النجاح شكله إيه؟ |
|---|---|---|
| Backend `/internal/ai/data` | المقابل الحقيقي مش منفذ | authenticated responses من services الحالية وبنفس DTO |
| Ownership | mock يعرف synthetic identities بس | wrong business/customer/conversation يتمنع داخل Backend نفسه |
| Stable history snapshot | fixture بيضمن metadata | concurrent writes ما تغيرش pages لنفس bound context |
| Live Groq | stub يعيد rulesHint وترتيب clauses | understanding/reply live ناجحين، latency/quota/fallback متراجعين بموافقة operator |
| DB price/stock freshness | offline map مش transaction real | correct current variant/Decimal، no cross-call guarantees مزيفة |
| Duplicate delivery | مفيش real webhook/outbox | نفس external message ما يكرر AI reply أو notification |
| Railway proxy/TLS | mock scope مش actual edge | verified proxy CIDRs وHTTPS reject/accept صح، health/readiness وفشل restart متراجعين |
| WhatsApp owner/customer reply | مفيش provider integration | signature، persistence، consent، delivery receipts/retries |

ما تشغلش live tests قبل Backend prerequisites. خطوات staging من غير تنفيذ في [Railway readiness](BRANDORA_RAILWAY_READINESS.md)، وعقد القبول في [Backend checklist](BRANDORA_BACKEND_IMPLEMENTATION_CHECKLIST.md).
