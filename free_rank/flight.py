"""Decode the data a Next.js page streams to its browser client.

Next.js app-router pages carry their data as ``self.__next_f.push([1, "<chunk>"])`` script
calls. Joined in order, the chunks form a text stream with JSON objects embedded in it. This
module joins the stream and pulls out every JSON object that starts at a given regular
expression, so a source adapter can say "objects that begin with an id and a release" without
knowing where in the page they sit.
"""
from __future__ import annotations

import json
import re

_PUSH = re.compile(r"self\.__next_f\.push\((\[.*?\])\)</script>", re.S)


def stream(html: str) -> str:
    parts = []
    for match in _PUSH.finditer(html):
        try:
            arr = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if len(arr) > 1 and isinstance(arr[1], str):
            parts.append(arr[1])
    return "".join(parts)


def objects(text: str, start_pattern: str, require: tuple[str, ...] = ()) -> list[dict]:
    """Every JSON object in ``text`` whose opening matches ``start_pattern``.

    ``require`` lists keys an object must have to be kept. Objects are returned in stream
    order; one that fails to decode is skipped.
    """
    decoder = json.JSONDecoder()
    found = []
    for match in re.finditer(start_pattern, text):
        try:
            value, _ = decoder.raw_decode(text, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and all(k in value for k in require):
            found.append(value)
    return found
