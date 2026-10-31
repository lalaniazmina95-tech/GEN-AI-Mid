"""Quote verification: the anti-fabrication check.

The model must support every extracted fact with a verbatim quote from what the
team wrote. A fact whose quote cannot be found in the team's text is dropped
and logged. This is what keeps the model card and system card traceable.
"""
import re
from difflib import SequenceMatcher


def norm(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    s = re.sub(r"[^\w%:/.'\- ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip(" .")


def quote_supported(quote: str, source: str, threshold: float = 0.85) -> bool:
    q, src = norm(quote), norm(source)
    if len(q) < 3:
        return False
    if q in src:
        return True
    # tolerate small differences (punctuation, a dropped word) on longer quotes
    if len(q) < 20:
        return False
    sm = SequenceMatcher(None, src, q, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    if matched / len(q) < threshold:
        return False
    # and the longest contiguous block must be substantial
    longest = max((b.size for b in sm.get_matching_blocks()), default=0)
    return longest >= min(len(q) * 0.5, 40)
