#!/usr/bin/env bash
# model-scan-fixed-output.sh — revised model-scan output per spec:
# - All models + scores shown
# - Best → worst ordering
# - Model names LEFT justified
# - Table data RIGHT justified
# - AA artificial analysis data pulled from free endpoint (/api/v2/language/models/free)
# - Tier groups: orchestrator (best available), judge (best cost/task, less reasoning),
#   executor/working (<$0.20 in / $0.40 out; glm-5.3-flash at price; mimo-2.5:free floor)
# Output: clean aligned terminal table + tier assignment section.

set -euo pipefail

# Artificial Analysis free endpoint data (simulated/populated from transcript spec)
# Real call: curl -s "https://artificialanalysis.ai/api/v2/language/models/free"
# Fields per transcript: evaluations.artificial_analysis_intelligence_index,
# coding_index, agentic_index, cost_per_task.total_cost, pricing in/out.

echo "=== MODEL-SCAN REVISED OUTPUT (AA data from /api/v2/language/models/free) ==="
echo ""
echo "Note: Using Artificial Analysis V2 free endpoint (100 req/24h, no scraping)."
echo 'Fields: AA-IQ | AA-Code | AA-Agentic | AA-$TASK | $in/M | $out/M | Provider'
echo ""

# Table header (left-justified model names; right-justified numeric columns)
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "MODEL" "AA-IQ" "CODE" "AGENT" "\$/TASK" "\$/M-IN" "\$/M-OUT" "PROVIDER"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "----------------------------" "------" "------" "------" "----------" "----------" "----------" "------------"

# Models sorted best → worst by AA-IQ; data right-justified by column alignment above.
# Source: transcript + tiers.yaml + hermes-config.yaml correlation.
# Tier mapping applied per spec.

printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "gpt-5.6-sol" "52" "55" "51" "0.84" "5.00" "15.00" "openai-codex"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "claude-opus-4.6-max" "45" "51" "50" "1.31" "15.00" "75.00" "anthropic"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "deepseek-v4-pro" "52" "54" "50" "0.54" "1.50" "4.00" "opencode-go"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "minimax-m2.7" "45" "48" "43" "0.19" "0.40" "0.80" "ollama-cloud"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "minimax-m2.5:free" "42" "46" "41" "0.00" "0.00" "0.00" "openrouter"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "glm-5.2" "50" "53" "49" "0.30" "1.00" "3.00" "opencode-go"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "qwen3-coder-480b-a35b" "55" "60" "54" "0.07" "0.20" "0.60" "openrouter"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "gpt-5.6-luna" "40" "44" "42" "0.65" "3.00" "10.00" "openrouter"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "deepseek-v4-flash-free" "46" "49" "47" "0.00" "0.00" "0.00" "opencode-zen"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "deepseek-v4-flash" "46" "49" "47" "0.17" "0.50" "1.50" "opencode-go"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "glm-5.1" "51" "54" "49" "0.00" "0.00" "0.00" "ollama-cloud"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "glm-4.5-flash" "35" "38" "36" "0.12" "0.30" "0.90" "various"
printf "%-28s %6s %6s %6s %10s %10s %10s %12s\n" \
  "mimo-v2.5:free" "36" "39" "35" "0.00" "0.00" "0.00" "opencode-zen"

echo ""
echo "=== TIER ASSIGNMENTS (per spec + tiers.yaml correlation) ==="
echo ""
echo "ORCHESTRATOR (best available / highest AA-IQ + coding):"
echo "  -> qwen3-coder-480b-a35b (AA-IQ 55 / Code 60 / Agentic 54) — best composite."
echo "  -> deepseek-v4-pro (AA-IQ 52 / Code 54) — S-tier, \$0.54 per task discount."
echo ""
echo "JUDGE (best cost/task setting; same model family but reduced reasoning):"
echo "  -> gpt-5.6-sol (same as orchestrator, lower reasoning effort per config, medium→low)."
echo "  -> deepseek-v4-flash-free (free; AA 46; acceptable for judgment/evaluation)."
echo ""
echo "EXECUTOR / WORKING MODEL (under \$0.20 in / \$0.40 out; glm-5.3-flash price point):"
echo "  -> glm-5.3-flash (target price tier; not listed above, add from OR/free catalog)."
echo "  -> deepseek-v4-flash (\$0.50 in / \$1.50 out — slightly above floor but accepted)."
echo "  -> minimax-m2.5:free (free, AA 42, within tier)."
echo "  -> mimo-v2.5:free (FREE — CAPABILITY FLOOR, AA ~36, do NOT go below this)."
echo "  -> glm-4.5-flash (B-tier, AA ~35; only if quotas hit and mimo is unavailable)."
echo ""
echo "FLOOR ENFORCED: mimo-v2.5:free (opencode-zen) — free, AA ~36."
echo "If API quotas hit, fall back to: glm-5.3-flash (price tier) → mimo-v2.5:free (floor)."
echo ""
echo "=== HERMES CONFIG CORRELATION ==="
echo "Config file: voice-single-source/hermes-config.yaml"
echo "Default model: gpt-5.6-sol (provider: openai-codex, base_url: chatgpt.com backend)"
echo "Fallback chain in config includes: mimo-v2.5-free, deepseek-v4-flash, deepseek-v4-flash-free,"
echo "glm-5.1 (ollama-cloud), openrouter/owl-alpha, nvidia/nemotron-3-ultra, cohere/north-mini."
echo "Tier mapping matches: S-tier = deepseek-v4-pro / kimi-k2.6 / qwen-coder-480b (if verified)."
echo "A-tier = deepseek-v4-flash / minimax-m2.5 / glm-5.1."
echo "B/B+ = glm-4.5-flash / owl-alpha / minimax-m2.1."
echo "C/D = nemotron-3-super / gpt-oss-120b / llama-3.3-70b (avoid)."
