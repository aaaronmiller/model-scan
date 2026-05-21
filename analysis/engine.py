"""
model-scan — Multi-Source Analysis Engine

Fuses data from 3 sources to compute novel derived metrics:
  - AA API: intelligence/coding/math indices, speed, 15 eval benchmarks
  - Models.dev: pricing, context, capabilities, modalities, open weights
  - PinchBench: agent-task success rates, execution time, cost

Derived metrics combine these into unique analysis dimensions not 
available from any single source.
"""
from __future__ import annotations

import json
import math
import sqlite3
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from statistics import mean, stdev, median
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "model-scan"
DB_PATH = CONFIG_DIR / "model_scan.db"
AA_CACHE = CONFIG_DIR / "aa_cache.json"
BENCHMARKS_PATH = CONFIG_DIR / "benchmarks.json"
OUTPUT_DIR = CONFIG_DIR / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── FETCHERS ────────────────────────────────────────────────────────────────

def fetch_aa_data() -> dict[str, dict]:
    """Return AA API models keyed by normalized model ID."""
    if not AA_CACHE.exists():
        return {}
    try:
        raw = json.loads(AA_CACHE.read_text())
        if isinstance(raw, dict) and "lookup" in raw:
            data = raw["lookup"]
            return data
        data = raw.get("data") if isinstance(raw, dict) else raw
        if isinstance(data, list):
            result = {}
            for m in data:
                slug = m.get("slug", "").lower()
                result[slug] = m
            return result
        return {}
    except Exception:
        return {}


def fetch_models_dev() -> dict[str, dict]:
    """Fetch models.dev data. Returns dict of {provider: {model: {...}}}."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://models.dev/api.json",
            headers={"User-Agent": "model-scan/5.0 (analysis engine)"}
        )
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠ models.dev fetch failed: {e}")
        return {}


def fetch_pinchbench() -> list[dict]:
    """Fetch PinchBench leaderboard data."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://api.pinchbench.com/api/leaderboard",
            headers={"User-Agent": "model-scan/5.0 (analysis engine)"}
        )
        r = urllib.request.urlopen(req, timeout=10)
        data = json.loads(r.read().decode())
        return data.get("leaderboard", [])
    except Exception as e:
        print(f"  ⚠ pinchbench fetch failed: {e}")
        return []


