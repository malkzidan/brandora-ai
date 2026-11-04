# Independent on-demand history verification

All data/credentials/keys are synthetic. No Backend server, database, Docker,
real provider key or production access is needed. The real FastAPI route,
authentication, history decision, HTTP BackendClient, typed history reader,
ChatSession, Product tools, Groq-compatible HTTP stub and Guard all execute.

## Commands

```powershell
$env:AI_PROVIDER='rules'
$env:ENABLE_DEV_ENDPOINTS='false'
$env:PYTHON_DOTENV_DISABLED='1'
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe -m pytest tests/test_canonical_integration.py -q
.\venv\Scripts\python.exe -m pytest tests/test_products_integration.py -q
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m app.offline_demo --evaluate
.\venv\Scripts\python.exe -m app.chat.evaluate --mode rules
.\venv\Scripts\python.exe -m app.chat.evaluate --mode fake
```

The independent evaluator calls `/v2/ai/respond` with only businessId, customerId,
conversationId, messageId and message. The mock Backend stores messages and
serves them only when `get_conversation_history` is requested. It validates the
outbound service credential and signed context, returns newest-first scoped
snapshot pages and excludes the current message. There is no hidden supplied
history field in the HTTP request. Unit-test fixture helpers may seed Backend
storage; this is not caller-supplied FastAPI context.

Each evaluator turn prints the actual attempted tool names and syntheticGroq=true.
The stub uses the real GroqClient request/schema/parser interface, not live Groq
inference. Current Product evidence is always obtained through the mock tool
transport. No startup probe or external model call occurs.

## Interactive full HTTP conversation

```powershell
.\venv\Scripts\python.exe -m app.offline_demo
```

The synthetic Backend caller stores each current message before making its signed
HTTP request. The AI decides whether to request history. Tools> shows the exact
calls per turn. `/reset` resets synthetic Backend state/keys; `/quit` exits.
This tests canonical FastAPI, not the separate historical chat CLI.

## Local mock server and simulated Backend requests

```powershell
.\venv\Scripts\python.exe -m app.offline_demo --serve
```

Only127.0.0.1:8787 is bound. In a second terminal:

```powershell
$request = @{
  businessId = '00000001-0000-4000-8000-000000000001'
  customerId = '00000002-0000-4000-8000-000000000001'
  conversationId = '00000003-0000-4000-8000-000000000011'
  messageId = '00000009-0000-4000-8000-000000000001'
  message = 'عندكم تيشيرت أسود؟'
}
$signed = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/demo/context `
  -ContentType 'application/json; charset=utf-8' `
  -Body ([Text.Encoding]::UTF8.GetBytes(($request | ConvertTo-Json)))
$headers = @{}
$signed.headers.PSObject.Properties | ForEach-Object { $headers[$_.Name] = $_.Value }
$headers.Remove('Content-Type')
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/v2/ai/respond `
  -Headers $headers -ContentType 'application/json; charset=utf-8' `
  -Body ([Text.Encoding]::UTF8.GetBytes($signed.body))
```

For the next turn change messageId to a new UUID and message to `طب مقاس L بكام؟`,
then repeat signing/sending. **Do not add history/historyStatus.** The loopback
demo helper persists the synthetic current message and signs its exact bytes;
the mock Backend supplies previous messages through the history tool. A restarted
demo invalidates old contexts. Do not deploy this helper or its synthetic issuer.
The release app.server never imports it. Readiness/liveness endpoints are
configuration/process checks only, not real Backend acceptance.

## Arabic/Egyptian scenarios and required outcomes

Reset between rows; the first ten Arabic cases and additional Franco case remain
automated in the independent evaluation (11 scenarios/19 turns).

