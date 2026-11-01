"""B10 integration quality gates and seven-day E2E report."""

from .detectors import (
    detect_director_overreach,
    detect_duplicate_dialogue,
    detect_fact_conflicts,
    detect_npc_omniscience,
    detect_prompt_injection,
    detect_public_projection_leak,
    detect_world_write_intents,
    run_release_gates,
)
from .e2e import run_seven_day_e2e

__all__ = [
    "detect_director_overreach",
    "detect_duplicate_dialogue",
    "detect_fact_conflicts",
    "detect_npc_omniscience",
    "detect_prompt_injection",
    "detect_public_projection_leak",
    "detect_world_write_intents",
    "run_release_gates",
    "run_seven_day_e2e",
]