def load_scan_models() -> list[dict]:
    """Load latest scan models from SQLite."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT MAX(scan_id) FROM scans")
    scan_id = cur.fetchone()[0]
    if not scan_id:
        conn.close()
        return []
    cur = conn.execute(
        "SELECT * FROM models WHERE scan_id = ? AND accessible = 1",
        (scan_id,)
    )
    models = [dict(r) for r in cur.fetchall()]
    conn.close()
    return models


def normalize_id(mid: str) -> str:
    """Normalize a model ID across different data sources."""
    return mid.lower().strip().replace(" ", "-").replace("_", "-")


# ── DERAILED METRICS ENGINE ─────────────────────────────────────────────────

class MetricEngine:
    """Computes novel derived metrics from fused data sources."""
    
    def __init__(self, aa_data: dict, md_data: dict, pb_data: list[dict], scan_models: list[dict]):
        self.aa = aa_data
        self.md = md_data
        self.pb = pb_data
        self.scan = scan_models
        self.results: dict[str, dict] = {}
        
        # Build cross-reference index
        self._crossref()
    
    def _crossref(self):
        """Build cross-reference index: model_id → {aa, md, pb, scan}."""
        self.ref: dict[str, dict] = defaultdict(lambda: {"aa": None, "md": None, "pb": None, "scan": None})
        
        # AA data
        for slug, m in self.aa.items():
            nid = normalize_id(slug)
            self.ref[nid]["aa"] = m
            # Also index by name
            name = normalize_id(m.get("name", ""))
            self.ref[name]["aa"] = m
        
        # Models.dev data
        for pid, p in self.md.items():
            for mid, m in p.get("models", {}).items():
                full_id = normalize_id(f"{pid}/{mid}")
                self.ref[full_id]["md"] = m
                # Also index without provider
                self.ref[normalize_id(mid)]["md"] = m
        
        # PinchBench data
        for entry in self.pb:
            mid = normalize_id(entry.get("model", ""))
            self.ref[mid]["pb"] = entry
            # Short name
            parts = mid.split("/")
            if len(parts) > 1:
                self.ref[normalize_id(parts[-1])]["pb"] = entry
        
        # Scan data
        for m in self.scan:
            mid = normalize_id(m.get("model_id", "") or m.get("model", ""))
            self.ref[mid]["scan"] = m
    
    def compute_all(self) -> dict[str, Any]:
        """Compute all derived metrics for all cross-referenced models."""
        results = {}
        
        for nid, sources in self.ref.items():
            aa = sources["aa"]
            md = sources["md"]
            pb = sources["pb"]
            scan = sources["scan"]
            
            # Only compute if we have AA data (core requirement for quality)
            if not aa and not pb:
                continue
            
            metrics = self._compute_for_model(nid, aa, md, pb, scan)
            if metrics:
                results[nid] = metrics
        
        return results
    
    def _compute_for_model(self, nid: str, aa: dict | None, md: dict | None,
                          pb: dict | None, scan: dict | None) -> dict | None:
        """Compute derived metrics for a single model cross-reference."""
        
        # ── Extract raw values from each source ──
        
        # AA values
        evals = aa if aa else {}  # AA data is flat dict in our cache
        ai_intel = evals.get("ai_index")
        ai_coding = evals.get("ai_coding")
        ai_math = evals.get("ai_math")
        tps = evals.get("median_tps") or evals.get("median_output_tokens_per_second")
        ttft = evals.get("median_ttft") or evals.get("median_time_to_first_token_seconds")
        aa_ttfa = evals.get("median_time_to_first_answer_token")
        
        # AA pricing
        cost_input = evals.get("price_input") or evals.get("price_1m_input_tokens")
        cost_output = evals.get("price_output") or evals.get("price_1m_output_tokens")
        cost_blended = evals.get("price_blended") or evals.get("price_1m_blended_3_to_1")
        
        # AA eval individual — from flat AA cache fields
        aime = evals.get("aime")
        gpqa = evals.get("gpqa")
        mmlu = evals.get("mmlu_pro")
        livecode = evals.get("livecodebench")
        scicode = evals.get("scicode")
        terminal = evals.get("terminalbench_hard")
        ifbench = evals.get("ifbench")
        lcr = evals.get("lcr")
        hle = evals.get("hle")
        tau2 = evals.get("tau2")
        
        # Models.dev values
        cost_md = md.get("cost", {}) if md else {}
        md_input = cost_md.get("input")
        md_output = cost_md.get("output")
        md_cache_read = cost_md.get("cache_read")
        md_cache_write = cost_md.get("cache_write")
        md_reasoning_cost = cost_md.get("reasoning")
        
        limits = md.get("limit", {}) if md else {}
        ctx = limits.get("context", 0) or 0
        max_output = limits.get("output", 0) or 0
        
        modalities = md.get("modalities", {}) if md else {}
        input_mods = modalities.get("input", [])
        output_mods = modalities.get("output", [])
        
        reasoning_capable = md.get("reasoning", False) if md else False
        tool_call_capable = md.get("tool_call", False) if md else False
        open_weights = md.get("open_weights", False) if md else False
        structured_output = md.get("structured_output", False) if md else False
        attachment_support = md.get("attachment", False) if md else False
        family = md.get("family", "") if md else ""
        knowledge = md.get("knowledge", "") if md else ""
        
        # PinchBench values
        pb_best = pb.get("best_score_percentage") if pb else None
        pb_avg = pb.get("average_score_percentage") if pb else None
        pb_best_time = pb.get("best_execution_time_seconds") if pb else None
        pb_avg_time = pb.get("average_execution_time_seconds") if pb else None
        pb_best_cost = pb.get("best_cost_usd") if pb else None
        pb_avg_cost = pb.get("average_cost_usd") if pb else None
        pb_submissions = pb.get("submission_count", 0) if pb else 0
        pb_weights = pb.get("weights", "") if pb else ""
        
        # Scan values
        scan_tps = scan.get("tps") if scan else None
        scan_lat = scan.get("latency_s") if scan else None
        scan_tier = scan.get("tier") if scan else None
        scan_has_tools = scan.get("has_tools", False) if scan else False
        scan_has_vision = scan.get("has_vision_capability", False) if scan else False
        scan_price = scan.get("price_blended") if scan else None
        
        # Best available values from any source
        best_tps = scan_tps or tps or 0
        best_cost_blended = scan_price or cost_blended or (md_input or 0 + (md_output or 0)) / 2 if (md_input or md_output) else None
        best_cost_input = cost_input or md_input
        best_cost_output = cost_output or md_output
        
        # ── DERIVED METRIC 1: Agent Value Index (AVI) ──
        # Fuses AA intelligence with PinchBench agent-task performance
        avi = None
        if ai_intel and pb_best:
            avi = round(ai_intel * pb_best / 60.0 * 100, 1)
        elif ai_intel:
            avi = round(ai_intel / 60.0 * 100, 1)
        
        # ── DERIVED METRIC 2: Cost-Adjusted Intelligence (CAI) ──
        # Intelligence per dollar per million tokens
        cai = None
        if ai_intel and best_cost_blended and best_cost_blended > 0:
            cai = round(ai_intel / best_cost_blended, 1)
        
        # ── DERIVED METRIC 3: Speed/Quality Ratio (SQR) ──
        # How fast you get quality output. Higher = better balance.
        sqr = None
        if best_tps and best_tps > 0 and ai_intel:
            sqr = round(best_tps / max(1, 100 - ai_intel) * 10, 1)
        
        # ── DERIVED METRIC 4: Capability Density (CD) ──
        # Features per dollar: tools + reasoning + vision + structured output + attachment
        capability_count = sum([
            1 if tool_call_capable else 0,
            1 if reasoning_capable else 0,
            1 if scan_has_vision else 0,
            1 if structured_output else 0,
            1 if attachment_support else 0,
            1 if open_weights else 0,
        ])
        cd = None
        if best_cost_blended and best_cost_blended > 0:
            cd = round(capability_count / best_cost_blended, 1)
        
        # ── DERIVED METRIC 5: Open-Source Value Score (OSV) ──
        # Intelligence-per-dollar adjusted for open-availability premium
        osv = None
        if ai_intel and best_cost_blended and best_cost_blended > 0:
            multiplier = 1.25 if open_weights else 1.0
            osv = round(ai_intel / best_cost_blended * multiplier, 1)
        
        # ── DERIVED METRIC 6: Benchmark Consistency Index (BCI) ──
        # How consistent across ALL benchmarks. Lower stddev = more generalist
        bench_scores = [v for v in [aime, gpqa, mmlu, livecode, scicode, ifbench, lcr, tau2] if v]
        bci = None
        if len(bench_scores) >= 3:
            bci = round(mean(bench_scores) * 100 / max(1, stdev(bench_scores) * 100), 2) if stdev(bench_scores) > 0 else 999.0
        
        # ── DERIVED METRIC 7: Modality Breadth Score ──
        mbs = len(input_mods) * len(output_mods) if input_mods and output_mods else 0
        
        # ── DERIVED METRIC 8: Context ROI ──
        # Context window per unit of intelligence
        ctx_roi = None
        if ctx and ai_intel and ai_intel > 0:
            ctx_roi = round(ctx / 1000 / ai_intel, 2)
        
        # ── DERIVED METRIC 9: Cache Savings Potential (CSP) ──
        # % cost savings possible from caching
        csp = None
        if md_cache_read and md_cache_write and md_input and md_output:
            no_cache = md_input + md_output
            with_cache = md_cache_read + md_cache_write
            if no_cache > 0:
                csp = round((no_cache - with_cache) / no_cache * 100, 1)
        
        # ── DERIVED METRIC 10: Task Specialization Score (TSS) ──
        # How specialized vs generalist. High = excels at specific categories
        tss = None
        if len(bench_scores) >= 3:
            tss = round(stdev(bench_scores) * 100, 1)
        
        # ── DERIVED METRIC 11: Reasoning Efficiency (RE) ──
        # How much reasoning costs vs the intelligence gain
        re = None
        if reasoning_capable and ai_intel and best_cost_blended and best_cost_blended > 0:
            re = round(ai_intel / best_cost_blended, 1)
        
        # ── DERIVED METRIC 12: Knowledge Freshness Index (KFI) ──
        # Months since knowledge cutoff
        kfi = None
        if knowledge:
            try:
                kdate = datetime.strptime(knowledge + "-01" if len(knowledge) == 7 else knowledge, "%Y-%m-%d")
                kfi = max(0, round((datetime.now() - kdate).days / 30.44, 1))
            except ValueError:
                pass
        
        # ── DERIVED METRIC 13: Agent ROI (A-ROI) ──
        # PinchBench score per dollar per minute
        aroi = None
        if pb_best and pb_avg_cost and pb_avg_cost > 0 and pb_avg_time and pb_avg_time > 0:
            aroi = round(pb_best / pb_avg_cost * 60 / (pb_avg_time / 60), 1)
        
        # ── DERIVED METRIC 14: Efficiency Frontier Distance ──
        # Log-scale distance from hypothetical Pareto frontier
        efd = None
        if ai_intel and best_tps:
            efd = round(math.log(ai_intel * best_tps + 1), 1)
        
        # ── DERIVED METRIC 15: Composite Score (multi-axis) ──
        # Weighted combination of all signals, normalized 0-100
        components = []
        weights = []
        
        if ai_intel:
            components.append(ai_intel / 60.0 * 100)
            weights.append(0.25)
        if pb_best:
            components.append(pb_best * 100)
            weights.append(0.20)
        if best_tps:
            components.append(min(100, best_tps / 100 * 100))
            weights.append(0.10)
        if cai:
            components.append(min(100, cai / 10 * 100))
            weights.append(0.10)
        if avi:
            components.append(min(100, avi))
            weights.append(0.15)
        if cd:
            components.append(min(100, cd * 5))
            weights.append(0.10)
        if ctx:
            components.append(min(100, math.log(ctx) / math.log(200000) * 100))
            weights.append(0.10)
        
        composite = None
        if components:
            total_w = sum(weights)
            composite = round(sum(c * w for c, w in zip(components, weights)) / total_w, 1)
        
        # ── CALCULUS-ENHANCED METRICS ─────────────────────────────────────
        # These use mathematical functions to model non-linear relationships,
        # diminishing returns, ideal ranges, and rate-of-change.
        
        # ── CM1: Sigmoid Quality Score ──
        # Clamps any raw score to [0, 1] using logistic function
        # σ(x) = 1 / (1 + e^(-k(x - x₀)))
        # Where k controls steepness, x₀ is the inflection point
        def sigmoid(x, k=0.1, x0=50):
            return 1.0 / (1.0 + math.exp(-k * (x - x0)))
        
        sigmoid_quality = round(sigmoid(ai_intel or 0, k=0.12, x0=35) * 100, 1) if ai_intel else None
        
        # ── CM2: Quadratic Intelligence Modifier ──
        # Models diminishing returns: high intelligence has sub-linear value
        # I_quad = I_linear - α × I² where α dampens extreme values
        # This prevents 60 AI from being valued 2x a 30 AI
        quad_intel = None
        if ai_intel:
            alpha = 0.003  # Dampening factor
            quad_intel = round(ai_intel - alpha * (ai_intel ** 2), 1)
        
        # ── CM3: Bell-Curve Latency Penalty ──
        # Models ideal latency range using Gaussian function
        # P(t) = 1 - e^(-((t - μ)² / 2σ²))
        # Where μ is ideal latency (1.0s), σ is tolerance (2.0s)
        # Too-fast (<0.2s) and too-slow (>5s) both penalized
        bell_latency = None
        if ttft or scan_lat:
            lat = ttft or scan_lat or 0
            mu = 0.8   # ideal TTFT (seconds)
            sigma = 1.5  # tolerance
            penalty = 1.0 - math.exp(-((lat - mu) ** 2) / (2 * sigma ** 2))
            bell_latency = round(max(0, min(100, (1 - penalty) * 100)), 1)
        
        # ── CM4: Derivative — Marginal Intelligence per Dollar ──
        # Approximates d(Intelligence)/d(Cost): how much more quality
        # you get by spending more. Higher = better value at margin.
        # dI/dC ≈ ΔI/ΔC across price brackets
        marginal_intel_per_dollar = None
        if ai_intel and best_cost_blended and best_cost_blended > 0.01:
            # Approximate derivative as intel/cost (linear model)
            # In a refined version this would be a true finite difference
            marginal_intel_per_dollar = round(ai_intel / best_cost_blended * 0.1, 3)
        
        # ── CM5: Integral — Cumulative Value Score ──
        # ∫(performance d(cost)) from 0 to current cost
        # Models total value delivered up to the price point
        # Approximated as area under the performance curve:
        # ∫P(c)dc ≈ ½ × (P_at_cost + P_at_0) × cost
        integral_value = None
        if ai_intel and best_cost_blended and best_cost_blended > 0:
            perf_at_zero = ai_intel * 0.5  # assume 50% perf at zero cost
            integral_value = round(0.5 * (ai_intel + perf_at_zero) * best_cost_blended, 1)
        
        # ── CM6: Gradient Component — Weight Sensitivity ──
        # ∂Composite/∂Weight_i — how sensitive the composite is to each weight
        # Helps identify which metrics dominate the score
        # Computed as: Δcomposite / Δweight for small perturbations
        gradient_sensitivity = None
        if composite:
            # Normalize: higher sensitivity means small weight changes
            # have large effects on the final score
            top_contributors = []
            if ai_intel and weights and len(weights) > 0:
                intel_contrib = (ai_intel / 60.0 * 100) * 0.25 / max(composite, 1)
                top_contributors.append(("intelligence", round(intel_contrib, 3)))
            if pb_best:
                pb_contrib = (pb_best * 100) * 0.20 / max(composite, 1)
                top_contributors.append(("pinchbench", round(pb_contrib, 3)))
            if best_tps:
                tps_contrib = (min(100, best_tps / 100 * 100)) * 0.10 / max(composite, 1)
                top_contributors.append(("speed", round(tps_contrib, 3)))
            gradient_sensitivity = sorted(top_contributors, key=lambda x: -x[1])
        
        # ── CM7: Tanh Clamped Latency ──
        # tanh(latency) normalizes unbounded latency to [0, 1)
        # with smooth saturation at high values
        tanh_latency = None
        if ttft or scan_lat:
            lat = ttft or scan_lat or 0
            tanh_latency = round(math.tanh(lat * 1.5) * 100, 1)  # Lower is better
        
        # ── CM8: Exponential Intelligence Decay ──
        # Models how freshness affects intelligence value
        # I_effective = I_base × e^(-λ × months_since_training)
        # Older models get exponentially less valuable
        exp_intel = None
        if ai_intel:
            decay_lambda = 0.03  # 3% decay per month
            age_factor = kfi if (kfi or 0) > 0 else 6  # assume 6 months if unknown
            exp_intel = round(ai_intel * math.exp(-decay_lambda * age_factor), 1) if ai_intel else None
        
        # ── CM9: Composite — Weighted with Calculus Terms ──
        # Enhanced composite that includes calculus modifiers
        calc_components = []
        calc_weights = []
        
        if sigmoid_quality:
            calc_components.append(sigmoid_quality)
            calc_weights.append(0.20)
        if quad_intel:
            calc_components.append(min(100, quad_intel * 2))
            calc_weights.append(0.15)
        if bell_latency:
            calc_components.append(bell_latency)
            calc_weights.append(0.10)
        if exp_intel:
            calc_components.append(exp_intel)
            calc_weights.append(0.10)
        if composite:
            calc_components.append(composite)
            calc_weights.append(0.25)
        if integral_value:
            calc_components.append(min(100, integral_value))
            calc_weights.append(0.10)
        if marginal_intel_per_dollar:
            calc_components.append(min(100, marginal_intel_per_dollar * 100))
            calc_weights.append(0.10)
        
        calc_composite = None
        if calc_components:
            total_cw = sum(calc_weights)
            calc_composite = round(sum(c * w for c, w in zip(calc_components, calc_weights)) / total_cw, 1)
        
        # ── DERIVED METRIC 16: Provider-Pareto Rank ──
        # Rank within same provider family
        ppr = None
        
        return {
            # Raw values (cross-referenced)
            "sources": {
                "aa": bool(aa), "models_dev": bool(md),
                "pinchbench": bool(pb), "scan": bool(scan),
            },
            "family": family,
            "open_weights": open_weights,
            "reasoning_capable": reasoning_capable,
            "tool_call_capable": tool_call_capable,
            
            # Raw intelligence metrics
            "ai_intelligence": round(ai_intel, 1) if ai_intel else None,
            "ai_coding": round(ai_coding, 1) if ai_coding else None,
            "ai_math": round(ai_math, 1) if ai_math else None,
            "tps": round(best_tps, 1) if best_tps else None,
            "ttft_s": round(ttft, 3) if ttft else None,
            "context_k": round(ctx / 1000, 0) if ctx else None,
            "max_output_k": round(max_output / 1000, 0) if max_output else None,
            
            # Pricing
            "cost_input_per_m": cost_input or md_input,
            "cost_output_per_m": cost_output or md_output,
            "cost_blended_per_m": best_cost_blended,
            "cache_read_per_m": md_cache_read,
            "cache_write_per_m": md_cache_write,
            "cache_savings_pct": csp,
            
            # PinchBench
            "pinchbench_best_pct": round(pb_best * 100, 1) if pb_best else None,
            "pinchbench_avg_pct": round(pb_avg * 100, 1) if pb_avg else None,
            "pinchbench_best_cost_usd": pb_best_cost,
            "pinchbench_avg_cost_usd": pb_avg_cost,
            "pinchbench_best_time_min": round(pb_best_time / 60, 1) if pb_best_time else None,
            "pinchbench_avg_time_min": round(pb_avg_time / 60, 1) if pb_avg_time else None,
            "pinchbench_submissions": pb_submissions,
            
            # ── NOVEL DERIVED METRICS ──
            "derived": {
                "agent_value_index": avi,
                "cost_adjusted_intelligence": cai,
                "speed_quality_ratio": sqr,
                "capability_density": cd,
                "open_source_value": osv,
                "benchmark_consistency": bci,
                "modality_breadth": mbs,
                "context_roi": ctx_roi,
                "task_specialization": tss,
                "reasoning_efficiency": re,
                "knowledge_freshness_months": kfi,
                "agent_roi": aroi,
                "efficiency_frontier_dist": efd,
                "composite_score": composite,
                # Calculus-enhanced metrics
                "sigmoid_quality": sigmoid_quality,
                "quadratic_intel": quad_intel,
                "bell_curve_latency": bell_latency,
                "marginal_intel_per_dollar": marginal_intel_per_dollar,
                "integral_cumulative_value": integral_value,
                "gradient_sensitivity": gradient_sensitivity,
                "tanh_latency_penalty": tanh_latency,
                "exponential_decay_intel": exp_intel,
                "calculus_composite": calc_composite,
            }
        }


# ── HIGH-LEVEL ANALYSES ─────────────────────────────────────────────────────

class AnalysisSuite:
    """Runs multi-dimensional analyses across all models."""
    
    def __init__(self, engine: MetricEngine, all_metrics: dict):
        self.engine = engine
        self.metrics = all_metrics
    
    def pareto_frontier(self, x_key: str, y_key: str, higher_better: tuple[bool, bool] = (True, True)) -> list[dict]:
        """Find models on the Pareto-optimal frontier for two metrics."""
        items = []
        for nid, m in self.metrics.items():
            x = m.get(x_key) if x_key in m else m.get("derived", {}).get(x_key)
            y = m.get(y_key) if y_key in m else m.get("derived", {}).get(y_key)
            if x is not None and y is not None:
                items.append({"model_id": nid, "x": x, "y": y, **m.get("sources", {})})
        
        if len(items) < 3:
            return items
        
        # Normalize and find frontier
        x_sign = 1 if higher_better[0] else -1
        y_sign = 1 if higher_better[1] else -1
        
        # Sort by x
        items.sort(key=lambda i: i["x"] * x_sign)
        
        frontier = []
        max_y = -float("inf") if higher_better[1] else float("inf")
        for item in items:
            if higher_better[1]:
                if item["y"] > max_y:
                    max_y = item["y"]
                    frontier.append(item)
            else:
                if item["y"] < max_y:
                    max_y = item["y"]
                    frontier.append(item)
        
        return frontier
    
    def capability_clusters(self) -> dict:
        """Cluster models by capability profile."""
        clusters = {
            "full_stack": [],  # tools + reasoning + vision + structured + attachments
            "agent_ready": [],  # tools + reasoning but no vision
            "reasoning_only": [],  # reasoning + high intelligence, no tools
            "lightweight": [],  # no reasoning, no tools, fast
            "open_workhorses": [],  # open weights, decent intelligence, tools
            "vision_specialists": [],  # vision-capable
        }
        
        for nid, m in self.metrics.items():
            d = m.get("derived", {})
            ai = m.get("ai_intelligence") or 0
            tool_call = m.get("tool_call_capable", False)
            reasoning = m.get("reasoning_capable", False)
            open_w = m.get("open_weights", False)
            cost = m.get("cost_blended_per_m") or 999
            tps = m.get("tps") or 0
            
            has_vision = m.get("sources", {}).get("scan") or False  # from scan data
            
            # Vision specialists
            if has_vision:
                clusters["vision_specialists"].append(nid)
            
            # Full stack: every capability
            if tool_call and reasoning:
                clusters["agent_ready"].append(nid)
                clusters["full_stack"].append(nid)
            
            # Reasoning only (no tools)
            if reasoning and not tool_call:
                clusters["reasoning_only"].append(nid)
            
            # Lightweight: fast, cheap, no extras
            if not reasoning and ai < 30 and tps > 50 and cost < 1:
                clusters["lightweight"].append(nid)
            
            # Open workhorses
            if open_w and ai > 25 and tool_call and cost < 5:
                clusters["open_workhorses"].append(nid)
        
        return {k: v[:20] for k, v in clusters.items()}
    
    def price_intelligence_equilibrium(self) -> dict:
        """Find the price point where intelligence stops correlating with cost."""
        points = []
        for nid, m in self.metrics.items():
            ai = m.get("ai_intelligence")
            cost = m.get("cost_blended_per_m")
            if ai and cost and cost > 0:
                points.append({"model": nid, "intel": ai, "cost": cost})
        
        # Sort by cost, find where incremental cost/benefit drops below threshold
        points.sort(key=lambda p: p["cost"])
        
        # Rolling efficiency
        segments = []
        for i in range(0, len(points) - 1, max(1, len(points) // 10)):
            segment = points[i:i + max(5, len(points) // 20)]
            if segment:
                avg_cost = mean(p["cost"] for p in segment)
                avg_intel = mean(p["intel"] for p in segment)
                segments.append({
                    "cost_bracket": round(avg_cost, 2),
                    "avg_intel": round(avg_intel, 1),
                    "count": len(segment),
                })
        
        # Find equilibrium: where efficiency (intel/cost) peaks
        efficiencies = [(p["intel"] / p["cost"], p["cost"], p["model"]) for p in points if p["cost"] > 0.01]
        efficiencies.sort(reverse=True)
        
        sweet_spot = {"cost": None, "model": None, "efficiency": 0}
        for eff, cost, model in efficiencies[:5]:
            if eff > sweet_spot["efficiency"]:
                sweet_spot = {"cost": round(cost, 3), "model": model, "efficiency": round(eff, 1)}
        
        return {
            "sweet_spot": sweet_spot,
            "segments": segments,
            "total_points": len(points),
            "correlation": self._spearman([p["cost"] for p in points[:50]], [p["intel"] for p in points[:50]]),
        }
    
    def open_vs_closed_gap(self) -> dict:
        """Compute the intelligence gap between open and closed models at similar price points."""
        open_scores = []
        closed_scores = []
        
        for nid, m in self.metrics.items():
            ai = m.get("ai_intelligence")
            cost = m.get("cost_blended_per_m")
            if ai and cost:
                if m.get("open_weights"):
                    open_scores.append({"model": nid, "intel": ai, "cost": cost})
                else:
                    closed_scores.append({"model": nid, "intel": ai, "cost": cost})
        
        # Bucket by price range
        from collections import defaultdict
        buckets = defaultdict(lambda: {"open": [], "closed": []})
        
        for s in open_scores:
            bucket = round(s["cost"] * 2) / 2  # round to nearest $0.50
            buckets[bucket]["open"].append(s["intel"])
        
        for s in closed_scores:
            bucket = round(s["cost"] * 2) / 2
            buckets[bucket]["closed"].append(s["intel"])
        
        gaps = {}
        for bucket, data in sorted(buckets.items()):
            if data["open"] and data["closed"]:
                avg_open = mean(data["open"])
                avg_closed = mean(data["closed"])
                gaps[f"${bucket:.1f}"] = {
                    "open_intel": round(avg_open, 1),
                    "closed_intel": round(avg_closed, 1),
                    "gap": round(avg_closed - avg_open, 1),
                    "gap_pct": round((avg_closed - avg_open) / avg_open * 100, 1) if avg_open > 0 else 0,
                }
        
        return {
            "gaps": gaps,
            "open_count": len(open_scores),
            "closed_count": len(closed_scores),
            "avg_open_intel": round(mean([s["intel"] for s in open_scores]), 1) if open_scores else 0,
            "avg_closed_intel": round(mean([s["intel"] for s in closed_scores]), 1) if closed_scores else 0,
        }
    
    def release_velocity_by_provider(self) -> dict:
        """Count model releases per year by provider."""
        from collections import Counter
        yearly = Counter()
        
        for nid, m in self.metrics.items():
            family = m.get("family", "")
            if family:
                yearly[family] += 1
        
        return dict(yearly.most_common(20))
    
    def top_by_composite(self, n: int = 20) -> list[dict]:
        """Top N models by composite score."""
        scored = []
        for nid, m in self.metrics.items():
            cs = m.get("derived", {}).get("composite_score")
            if cs:
                scored.append({
                    "model_id": nid,
                    "composite": cs,
                    "ai_intel": m.get("ai_intelligence"),
                    "tps": m.get("tps"),
                    "cost": m.get("cost_blended_per_m"),
                    "pinchbench": m.get("pinchbench_best_pct"),
                    "has_scan": m.get("sources", {}).get("scan", False),
                })
        
        scored.sort(key=lambda x: x["composite"], reverse=True)
        return scored[:n]
    
    def _spearman(self, x: list[float], y: list[float]) -> float:
        """Simple rank correlation."""
        n = min(len(x), len(y))
        if n < 3:
            return 0
        # Normalize to ranks
        x_ranks = {v: i for i, v in enumerate(sorted(set(x)))}
        y_ranks = {v: i for i, v in enumerate(sorted(set(y)))}
        
        d_sum = sum((x_ranks.get(x[i], 0) - y_ranks.get(y[i], 0)) ** 2 for i in range(n))
        return round(1 - (6 * d_sum) / (n * (n ** 2 - 1)), 3)


# ── MAIN ────────────────────────────────────────────────────────────────────

def run_full_analysis() -> dict:
    """Run the full multi-source analysis pipeline."""
    print("  Fetching AA data...")
    aa = fetch_aa_data()
    print(f"  ✓ {len(aa)} AA models")
    
    print("  Fetching models.dev data...")
    md = fetch_models_dev()
    model_count = sum(len(p.get("models", {})) for p in md.values())
    print(f"  ✓ {len(md)} providers, {model_count} models")
    
    print("  Fetching PinchBench data...")
    pb = fetch_pinchbench()
    print(f"  ✓ {len(pb)} leaderboard entries")
    
    print("  Loading scan models...")
    scan = load_scan_models()
    print(f"  ✓ {len(scan)} models")
    
    print("  Computing derived metrics...")
    engine = MetricEngine(aa, md, pb, scan)
    metrics = engine.compute_all()
    print(f"  ✓ {len(metrics)} cross-referenced models with metrics")
    
    print("  Running analysis suite...")
    analysis = AnalysisSuite(engine, metrics)
    
    composite_top = analysis.top_by_composite(30)
    print(f"  ✓ Composite ranking: top = {composite_top[0]['model_id'] if composite_top else 'N/A'} ({composite_top[0]['composite'] if composite_top else 0})")
    
    pareto = analysis.pareto_frontier("ai_intelligence", "tps")
    print(f"  ✓ Pareto frontier: {len(pareto)} points")
    
    clusters = analysis.capability_clusters()
    print(f"  ✓ Capability clusters: {sum(len(v) for v in clusters.values())} categorized")
    
    equilibrium = analysis.price_intelligence_equilibrium()
    print(f"  ✓ Price equilibrium: sweet spot at ${equilibrium['sweet_spot']['cost']}/M")
    
    open_gap = analysis.open_vs_closed_gap()
    print(f"  ✓ Open/closed gap: {open_gap.get('gap_pct', 'N/A')}% avg penalty")
    
    return {
        "generated_at": datetime.now().isoformat(),
        "sources": {
            "aa_models": len(aa),
            "models_dev_providers": len(md),
            "models_dev_models": model_count,
            "pinchbench_entries": len(pb),
            "scan_models": len(scan),
        },
        "cross_referenced_count": len(metrics),
        "top_by_composite": composite_top,
        "pareto_frontier": pareto,
        "capability_clusters": clusters,
        "price_intelligence_equilibrium": equilibrium,
        "open_vs_closed_gap": open_gap,
        "derived_metrics": metrics,
    }


def main():
    print("┌─ Multi-Source Analysis Engine ───────────────────")
    print(f"│ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("└───────────────────────────────────────────────────")
    
    results = run_full_analysis()
    
    json_path = OUTPUT_DIR / f"analysis_{datetime.now().strftime('%Y%m%d')}.json"
    json_path.write_text(json.dumps(results, indent=2, default=str))
    
    print(f"\n  Output: {json_path.name}")
    print(f"  ├─ {results['cross_referenced_count']} models analyzed")
    print(f"  ├─ {len(results.get('derived_metrics', {}))} derived metric sets")
    print(f"  ├─ Pareto frontier: {len(results.get('pareto_frontier', []))} optimal points")
    print(f"  └─ Clusters: {sum(len(v) for v in results.get('capability_clusters', {}).values())} categorized")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
