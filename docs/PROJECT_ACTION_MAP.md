# Project Action Map — 2026-06-19 Session
# For each project touched, lists files created/modified and remaining work.
# Intent: one place to see what was done and what's still open.

---

## surface-fixed-event-quell

**Intent:** The tray indicator should be a "wonky shit that happens to this Surface" remediation hub.

### Files created/modified:
| File | Action | Status |
|------|--------|--------|
| `indicator.py` | Added cycle-extensions, Log SOUND/NO-SOUND, Reset BT, Safe Shutdown/Reboot, Toggle Module buttons | ✅ Done |
| `surface_fixed_event_quell.c` | Added reboot notifier (v1.3.0) to fix shutdown hang | ✅ Done |

### System files created:
| File | Action | Status |
|------|--------|--------|
| `/etc/udev/rules.d/99-bt-autofix.rules` | Auto-cycle BT when paired devices exist but none connect | ✅ Done |
| `/usr/local/bin/bt-autofix.sh` | BT auto-fix script (triggered by udev) | ✅ Done |
| `/usr/lib/systemd/system-shutdown/aaa-memory-cleanup.sh` | Unload quell module before power-off | ✅ Done |
| `~/.config/systemd/user/aaa-memory-sound-monitor.*` | Periodic sound detector (IRQ9 + audio-reset monitoring) | ✅ Done |

### Remaining:
- [ ] None — all Surface issues addressed

---

## custom-skills/git-audit-sync

**Intent:** Fully automated git audit/sync tool with sub-agent architecture.

### Files created/modified:
| File | Action | Status |
|------|--------|--------|
| `SKILL.md` | Created with progressive disclosure, workflow decision tree, all flags documented | ✅ Done |
| `scripts/audit_sync.py` | Full automation: discover, classify, commit, push, pull with parallel workers | ✅ Done |

### Zsh functions added (in `~/.zshrc`):
| Function | Action | Status |
|----------|--------|--------|
| `repo-status` | Full single-repo report (status, logs, ahead/behind, actionable tips) | ✅ Done |
| `repo-scan` | Multi-repo scan with `--fix`, `--dry-run`, `--table`, `--push` flags | ✅ Done |
| `repo-scan --fix` | Auto-remediate all repos (commit, push, pull) with backup branches | ✅ Done |
| `recent` | Find recently modified files (fd-based) | ✅ Done |
| `whatschanged` | Show repos with recent activity | ✅ Done |
| `real-age` | Show newest file's mtime in a project tree | ✅ Done |

### Remaining:
- [ ] Add Pi model check at start of repo-scan (reads ~/.pi/agent/settings.json)
- [ ] REMEDIATION_PLAN.md appends with reposcan marker on subsequent runs

---

## crash-guard

**Intent:** Utility scripts for Surface remediation and system maintenance.

