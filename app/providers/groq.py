"""GroqCloud chat completions; no xAI/Grok, tools or arbitrary URLs."""
import asyncio
import time

import httpx

from .base import ProviderUnavailable
from .structured import ProviderDiagnostic, wire_json_schema


def groq_schema(schema):
    """Use strict decoding only when every object is closed and fully required.

    Meaning has dynamic business-defined option maps; Groq's strict mode cannot
    encode those. Use documented best-effort JSON Schema with identical strict
    application validation. Closed response-composition schemas use strict mode.
    """
    wire = wire_json_schema(schema)
    def closed(node):
        if isinstance(node, list):
            return all(closed(v) for v in node)
        if not isinstance(node, dict):
            return True
        if node.get("type") == "object" and (
                node.get("additionalProperties") is not False
                or set(node.get("properties", {})) != set(node.get("required", []))):
            return False
        return all(closed(v) for v in node.values())
    return {"type": "json_schema", "json_schema": {
        "name": schema.__name__, "strict": closed(wire), "schema": wire}}


class GroqClient:
    """One HTTP attempt per model; higher-level failover owns the total budget."""
    provider_name = "groq"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def api_key(self):
        return self.settings.groq_api_key

    @property
    def model_ids(self):
        return self.settings.groq_models

    def request_body(self, model, system, user, schema, temperature):
        return {"model": model,
                "messages": [{"role":"system","content":system},{"role":"user","content":user}],
                "temperature": temperature, "max_completion_tokens": 2048,
                "response_format": groq_schema(schema)}

    def __init__(self, settings, *, transport=None, clock=time.monotonic):
        self.settings, self._transport, self._clock = settings, transport, clock
        self._cooldowns = {}  # model health only; no prompts or response payloads

    async def call(self, *, stage, models, system, user, parse, schema, temperature=0.0, mime="application/json"):
        if not self.api_key:
            raise ProviderUnavailable("Provider not configured", diagnostics=(ProviderDiagnostic("missing_key_configuration", "configuration"),))
        diagnostics = []
        deadline = self._clock() + self.settings.chat_total_timeout_seconds
        for model in self.model_ids[:4]:
            remaining = deadline - self._clock()
            if remaining <= 0:
                diagnostics.append(ProviderDiagnostic("timeout","deadline"))
                break
            if self._cooldowns.get(model, 0) > self._clock():
                continue
            try:
                async with httpx.AsyncClient(transport=self._transport, trust_env=False, follow_redirects=False,
                        timeout=self.settings.chat_provider_timeout_seconds) as client:
                    response = await asyncio.wait_for(client.post(self.endpoint,
                        headers={"Authorization": "Bearer " + self.api_key},
                        json=self.request_body(model,system,user,schema,temperature)),timeout=remaining)
                code = response.status_code
                if code != 200:
                    category = ("authentication" if code == 401 else "permission_denied" if code == 403 else
                                "rate_limit_or_quota" if code == 429 else "model_unavailable" if code == 404 else
                                "api_schema_or_request_error" if code == 400 else "api_unavailable")
                    diagnostics.append(ProviderDiagnostic(category, "sdk", code))
                    if code in {401, 403}:
                        break
                    self._cooldowns[model] = self._clock() + self.settings.chat_circuit_seconds
                    continue
                payload = response.json()
                choice = payload["choices"][0]
                if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
                    raise ValueError()
                result = parse(choice["message"]["content"])
                if result is None:
                    raise ValueError()
                return result, model
            except (httpx.TimeoutException, asyncio.TimeoutError):
                diagnostics.append(ProviderDiagnostic("timeout", "sdk"))
            except httpx.HTTPError:
                diagnostics.append(ProviderDiagnostic("transport_error", "sdk"))
            except (ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
                from .structured import StructuredOutputError
                category = error.category if isinstance(error, StructuredOutputError) else "invalid_provider_output"
                diagnostics.append(ProviderDiagnostic(category, "parse"))
            self._cooldowns[model] = self._clock() + self.settings.chat_circuit_seconds
        raise ProviderUnavailable("Provider unavailable", diagnostics=diagnostics) from None
