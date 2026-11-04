# Named comparisons and Gemini reply diagnostics — 4 November 2026

## Verified findings

The reported Groq response was syntactically valid, but its original `Meaning`
fields were not retained. We cannot claim the live model invented a search or a
handle. Controlled Gemini/Groq-compatible responses reproduce the AI-side failure:

* Existing Arabic token keys already normalize `التيشيرت` to `تيشيرت`, but the
  conversational named-product detector used raw normalized words instead of
  these keys. An explicit article could therefore fail to establish a new product.
* Full conversational questions reached legacy product scoring. The named
  example produced tokens including `قصدي`, `والابيض`, `انهي`, `ارخص` alongside
  the two product-name tokens. Two matching terms out of six fell below the
  matcher's threshold. This is independent of successful structured JSON parsing.
* Two color alternatives were extracted deterministically only when a previous
  product existed. A failed initial search therefore deprived the named follow-up
  of comparison structure. No trusted price-difference operation existed.

The standalone path now shares search normalization between interpretation and
retrieval (`app/data/search.py`). It reuses Arabic articles, existing product
synonyms and spelling matching; strips question/comparison/option tokens; adds a
matching-only cotton alias; and keeps substantive qualifiers. Every remaining
term must match catalog evidence. Cotton cannot silently match polyester.
Legacy v1 NLU and matching are unchanged.

`app/chat/understanding.py` validates explicit selections, search provenance,
known handles, and requested comparison alternatives inside the provider parse
callback. Semantically unusable results trigger existing bounded model/provider
attempts before deterministic fallback. Untrusted model names do not authorize
new reads or scope. Search shortening cannot discard an explicit customer noun
or qualifier. Shared size and two color alternatives are represented separately.

A bare two-color question without product context asks which product; a named
follow-up resolves fresh evidence. Failed searches do not create a product
selection. Existing cancellation and unrelated-topic clearing remain covered.
Comparisons clear inherited purchase intent and quantity.

`app/pipeline/price_comparison.py` subtracts two current, active, option-verified,
same-product, same-currency Decimal prices with a local precision context. It
requires exactly two requested alternatives and two resolved variants. Missing
prices/alternatives, multiple sizes/products or ambiguous pairs cannot produce a
cheapest claim. Equality is handled explicitly. It compares only the requested
pair, without claiming a global catalog minimum or stock reservation.

The immutable price-difference clause is mandatory in natural composition.
Python renders it; neither model supplies prices or arithmetic. The existing
manifest and composition checks remain active. `orderCandidate` stays null.

The captured rules/fake follow-up now says:

> الأسود مقاس L بـ275 جنيه، والأبيض بنفس المقاس بـ285 جنيه، والأسود مقاس L أرخص بـ10 جنيه

## Gemini HTTP 400: unresolved live cause

No live calls were made. The exact `NaturalReply` schema passes serialization
through installed google-genai **2.33.0**, including `$defs`/`$ref`, array bounds,
closed objects, required fields and enum fields. The actual Gemini client's config
uses `response_json_schema`, JSON MIME and the requested temperature; an offline
SDK stub regression confirms this path. This proves local SDK compatibility,
not model/server acceptance, account access or live API compatibility.

`app/providers/structured.py` now identifies confirmed schema-area failures from
BadRequest field violations or explicit known SDK/API schema markers. Only fixed
labels (`response_json_schema`, `response_schema`, `schema_constraints`) and
allowlisted category/status are exposed. Raw paths, descriptions, messages,
customer text and credentials are never added to diagnostics. Generic HTTP 400
remains `api_request_error`, with no schema hint. It is **not** assumed to be a
schema failure. The existing provider fallback preserves strict output validation.
No model identifiers or API configuration were blindly changed.

## Files changed in this correction

