"""Prompt injection detection for LLM inputs.

Scans user-provided text (resumes, JDs, manual input) for
injection patterns before sending to LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InjectionScanResult:
    is_safe: bool
    threats: list[dict[str, str]]  # [{pattern, matched_text, severity}]


INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?previous\s+instructions", "high", "instruction_override"),
    (r"system\s*:", "medium", "system_prompt_injection"),
    (r"<\|im_start\|>", "high", "chat_template_injection"),
    (r"\[INST\]", "high", "llama_template_injection"),
    (r"<<SYS>>", "high", "llama_system_injection"),
    (r"```\s*tool_call", "high", "tool_call_injection"),
    (r"you\s+are\s+now\s+", "medium", "role_override"),
    (r"act\s+as\s+(a|an)\s+", "low", "role_assignment"),
    (r"new\s+instructions?\s*:", "high", "instruction_injection"),
    (r"forget\s+(everything|all|your)", "high", "memory_wipe"),
    (r"do\s+not\s+follow\s+(your|the)\s+", "high", "instruction_override"),
    (r"override\s+(safety|security|content)", "high", "safety_bypass"),
    (r"jailbreak", "high", "jailbreak_attempt"),
    (r"DAN\s+mode", "high", "jailbreak_attempt"),
    (r"developer\s+mode\s+enabled", "high", "jailbreak_attempt"),
]


class PromptGuard:
    def __init__(self, extra_patterns: list[tuple[str, str, str]] | None = None):
        self._patterns = list(INJECTION_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)
        self._compiled = [
            (re.compile(p, re.IGNORECASE), sev, name) for p, sev, name in self._patterns
        ]

    def scan(self, text: str) -> InjectionScanResult:
        threats = []
        for pattern, severity, name in self._compiled:
            match = pattern.search(text)
            if match:
                threats.append(
                    {
                        "pattern": name,
                        "matched_text": match.group()[:100],
                        "severity": severity,
                    }
                )

        is_safe = not any(t["severity"] == "high" for t in threats)
        if threats:
            logger.warning(
                "Prompt injection detected", threat_count=len(threats), high_severity=not is_safe
            )
        return InjectionScanResult(is_safe=is_safe, threats=threats)

    def sanitize(self, text: str) -> str:
        """Remove detected injection patterns from text."""
        result = text
        for pattern, severity, _name in self._compiled:
            if severity == "high":
                result = pattern.sub("[REDACTED]", result)
        return result


prompt_guard = PromptGuard()
