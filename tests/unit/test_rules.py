import pytest

from app.pipeline.preprocess import clean_message
from app.pipeline.rules import EMPTY_REPLY, RULES, empty_response, match_rule

SALAM = "وعليكم السلام ورحمة الله وبركاته! أهلاً بحضرتك، إزاي أقدر أساعدك؟"


@pytest.mark.parametrize("msg", ["السلام عليكم", "سلام عليكم", "السلام عليكم ورحمة الله وبركاته", "السلام عليكم ورحمة الله",
                                 "السلامُ عليكم", "السلام عليكم!", "السلام عليكم يا فندم", "assalamu alaikum", "Salam Alaikum",
                                 "السلااااام عليكم", "السلام عليكم 🌹"])
def test_salam_always_gets_the_same_reply(msg):
    out = match_rule(clean_message(msg))
    assert out is not None and out.reply == SALAM and out.intent.value == "GREETING"


@pytest.mark.parametrize("msg,intent,starts", [
    ("صباح الخير", "GREETING", "صباح النور"), ("صباح الخيييير", "GREETING", "صباح النور"), ("Good morning", "GREETING", "صباح النور"),
    ("sabah el kheir", "GREETING", "صباح النور"),
    ("مساء الخير", "GREETING", "مساء النور"), ("good evening", "GREETING", "مساء النور"),
    ("اهلا", "GREETING", "أهلاً وسهلاً"), ("أهلاً", "GREETING", "أهلاً وسهلاً"), ("أهلاً وسهلاً", "GREETING", "أهلاً وسهلاً"),
    ("اهلاااا", "GREETING", "أهلاً وسهلاً"), ("مرحبا", "GREETING", "أهلاً وسهلاً"), ("هاي", "GREETING", "أهلاً وسهلاً"),
    ("Hello", "GREETING", "أهلاً وسهلاً"), ("hi", "GREETING", "أهلاً وسهلاً"), ("اهلا يا فندم", "GREETING", "أهلاً وسهلاً"),
    ("ازيك؟", "GREETING", "الحمد لله"), ("عامل ايه", "GREETING", "الحمد لله"), ("how are you?", "GREETING", "الحمد لله"),
    ("شكرا", "THANKYOU", "العفو"), ("شكراً جداً", "THANKYOU", "العفو"), ("شكرا ليك", "THANKYOU", "العفو"),
    ("متشكر", "THANKYOU", "العفو"), ("تسلم ايدك", "THANKYOU", "العفو"), ("ميرسى", "THANKYOU", "العفو"),
    ("thanks", "THANKYOU", "العفو"), ("Thank you!", "THANKYOU", "العفو"), ("شكرااااا", "THANKYOU", "العفو"),
    ("شكرا 🙏🙏", "THANKYOU", "العفو"),
])
def test_rule_matches(msg, intent, starts):
    out = match_rule(clean_message(msg))
    assert out is not None and out.intent.value == intent and out.reply.startswith(starts)


@pytest.mark.parametrize("msg", [
    "السلام عليكم عايز تيشيرت", "صباح الخير عايز اسأل عن الاسعار", "اهلا الهودي بكام؟", "شكرا بس الاوردر اتأخر",
    "عايز تيشيرت", "الهودي بكام؟", "سلام", "تمام", "ايوه", "لا", "هاي كام سعر الجينز", "شكرا الغي الطلب",
    "مساء الخير فين طلبي", "hello i want to order", "", "asdfgh", "ازيك الطلب وصل؟",
])
def test_non_greetings_are_not_ruled(msg):
    assert match_rule(clean_message(msg)) is None


def test_bare_salam_is_not_treated_as_greeting():       # "سلام" at the end of a chat means goodbye
    assert match_rule("سلام") is None and match_rule("salam") is None


def test_all_rule_replies_are_valid_contract_responses():
    for rule in RULES:
        out = match_rule(rule.phrases[0])
        assert out.productReference is None and out.orderCandidate is None and out.requiresReview is False


def test_no_phrase_belongs_to_two_rules():
    from app.pipeline.rules import _key
    seen = {}
    for rule in RULES:
        for p in rule.phrases:
            assert seen.setdefault(_key(p), rule.name) == rule.name, p


def test_empty_response():
    out = empty_response()
    assert out.intent.value == "UNKNOWN" and out.reply == EMPTY_REPLY
