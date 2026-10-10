from __future__ import annotations

import argparse
import sys

from src.api.runtime import create_runtime
from src.ui.prompt_shell import PromptShell


def main() -> None:
    parser = argparse.ArgumentParser(description="AgenticOS v0.1 Prompt Shell")
    parser.add_argument("prompt", nargs="*", help="Optional single prompt to execute")
    args = parser.parse_args()

    runtime = create_runtime()
    shell = PromptShell(runtime.platform)

    if args.prompt:
        prompt_text = " ".join(args.prompt)
        shell.render_execution(prompt_text)
        return

    print("AgenticOS Interactive Prompt Shell. Type 'exit' or 'quit' to stop.\n")
    while True:
        try:
            user_input = input("AgenticOS > ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting AgenticOS.")
                break
            shell.render_execution(user_input)
            print()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    main()
