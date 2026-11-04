"""Explicit local operator entry point. Synthetic Backend in every mode."""
import argparse
import asyncio
from dataclasses import replace
import json
import os
from uuid import uuid4

from ..config import Settings, load_settings
from ..providers.gemini import GeminiClient
from ..providers.groq import GroqClient
from ..providers.openrouter import OpenRouterClient, validate_free_models, ModelCapabilityError
from ..providers.failover import ProviderChain
from ..clients.development_backend import DevelopmentBackendClient, MAIN_REVISION
from ..data.backend import BackendDataAccess
from ..schemas.backend import ExpectedScope
from .application import ChatSession
from .fake import DemoGemini
from .natural import NaturalResponder
from .synthetic import SyntheticBackend
from .understanding import ConversationInterpreter


class ChatConfigurationError(ValueError):
    """Safe, fixed local preflight failure; never contains a secret."""


def build(mode):
    if mode not in {"rules", "fake", "gemini", "auto", "groq", "openrouter"}:
        raise ValueError("Unknown local mode")
    if mode in {"gemini","auto","groq","openrouter"}:
        # This branch is entered only by an explicit operator-selected CLI mode.
        settings = replace(load_settings(), ai_provider="gemini")
        if mode == "gemini":
            settings.validate()
        if mode == "groq" and not settings.groq_api_key:
            raise ChatConfigurationError("GROQ_API_KEY is missing; configure it privately before GroqCloud testing.")
        if mode == "openrouter" and not settings.openrouter_api_key:
            raise ChatConfigurationError("OPENROUTER_API_KEY is missing; configure it privately before OpenRouter testing.")
        order = ((mode,) if mode in {"groq","openrouter"} else
                 tuple(dict.fromkeys(("gemini",*settings.chat_provider_order))) if mode == "gemini" else settings.chat_provider_order)
        retired = {"gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.0-flash-lite", "gemini-2.0-flash-lite-001"}
        if "gemini" in order and settings.gemini_api_key and any(model.removeprefix("models/") in retired for model in (*settings.router_models, *settings.generator_models)):
            raise ChatConfigurationError("Configured Gemini 2.0 model is retired. Run explicit model discovery and configure accessible active IDs.")
        if set(settings.chat_provider_order) - {"gemini","groq","openrouter"} or len(set(settings.chat_provider_order)) != len(settings.chat_provider_order):
            raise ChatConfigurationError("CHAT_PROVIDER_ORDER must contain distinct groq/openrouter/gemini names")
        if "openrouter" in order:
            try:
                validate_free_models(settings.openrouter_models)
            except ModelCapabilityError:
                raise ChatConfigurationError("unsupported_model_capabilities: OPENROUTER_MODELS contains a model without a supported explicit capability policy.") from None
            except ValueError:
                raise ChatConfigurationError("OPENROUTER_MODELS must contain only explicit vendor/model:free identifiers; paid models and routers are forbidden.") from None
        providers = {}
        if settings.gemini_api_key and "gemini" in order:
            providers["gemini"] = GeminiClient(replace(settings,gemini_max_retries=1,gemini_retry_delay_seconds=0,
                                                       gemini_cooldown_seconds=settings.chat_circuit_seconds))
        if settings.groq_api_key and "groq" in order:
            providers["groq"] = GroqClient(settings)
        if settings.openrouter_api_key and "openrouter" in order:
            providers["openrouter"] = OpenRouterClient(settings)
        client = ProviderChain([(name,providers[name]) for name in order if name in providers],settings)
    elif mode == "fake":
        settings = Settings(ai_provider="gemini", gemini_api_key="synthetic-not-a-secret",
                            gemini_retry_delay_seconds=0)
        client = DemoGemini(settings)
    else:
        settings, client = Settings(ai_provider="rules"), None
    return SyntheticBackend(), ConversationInterpreter(client, settings), NaturalResponder(client, settings)


