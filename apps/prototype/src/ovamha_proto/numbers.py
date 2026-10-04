"""Spoken number -> value, for the voice alternative on keypad fields.

The parsed value only FILLS the field. The worker sees it, hears it read back and
must confirm it like any keypad entry; keypad stays the default (decision 3).
Handles digits ("140") and English number words ("one hundred and forty"),
which is also how Krio numbers are usually transcribed. Blood pressure may be said
as "140 over 90". Anything ambiguous returns None and the worker types it instead.
"""
from __future__ import annotations

import re

UNITS = {"zero": 0, "oh": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
         "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
FILLER = {"and", "a", "point"}


def _words_to_numbers(text: str) -> list[float]:
    """Find every number in text, whether written as digits or English words."""
    t = text.lower().replace("-", " ")
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)
    tokens = re.findall(r"\d+(?:\.\d+)?|[a-z]+", t)
    out: list[float] = []
    cur: float | None = None
    decimal = False
    for tok in tokens:
        if re.fullmatch(r"\d+(?:\.\d+)?", tok):
            if cur is not None and not decimal:
                out.append(cur)
            if decimal and cur is not None:
                cur = float(f"{int(cur)}.{tok}")
                decimal = False
            else:
                cur = float(tok)
            continue
        if tok in UNITS or tok in TENS:
            v = UNITS.get(tok, TENS.get(tok))
            if decimal and cur is not None:
                cur = float(f"{int(cur)}.{v}")
                decimal = False
            elif cur is None:
                cur = v
            elif tok in UNITS and cur % 10 == 0 and cur % 100 != 0 and v < 10:
                cur += v  # forty + two
            elif cur >= 100 and cur % 100 == 0:
                cur += v  # hundred (and) forty
            else:
                out.append(cur)
                cur = v
            continue
        if tok == "hundred" and cur is not None:
            cur *= 100
            continue
        if tok == "point" and cur is not None:
            decimal = True
            continue
        if tok in FILLER:
            continue
        if cur is not None:
            out.append(cur)
            cur = None
        decimal = False
    if cur is not None:
        out.append(cur)
    return [int(n) if float(n).is_integer() else n for n in out]


def parse_number(text: str) -> float | None:
    nums = _words_to_numbers(text)
    return nums[0] if len(nums) == 1 else None


def parse_bp(text: str) -> tuple[float, float] | None:
    """'140 over 90' / '140/90' / 'one forty over ninety' -> (140, 90)."""
    t = text.lower().replace("/", " over ")
    if " over " not in f" {t} ":
        return None
    left, right = t.split("over", 1)
    a, b = _words_to_numbers(left), _words_to_numbers(right)
    if len(b) != 1 or not a:
        return None
    # "one forty" is commonly said for 140.
    sys_ = a[0] * 100 + a[1] if len(a) == 2 and a[0] < 3 and a[1] < 100 else (a[0] if len(a) == 1 else None)
    return (sys_, b[0]) if sys_ is not None else None
