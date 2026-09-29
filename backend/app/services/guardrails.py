"""Input screening for prompt injection and policy-bypass attempts.

Defence in depth: even if something slips past these patterns, the LLM
cannot change the outcome, because the policy engine decides from DB facts.
"""
import re
from dataclasses import dataclass, field

MAX_LEN = 2000

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier)?\s*(instructions|rules|policy|policies)",
    r"disregard\s+(the\s+|your\s+)?(instructions|rules|policy)",
    r"system\s*prompt",
    r"you\s+are\s+now",
    r"act\s+as\s+(an?\s+)?(admin|administrator|developer|manager)",
    r"developer\s+mode|jailbreak|\bDAN\b",
    r"(override|bypass)\s+(the\s+)?(policy|rules|system)",
    r"approve\s+(this|it|my\s+refund)\s+(anyway|regardless|no\s+matter)",
    r"</?\s*(system|assistant|instructions?|customer_message)\s*>",
    r"\b(i\s+am|i'm)\s+(an?\s+)?(admin|administrator|manager|staff)\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


@dataclass
class ScreenResult:
    text: str
    flags: list = field(default_factory=list)

    @property
    def injection_suspected(self) -> bool:
        return any(f.startswith("injection") for f in self.flags)


def screen(message: str) -> ScreenResult:
    flags = []
    text = message.replace("\x00", "").strip()
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN]
        flags.append("truncated")
    for pattern in _COMPILED:
        if pattern.search(text):
            flags.append(f"injection:{pattern.pattern[:40]}")
    return ScreenResult(text=text, flags=flags)


def wrap_untrusted(text: str) -> str:
    """Delimit customer text so the model treats it as data, not instructions."""
    safe = text.replace("<", "&lt;").replace(">", "&gt;")
    return f"<customer_message>\n{safe}\n</customer_message>"
