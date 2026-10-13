"""F1 / step 1: clean the customer's text BEFORE anything else sees it.
WhatsApp text is messy: double spaces, "تمااااام", emoji, Arabic-Indic digits, invisible characters.
Cleaning makes every later step (rules, search, LLM) simpler and more predictable."""
import re
import unicodedata

MAX_MESSAGE_CHARS = 2000

_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
_TATWEEL = re.compile(r"\u0640")                                  # the elongation stick: "تيـــشيرت"
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")
_REPEATED_LETTER = re.compile(r"([^\W\d_])\1{2,}")                # same LETTER 3+ times (digits are never touched)
_SPACES = re.compile(r"\s+")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def clean_message(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = _ZERO_WIDTH.sub("", t)
    t = _TATWEEL.sub("", t)
    t = _EMOJI.sub(" ", t)
    t = t.translate(_AR_DIGITS)
    t = _REPEATED_LETTER.sub(r"\1", t)          # "تمااااام" -> "تمام"   |  "1000" stays "1000"
    t = _SPACES.sub(" ", t).strip()
    return t[:MAX_MESSAGE_CHARS].strip()
