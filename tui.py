"""
model-scan — Textual TUI

Keyboard-driven terminal UI with:
  - Model list (sortable, filterable)
  - Model detail pane (benchmarks, slots, scores)
  - Compare mode (up to 4 models side-by-side)
  - Search/filter system
  - Config patch preview

Keyboard:
  ↑/↓           Navigate model list
  /             Search
  s             Cycle sort
  c             Add to compare / show compare
  f             Cycle qualification filter
  t             Cycle tier filter
  Tab           Focus shift
  q / Esc       Quit
  Enter         Open detail
  v             Toggle compact/comfortable
  p             Preview config patch
  r             Refresh
  1-9           Quick slot view
  ?             Help overlay
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Input, Button, RichLog, DataTable, SelectionList
from textual.widget import Widget
from textual import events


CONFIG_DIR = Path.home() / ".config" / "model-scan"
DB_PATH = CONFIG_DIR / "model_scan.db"
SLOTS_PATH = CONFIG_DIR / "slot_definitions.yaml"


TIER_COLORS = {
    "S": "bold yellow",
    "A": "bold green",
    "B": "bold cyan",
    "C": "gray",
    "—": "dim",
}


@dataclass
class ModelSummary:
    model_id: str
    provider: str
    tps: float
    latency_s: float
    tier: str
    ai_index: float | None
    composite: float
    has_tools: bool
    accessible: bool


def load_models() -> list[dict]:
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


def load_slot_defs() -> dict:
    if not SLOTS_PATH.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(open(SLOTS_PATH)) or {}
    except Exception:
        return {}


def load_slots_for_model(model_id: str, models: list[dict]) -> list[dict]:
    """Get slot fitness for a specific model."""
    m = next((m for m in models if m.get("model_id") == model_id), None)
    if not m:
        return []
    # Read from database
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT MAX(scan_id) FROM scans")
    scan_id = cur.fetchone()[0]
    if scan_id:
        cur = conn.execute(
            "SELECT slot_id, fitness FROM slot_fitness WHERE scan_id = ? AND model_id = ?",
            (scan_id, model_id)
        )
        rows = [{"slot_id": r["slot_id"], "fitness": r["fitness"]} for r in cur.fetchall()]
        conn.close()
        return rows
    conn.close()
    return []


# ─────────────────────────────────────────────────────────────────────────────
# WIDGETS
# ─────────────────────────────────────────────────────────────────────────────

class ModelListItem(ListItem):
    """A single model in the list view."""
    
    def __init__(self, model: dict, index: int, compact: bool = False):
        super().__init__()
        self.model_data = model
        self.idx = index
        self.compact_mode = compact
    
    def compose(self) -> ComposeResult:
        tier = self.model_data.get("tier", "—")
        tc = TIER_COLORS.get(tier, "dim")
        model_id = self.model_data.get("model_id", "?")
        provider = self.model_data.get("provider", "?")
        tps = self.model_data.get("tps", 0) or 0
        composite = self.model_data.get("composite", 0) or 0
        ai = self.model_data.get("ai_index")
        ai_str = f"[dim]AA=[/]{ai:.0f}" if ai else ""
        
        # Provenance tag
        has_probe = "🔬" if (self.model_data.get("tps") or 0) > 0 else ""
        has_bench = "📈" if (self.model_data.get("benchmark_swe_verified") or 0) > 0 else ""
        prov = f"{has_probe}{has_bench}" if (has_probe or has_bench) else "[dim]·[/]"
        
        if self.compact_mode:
            yield Label(
                f"{prov} [dim]#{self.idx + 1:2d}[/] [{tc}]{tier}[/]  "
                f"{model_id[:34]:34s} "
                f"[dim]{provider[:14]:14s}[/] "
                f"[bold]{tps:>5.0f}[/] tps  "
                f"[dim]{composite:>5.1f}[/]  {ai_str}"
            )
        else:
            yield Label(
                f"  {prov}  [dim]#{self.idx + 1:2d}[/]  [{tc}]{tier:^5}[/]  "
                f"[bold]{model_id[:40]:40s}[/]  "
                f"[dim]{provider[:18]:18s}[/]  "
                f"[bold]{tps:>6.0f}[/] [dim]tps[/]  "
                f"{composite:>5.1f}  {ai_str}"
            )
    
    def on_click(self):
        self.app.post_message(self.app.ModelSelected(self.model_data))


class ModelDetail(Static):
    """Right-panel model detail view."""
    
    def __init__(self):
        super().__init__()
        self.current_model: dict | None = None
    
    def set_model(self, m: dict | None):
        self.current_model = m
        if m:
            self.update(self._render(m))
        else:
            self.update("[dim]Select a model to see details[/]")
    
    def _render(self, m: dict) -> str:
        tier = m.get("tier", "—")
        tc = TIER_COLORS.get(tier, "dim")
        lines = [
            f"[bold]{m['model_id']}[/]",
            f"[dim]{m.get('provider', '?')}[/]",
            f"",
            f"[{tc}]Tier: {tier}[/]",
            f"TPS:  [bold]{m.get('tps', 0):.0f}[/]  Latency: {m.get('latency_s', 0):.1f}s",
            f"Tools: {'[green]✓[/]' if m.get('has_tools') else '[dim]·[/]'}  "
            f"Vision: {'[green]✓[/]' if m.get('has_vision_capability') else '[dim]·[/]'}",
        ]
        ai = m.get("ai_index")
        if ai:
            lines.append(f"AA Index: {ai:.0f}")
        comp = m.get("composite", 0)
        if comp:
            lines.append(f"Composite: {comp:.1f}")
        sw = m.get("benchmark_swe_verified")
        if sw:
            lines.append(f"SWE-Verified: [bold]{sw:.0f}%[/]")
        
        # Popularity score
        try:
            from analysis.popularity import for_model as pop_for
            pop = pop_for(m.get("model_id", "") or m.get("model", ""))
            if pop is not None:
                bar = "█" * int(pop / 5) + "░" * (20 - int(pop / 5))
                lines.append(f"[bold]Popularity:[/] {bar} [dim]{pop:.0f}/100[/]")
        except ImportError:
            pass
        
        # Provenance tags
        prov_parts = []
        if (m.get("tps") or 0) > 0:
            prov_parts.append("[cyan]🔬 Live[/]")
        if (m.get("benchmark_swe_verified") or 0) > 0:
            prov_parts.append("[yellow]📈 Bench[/]")
        if ai:
            prov_parts.append("[blue]📊 AA[/]")
        if prov_parts:
            lines.append(f"[dim]Data:[/] {' '.join(prov_parts)}")
        
        # Slot fitness
        slots = load_slots_for_model(m.get("model_id", ""), [m])
        if slots:
            lines.append(f"")
            lines.append(f"[bold]Slot Fitness:[/]")
            for s in sorted(slots, key=lambda x: -x["fitness"]):
                lines.append(f"  {s['slot_id']}: {s['fitness']:.1f}")
        
        return "\n".join(lines)


class ComparePanel(Static):
    """Side-by-side model comparison."""
    
    def __init__(self):
        super().__init__()
        self.models: list[dict] = []
    
    def add_model(self, m: dict) -> bool:
        if len(self.models) >= 4:
            return False
        if any(m2.get("model_id") == m.get("model_id") for m2 in self.models):
            return False
        self.models.append(m)
        self._refresh()
        return True
    
    def clear(self):
        self.models.clear()
        self.update("")
    
    def _refresh(self):
        if not self.models:
            self.update("[dim]Compare mode: press [b]c[/] to add models[/]")
            return
        
        # Header row
        header = f"[bold]COMPARE — {len(self.models)} models[/]"
        for m in self.models:
            header += f"  |  [bold]{m.get('model_id', '?')[:25]}[/]"
        
        lines = [header, ""]
        
        # Metrics rows
        metrics = [
            ("TPS", lambda m: f"{m.get('tps', 0):.0f}"),
            ("Latency", lambda m: f"{m.get('latency_s', 0):.1f}s"),
            ("Tier", lambda m: m.get('tier', '—')),
            ("AA Index", lambda m: f"{m.get('ai_index', 0):.0f}" if m.get('ai_index') else "—"),
            ("Composite", lambda m: f"{m.get('composite', 0):.1f}"),
            ("Tools", lambda m: "✓" if m.get('has_tools') else "·"),
            ("Vision", lambda m: "✓" if m.get('has_vision_capability') else "·"),
            ("SWE-V", lambda m: f"{m.get('benchmark_swe_verified', 0):.0f}%" if m.get('benchmark_swe_verified') else "—"),
        ]
        
        for name, fn in metrics:
            row = f"  [bold]{name:12s}[/]"
            for m in self.models:
                row += f"  {fn(m):>10s}"
            lines.append(row)
        
        lines.append("")
        lines.append("[dim]Press [b]C[/] to close compare[/]")
        self.update("\n".join(lines))


class StatusBar(Static):
    """Footer status bar."""
    
    def __init__(self):
        super().__init__()
        self.cron_text = " · [dim]cron: —[/]"
        self.mode_text = ""
    
    def update_status(self, models: list[dict], mode_info: str = ""):
        accessible = sum(1 for m in models if m.get("accessible"))
        total = len(models)
        providers = len(set(m.get("provider", "") for m in models))
        self.mode_text = mode_info
        self.update(
            f"  [bold]{total}[/] models · "
            f"[green]{accessible}[/] accessible · "
            f"[dim]{providers}[/] providers"
            f"{self.mode_text}"
            f"{self.cron_text}"
        )
    
    def set_cron_status(self, status: str):
        """Update cron schedule display."""
        if status:
            self.cron_text = f" · [dim]cron: {status}[/]"
        else:
            self.cron_text = " · [dim]cron: —[/]"


# ─────────────────────────────────────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────────────────────────────────────

class HelpScreen(ModalScreen):
    """Help overlay."""
    
    def compose(self) -> ComposeResult:
        yield Grid(
            Static(
                "[bold]Keyboard Shortcuts[/]\n\n"
                "↑/↓         Navigate model list\n"
                "/           Search/filter models\n"
                "s           Cycle sort order\n"
                "c           Add to compare (C to show)\n"
                "Ctrl+S      Save filtered list to file\n"
                "p / P       Cycle preset: all → free → best value → agent ready → S-tier → DeepSeek\n"
                "f           Cycle filter: all → qualified → incumbent → accessible\n"
                "t           Cycle tier filter: all → S/A/B/C/—\n"
                "Enter       Show model details\n"
                "Tab         Cycle focus panels\n"
                "v           Toggle compact/comfortable\n"
                "r           Refresh scan data\n"
                "k           Cron auto-deployment settings\n"
                "q / Esc     Quit / close panel\n"
                "1-9         Quick slot view\n"
                "?           This help\n"
                "\n[dim]Press any key to close[/]",
                id="help-text",
            ),
            id="help-dialog",
        )
    
    def on_key(self, event):
        self.dismiss()


class CronModal(ModalScreen):
    """Cron auto-deployment settings modal."""
    
    def compose(self) -> ComposeResult:
        try:
            from cron_manager import load_config
            cfg = load_config()
        except Exception:
            cfg = {"daily": {"enabled": False, "schedule": None}, "weekly": {"enabled": False, "schedule": None}}
        
        lines = []
        lines.append("[bold]Auto-Deployment Cron Settings[/]\n")
        lines.append("Configure schedules for automatic daily/weekly scans.\n")
        lines.append("Set via CLI:   dink.py --cron-set daily \"30 6 * * *\"")
        lines.append("")
        for job in ("daily", "weekly"):
            j = cfg.get(job, {})
            enabled = j.get("enabled", False)
            schedule = j.get("schedule") or "—"
            icon = "●" if enabled else "○"
            lines.append(f"  {icon} [bold]{job.title()}[/]  [dim]{schedule}[/]")
        lines.append("")
        lines.append("[dim]Press any key to close[/]")
        
        yield Grid(
            Static("\n".join(lines), id="cron-text"),
            id="cron-dialog",
        )
    
    def on_key(self, event):
        self.dismiss()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

class ModelScanTUI(App):
    """model-scan Textual TUI."""
    
    TITLE = "model-scan v5"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
    }
    
    #list-panel {
        width: 48%;
        min-width: 40;
        border-right: solid $primary;
    }
    
    #detail-panel {
        width: 27%;
        min-width: 30;
        padding: 1;
    }
    
    #compare-panel {
        width: 25%;
        min-width: 30;
        padding: 1;
        border-left: solid $secondary;
    }
    
    #status-bar {
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    #search-input {
        dock: top;
        height: 1;
        margin: 0 0 1 0;
    }
    
    .model-list {
        height: 100%;
    }
    
    #help-dialog {
        width: 50;
        height: auto;
        padding: 2;
        background: $surface;
        border: thick $primary;
    }
    
    #help-text {
        padding: 1;
    }
    
    ModelListItem {
        padding: 0 1;
    }
    ModelListItem:hover {
        background: $accent;
    }
    ModelListItem:focus {
        background: $primary 30%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("s", "cycle_sort", "Sort"),
        Binding("c", "toggle_compare", "Compare"),
        Binding("C", "toggle_compare", "Show Compare"),
        Binding("f", "cycle_filter", "Filter"),
        Binding("t", "cycle_tier_filter", "Tier"),
        Binding("v", "toggle_compact", "Compact"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("p", "cycle_preset", "Preset"),
        Binding("P", "cycle_preset", "Preset"),
        Binding("k", "show_cron", "Cron"),
        Binding("?", "show_help", "Help"),
        Binding("ctrl+s", "save_selection", "Save"),
    ]
    
    # Messages
    class ModelSelected(events.Message):
        def __init__(self, model: dict):
            super().__init__()
            self.model = model
    
    def __init__(self):
        super().__init__()
        self.models: list[dict] = []
        self.filtered_models: list[dict] = []
        self.selected_index = 0
        self.compact_view = False
        self.show_compare = False
        self.show_detail = True
        self.sort_key = "composite"
        self.sort_reverse = True
        self.filter_mode = "all"  # all, accessible, S, A, B, C
        self.preset_mode = "all"   # all, free, best_value, agent_ready, s_tier, deepseek
        self.compare_models: list[dict] = []
        self.search_text = ""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Container(
                    Input(placeholder="Search...", id="search-input"),
                    ListView(id="model-list"),
                    id="list-panel",
                ),
                ModelDetail(id="detail-panel"),
                ComparePanel(id="compare-panel"),
                id="main-container",
            ),
        )
        yield StatusBar(id="status-bar")
    
    def on_mount(self):
        self.load_data()
        self.query_one("#detail-panel").display = self.show_detail
        self.query_one("#compare-panel").display = self.show_compare
        # Load cron status in background
        self.load_cron_status()
    
    def load_data(self):
        self.models = load_models()
        self._apply_filters()
        self._refresh_list()
        self._update_status()
    
    @work(thread=True)
    def load_cron_status(self):
        """Load cron status in a background thread."""
        try:
            from cron_manager import load_config
            cfg = load_config()
            parts = []
            for job in ("daily", "weekly"):
                j = cfg.get(job, {})
                if j.get("enabled") and j.get("schedule"):
                    parts.append(f"{job[0].upper()}:{j['schedule']}")
            status = " ".join(parts) if parts else ""
            self.call_from_thread(self._update_cron_status, status)
        except Exception:
            self.call_from_thread(self._update_cron_status, "")
    
    def _update_cron_status(self, status: str):
        bar = self.query_one(StatusBar)
        bar.set_cron_status(status)
        
    def _apply_filters(self):
        lst = self.models
        
        # Search filter
        if self.search_text:
            q = self.search_text.lower()
            lst = [m for m in lst if q in (m.get("model_id", "") or "").lower() or q in (m.get("provider", "") or "").lower()]
        
        # Tier filter
        if self.filter_mode != "all":
            if self.filter_mode == "accessible":
                lst = [m for m in lst if m.get("accessible")]
            elif self.filter_mode in ("S", "A", "B", "C"):
                lst = [m for m in lst if m.get("tier") == self.filter_mode]
        
        # Preset filters (override individual filters when active)
        if self.preset_mode != "all":
            if self.preset_mode == "free":
                lst = [m for m in lst if (m.get("model_id","") or "").lower().endswith(":free") or (m.get("model_id","") or "").lower().endswith("-free") or (m.get("provider","") or "").lower() in ("groq","cerebras")]
            elif self.preset_mode == "s_tier":
                lst = [m for m in lst if m.get("tier") == "S"]
            elif self.preset_mode == "agent_ready":
                lst = [m for m in lst if m.get("has_tools") and m.get("tier") in ("S","A")]
            elif self.preset_mode == "deepseek":
                lst = [m for m in lst if "deepseek" in (m.get("model_id","") or "").lower() or "deepseek" in (m.get("model","") or "").lower()]
        
        # Sort — best_value preset uses CAI sorting
        reverse = self.sort_reverse
        if self.preset_mode == "best_value":
            lst.sort(key=lambda m: (m.get("ai_index", 0) or 0) / max((m.get("price_blended", 0) or 0.01), 0.01), reverse=True)
        elif self.sort_key == "tps":
            lst.sort(key=lambda m: m.get("tps", 0) or 0, reverse=reverse)
        elif self.sort_key == "latency_s":
            lst.sort(key=lambda m: m.get("latency_s", 999) or 999, reverse=reverse)
        elif self.sort_key == "tier":
            tier_order = {"S": 4, "A": 3, "B": 2, "C": 1, "—": 0}
            lst.sort(key=lambda m: tier_order.get(m.get("tier", "—"), 0), reverse=reverse)
        elif self.sort_key == "ai_index":
            lst.sort(key=lambda m: m.get("ai_index", 0) or 0, reverse=reverse)
        else:
            lst.sort(key=lambda m: m.get("composite", 0) or 0, reverse=True)
        
        self.filtered_models = lst
    
    def _refresh_list(self):
        lv = self.query_one("#model-list", ListView)
        lv.clear()
        for i, m in enumerate(self.filtered_models):
            lv.append(ModelListItem(m, i, compact=self.compact_view))
    
    def _update_status(self):
        status = self.query_one("#status-bar", StatusBar)
        if self.models:
            presets = {"all": "All", "free": "Free", "best_value": "Best$", "agent_ready": "Agent", "s_tier": "S-Tier", "deepseek": "DS"}
            filters = {"all": "All", "accessible": "Acc", "S": "S", "A": "A", "B": "B", "C": "C"}
            mode = f" · [{self._sort_color()}]{self.sort_key}[/]"
            mode += f" · [dim]{filters.get(self.filter_mode, self.filter_mode)}[/]"
            if self.preset_mode != "all":
                mode += f" · [bold cyan]{presets.get(self.preset_mode, self.preset_mode)}[/]"
            status.update_status(self.models, mode)
    
    def _sort_color(self) -> str:
        colors = {"composite": "yellow", "tps": "green", "latency_s": "cyan", "ai_index": "magenta", "tier": "blue"}
        return colors.get(self.sort_key, "dim")
    
    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            self.search_text = event.value
            self._apply_filters()
            self._refresh_list()
    
    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, ModelListItem):
            self.show_model_detail(item.model_data)
    
    def show_model_detail(self, model: dict):
        detail = self.query_one("#detail-panel", ModelDetail)
        detail.set_model(model)
        if not self.show_detail:
            self.show_detail = True
            detail.display = True
    
    def action_focus_search(self):
        self.query_one("#search-input", Input).focus()
    
    def action_cycle_sort(self):
        sorts = ["composite", "tps", "latency_s", "ai_index", "tier"]
        idx = sorts.index(self.sort_key) if self.sort_key in sorts else 0
        idx = (idx + 1) % len(sorts)
        self.sort_key = sorts[idx]
        self._apply_filters()
        self._refresh_list()
        self.notify(f"Sort: {self.sort_key}")
    
    def action_toggle_compare(self):
        if self.show_compare:
            self.show_compare = False
            self.query_one("#compare-panel").display = False
        else:
            self.show_compare = True
            self.query_one("#compare-panel").display = True
            # Add selected model if not already added
            if self.filtered_models and self.selected_index < len(self.filtered_models):
                m = self.filtered_models[self.selected_index]
                cp = self.query_one("#compare-panel", ComparePanel)
                cp.add_model(m)
                cp._refresh()
    
    def action_cycle_preset(self):
        """Cycle through preset filters."""
        presets = ["all", "free", "best_value", "agent_ready", "s_tier", "deepseek"]
        labels = {"all": "All Models", "free": "Free Only", "best_value": "Best Value",
                  "agent_ready": "Agent Ready", "s_tier": "S-Tier", "deepseek": "DeepSeek Fleet"}
        idx = presets.index(self.preset_mode) if self.preset_mode in presets else 0
        idx = (idx + 1) % len(presets)
        self.preset_mode = presets[idx]
        self._apply_filters()
        self._refresh_list()
        self.notify(f"Preset: {labels.get(self.preset_mode, self.preset_mode)}")
    
    def action_cycle_filter(self):
        filters = ["all", "accessible", "S", "A", "B", "C"]
        idx = filters.index(self.filter_mode) if self.filter_mode in filters else 0
        idx = (idx + 1) % len(filters)
        self.filter_mode = filters[idx]
        self._apply_filters()
        self._refresh_list()
        self.notify(f"Filter: {self.filter_mode}")
    
    def action_cycle_tier_filter(self):
        filters = ["all", "S", "A", "B", "C", "—"]
        idx = filters.index(self.filter_mode) if self.filter_mode in filters else 0
        idx = (idx + 1) % len(filters)
        self.filter_mode = filters[idx]
        self._apply_filters()
        self._refresh_list()
        self.notify(f"Tier filter: {self.filter_mode}")
    
    def action_toggle_compact(self):
        self.compact_view = not self.compact_view
        self._refresh_list()
        self.notify(f"Compact view: {'ON' if self.compact_view else 'OFF'}")
    
    def action_refresh_data(self):
        self.load_data()
        self.notify("Data refreshed")
    
    def action_show_help(self):
        self.push_screen(HelpScreen())
    
    def action_show_cron(self):
        self.push_screen(CronModal())
    
    def action_save_selection(self):
        """Save filtered model list to a timestamped file."""
        if not self.filtered_models:
            self.notify("No models to save", severity="error")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = CONFIG_DIR / f"tui_export_{ts}.json"
        data = [
            {"model_id": m.get("model_id"), "provider": m.get("provider"),
             "tier": m.get("tier"), "composite": m.get("composite"),
             "tps": m.get("tps"), "ai_index": m.get("ai_index")}
            for m in self.filtered_models
        ]
        out.write_text(json.dumps(data, indent=2))
        self.notify(f"Saved {len(data)} models to {out.name}")
    
    def on_key(self, event):
        if event.key == "enter" and self.filtered_models:
            idx = self.selected_index
            if idx < len(self.filtered_models):
                self.show_model_detail(self.filtered_models[idx])
        
        # Numeric for slot switching
        if event.key in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            slot_idx = int(event.key) - 1
            slots = load_slot_defs()
            slot_ids = list(slots.keys())
            if slot_idx < len(slot_ids):
                sid = slot_ids[slot_idx]
                self.notify(f"Slot: {sid}")
        
        # Tab cycling
        if event.key == "tab":
            panels = [
                self.query_one("#search-input", Input),
                self.query_one("#model-list", ListView),
                self.query_one("#detail-panel", ModelDetail),
                self.query_one("#compare-panel", ComparePanel),
            ]
            panels = [p for p in panels if p.display]
            current = self.focused or panels[0]
            idx = next((i for i, p in enumerate(panels) if p is current or p.id == current.parent.id if current and hasattr(current, 'id')), -1)
            if idx >= 0:
                next_idx = (idx + 1) % len(panels)
                if next_idx == 0:
                    panels[0].focus()
            else:
                panels[0].focus()


def main():
    app = ModelScanTUI()
    app.run()


if __name__ == "__main__":
    main()
