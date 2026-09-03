"""Adapter interface — D2.3 (gap G3).

adapter_id names the package that knows how to invoke a binding. The adapter
owns the command line; callers name only a lane.

Two implementations prove the abstraction:
  - OMPAdapter  (in-harness, e.g. omp -p --model <provider/model> --cwd ...)
  - AgyAdapter  (exo-harness, e.g. agy --model <model> -p ...)

Acceptance: renaming a model in registry data requires no change to any prompt
artifact and no change to any component source. The adapter resolves lane →
invocation at runtime from registry data.

Caller API:
    adapter = get_adapter(adapter_id)  # e.g. "omp", "agy"
    cmd = adapter.build_command(binding, prompt)
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable
import shlex


@runtime_checkable
class Adapter(Protocol):
    adapter_id: str

    def build_command(self, binding: dict, prompt: str, cwd: str | None = None) -> list[str]:
        """Return argv that would invoke the binding for the prompt."""
        ...

    def describe(self) -> str:
        ...


class OMPAdapter:
    """In-harness adapter: omp -p --model <model>"""

    adapter_id = "omp"

    def build_command(self, binding: dict, prompt: str, cwd: str | None = None) -> list[str]:
        # model_id may be "unknown" -> caller should have blocked, but we emit a safe sentinel
        model = binding.get("model_id", "unknown")
        provider = binding.get("provider", "unknown")
        # Map provider+model to omp model identifier without hardcoding model names.
        # Convention: provider is already the omp model prefix where needed.
        if provider not in ("unknown", None) and "/" not in str(model):
            omp_model = f"{provider}/{model}" if provider.startswith("opencode") else str(model)
        else:
            omp_model = str(model)
        cmd = ["omp", "-p", "--model", omp_model]
        if cwd:
            cmd += ["--cwd", cwd]
        # Prompt is passed as positional arg per omp contract; avoid shell injection
        cmd += [prompt]
        return cmd

    def describe(self) -> str:
        return "omp in-harness adapter (opencode-go/zen via omp)"


class AgyAdapter:
    """Exo-harness adapter: agy --model <model> -p"""

    adapter_id = "agy"

    def build_command(self, binding: dict, prompt: str, cwd: str | None = None) -> list[str]:
        model = binding.get("model_id", "unknown")
        # agy model id is provider-agnostic in this harness
        cmd = ["agy", "--model", str(model), "-p", prompt]
        return cmd

    def describe(self) -> str:
        return "agy exo-harness adapter (codex/agy family)"


_REGISTRY: dict[str, Adapter] = {
    OMPAdapter.adapter_id: OMPAdapter(),
    AgyAdapter.adapter_id: AgyAdapter(),
}


def get_adapter(adapter_id: str) -> Adapter:
    try:
        return _REGISTRY[adapter_id]
    except KeyError:
        raise KeyError(f"unknown adapter_id {adapter_id!r}; known: {sorted(_REGISTRY)}")


def list_adapters() -> list[str]:
    return sorted(_REGISTRY.keys())


def shell_preview(binding: dict, prompt: str = "hello") -> str:
    """Human-readable shell command for table/debug output."""
    adapter = get_adapter(binding.get("adapter_id", ""))
    return shlex.join(adapter.build_command(binding, prompt))
