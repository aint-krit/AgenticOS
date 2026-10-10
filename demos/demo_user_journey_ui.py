"""
AgenticOS v0.1 Alpha - 10 October User Journey & Multimodal Prompt UI Demo.

Demonstrates the complete vertical architecture:
User -> Human Interface -> Intent Intelligence -> Goal Runtime -> Workflow Runtime
-> Global Agent Manager -> Capability & Permissions -> Agent Bus -> Core/Specialized Agents
-> Results & Transparent UX rendering.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.runtime import create_runtime
from src.ui.prompt_shell import PromptShell


def main() -> None:
    runtime = create_runtime()
    shell = PromptShell(runtime.platform)

    print("=" * 70)
    print("AgenticOS v0.1 Alpha - Complete User Journey Demonstration")
    print("=" * 70)
    print()

    # Demonstration 1: Multi-step compound prompt
    prompt1 = "Open Chrome and create file Project_Folder/readme.txt with content Welcome to AgenticOS"
    shell.render_execution(prompt1)
    print()

    # Demonstration 2: System telemetry prompt
    prompt2 = "Show my CPU and memory usage"
    shell.render_execution(prompt2)
    print()

    # Clean up demo file
    demo_file = runtime.workspace / "Project_Folder" / "readme.txt"
    if demo_file.exists():
        demo_file.unlink()
    demo_dir = runtime.workspace / "Project_Folder"
    if demo_dir.exists():
        demo_dir.rmdir()


if __name__ == "__main__":
    main()
