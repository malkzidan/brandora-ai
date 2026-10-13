"""Small Arabic text helpers (F1 will extend this file)."""
import re

_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u0640]")  # tashkeel + tatweel
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})


def normalize_arabic(text: str) -> str:
    """Lower-case, drop diacritics, unify alef/yaa/taa-marbuta, Arabic digits -> 0-9, collapse spaces."""
    t = text.lower().translate(_AR_DIGITS)
    t = _DIACRITICS.sub("", t).translate(_LETTERS)
    return re.sub(r"\s+", " ", t).strip()
