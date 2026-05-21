#!/usr/bin/env bash
# install.sh — Install model-scan to ~/.local/bin
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.local/bin/model-scan"

echo "Installing model-scan..."
echo "  Source: $SCRIPT_DIR/model-scan"
echo "  Target: $TARGET"

# Check dependencies
echo ""
echo "Checking dependencies..."

missing=()
for cmd in python3; do
    if ! command -v "$cmd" &>/dev/null; then
        missing+=("$cmd")
    fi
done

# Check Python packages
python3 -c "import httpx" 2>/dev/null || missing+=("python3-httpx")
python3 -c "import rich" 2>/dev/null || missing+=("python3-rich")
python3 -c "import dotenv" 2>/dev/null || missing+=("python3-dotenv")

if [ ${#missing[@]} -gt 0 ]; then
    echo "  Missing dependencies: ${missing[*]}"
    echo "  Install with: pip install --user httpx rich python-dotenv"
    echo ""
    read -p "Install missing packages now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install --user httpx rich python-dotenv
    else
        echo "  Skipping. Install manually before running model-scan."
    fi
else
    echo "  All dependencies found."
fi

# Copy script
cp "$SCRIPT_DIR/model-scan" "$TARGET"
chmod +x "$TARGET"

echo ""
echo "Installed to $TARGET"
echo ""
echo "Usage:"
echo "  model-scan                    # Scan all configured providers"
echo "  model-scan --provider groq    # Scan only Groq"
echo "  model-scan --working-only     # Show only healthy models"
echo "  model-scan --json             # Output JSON"
echo ""
echo "Required API keys (set in ~/.hermes/.env or shell):"
echo "  OPENROUTER_API_KEY     — OpenRouter (free models)"
echo "  CEREBRAS_API_KEY       — Cerebras"
echo "  GROQ_API_KEY           — Groq"
echo "  NVIDIA_API_KEY         — NVIDIA NIM"
echo "  OPENCODE_GO_API_KEY    — OpenCode Go"
echo ""
echo "Optional:"
echo "  AA_API_KEY             — Artificial Analysis (for live AA scores)"
