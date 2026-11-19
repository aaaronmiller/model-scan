"""Read the gateway catalogues and keep the routes each one itself prices at zero.

Each catalogue format has its own pricing and metadata fields; the free rule for each is
stated in ``config.json`` and implemented here from the catalogue's own fields only:

* ``opencode`` (Zen and Go): every price under ``cost`` is zero.
* ``kilo``: ``isFree`` is true and the prompt and completion prices are zero.
* ``openrouter``: every field under ``pricing`` is zero.

A route record keeps the identity strings the catalogue gives (canonical id, weights repo,
id, display name) for the matcher, plus kind, tool support, context and the limit tags the
catalogue itself states.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from . import load_config
from .matcher import Identity

CFG = load_config()


def _zero(value) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _all_prices_zero(node) -> bool:
    """True when every number found under keys named 'price' is zero (and there is one)."""
    prices = []

    def walk(n, key=None):
        if isinstance(n, dict):
            for k, v in n.items():
                walk(v, k)
        elif isinstance(n, list):
            for v in n:
                walk(v, key)
        elif key == "price":
            prices.append(n)

    walk(node)
    return bool(prices) and all(_zero(p) for p in prices)


@dataclass
class Route:
    gateway: str
    route_id: str
    name: str
    kind: str
    tools: bool
    context: int | None
    identities: list = field(default_factory=list)
    tags: dict = field(default_factory=dict)
    description: str = ""

    def key(self) -> str:
        return f"{self.gateway}:{self.route_id}"


def _description_tags(text: str) -> dict:
    tags = {}
    low = (text or "").lower()
    for tag, patterns in CFG["tags"]["description_patterns"].items():
        for pat in patterns:
            if re.search(pat, low):
                tags[tag] = "catalogue description"
                break
    return tags


def _vendor_of(text: str | None) -> str:
    if text and "/" in text:
        return text.split("/", 1)[0]
    return ""


def _opencode(gateway: str, data: dict) -> list[Route]:
    routes = []
    for m in data.get("data", []):
        if not _all_prices_zero(m.get("cost") or {}):
            continue
        canonical = m.get("canonical_id")
        vendor = _vendor_of(canonical)
        ids = [Identity(m["id"], "id", vendor), Identity(m.get("name", ""), "name", vendor)]
        if canonical:
            ids.insert(0, Identity(canonical, "canonical", vendor))
        tags = _description_tags(m.get("description", ""))
        go = m.get("go") or {}
        if go.get("training"):
            tags["sharing"] = "catalogue: go.training"
        if go.get("limited_regions"):
            tags["region-restricted"] = "catalogue: go.limited_regions"
        if go.get("zdr") is True:
            tags["zero-retention"] = "catalogue: go.zdr"
        out = (m.get("modalities") or {}).get("output") or []
        kind = m.get("type") or ("chat" if "text" in out else "other")
        routes.append(Route(gateway, m["id"], m.get("name", m["id"]), kind,
                            bool(((m.get("capabilities") or {}).get("tools") or {}).get("supported")),
                            (m.get("limit") or {}).get("context"), ids, tags, m.get("description", "")))
    return routes


def _openai_style(gateway: str, data: dict, require_flag: str | None) -> list[Route]:
    routes = []
    for m in data.get("data", []):
        pricing = m.get("pricing") or {}
        if require_flag:
            if not m.get(require_flag) or not (_zero(pricing.get("prompt")) and _zero(pricing.get("completion"))):
                continue
        elif not pricing or not all(_zero(v) for v in pricing.values()):
            continue
        vendor = _vendor_of(m["id"])
        ids = []
        if m.get("canonical_slug"):
            ids.append(Identity(m["canonical_slug"], "canonical", vendor))
        if m.get("hugging_face_id"):
            ids.append(Identity(m["hugging_face_id"], "weights", vendor))
        ids += [Identity(m["id"], "id", vendor), Identity(m.get("name", ""), "name", vendor)]
        arch = m.get("architecture") or {}
        out = arch.get("output_modalities") or []
        inp = arch.get("input_modalities") or []
        kind = "chat" if out == ["text"] and "text" in inp else ("+".join(out) or "other")
        tags = _description_tags(m.get("description", ""))
        if m.get("mayTrainOnYourPrompts"):
            tags["sharing"] = "catalogue: mayTrainOnYourPrompts"
        if m.get("autoRouting"):
            tags["router"] = "catalogue: autoRouting"
        if m.get("expiration_date"):
            tags["expires"] = m["expiration_date"]
        ctx = m.get("context_length") or (m.get("top_provider") or {}).get("context_length") or None
        routes.append(Route(gateway, m["id"], m.get("name", m["id"]), kind,
                            "tools" in (m.get("supported_parameters") or []), ctx, ids, tags,
                            m.get("description", "")))
    return routes


def parse(gateway: str, raw: bytes) -> list[Route]:
    data = json.loads(raw)
    fmt = CFG["catalogues"][gateway]["format"]
    if fmt == "opencode":
        return _opencode(gateway, data)
    if fmt == "kilo":
        return _openai_style(gateway, data, require_flag="isFree")
    if fmt == "openrouter":
        return _openai_style(gateway, data, require_flag=None)
    raise ValueError(f"unknown catalogue format {fmt!r} for {gateway}")
