# Conversational application delivery — 3 November 2026

Workspace: `brandora-ai`, branch `feature/backend-ai-integration`.
Existing Phase 1–8 work was retained. No commit, push, merge, deployment, live
Backend/Gemini call, production data access or `.env` edit was performed.
Backend repository inspection was read-only through GitHub.

## Files in this delivery

Created:

- `app/chat/__init__.py`, `__main__.py`: local-only package/CLI and mode selection.
- `app/chat/application.py`: scoped serialized conversations and per-turn planning.
- `app/chat/understanding.py`: structured Gemini interpretation/rules fallback.
- `app/chat/responding.py`: evidence-validated conversational speech-act grammar.
- `app/chat/synthetic.py`: two synthetic businesses and mocked six-tool protocol.
- `app/chat/fake.py`: offline SDK-boundary stand-in using existing GeminiClient.
- `app/chat/evaluate.py`: rules/fake and explicitly opt-in live acceptance harness.
- `tests/test_chat_application.py`: 52 new conversation/security/CLI cases.
- `docs/LOCAL_CHATBOT.md`: installation, architecture, manual/live testing guide.
- `docs/BACKEND_HANDOFF.md`: verified main, missing contracts and exact checklist.
- `docs/CHAT_ACCEPTANCE_RULES.jsonl`, `CHAT_ACCEPTANCE_FAKE.jsonl`: captured actual
  synthetic conversations, checks and diagnostics (timings are observations).
- This delivery report.

Modified:

- `app/data/routing.py`: standalone delayed-order complaint and exact help/review
  routing. Legacy live Router is unaffected.
- `app/pipeline/extensions.py`: provisional options, missing selections and
  confirmation-required metadata; Orders remain disabled.
- `app/pipeline/standalone.py`: pass immutable requested options to disabled seam.
- `app/providers/evidence.py`: clarify responder-interface documentation.
- `README.md`, `docs/INTEGRATION_GUIDE.md`, `docs/BACKEND_AI_CONTRACT.md`: point to
  current chatbot/handoff and distinguish retained historical v1 contracts.

Removed: none. Existing uncommitted earlier-phase files, including changes in
`main.py`, `app/dev.py`, legacy orchestrator/provider and earlier tests, were
already present and were not reverted or rewritten in this delivery.

## Implemented and tested

Execution is: local input validation → deterministic hard rules / structured
Gemini interpretation → scoped semantic selection → existing bounded read-only
retrieval → typed evidence planning → validated mandatory conversational acts →
Gemini approved-phrase choices / deterministic fallback → existing AiResponse.
No new SDK or parallel implementation of catalog/inventory business logic exists.

Gemini understands product search, handles, changed options, requested quantity,
language and novel complaints. Python controls identity, tools, actual matches,
price/stock facts, review and all permissions. Factual slots and required warnings
cannot be replaced with arbitrary model prose. Generation has multiple approved
wordings per act, focused questions and semantic understanding; it is not limited
to the Phase 7 opening/spacing baseline. It remains a closed bilingual grammar.

Each local session serializes turns and retains only scoped selection hints;
provider input excludes prior price/stock and tenant/token identity. Current
Backend reads revalidate follow-ups. New products, declines and failures clear
stale selections. Different businesses/customers do not share conversation state.
Shared SDK/model-health/schema-capability state contains operational categories,
not customer execution data. Synthetic fixture mutation is confined to its local
Backend instance. No context token is persisted on a session/provider.

Purchase information stays provisional: product/actual variant references,
requested options/quantity, missing selections and confirmation-required flag.
`orderCandidate=null` always. Future Backend execution must freshly validate
authorization, variant/options, price/stock, idempotency and owner-approved state
transitions in its transaction. No handler or enable switch is implemented here.

Complete test run with `AI_PROVIDER=rules`, `ENABLE_DEV_ENDPOINTS=false`:

```text
1196 passed, 2 warnings in 9.11s
```

The 1,144 earlier tests still pass plus 52 new cases. Warnings are the existing
Starlette/httpx deprecation and Windows pytest-cache access warning. No unrelated
test assertions were changed. `git diff --check` passed; new Python files were
also checked for trailing whitespace. Rules and fake evaluation each completed
all five scenario groups with `failedChecks: []`. Actual replies were inspected,
including variant changes, unknown prices, untracked/zero stock and complaints.

Selected tested results (full text/diagnostics in captured JSONL):

| Customer | Verified reply behavior |
| --- | --- |
| عندكم تيشيرت أسود؟ | Black/M 250.00 and Black/L 275.00; asks for size |
| طب مقاس L بكام؟ | Black/L 275.00 EGP, recorded stock 4; no redundant question |
| عايزة اتنين منه. | Provisional quantity 2; explicitly no order or reservation |
| طب غيرت رأيي عايزة الأبيض. | Fresh White/L 285.00 EGP, stock 8; retains quantity 2 |
| white tshirt size M price | 225.00 EGP; untracked stock, availability needs confirmation |
| cap price | No confirmed price; never substitutes zero |
| Can you guarantee delivery tomorrow? | No confirmed information/action; no promise |

One exact tested purchase sentence:
`الكمية المطلوبة مبدئيًا: 2. ده طلب مبدئي فقط؛ ما اتعملش طلب شراء أو حجز.`

## Implemented, not verified live

Explicit `--mode gemini` uses private existing configuration and the existing
GeminiClient. The synthetic live-evaluation command additionally requires
`--allow-live`. Neither was run. Model IDs, key permissions, actual structured
schema support, latency and live understanding/naturalness require acceptance.
Fake mode proves offline control flow and guard behavior, not live model quality.

## External dependencies / intentionally unavailable functionality

Verified Backend main is commit `83a65e9fc1f3f6994a7d115d6b83d86d3dd4d08b`.
It has owner-authenticated product/variant/business APIs, two-decimal presenters
and variant inventory primitives. The proposed AI dispatcher/customer context,
conversation/history services, business aggregate and Orders API were not found
in inspected main. Precise requests, envelope examples, errors, authorization,
history and eventual Orders tasks are in [BACKEND_HANDOFF.md](BACKEND_HANDOFF.md).

No customer-facing v2 activation, signed ingress, durable/distributed conversation
state, live Backend connection, business-policy knowledge, actual Orders or
WhatsApp is implemented/enabled. These are not simulated as successful actions.

No known failing automated cases remain. Residual product limits: rules fallback
has finite vocabulary; the approved wording grammar is deliberately constrained;
catalog names/options remain untranslated; ambiguous/partial data cannot establish
global absence or guaranteed stock. Semantic model accuracy and subjective
naturalness are not mathematically guaranteed by structural grounding.

Ready for **local demonstration and offline integration testing**. Live Backend
integration and production readiness remain pending the explicit contracts,
authentication/persistence, live-model acceptance and operational verification.
Use [LOCAL_CHATBOT.md](LOCAL_CHATBOT.md) for exact Windows commands and scenarios.
