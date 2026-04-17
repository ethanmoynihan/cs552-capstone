from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Protocol
from llama_cpp import Llama

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


class LlamaCppLatexGenerator:
    """Real inference via llama-cpp-python against a local GGUF."""

    def __init__(self) -> None:
        """Load the GGUF weights onto Metal and read in the system prompts."""


        if not settings.llama_gguf_path.exists():
            raise FileNotFoundError(
                f"GGUF weights not found at {settings.llama_gguf_path}. "
                "Download the model or adjust LLAMA_GGUF_PATH."
            )

        self._system_generate = (PROMPTS_DIR / "generate.txt").read_text().strip()
        self._system_edit = (PROMPTS_DIR / "edit.txt").read_text().strip()

        self._llm = Llama(
            model_path=str(settings.llama_gguf_path),
            n_ctx=settings.llama_n_ctx,
            n_gpu_layers=settings.llama_n_gpu_layers,
            verbose=False,
        )

    def generate(self, text: str) -> tuple[str, int, int]:
        """
        Generate a LaTeX equation from natural language text.

        Args:
            text: The natural language text to generate a LaTeX equation from.

        Returns:
            A tuple containing the LaTeX equation, the number of tokens used, and the inference time in milliseconds.
        """
        return self._chat(self._system_generate, text)

    def edit(self, current_latex: str, edit_command: str) -> tuple[str, int, int]:
        """
        Edit a LaTeX equation using natural language instructions.

        Args:
            current_latex: The current LaTeX equation to edit.
            edit_command: The natural language instruction to edit the LaTeX equation.

        Returns:
            A tuple containing the edited LaTeX equation, the number of tokens used, and the inference time in milliseconds.
        """
        user = f"Current LaTeX: {current_latex}\nEdit instruction: {edit_command}"
        return self._chat(self._system_edit, user)

    def _chat(self, system: str, user: str) -> tuple[str, int, int]:
        """Run a single chat completion and return (cleaned_latex, tokens_used, elapsed_ms)."""
        start = time.perf_counter()
        resp = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=settings.llama_max_new_tokens,
            temperature=settings.llama_temperature,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        raw = resp["choices"][0]["message"]["content"]
        tokens_used = int(resp.get("usage", {}).get("completion_tokens", 0))
        return _clean_latex(raw), tokens_used, elapsed_ms


def _clean_latex(raw: str) -> str:
    """Strip common mistakes the model makes: $ wrappers, code fences, stray prose."""
    s = raw.strip()
    # fenced code blocks: ```latex ... ``` or ``` ... ```
    fence = re.match(r"^```(?:latex|tex)?\s*(.*?)\s*```$", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    # dollar-sign wrappers
    if s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    # \[ ... \] wrappers
    if s.startswith(r"\[") and s.endswith(r"\]"):
        s = s[2:-2].strip()
    return s


_generator: LatexGenerator | None = None


def get_generator() -> LatexGenerator:
    global _generator
    if _generator is None:
        _generator = StubLatexGenerator() if settings.use_stub_llama else LlamaCppLatexGenerator()
    return _generator


def warm_generator() -> None:
    """Call at app startup to pay the model-load cost up front."""
    get_generator()
