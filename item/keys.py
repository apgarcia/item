"""Hierarchy-aware key parsing and formatting.

Top-level tasks:  1, 2, 3, ...
Subtasks:         1a, 1b, ..., 1z, 1aa, 1ab, ...  (bijective base-26)
"""

import re


def index_to_suffix(n: int) -> str:
    """0-based index → bijective base-26 letter suffix.

    0 → 'a', 25 → 'z', 26 → 'aa', 27 → 'ab', ...
    """
    result = ""
    n += 1
    while n > 0:
        n -= 1
        result = chr(ord("a") + n % 26) + result
        n //= 26
    return result


def suffix_to_index(s: str) -> int:
    """Bijective base-26 letter suffix → 0-based index.

    'a' → 0, 'z' → 25, 'aa' → 26, ...
    """
    result = 0
    for c in s:
        result = result * 26 + (ord(c) - ord("a") + 1)
    return result - 1


def parse_key(key: str) -> tuple[int, int | None]:
    """Parse a key string into (top_idx, sub_idx), both 0-based.

    sub_idx is None for top-level tasks.

    '1'  → (0, None)
    '2a' → (1, 0)
    '1z' → (0, 25)
    '1aa'→ (0, 26)

    Raises ValueError on invalid input.
    """
    m = re.fullmatch(r"([1-9]\d*)([a-z]*)", key)
    if not m:
        raise ValueError(f"Invalid key: {key!r}  (expected e.g. 1, 2a, 3ab)")
    top = int(m.group(1)) - 1
    letters = m.group(2)
    sub = suffix_to_index(letters) if letters else None
    return top, sub


def format_key(top: int, sub: int | None = None) -> str:
    """Format 0-based indices back into a key string."""
    s = str(top + 1)
    if sub is not None:
        s += index_to_suffix(sub)
    return s
