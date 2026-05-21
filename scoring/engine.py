"""
Multi-Axis Scoring Engine — orchestrates 4 primary axes with cross-influence modifiers.

Usage:
    engine = ScoringEngine(model_data, benchmark_data)
    scores = engine.compute_all()
    print(scores.to_dict())
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import AxisScore, ModifierTrace, MultiAxisScores
from .calibration import (
    calibrate_aa_index, calibrate_tps, calibrate_latency,
    calibrate_bfcl, calibrate_arena_elo, calibrate_swe_verified,
)
from .modifiers import (
    mod_knowledge_cutoff, mod_release_recency, mod_reasoning,
    mod_context_window, mod_multimodal,
    mod_reasoning_penalty, mod_free_tier_penalty,
    mod_structured_output, mod_max_output_tokens,
    mod_context_coding, mod_benchmark_verified,
)


class ScoringEngine:
    """Orchestrates multi-axis scoring with full traceability."""

    def __init__(self, model_data: dict, benchmarks: dict | None = None):
        self.m = model_data
        self.benchmarks = benchmarks or {}
        self._cache: dict = {}

        # Intelligence modifiers (applied in order)
        self.is_modifiers = [
            mod_knowledge_cutoff,
            mod_release_recency,
            mod_reasoning,
            mod_context_window,
            mod_multimodal,
        ]
        # Speed modifiers
        self.ss_modifiers = [
            mod_reasoning_penalty,
            mod_free_tier_penalty,
        ]
        # Agentic modifiers
        self.as_modifiers = [
            mod_structured_output,
            mod_max_output_tokens,
            mod_reasoning,
            mod_context_window,
            mod_knowledge_cutoff,
        ]
        # Coding modifiers
        self.cs_modifiers = [
            mod_context_coding,
            mod_benchmark_verified,
            mod_reasoning,
            mod_max_output_tokens,
        ]

    def compute_all(self) -> MultiAxisScores:
        return MultiAxisScores(
            intelligence=self._compute_intelligence(),
            speed=self._compute_speed(),
            agentic=self._compute_agentic(),
            coding=self._compute_coding(),
        )

    def _apply(self, base: float, modifiers: list) -> AxisScore:
        """Apply a chain of modifiers, recording traces."""
        traces = []
        current = base
        for mod_fn in modifiers:
            new_val, trace = mod_fn(current, self.m, self._cache)
            traces.append(trace)
            current = new_val
        return AxisScore(
            base=round(base, 1),
            final=round(max(0, min(100, current)), 1),
            modifiers=traces,
        )

    def _compute_intelligence(self) -> AxisScore:
        aa_raw = self.m.get("ai_index") or self.m.get("aa_raw")
        base = calibrate_aa_index(aa_raw)
        # Heuristic override if AA not available
        if aa_raw is None:
            heuristic = self._estimate_intelligence_heuristic()
            if heuristic is not None:
                base = heuristic * (100 / 60)  # calibrate heuristic to same scale
        return self._apply(base, self.is_modifiers)

    def _compute_speed(self) -> AxisScore:
        tps = self.m.get("tps", 0)
        lat = self.m.get("latency_s", 0)
        tps_score = calibrate_tps(tps)
        lat_score = calibrate_latency(lat)
        base = tps_score * 0.55 + lat_score * 0.45
        # Provider multiplier (from median speed data)
        prov = self.m.get("provider", "").lower()
        prov_mult = {"groq": 1.3, "cerebras": 1.25}.get(prov, 1.0)
        base = min(100, base * prov_mult)
        return self._apply(base, self.ss_modifiers)

    def _compute_agentic(self) -> AxisScore:
        bfcl = self._get_benchmark("bfcl")
        if bfcl:
            overall = bfcl.get("overall", 0) or bfcl.get("score", 0)
            base = calibrate_bfcl(overall)
        else:
            has_tools = self.m.get("has_tools", False)
            base = 60.0 if has_tools else 30.0
        return self._apply(base, self.as_modifiers)

    def _compute_coding(self) -> AxisScore:
        aa_coding = self.m.get("ai_coding")
        swe_data = self._get_benchmark("swe_verified")
        elo_data = self._get_benchmark("arena_elo")
        
        q_parts = []
        if aa_coding is not None:
            q_parts.append(calibrate_aa_index(aa_coding) * 0.6)
        else:
            q_parts.append(40.0 * 0.6)
        
        if swe_data is not None:
            swe_score = swe_data.get("score", 0)
            q_parts.append(calibrate_swe_verified(swe_score) * 0.4)
        elif elo_data is not None:
            elo_score = elo_data.get("elo", 0) or elo_data.get("score", 0)
            q_parts.append(calibrate_arena_elo(elo_score) * 0.3)
        else:
            q_parts.append(30.0 * 0.4)
        
        speed_component = calibrate_tps(self.m.get("tps", 0)) * 0.15
        base = sum(q_parts) + speed_component
        return self._apply(base, self.cs_modifiers)

    def _get_benchmark(self, source: str) -> dict | None:
        """Get benchmark data for this model from a specific source."""
        source_data = self.benchmarks.get(source)
        if not source_data or not isinstance(source_data, dict):
            return None
        mid = (self.m.get("model_id") or self.m.get("model") or "").lower()
        # Direct match
        if mid in source_data:
            val = source_data[mid]
            if isinstance(val, dict):
                return val
            if isinstance(val, (int, float)):
                return {"score": val}
        # Fuzzy match
        for key, val in source_data.items():
            if key.startswith("_"):
                continue
            norm_key = key.lower().replace("-", "").replace("_", "")
            norm_mid = mid.replace("-", "").replace("_", "")
            if norm_key in norm_mid or norm_mid in norm_key:
                if isinstance(val, dict):
                    return val
                if isinstance(val, (int, float)):
                    return {"score": val}
        return None

    def _estimate_intelligence_heuristic(self) -> float | None:
        """Heuristic when no AA data. Mirrors dink.py's _estimate_intelligence."""
        mid = (self.m.get("model_id") or self.m.get("model") or "").lower()
        if any(p in mid for p in ['kimi-k2.6', 'kimi-k2.5']):
            return 59.0
        if any(p in mid for p in ['deepseek-v4-flash', 'deepseek-v4-pro']):
            return 60.0
        if any(p in mid for p in ['glm-5.1', 'glm-5']):
            return 58.0
        if 'minimax-m2.7' in mid:
            return 52.0
        if 'minimax-m2.5' in mid:
            return 51.0
        if 'mimo-v2.5-pro' in mid:
            return 53.0
        return 28.0  # conservative C-tier


def load_benchmarks(path: str | Path | None = None) -> dict:
    """Load benchmarks.json from default or specified path."""
    if path is None:
        path = Path.home() / ".config" / "model-scan" / "benchmarks.json"
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def score_model(model_dict: dict, benchmarks: dict | None = None) -> dict:
    """Convenience: score a single model dict and return results dict."""
    if benchmarks is None:
        benchmarks = load_benchmarks()
    engine = ScoringEngine(model_dict, benchmarks)
    scores = engine.compute_all()
    return scores.to_dict()
