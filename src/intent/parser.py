from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedIntent:
    """Structured representation of parsed natural language intent."""
    intent: str
    confidence: float
    parameters: dict[str, Any] = field(default_factory=dict)
    risk: str = "low"
    clarification_needed: bool = False
    clarification_prompt: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "parameters": self.parameters,
            "risk": self.risk,
            "clarification_needed": self.clarification_needed,
            "clarification_prompt": self.clarification_prompt,
            "error": self.error,
        }


class IntentParser:
    """
    AgenticOS Intent Intelligence Layer.

    Converts natural language input into structured intent objects.
    Supports single-intent extraction, parameter extraction,
    prompt-injection / safety filtering, and composite command decomposition.
    """

    # Patterns indicating potentially malicious instructions or prompt injections
    SUSPICIOUS_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"system\s+override", re.IGNORECASE),
        re.compile(r"drop\s+database", re.IGNORECASE),
        re.compile(r"rm\s+-rf\s+/", re.IGNORECASE),
        re.compile(r";\s*rm\b", re.IGNORECASE),
        re.compile(r"format\s+[a-z]:", re.IGNORECASE),
        re.compile(r"\b(sudo\s+su|chmod\s+777)\b", re.IGNORECASE),
    ]

    def __init__(self) -> None:
        pass

    def check_safety(self, text: str) -> str | None:
        """Return warning reason if text matches prompt-injection patterns, else None."""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.search(text):
                return f"Potentially malicious instruction or prompt injection detected: {pattern.pattern}"
        return None

    def parse(self, text: str) -> ParsedIntent:
        """Parse natural language into a single primary structured intent."""
        if not isinstance(text, str) or not text.strip():
            return ParsedIntent(
                intent="unknown",
                confidence=0.0,
                error="Prompt is empty or not a string.",
            )

        cleaned = text.strip()

        # Security & prompt injection guard
        safety_violation = self.check_safety(cleaned)
        if safety_violation:
            return ParsedIntent(
                intent="blocked",
                confidence=1.0,
                risk="critical",
                error=safety_violation,
            )

        lower = cleaned.lower()

        # 1. Browser & application launch
        if any(keyword in lower for keyword in ["open browser", "launch browser", "open chrome", "browse to", "open web"]):
            url = "https://www.google.com"
            url_match = re.search(r"https?://[^\s]+", cleaned)
            if url_match:
                url = url_match.group(0)
            elif "to " in lower:
                potential = cleaned.split("to ", 1)[-1].strip()
                if "." in potential and not potential.startswith("http"):
                    url = f"https://{potential}"
            return ParsedIntent(
                intent="open_browser",
                confidence=0.95,
                parameters={"url": url},
                risk="low",
            )

        # 2. File creation
        create_match = re.search(
            r"(?:create|make|write)\s+(?:a\s+)?(?:new\s+)?(?:file|folder|dir|directory)\s+(?:called\s+|named\s+)?['\"]?([^'\"\s]+)['\"]?(?:\s+with\s+(?:content|text)\s+['\"]?([^'\"]*)['\"]?)?",
            cleaned,
            re.IGNORECASE,
        )
        if create_match:
            path = create_match.group(1).strip()
            content = (create_match.group(2) or "").strip()
            return ParsedIntent(
                intent="create_file",
                confidence=0.9,
                parameters={"path": path, "content": content},
                risk="low",
            )

        # Simpler file create patterns
        if lower.startswith("create file ") or lower.startswith("make file "):
            parts = cleaned.split(maxsplit=2)
            if len(parts) >= 3:
                path = parts[2].strip().strip("'\"")
                return ParsedIntent(
                    intent="create_file",
                    confidence=0.85,
                    parameters={"path": path, "content": ""},
                    risk="low",
                )

        # 3. Read file
        read_match = re.search(
            r"(?:read|cat|view|show|display)\s+(?:file\s+)?['\"]?([^'\"\s]+)['\"]?",
            cleaned,
            re.IGNORECASE,
        )
        if read_match and not any(term in lower for term in ["cpu", "memory", "system", "usage", "telemetry", "status"]):
            path = read_match.group(1).strip()
            return ParsedIntent(
                intent="read_file",
                confidence=0.85,
                parameters={"path": path},
                risk="low",
            )

        # 4. Write / update file
        write_match = re.search(
            r"(?:update|overwrite|write\s+to)\s+(?:file\s+)?['\"]?([^'\"\s]+)['\"]?\s+(?:with\s+)?['\"]?([^'\"]*)['\"]?",
            cleaned,
            re.IGNORECASE,
        )
        if write_match:
            path = write_match.group(1).strip()
            content = write_match.group(2).strip()
            return ParsedIntent(
                intent="write_file",
                confidence=0.85,
                parameters={"path": path, "content": content},
                risk="medium",
            )

        # 5. Delete file
        delete_match = re.search(
            r"(?:delete|remove|rm|unlink)\s+(?:file\s+)?['\"]?([^'\"\s]+)['\"]?",
            cleaned,
            re.IGNORECASE,
        )
        if delete_match:
            path = delete_match.group(1).strip()
            return ParsedIntent(
                intent="delete_file",
                confidence=0.9,
                parameters={"path": path},
                risk="medium",
            )

        # 6. System telemetry / Kernel intelligence
        if any(term in lower for term in ["cpu", "ram", "memory", "usage", "system stats", "telemetry", "system info", "why is my system slow", "system slow", "lag", "bottleneck"]):
            return ParsedIntent(
                intent="system_info",
                confidence=0.95,
                parameters={},
                risk="low",
            )

        # 7. Memory / Knowledge
        if lower.startswith("remember ") or lower.startswith("store memory "):
            fact = cleaned.split(maxsplit=1)[1].strip()
            key = re.sub(r"[^a-zA-Z0-9_]+", "_", fact[:30]).strip("_").lower() or "user_fact"
            return ParsedIntent(
                intent="remember",
                confidence=0.9,
                parameters={"memory_id": key, "key": key, "content": fact, "fact": fact},
                risk="low",
            )
        if any(lower.startswith(prefix) for prefix in ["recall ", "what did i say about ", "search memory for ", "retrieve memory "]):
            query = cleaned.split(maxsplit=1)[1].strip()
            key = re.sub(r"[^a-zA-Z0-9_]+", "_", query[:30]).strip("_").lower() or "query"
            return ParsedIntent(
                intent="retrieve_memory",
                confidence=0.85,
                parameters={"memory_id": key, "key": key, "query": query},
                risk="low",
            )

        # Ambiguous prompt detection
        if len(cleaned.split()) <= 2:
            return ParsedIntent(
                intent="ambiguous",
                confidence=0.4,
                clarification_needed=True,
                clarification_prompt=f"Could you please be more specific about what you'd like to do with '{cleaned}'?",
            )

        return ParsedIntent(
            intent="unknown",
            confidence=0.0,
            error=f"Could not reliably determine intent from prompt: '{cleaned}'.",
        )

    def parse_composite(self, text: str) -> list[ParsedIntent]:
        """
        Decompose multi-step compound commands connected by 'and', 'then', ';'.
        Example: 'Open browser and create file notes.txt' -> [open_browser, create_file]
        """
        if not isinstance(text, str) or not text.strip():
            return []

        tokens = re.split(r"\s*;\s*|\s+then\s+", text.strip(), flags=re.IGNORECASE)
        clauses: list[str] = []
        for token in tokens:
            and_parts = re.split(
                r"\s+and\s+(?=(?:open|launch|create|make|write|read|cat|delete|remove|rm|show|view|remember|recall|search)\b)",
                token,
                flags=re.IGNORECASE,
            )
            clauses.extend(and_parts)

        results: list[ParsedIntent] = []
        for clause in clauses:
            clause_clean = clause.strip()
            if clause_clean:
                results.append(self.parse(clause_clean))
        return results

