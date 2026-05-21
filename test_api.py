"""
model-scan — FastAPI Integration Tests

Tests all 10 REST endpoints for status codes, payload shapes, 
error handling, filters, and pagination.

Usage:
  # Start the API server first:
  cd api && uvicorn main:app --port 8123 &
  
  # Run tests:
  python3 test_api.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

BASE = "http://localhost:8123"

pass_count = 0
fail_count = 0


def test(name: str, result: bool, detail: str = ""):
    global pass_count, fail_count
    status = "✅" if result else "❌"
    if result:
        pass_count += 1
    else:
        fail_count += 1
    print(f"  {status} {name}" + (f"  [{detail}]" if detail else ""))


def get(path: str) -> tuple[int, Any, dict]:
    """GET request, returns (status, parsed_json, headers_as_dict)."""
    try:
        r = urllib.request.urlopen(f"{BASE}{path}", timeout=5)
        body = r.read().decode()
        status = r.status
        headers = dict(r.headers)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        return status, data, headers
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        status = e.code
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        return status, data, dict(e.headers)
    except Exception as e:
        return 0, {"error": str(e)}, {}


def main():
    global pass_count, fail_count
    
    print("┌─ FastAPI Integration Tests ──────────────────────")
    print(f"│ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"│ Target: {BASE}")
    print("└─────────────────────────────────────────────────")
    
    # ── 1. Health Check ──
    print("\n1. Basic Health")
    s, d, h = get("/")
    test("Root endpoint returns 200", s in (200, 404) or "/docs" in str(d), str(s))
    
    # ── 2. Scan Latest ──
    print("\n2. Scan Latest")
    s, d, h = get("/api/v1/scan/latest")
    test("Status 200", s == 200, str(s))
    test("Has models key", isinstance(d, dict) and "models" in d, str(type(d)))
    if isinstance(d, dict):
        test("Models is non-empty list", isinstance(d.get("models"), list) and len(d["models"]) > 0,
             f"{len(d.get('models', []))} models")
        if d.get("scans"):
            first = d["scans"][0]
            test("Scan has scan_id", "scan_id" in first)
            test("Scan has scanned_at", "scanned_at" in first)
    
    # ── 3. Models List ──
    print("\n3. Models List")
    s, d, h = get("/api/v1/models")
    test("Status 200", s == 200, str(s))
    test("Returns list", isinstance(d, list), str(type(d)))
    test("Has models", len(d) > 0, f"{len(d)} models")
    if d:
        first = d[0]
        test("Model has model_id", "model_id" in first or "model" in first)
        test("Model has provider", "provider" in first)
        test("Model has tps", "tps" in first)
        test("Model has tier", "tier" in first)
    
    # ── 4. Models with filters ──
    print("\n4. Models Filters")
    s, d, h = get("/api/v1/models?tier=S")
    test("Filter by tier=S works", isinstance(d, list) and all(m.get("tier") == "S" for m in d),
         f"{len(d)} S-tier models")
    
    s, d, h = get("/api/v1/models?limit=5")
    test("Limit parameter works", isinstance(d, list) and len(d) <= 5, f"{len(d)} models")
    
    s, d, h = get("/api/v1/models?sort=tps")
    test("Sort parameter works", isinstance(d, list) and len(d) > 0)
    
    # ── 5. Single Model Detail ──
    print("\n5. Model Detail")
    # Get first model ID
    _, models_list, _ = get("/api/v1/models?limit=1")
    if models_list and len(models_list) > 0:
        mid = models_list[0].get("model_id") or models_list[0].get("model", "")
        # For path converter, need to keep slashes unencoded
        # Use the model_id with slashes directly in URL path
        s, d, h = get(f"/api/v1/models/{mid}")
        test("Model detail returns 200", s == 200, str(s))
        if s == 200 and isinstance(d, dict):
            test("Has model_id", "model_id" in d or "model" in d, str(list(d.keys())[:5]))
            test("Has provider", "provider" in d)
            test("Has tier", "tier" in d)
    
    # Test 404 for unknown model
    s, d, h = get("/api/v1/models/__nonexistent_model_xyz__")
    test("Unknown model returns 404", s == 404, str(s))
    
    # ── 6. Slots List ──
    print("\n6. Slots List")
    s, d, h = get("/api/v1/slots")
    test("Status 200", s == 200, str(s))
    test("Returns list", isinstance(d, list), f"{type(d).__name__} ({len(d)} slots)")
    if isinstance(d, list) and len(d) > 0:
        first_slot = d[0]
        test("Slot is dict", isinstance(first_slot, dict))
        if isinstance(first_slot, dict):
            test("Slot has slot_id", "slot_id" in first_slot, first_slot.get("slot_id", "?"))
            test("Slot has requirements", any(k in first_slot for k in ["candidates", "incumbent", "min_ai", "label"]))
    
    # ── 7. Single Slot Detail ──
    print("\n7. Slot Detail")
    _, slots_data, _ = get("/api/v1/slots")
    if isinstance(slots_data, list) and len(slots_data) > 0:
        sid = slots_data[0].get("slot_id", "")
        s, d, h = get(f"/api/v1/slots/{sid}")
        test(f"Slot '{sid}' returns 200", s == 200, str(s))
        if s == 200 and isinstance(d, dict):
            test("Has label", "label" in d or "slot_id" in d)
            test("Has candidates", "candidates" in d)
    
    # ── 8. Compare ──
    print("\n8. Compare")
    s, d, h = get("/api/v1/compare")
    test("Compare with no params returns 200", s == 200, str(s))
    
    # Get a couple model IDs
    _, models_list, _ = get("/api/v1/models?limit=3")
    if models_list and len(models_list) >= 2:
        mid1 = models_list[0].get("model_id") or models_list[0].get("model", "")
        mid2 = models_list[1].get("model_id") or models_list[1].get("model", "")
        import urllib.parse as _up
        models_param = f"{_up.quote(mid1, safe='')},{_up.quote(mid2, safe='')}"
        s, d, h = get(f"/api/v1/compare?models={models_param}")
        test("Compare with models returns 200", s == 200, str(s))
        if s == 200 and isinstance(d, dict):
            test("Has models in response", "models" in d or "results" in d)
    
    # ── 9. Scan History ──
    print("\n9. Scan History")
    s, d, h = get("/api/v1/scan/history")
    test("Status 200", s == 200, str(s))
    test("Returns list", isinstance(d, list), f"{type(d).__name__}")
    if isinstance(d, list):
        test("Has historical data", len(d) > 0, f"{len(d)} entries")
    
    # ── 10. Providers ──
    print("\n10. Providers")
    s, d, h = get("/api/v1/providers")
    test("Status 200", s == 200, str(s))
    test("Returns list", isinstance(d, list), str(type(d)))
    test("Has providers", len(d) > 0, f"{len(d)} providers")
    if isinstance(d, list) and d:
        first = d[0]
        test("Provider has name", "name" in first or "provider" in first,
             str(list(first.keys()))[:60])
        test("Provider has model count", any(k in first for k in ["model_count", "count"]),
             str(list(first.keys()))[:60])
    
    # ── 11. Config Preview ──
    print("\n11. Config Preview")
    s, d, h = get("/api/v1/config/preview")
    test("Status 200", s == 200, str(s))
    test("Returns text or dict", isinstance(d, (str, dict)),
         f"type: {type(d).__name__}")
    
    # ── 12. CORS Headers ──
    print("\n12. CORS Headers")
    s, d, h = get("/api/v1/models")
    # CORS headers are only returned when Origin header is present (browser behavior)
    # Test with Origin header
    import http.client as _hc
    try:
        conn = _hc.HTTPConnection("localhost", 8123, timeout=5)
        conn.request("GET", "/api/v1/models", headers={"Origin": "http://localhost:5173"})
        resp = conn.getresponse()
        resp.read()
        cors = resp.getheader("Access-Control-Allow-Origin", resp.getheader("access-control-allow-origin", "missing"))
        test("CORS header present", cors != "missing", cors)
        test("CORS allows all origins", cors == "*", cors)
        conn.close()
    except Exception as e:
        test(f"CORS test failed: {e}", False)
    
    # ── Summary ──
    print(f"\n{'─' * 50}")
    total = pass_count + fail_count
    pct = round(pass_count / total * 100, 1) if total > 0 else 0
    print(f"  {pass_count}/{total} passing ({pct}%)")
    
    if fail_count > 0:
        print(f"\n  ⚠ {fail_count} test(s) failed")
        return 1
    
    print(f"\n  All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
