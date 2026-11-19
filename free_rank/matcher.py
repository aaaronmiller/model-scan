"""Match model identities across catalogues and benchmark sources from their own data.

There is no table of model names here. Two identity strings refer to the same model when,
after the same normalisation, they agree:

* ``compact``: the alphanumeric characters, in order, are identical
  (``Zorbo3-2B`` and ``zorbo-3-2b``);
* ``tokens``: the token multisets are identical (word order differs);
* ``size``: one side is the other plus parameter-size tokens only (``120b``, ``a12b``), and
  the shorter side states no size at all. A release named without its size matches the
  sized catalogue id; two different sizes never match.

Normalisation lower-cases, drops parenthetical qualifiers such as effort levels, drops a
``Vendor:`` display prefix, drops the organisation part of ``org/model`` ids, the ``:variant``
suffix and a trailing ``-YYYYMMDD`` date stamp, splits on every non-alphanumeric character,
and removes the vendor's own name and the ignorable tokens listed in ``config.json``. Version
numbers are never removed, so different versions of a family never match.

Identity strings carry a priority. A route's catalogue-declared canonical id outranks its
display name, so a name that also fits an older checkpoint cannot win over the exact id.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import load_config

_CFG = load_config()["matching"]
IGNORABLE = frozenset(_CFG["ignorable_tokens"])
SIZE = re.compile(_CFG["size_token_pattern"])
DATE_STAMP = re.compile(_CFG["date_stamp_pattern"])

# Priority of identity kinds: lower is stronger.
PRIORITY = {"canonical": 0, "weights": 1, "id": 2, "name": 3}


@dataclass(frozen=True)
class Identity:
    text: str
    kind: str  # one of PRIORITY
    vendor: str = ""

    @property
    def priority(self) -> int:
        return PRIORITY[self.kind]


@dataclass
class Key:
    tokens: tuple[str, ...]
    compact: str = field(init=False)

    def __post_init__(self):
        self.compact = "".join(self.tokens)


def _strip_id(text: str) -> str:
    text = text.split(":", 1)[0].rsplit("/", 1)[-1]
    return DATE_STAMP.sub("", text)


def tokens(identity: Identity, extra_vendor: str = "") -> tuple[str, ...]:
    text = identity.text or ""
    if identity.kind in ("canonical", "weights", "id"):
        text = _strip_id(text)
    else:
        text = re.sub(r"\([^)]*\)", " ", text)
        if ":" in text:
            text = text.split(":", 1)[1]
    text = text.lower().replace("+", " plus ")
    toks = [t for t in re.split(r"[^a-z0-9]+", text) if t]
    vendor_toks = set()
    for v in (identity.vendor, extra_vendor):
        vendor_toks |= {t for t in re.split(r"[^a-z0-9]+", (v or "").lower()) if t}
    kept = tuple(t for t in toks if t not in IGNORABLE)
    stripped = tuple(t for t in kept if t not in vendor_toks)
    # A vendor name is dropped only when a named token survives; a bare version number
    # ("1") left over from "Vendor-1" would otherwise match any other "Vendor-1".
    return stripped if any(c.isalpha() for t in stripped for c in t) else kept


def _is_size(tok: str) -> bool:
    return bool(SIZE.match(tok))


def relation(a: tuple[str, ...], b: tuple[str, ...]) -> str | None:
    """How two token tuples match: 'compact', 'tokens', 'size', or None."""
    if not a or not b or not any(c.isalpha() for t in a + b for c in t):
        return None
    if "".join(a) == "".join(b):
        return "compact"
    if sorted(a) == sorted(b):
        return "tokens"
    sa, sb = set(a), set(b)
    small, big = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    if small < big and all(_is_size(t) for t in big - small) and not any(_is_size(t) for t in small):
        return "size"
    return None


def match(left: list[Identity], right: list[Identity]) -> tuple[int, str, str, str] | None:
    """Best match between two identity lists.

    Returns ``(priority, relation, left_text, right_text)`` for the strongest pair, where
    priority is the sum of the two identity kinds' priorities (lower is stronger), or None when nothing matches. Vendor
    names on either side are removed from both sides of each comparison.
    """
    best = None
    for li in left:
        for ri in right:
            lt = tokens(li, ri.vendor)
            rt = tokens(ri, li.vendor)
            rel = relation(lt, rt)
            if rel is None:
                continue
            cand = (li.priority + ri.priority, rel, li.text, ri.text)
            if best is None or cand[:1] < best[:1]:
                best = cand
    return best


def best_matches(target: list[Identity], candidates: dict[str, list[Identity]]) -> tuple[list[str], dict]:
    """Candidates that match ``target`` at the strongest priority any of them reaches.

    Returns the candidate keys and, per key, the match evidence.
    """
    scored = {}
    for key, ids in candidates.items():
        m = match(target, ids)
        if m:
            scored[key] = m
    if not scored:
        return [], {}
    top = min(m[0] for m in scored.values())
    keys = sorted(k for k, m in scored.items() if m[0] == top)
    return keys, {k: scored[k] for k in keys}
