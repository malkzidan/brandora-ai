# brandora-ai

AI service for Brandora. NestJS backend calls it over HTTP; it returns a contract-valid JSON (E0-3, Schema v1.0).

    Customer (WhatsApp) -> NestJS (webhook, DB, validation) -> POST /v1/ai/respond -> reply + intent (+orderCandidate)
                                                            <- NestJS validates -> sends reply to WhatsApp

## Structure
    app/
      main.py                  FastAPI: POST /v1/ai/respond, GET /health
      config.py                env settings
      schemas/                 request.py / response.py  (contract v1.0, pydantic, extra=forbid)
      pipeline/
        preprocess.py          F1  clean text, empty check, throttle
        rules.py               hard-coded replies (greeting / thanks) - NO LLM
        intent.py              F2  intent + entities (+ F5 clarification)
        faq.py                 F3
        catalog_search.py      F4  rank/trim catalog before sending to LLM
        order_builder.py       F6  orderCandidate
        product_media.py       F7  productReference only
        orchestrator.py        wires the steps
      providers/               base.py, mock.py, gemini.py (F9 fallback chain), ollama.py (dev only)
      prompts/                 system prompt files
      validation/              output_guard.py  (contract checks 1-9, approval-claim scan)
      observability/           logging.py       (F8, redacts phones/addresses)
    mock_data/                 business / catalog / knowledge / customer + 20 golden scenarios
    tests/unit, tests/integration
    evals/                     100+ cases + run_eval.py (F10)
    docs/                      contract docx, features spec pdf, master decisions

## Branching
    main (stable) <- develop <- feature/f01-preprocess-rules, feature/f02-intent, ...
One PR per feature, each with its tests.

## Run (after F0)
    pip install -r requirements-dev.txt
    cp .env.example .env     # add GEMINI_API_KEY
    uvicorn app.main:app --reload     # Swagger at /docs

## Status
- F0 done: schemas (contract v1.0), output guard, provider interface + mock, orchestrator, FastAPI.
- F1 done: text cleaning, throttle, hard-coded replies (greetings / thanks), empty-message reply.

## Notes for the backend team (behaviour they must know)
- `429 AI_RATE_LIMITED` (+ `Retry-After` header): one customer sent more than THROTTLE_MAX_MESSAGES in THROTTLE_WINDOW_SECONDS.
  The backend should NOT reply to the customer in that case. Needs no schema change; it is an HTTP error envelope like the others.
- Greetings / thanks are answered by fixed rules (no LLM). The response is still the full contract shape.
- Header `X-AI-Service-Key` is required when AI_SERVICE_KEY is set in the AI service's `.env`.
- `catalogItemId` is validated as UUID (contract schema), although some contract examples use "product-123".