* `app/data/search.py`, `app/data/retrieval.py`, `app/data/options.py`: canonical search, qualifier checks and shared option normalization.
* `app/chat/understanding.py`: product anchors, comparisons, semantic validation/prompt.
* `app/pipeline/evidence_planner.py`, `app/chat/application.py`: per-turn comparison metadata.
* `app/pipeline/price_comparison.py`, `app/chat/natural.py`: exact grounded comparison.
* `app/providers/structured.py`: safe schema-specific failure classification.
* `app/chat/diagnose.py`: exact NaturalReply offline SDK check.
* `app/chat/evaluate.py`: reported two-turn acceptance scenario and parsed fields.
* `tests/test_named_comparison_regression.py`: 32 new offline cases.
* `docs/CHAT_ACCEPTANCE_RULES.jsonl`, `docs/CHAT_ACCEPTANCE_FAKE.jsonl`: refreshed captures.
* This document and `docs/MULTI_PROVIDER_DEVELOPMENT.md`: findings and verification.

The workspace already contains earlier uncommitted integration work; the list
above identifies this correction, rather than attributing all Git status entries
to this task. Actual `.env` credentials were not read or changed.

## Offline verification

With `AI_PROVIDER=rules` and `ENABLE_DEV_ENDPOINTS=false`:

* Full suite: **1,320 passed, 2 warnings**. Warnings: existing Starlette/httpx
  deprecation and Windows pytest cache write permission.
* Rules and fake evaluations: **all checks passed**, six scenarios / seventeen turns
  each, including the original five-turn conversation and the new named comparison.
* `python -m app.chat.diagnose`: Meaning, ConversationReply and NaturalReply
  serialization passed; `networkUsed=false`.

The new suite covers articles/synonyms, mixed and English-only catalog names,
Franco, noisy structured search, actual Groq MockTransport responses, Gemini SDK
config, provider semantic failover, missing alternatives, wrong size, fabricated
search/handles, changed selections, unrelated products, equal/missing prices,
Decimal boundary arithmetic, duplicate variants or two sizes of just one color,
and safe generic/schema HTTP 400 classification.
Existing cancellation, fresh purchase, tenant/token isolation, retrieval budgets
and guard suites pass unchanged.

## Operator-initiated live verification

Run from the repository root using locally configured provider credentials and
operator-verified model IDs. These commands use **synthetic Backend data only**.
No development/production Backend flags are needed. Each `--allow-live` command
spends provider quota; none was executed during this correction.

```powershell
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe -m app.chat.diagnose
.\venv\Scripts\python.exe -m app.chat.evaluate --mode groq --allow-live
.\venv\Scripts\python.exe -m app.chat.evaluate --mode gemini --allow-live
.\venv\Scripts\python.exe -m app.chat.evaluate --mode auto --allow-live
```

The evaluation prints `interpretation.search`, `product_handle`, `options`,
`option_alternatives`, prepared search, checks and sanitized provider diagnostics.
Those extra fields appear only in this fixed synthetic evaluator, not runtime
customer diagnostics. Inspect both turns in `named_price_comparison` and confirm
INQUIRY, two variants, both prices and the exact 10 EGP difference. Inspect
`replyProvider`: Groq fallback success does not establish Gemini reply success.
Gemini mode allows the configured secondary; a successful reviewed **Gemini**
reply is still required to close the live HTTP 400 issue.

If access/model errors occur, operator-authorized metadata discovery is:

```powershell
.\venv\Scripts\python.exe -m app.chat.diagnose --discover --allow-live
```

It lists accessible generation model identifiers without generation or credential
output. A generic 400 without a hint still needs operator inspection of the
provider's request diagnostics/support tools; do not paste raw sensitive payloads.

## Remaining limits

Lexical product matching is intentionally conservative. Unknown translations,
synonyms, brand-only references and unusual qualifiers may need clarification;
models cannot invent a catalog association to overcome this. Arbitrary options
still depend on declared Backend evidence. Price-difference presentation currently
supports exactly two resolved variants with one alternative dimension. Larger or
ambiguous comparisons retain safe clarification. Natural generation remains a
restricted composition grammar, not unrestricted sales prose. No Orders, live
Backend integration, v2 activation or v1/v2 unification was introduced.