| Scenario | Messages | Required outcome/tools |
| --- | --- | --- |
| Comparison after purchase/change | عندكم تيشيرت أسود؟ → طب مقاس L بكام؟ → عايزة اتنين منه → طب غيرت رأيي عايزة الأبيض → أنا محتارة بين الأسود والأبيض مقاس L أنهي أرخص؟ | First named inquiry no history; subsequent references fetch exact conversation history. Black/L275, White/L285, difference10, INQUIRY and no inherited quantity on comparison. |
| Changed size | عندكم تيشيرت أبيض مقاس L؟ → طب مقاس M بكام؟ | History only on follow-up; current White/M225. |
| Price reference | عندكم تيشيرت أسود؟ → طب مقاس L بكام؟ | History then fresh products/variants,275. |
| Excess quantity | عايزة10 تيشيرت أسود مقاس L | No history; requested10 versus recorded4, no reservation. |
| Named comparison | قصدي التيشيرت القطن الأسود والأبيض مقاس L أنهي أرخص؟ | No history; actual two variants and exact Decimal difference10. |
| Zero stock | عندكم تيشيرت أزرق مقاس M؟ | No history; zero price valid, no recorded stock, no guarantee. |
| Untracked | عندكم تيشيرت أبيض مقاس M؟ |225, availability needs confirmation. |
| Missing price | عندكم كاب بكام؟ | Price unconfirmed; no invented base/default. |
| Cancellation | عايزة اتنين تيشيرت أسود مقاس L → خلاص مش عايزة | Cancel needs no history/model/tool and creates/cancels no actual order. |
| Greeting | أهلا | No history, Products or Groq calls. |
| Franco additional |3andkom tshirt eswed → bekam size L | On-demand history for size-only follow-up;275, Franco presentation. |

Additional HTTP regressions cover `والأبيض؟`, `غيرت رأيي خليها مقاس M`, and
`أنهي أرخص؟` with previously discussed alternatives. Changed colors/size/quantity
must supersede prior selectors. A named unrelated product cannot inherit one.

## Security and failure matrix

Automated tests cover:

* Inbound service/signature/audience/scope/time/ID/body binding, unchanged HTTPS
  and trusted proxy controls. Caller history/historyStatus are rejected.
* Exact three-argument history request, business/customer/conversation/anchor
  metadata checks and per-message conversation identity.
* Newest-first pages, reverse chronological reconstruction, exact/conflicting
  duplicates, timestamp ties, bad ordering/boundary and snapshot changes.
* Missing, AI-only, incomplete, unsupported or oversized history; bounded pages,
  characters, messages and deadline. No partial selection survives failure.
* History401/403 →403;404/5xx, timeout, invalid JSON → safe clarification without
  Products reads or invented previous choices.
* Groq failures → Python fallback; only current understanding/generation uses
  model calls. Historical AI/OWNER instructions/prices/stock are ignored.
* Fresh price changes, active/variant stock limitations, concurrent customers and
  businesses, duplicate current requests, no Orders and original Products45 tests.
* Explicit old supplied-context compatibility route/profile, with no automatic
  privilege upgrade or legacy token acceptance on the new canonical contract.

Pass criteria: expected HTTP status, exact E0-3 keys, null orderCandidate, correct
current prices/quantities/caveats, tool demand and scope, no historical facts or
instructions promoted to evidence, no data answer after authorization failure.
Saved synthetic results are in [AI_INDEPENDENT_RESULTS.jsonl](AI_INDEPENDENT_RESULTS.jsonl).
Final result: **1,546 passed, 0 failed, 0 skipped**, 2 existing warnings.
The canonical HTTP suite has 121 cases; all 45 original Products cases pass.
Independent evaluation passed 11 scenarios / 19 turns; rules/fake acceptance
passed 17 turns each. Synthetic local-server smoke returned200 for both turns,
with history not_requested on the named product and complete on the follow-up.
Warnings concern Starlette/httpx deprecation and Windows pytest cache permissions.

This proves **mocked AI-side behavior only**. It does not prove Backend has the
internal endpoint, authenticates the Conversations PR, can provide snapshot/
cutoff guarantees, agrees to the new context profile, or passes real Railway/
Groq staging acceptance. No real keys or .env secrets were inspected or changed.
The complete-system verdict remains **BLOCKED_BY_BACKEND**.
