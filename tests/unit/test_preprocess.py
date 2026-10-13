import pytest

from app.pipeline.preprocess import MAX_MESSAGE_CHARS, clean_message


@pytest.mark.parametrize("raw,expected", [
    ("  السلام    عليكم  ", "السلام عليكم"),
    ("عايز\n\n تيشيرت\t اسود", "عايز تيشيرت اسود"),
    ("تمااااام", "تمام"),
    ("حلوووووو", "حلو"),
    ("هههههههه", "ه"),
    ("اهلااااا", "اهلا"),
    ("yesssss please", "yes please"),
    ("عايز ٣ تيشيرتات", "عايز 3 تيشيرتات"),
    ("مقاس ٣٢", "مقاس 32"),
    ("عايز 1000 قطعة", "عايز 1000 قطعة"),          # digits are never collapsed
    ("عايز 100000 قطعة", "عايز 100000 قطعة"),
    ("تيـــشيرت", "تيشيرت"),
    ("شكراً 🌹🌹", "شكراً"),
    ("😍 عايز تيشيرت ❤️", "عايز تيشيرت"),
    ("عايز\u200b تيشيرت\u200f", "عايز تيشيرت"),
    ("ﻻ مش عايز", "لا مش عايز"),                    # presentation-form lam-alef -> normal letters
    ("تمام، شكراً.", "تمام، شكراً."),               # punctuation untouched
    ("3ayez 2 tshirt aswad XL", "3ayez 2 tshirt aswad XL"),
    ("عايز تيشيرت أسود", "عايز تيشيرت أسود"),         # hamza kept (LLM sees real text)
    ("", ""), ("   ", ""), ("\n\t", ""), ("🙂🙂🙂", ""), ("😂", ""),
])
def test_clean_message(raw, expected):
    assert clean_message(raw) == expected


def test_idempotent():
    for raw in ["تمااااام  🌹", "عايز ٣ قطع!!!", "  hello   world "]:
        once = clean_message(raw)
        assert clean_message(once) == once


def test_truncates_long_messages():
    out = clean_message("عايز " * 1000)
    assert len(out) <= MAX_MESSAGE_CHARS and out == out.strip()
