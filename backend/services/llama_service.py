from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from config import settings

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LatexGenerator(Protocol):
    def generate(self, text: str) -> tuple[str, int, int]: ...
    def edit(self, current_latex: str, edit_command: str) -> tuple[str, int, int]: ...


class StubLatexGenerator:
    """Phase 1 stand-in. Returns canned LaTeX so the pipeline works without the 8B model."""

    def __init__(self) -> None:
        """Read in the system prompts for generation and editing."""
        self._system_generate = (PROMPTS_DIR / "generate.txt").read_text().strip()
        self._system_edit = (PROMPTS_DIR / "edit.txt").read_text().strip()

    def generate(self, text: str) -> tuple[str, int, int]:
        """
        Generate a LaTeX equation from natural language text.

        Args:
            text: The natural language text to generate a LaTeX equation from.

        Returns:
            A tuple containing the LaTeX equation, the number of tokens used, and the inference time in milliseconds.
        """
        start = time.perf_counter()
        latex = _stub_latex_for(text)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return latex, len(latex.split()), elapsed_ms

    def edit(self, current_latex: str, edit_command: str) -> tuple[str, int, int]:
        """
        Edit a LaTeX equation using natural language instructions.

        Args:
            current_latex: The current LaTeX equation to edit.
            edit_command: The natural language instruction to edit the LaTeX equation.

        Returns:
            A tuple containing the edited LaTeX equation, the number of tokens used, and the inference time in milliseconds.
        """
        start = time.perf_counter()
        latex = f"{current_latex}  % edit: {edit_command}"
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return latex, len(latex.split()), elapsed_ms


def _stub_latex_for(text: str) -> str:
    lowered = text.lower().strip()
    if "integral" in lowered:
        return r"\int_{0}^{\infty} e^{-x^{2}} \, dx"
    if "squared" in lowered or "^2" in lowered:
        return r"x^{2} + 2x - 5 = 0"
    if "fraction" in lowered or "over" in lowered:
        return r"\frac{a}{b}"
    return r"E = mc^{2}"


_generator: LatexGenerator | None = None


def get_generator() -> LatexGenerator:
    global _generator
    if _generator is None:
        if settings.use_stub_llama:
            _generator = StubLatexGenerator()
        else:
            raise NotImplementedError(
                "Real LLaMA inference not wired yet. Set USE_STUB_LLAMA=true or add the "
                "transformers-backed implementation."
            )
    return _generator
