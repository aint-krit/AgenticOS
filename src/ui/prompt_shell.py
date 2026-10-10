from __future__ import annotations

import sys
from typing import Any

from src.agent_platform.orchestrator import AgentPlatform

# Ensure stdout can handle UTF-8 if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class PromptShell:
    """
    AgenticOS Human Interface & Prompt Shell.

    Renders transparent agent execution:
    Prompt -> Understanding -> Planning -> Executing -> Verified Results.
    """

    WIDTH = 56

    def __init__(self, platform: AgentPlatform) -> None:
        self.platform = platform
        # Check if terminal encoding supports unicode box drawing
        encoding = getattr(sys.stdout, "encoding", "") or ""
        self.use_unicode = "utf" in encoding.lower()

    def _format_box_top(self, title: str = "AgenticOS") -> str:
        c_left = "+" if self.use_unicode else "+"
        c_right = "+"
        horiz = "-" if self.use_unicode else "-"
        pipe = "|"
        line = c_left + horiz * (self.WIDTH - 2) + c_right
        title_line = f"{pipe} {title}".ljust(self.WIDTH - 1) + pipe
        return f"{line}\n{title_line}"

    def _format_box_bottom(self) -> str:
        c_left = "+" if self.use_unicode else "+"
        c_right = "+" if self.use_unicode else "+"
        horiz = "-" if self.use_unicode else "-"
        return c_left + horiz * (self.WIDTH - 2) + c_right

    def _box_line(self, text: str = "") -> str:
        pipe = "|"
        return f"{pipe} {text}".ljust(self.WIDTH - 1) + pipe

    def _check_mark(self) -> str:
        return "[OK]" if self.use_unicode else "[OK]"

    def _cross_mark(self) -> str:
        return "[X]" if self.use_unicode else "[FAIL]"

    def render_execution(self, prompt: str) -> dict[str, Any]:
        """
        Execute prompt and stream progress to stdout with the AgenticOS product UI layout.
        """
        ok = self._check_mark()
        fail = self._cross_mark()

        print(self._format_box_top("AgenticOS v0.1 Alpha"))
        print(self._box_line(""))
        print(self._box_line("What would you like me to do?"))
        print(self._box_line(""))
        print(self._box_line(f"> {prompt}"))
        print(self._box_line(""))
        print(self._box_line("Understanding..."))

        try:
            result = self.platform.execute_prompt(prompt)
        except Exception as exc:
            print(self._box_line(f"{fail} Failed: {exc}"))
            print(self._box_line(""))
            print(self._format_box_bottom())
            raise

        if result.get("status") == "clarification_needed":
            print(self._box_line("? Ambiguous Request"))
            print(self._box_line(f"  {result.get('clarification_prompt', '')}"))
            print(self._box_line(""))
            print(self._format_box_bottom())
            return result

        print(self._box_line("Planning..."))
        intents = result.get("intents", [])
        for item in intents:
            print(self._box_line(f"  * Plan: {item.get('intent')} (risk: {item.get('risk')})"))

        print(self._box_line("Executing..."))

        workflow = result.get("workflow", {})
        tasks = workflow.get("tasks", {})
        results = result.get("results", {})

        for task_id, task_data in tasks.items():
            desc = task_data.get("description", task_id)
            task_resp = results.get(task_id, {})
            payload = task_resp.get("payload", {})
            if isinstance(payload.get("result"), dict):
                payload = {**payload, **payload["result"]}

            if task_data.get("status") == "completed":
                status_desc = desc
                if payload.get("status") == "created":
                    status_desc = f"File created: {payload.get('path')}"
                elif payload.get("status") == "read":
                    status_desc = f"File read: {payload.get('path')}"
                elif payload.get("status") == "written":
                    status_desc = f"File updated: {payload.get('path')}"
                elif payload.get("status") == "deleted":
                    status_desc = f"File deleted: {payload.get('path')}"
                elif payload.get("action") == "open_browser":
                    status_desc = f"Browser opened: {payload.get('url', 'about:blank')}"
                elif payload.get("status") == "success" and (
                    "cpu_percent" in payload or "memory_percent" in payload
                ):
                    status_desc = (
                        f"System info: CPU {payload.get('cpu_percent', 'N/A')}%, "
                        f"RAM {payload.get('memory_percent', 'N/A')}%"
                    )

                print(self._box_line(f"{ok} {status_desc}"))
            else:
                print(self._box_line(f"{fail} {desc}: {task_data.get('error')}"))

        print(self._box_line(""))
        print(self._box_line(f"Request ID: {result.get('request_id')}"))
        print(self._format_box_bottom())
        return result

