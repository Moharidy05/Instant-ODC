from __future__ import annotations

from src.ai.gemini_client import generate_with_gemini


def generate_text(prompt: str, system_instruction: str, temperature: float = 0.2) -> str:
    return generate_with_gemini(prompt, system_instruction, temperature)
