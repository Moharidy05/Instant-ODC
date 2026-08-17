from __future__ import annotations

from src.ai.fallback_router import get_router


def generate_with_gemini(prompt: str, system_instruction: str, temperature: float = 0.2) -> str:
    return get_router().generate(prompt, system_instruction=system_instruction, temperature=temperature)
