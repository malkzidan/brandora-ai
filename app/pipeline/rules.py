"""F1 / step 3: hard-coded replies. If the WHOLE message is just a greeting / thanks, answer with a fixed,
identical reply and never call the LLM -> zero cost, zero latency, zero surprise.
Only exact matches count: "السلام عليكم عايز تيشيرت" is NOT a greeting rule - it goes on to the LLM."""
import re
from dataclasses import dataclass

from app.schemas import AiResponse, Intent
from app.text import normalize_arabic

HELP = "إزاي أقدر أساعدك؟"
EMPTY_REPLY = "معلش، ممكن توضح طلبك؟"


@dataclass(frozen=True)
class Rule:
    name: str
    intent: Intent
    reply: str
    phrases: tuple[str, ...]


RULES: tuple[Rule, ...] = (
    Rule("salam", Intent.GREETING, f"وعليكم السلام ورحمة الله وبركاته! أهلاً بحضرتك، {HELP}", (
        "السلام عليكم", "سلام عليكم", "السلام عليكم ورحمة الله", "السلام عليكم ورحمة الله وبركاته",
        "السلامو عليكم", "سلامو عليكم", "salam alaikum", "salam alaykum", "assalamu alaikum",
        "assalamu alaykum", "assalam alaikum", "asalamu alaikum", "peace be upon you")),
    Rule("morning", Intent.GREETING, f"صباح النور! أهلاً بحضرتك، {HELP}", (
        "صباح الخير", "صباح النور", "صباح الفل", "صباح الورد", "صباحو", "sabah el kheir", "sabah elkhir",
        "sabah al khair", "sabah el nour", "good morning", "morning")),
    Rule("evening", Intent.GREETING, f"مساء النور! أهلاً بحضرتك، {HELP}", (
        "مساء الخير", "مساء النور", "مساء الفل", "مساء الورد", "masa el kheir", "masaa el kheir",
        "masa elkhir", "good evening", "good afternoon")),
    Rule("hello", Intent.GREETING, f"أهلاً وسهلاً بحضرتك! {HELP}", (
        "اهلا", "اهلا وسهلا", "اهلين", "اهلا بيك", "اهلا بحضرتك", "اهلا بيكم", "مرحبا", "مرحبا بيك",
        "مرحبا بحضرتك", "هلا", "هاي", "هالو", "ahlan", "ahlan wa sahlan", "hello", "hi", "hey", "hii")),
    Rule("how_are_you", Intent.GREETING, f"الحمد لله، أهلاً بحضرتك! {HELP}", (
        "ازيك", "ازيكم", "ازاي حضرتك", "عامل ايه", "عاملة ايه", "اخبارك ايه", "عامل ايه النهارده",
        "izayak", "ezayak", "how are you", "how r u")),
    Rule("thanks", Intent.THANKYOU, "العفو! لو محتاج أي حاجة تانية أنا في الخدمة.", (
        "شكرا", "شكرا جدا", "شكرا ليك", "شكرا لحضرتك", "شكرا جزيلا", "الف شكر", "متشكر", "متشكرين", "مشكور",
        "تسلم", "تسلم ايدك", "ميرسي", "جزاك الله خيرا", "shukran", "thanks", "thank you", "thanks a lot",
        "thank u", "thx", "tnx", "thanx")),
)

_TRAILING_POLITE = ("يا فندم", "يا افندم", "فندم", "لو سمحت", "يا باشا", "please", "pls")


def _key(text: str) -> str:
    t = normalize_arabic(text)
    t = re.sub(r"[^\w\s]", " ", t)                       # drop punctuation: ! ? ، . ~
    t = re.sub(r"\s+", " ", t).strip()
    changed = True
    while changed:                                       # "اهلا يا فندم" -> "اهلا"
        changed = False
        for w in _TRAILING_POLITE:
            if t.endswith(" " + w):
                t, changed = t[: -len(w) - 1].strip(), True
    return t


_TABLE: dict[str, Rule] = {_key(p): rule for rule in RULES for p in rule.phrases}


def _response(intent: Intent, reply: str) -> AiResponse:
    return AiResponse(intent=intent, reply=reply, productReference=None, requiresReview=False, orderCandidate=None)


def match_rule(cleaned_message: str) -> AiResponse | None:
    rule = _TABLE.get(_key(cleaned_message))
    return _response(rule.intent, rule.reply) if rule else None


def empty_response() -> AiResponse:
    return _response(Intent.UNKNOWN, EMPTY_REPLY)
