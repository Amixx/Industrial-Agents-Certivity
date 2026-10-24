"""Requirements whose quoted paragraph holds no obligation of its own: a heading that points
elsewhere ("Failure provisions: See paragraph 4.6."), a clause that only brings other paragraphs
into force, or an item that spells out the approval mark the authority assigns."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .rewrite import Draft

POINTER = re.compile(
    r"^[^.;]{0,90}?:?\s*see\s+(?:paragraph|table|annex|figure)s?\b[^;]{0,40}\.?$", re.I
)
UMBRELLA = re.compile(
    r"shall\s+(?:conform|comply)\s+(?:to|with)\s+the\s+requirements\s+"
    r"(?:set\s+forth|specified|contained)\s+in\s+(?:paragraphs?|sections?)"
    r"|the\s+requirements\s+contained\s+in\s+sections?\s+[\d.]+.{0,80}?\s+shall\s+apply"
    r"|shall\s+be\s+so\s+manufactured\s+as\s+to\s+conform\s+to\s+the\s+type\s+approved",
    re.I,
)
MARK = re.compile(
    r"circle\s+(?:surrounding|containing)\s+the\s+letter"
    r"|number\s+of\s+this\s+regulation,?\s+followed\s+by\s+the\s+letter"
    r"|approval\s+marking\s+shall\s+consist\s+of"
    r"|^the\s+symbols\s+identifying\s+the",
    re.I,
)


def matches(quote: str) -> bool:
    q = quote.strip()
    return bool(POINTER.match(q) or UMBRELLA.search(q) or MARK.search(q))


def drop(drafts: Sequence[Draft]) -> list[Draft]:
    return [d for d in drafts if not matches(d.quote)]