async def run(mode, messages=None, *, development=False, allow_development=False, allow_model_data=False):
    backend, interpreter, responder = build(mode)
    development_client = None
    if development:
        if not allow_development:
            raise ChatConfigurationError("Development Backend reads require --allow-development-backend.")
        if mode not in {"rules","fake"} and not allow_model_data:
            raise ChatConfigurationError("Sending development catalog to providers requires --allow-development-data-to-models.")
        # Settings already loads dotenv. Values stay private and never enter
        # prompts/diagnostics. No account login or automatic token refresh.
        try:
            development_client = DevelopmentBackendClient(os.getenv("DEV_BACKEND_URL",""), os.getenv("DEV_BACKEND_OWNER_TOKEN",""),
                os.getenv("DEV_BACKEND_BUSINESS_ID",""),revision=os.getenv("DEV_BACKEND_REVISION",""))
        except ValueError:
            raise ChatConfigurationError("Development configuration requires loopback URL, private owner token, business UUID and reviewed main revision.") from None
        scope = ExpectedScope(business_id=development_client.business_id,customer_id=uuid4(),conversation_id=uuid4())
        dev_session = ChatSession(BackendDataAccess(development_client),scope,interpreter,responder)
    sessions, business, customer = {}, 1, 1
    print(f"Brandora local chatbot | {mode} | {'DEVELOPMENT HTTP / local conversation only' if development else 'SYNTHETIC Backend'} | Orders disabled")
    print("Commands: /reset, /business 1|2, /customer 1|2, /catalog, /quit")
    iterator = iter(messages) if messages is not None else None
    while True:
        try:
            text = next(iterator) if iterator is not None else input("You> ")
        except (EOFError, StopIteration):
            break
        if text.strip() == "/quit":
            break
        try:
            if text.startswith("/business ") or text.startswith("/customer "):
                if development:
                    print("Development scope is pinned to the operator-authorized business; restart with private configuration to change it.")
                    continue
                value = int(text.split()[1])
                backend.scope(value if text.startswith("/business") else business,
                              value if text.startswith("/customer") else customer)
                if text.startswith("/business"):
                    business = value
                else:
                    customer = value
                print(f"Synthetic business {business}, customer {customer}")
                continue
            if development:
                session = dev_session
            else:
                key = (business, customer)
                scope = backend.scope(*key)
                if key not in sessions:
                    sessions[key] = ChatSession(backend.data(), scope, interpreter, responder)
                session = sessions[key]
            if text == "/reset":
                await session.reset()
                print("Conversation reset.")
                continue
            if text == "/catalog":
                if development:
                    text = "show products"
                else:
                    for p in backend.products[business]:
                        print(p["name"], p["options"])
                    continue
            turn = await session.send(text, context_token=development_client.local_context_token() if development else backend.token(scope))
            print("AI> " + turn.response.reply)
            print(json.dumps({**turn.diagnostics(),"providerMode":mode,"backendSource":"development-http" if development else "synthetic", "historySource":"local-session"}, ensure_ascii=False))
        except (ValueError, TypeError):
            print("Invalid message or command; use a nonblank message up to 2000 characters.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("rules", "fake", "gemini", "auto", "groq", "openrouter"), default="rules",
                        help="auto/groq/openrouter/gemini use live providers; synthetic Backend by default")
    parser.add_argument("--message", action="append", help="Repeat for a deterministic multi-turn transcript")
    parser.add_argument("--backend",choices=("synthetic","development"),default="synthetic")
    parser.add_argument("--allow-development-backend",action="store_true")
    parser.add_argument("--allow-development-data-to-models",action="store_true")
    args = parser.parse_args()
    try:
        asyncio.run(run(args.mode, args.message,development=args.backend == "development",
                        allow_development=args.allow_development_backend,allow_model_data=args.allow_development_data_to_models))
    except KeyboardInterrupt:
        pass
    except ChatConfigurationError as error:
        print(str(error))
        raise SystemExit(1) from None
    except Exception:
        # Never print raw SDK/config errors or a traceback containing credentials.
        print("Local chat could not start or complete. Check configuration and installed dependencies.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