### Files created/modified:
| File | Action | Status |
|------|--------|--------|
| `scripts/sound-monitor.sh` | Periodic ACPI IRQ check + audio-reset logging (systemd timer) | ✅ Done |
| `scripts/mtime-sync.sh` | Periodic mtime sync for file browser accuracy | ✅ Done |
| `scripts/mtime-watcher.sh` | (Deprecated — inotify approach didn't work on Surface kernel) | ❌ Removed |

### Remaining:
- [ ] None — scripts are functional

---

## model-scan

**Intent:** Model scoring engine → Hermes config optimization. This session identified 14 new tasks.

### Files created/modified this session:
| File | Action | Status |
|------|--------|--------|
| `docs/RAW_USER_PROMPTS_2026-06-19.md` | Full verbatim capture of all 69 user prompts | ✅ Done |
| `docs/SESSION_DATA_2026-06-19.md` | Distilled data, observations, and 14 tasks | ✅ Done |
| `docs/PROJECT_ACTION_MAP.md` | This file — cross-project action map | ✅ Done |
| `docs/CALIBRATION_PLAN.md` | Phase 3 plan (needs fabricated-claim cleanup) | 🟡 Needs cleanup |
| `TODO.md` | Updated with Phase 3 tasks | ✅ Done |
| `empirical_observations.md` | User observations (superseded by SESSION_DATA) | 🟡 Can archive |
| `docs/SESSION_TASKS_2026-06-19.md` | Initial task capture (superseded by SESSION_DATA) | 🟡 Can archive |

### Files that need to be CREATED (from session tasks):

#### P0 — Must build first
| File | What it does | Prompt ref |
|------|-------------|------------|
| `scoring/arch_predictor.py` | Conditional scoring: estimate AI Index from arch type + params + release date when AA data is missing | P62 |
| `cli_overall.py` | `model-scan overall -a --free` CLI command returning best model for tier | P62 |

#### P1 — Core improvements
| File | What it does | Prompt ref |
|------|-------------|------------|
| `scoring/sentiment.py` | Scrape X/Reddit for "feels like" comparisons with region tags | P62 |
| `scoring/paper_benchmarks.py` | Extract benchmark tables from Chinese model papers (Kimi 2.6, GLM 5.2, Qwen 3.7, MiniMax M3) | P62 |
| `scoring/reliability_calibration.py` | Cross-reference model scores with real API error logs | P62 |

#### P2 — Nice to have
| File | What it does | Prompt ref |
|------|-------------|------------|
| `empirical_adjustments.json` | "Magic" factor tracking — over/underperformance deltas per model | P62 |
| `benchmarks/` directory | Scraped benchmark data from paper-referenced sources | P62 |

### Files that may need cleanup:
| File | Issue | Action |
|------|-------|--------|
| `docs/CALIBRATION_PLAN.md` | Lines 12-13, 49, 52 contain fabricated sentiment claims | Remove or mark as unverified |
| `docs/SESSION_TASKS_2026-06-19.md` | Superseded by SESSION_DATA (more complete) | Archive or delete |
| `empirical_observations.md` | Superseded by SESSION_DATA (consolidated) | Archive or delete |

### Cross-reference: user services to configure in Hermes slots
Available services (from prompts 32, 36):
- $20/mo: Anthropic, OpenAI, Google, Perplexity
- $10/mo: Opencode Go (~$50 usage + free models even when depleted)
- Free quota: Groq, Cerebras, NVIDIA NIM, Ollama Cloud, Opencode Zen
- Antigravity: Opus 4.7 (via Gemini, restricted to Antigravity CLI only)
- OpenRouter: free tier models

---

## aaa-memory

**Intent:** Multi-tier memory system for AI agent sessions. All 89 tasks completed, 49 tests passing.

### Remaining:
- [ ] Wire agent integrations (Claude hooks exist but not registered with ClawMem)
- [ ] Headless session testing with real agent runs
- [ ] Hermes MemoryProvider was stubbed but never activated

---

## Hermes config (~/Downloads/config.yaml)

**Intent:** Optimized Hermes configuration using scored model data.

### Status:
| File | Action | Status |
|------|--------|--------|
| `~/Downloads/config.yaml` | Draft with full service inventory and slot definitions | 🟡 Needs benchmark validation |

### Remaining:
- [ ] Validate model rankings with AA scores before deploying
- [ ] Confirm Opus 4.7 accessibility via Antigravity (user says it's restricted)
- [ ] Slot weights need calibration (currently guessed)

---

## .zshrc

### Aliases/functions added this session:
| Function | Purpose |
|----------|---------|
| `acpi-indicator-restart` | Restart tray indicator (fixed path) |
| `sqc` | Cycle GNOME extensions (sound fix) |
| `sqi` | Shorthand for indicator restart |
| `sqbt` | Reset Bluetooth |
| `sqoff` | Safe shutdown (unloads module first) |
| `sqreboot` | Safe reboot (unloads module first) |
| `sqls` | Open sound logs folder |
| `repo-status` | Git repo status report |
| `repo-scan` | Multi-repo scan with --fix/--dry-run |
| `recent` | Find recently modified files (fd-based) |
| `whatschanged` | Show repos with recent activity |
| `real-age` | Show newest file in project tree |
| `QT_QPA_PLATFORMTHEME=gtk3` | Fixed Qt menu display under GNOME |

---

## claude-code-proxy / claude-code-proxy-old

- **Intent:** Audit old fork vs current, determine if any changes need migrating.
- **Status:** Old repo deleted. No migration needed (primary was 77 commits ahead).
- **Files:** None created.

---

## voice-agent

- **Intent:** Fix hardcoded API keys, use .env or global env vars.
- **Status:** Done. Keys stripped, .env loading added, pushed.
- **Files:** `v2/.env.example` created, `v2/echo_node/agent_profiles.py` modified.

---

## switchboard

- **Intent:** Merge feature branch changes.
- **Status:** Done. Sidebar redesign mockups + version bump pushed.
- **Files:** 21 files committed on feat/multi-sidebar-panes branch.

---

## MASTER TASK LIST (all projects)

### Highest priority (P0):
1. **model-scan**: `scoring/arch_predictor.py` — conditional scoring from arch data
2. **model-scan**: `cli_overall.py` — `model-scan overall -a --free` command
3. **Hermes config**: Validate with real scores, deploy to `~/.hermes/config.yaml`

### Medium priority (P1):
4. **model-scan**: `scoring/sentiment.py` — user sentiment pipeline with region tags
5. **model-scan**: `scoring/paper_benchmarks.py` — find papers, extract benchmarks
6. **model-scan**: `scoring/reliability_calibration.py` — calibrate against error logs
7. **Hermes config**: Verify Antigravity Opus 4.7 access restrictions
8. **aaa-memory**: Wire agent integrations (Claude, Hermes, Codex hooks)

### Lower priority (P2):
9. **model-scan**: `empirical_adjustments.json` — magic factor tracking
10. **Hermes config**: Slot weight calibration
