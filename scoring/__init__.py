"""
model-scan v5 — Multi-Axis Scoring Engine

Four primary axes with cross-influence modifiers:
  IS = Intelligence Score  (AA Index + modifiers)
  SS = Speed Score          (TPS, TTFT, provider multiplier)
  AS = Agentic Score        (tool use, structured output, context)
  CS = Coding Score         (benchmarks + intelligence + speed)

Each axis records a trace of modifications for UI display.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModifierTrace:
    """Record of a single modifier application for UI trace display."""
    name: str
    description: str
    input_value: float
    delta: float
    output_value: float


@dataclass
class AxisScore:
    """Complete score for one axis with full traceability."""
    base: float          # Calibrated base score (0-100)
    final: float         # After all modifiers applied (0-100)
    modifiers: list[ModifierTrace] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def modifier_total(self) -> float:
        return sum(m.delta for m in self.modifiers)

    def summary(self) -> str:
        parts = [f"base={self.base:.1f}"]
        for m in self.modifiers:
            parts.append(f"{m.name}={m.delta:+.1f}")
        return f"{' → '.join(parts)} → {self.final:.1f}"


@dataclass
class MultiAxisScores:
    """All four axis scores for one model."""
    intelligence: AxisScore
    speed: AxisScore
    agentic: AxisScore
    coding: AxisScore

    def composite(self, weights: dict[str, float] | None = None) -> float:
        w = weights or {"intelligence": 0.5, "speed": 0.15, "agentic": 0.15, "coding": 0.20}
        return (
            w.get("intelligence", 0.5) * self.intelligence.final
            + w.get("speed", 0.15) * self.speed.final
            + w.get("agentic", 0.15) * self.agentic.final
            + w.get("coding", 0.20) * self.coding.final
        )

    def to_dict(self) -> dict:
        return {
            "intelligence": self.intelligence.final,
            "speed": self.speed.final,
            "agentic": self.agentic.final,
            "coding": self.coding.final,
            "composite": self.composite(),
            "traces": {
                "intelligence": self.intelligence.summary(),
                "speed": self.speed.summary(),
                "agentic": self.agentic.summary(),
                "coding": self.coding.summary(),
            }
        }
