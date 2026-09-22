"""Main executable runner for the LLM Harness.

Demonstrates task decomposition, dynamic skills injection, subagent orchestration,
and feedback remediation loops in the Software Engineering domain.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.panel import Panel
from rich.syntax import Syntax

from src.agents.dispatcher import DispatcherAgent
from src.config import LLMProvider, settings
from src.llm.client import create_llm_client
from src.skills.registry import SkillRegistry
from src.ui.logger import HarnessConsoleLogger, console

TEST_CASES = {
    "1": (
        "Case 1: Secure Session Token Manager",
        "Design and implement a production-grade Secure Session Token Manager in Python. "
        "It must issue cryptographically secure tokens, validate them against side-channel "
        "timing attacks, support TTL expiration, and provide token revocation.",
    ),
    "2": (
        "Case 2: Thread-Safe LRU Cache with TTL and Eviction Callbacks",
        "Implement a thread-safe in-memory LRU Cache in Python with TTL expiration, "
        "capacity bounds, explicit type hints, custom domain exceptions, and eviction notifications.",
    ),
}


def run_case(case_num: str, dispatcher: DispatcherAgent, logger: HarnessConsoleLogger, save_dir: Path | None = None):
    """Run an individual test case through the Harness."""
    title, prompt = TEST_CASES[case_num]
    console.print(f"\n[bold green]================================================================================[/bold green]")
    console.print(f"[bold green]▶ EXECUTING TEST CASE #{case_num}: {title}[/bold green]")
    console.print(f"[bold green]================================================================================[/bold green]")

    artifacts = dispatcher.run_harness(prompt, on_event=logger.on_event)

    # Show code artifacts
    console.print("\n[bold cyan]=== FINAL ARTIFACT: SOLUTION CODE ===[/bold cyan]")
    console.print(Syntax(artifacts["code"], "python", theme="monokai", line_numbers=True))

    console.print("\n[bold cyan]=== FINAL ARTIFACT: TEST SUITE (PYTEST) ===[/bold cyan]")
    console.print(Syntax(artifacts["tests"], "python", theme="monokai", line_numbers=True))

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        code_file = save_dir / f"case_{case_num}_solution.py"
        test_file = save_dir / f"test_case_{case_num}.py"
        code_file.write_text(artifacts["code"], encoding="utf-8")
        test_file.write_text(artifacts["tests"], encoding="utf-8")
        if case_num == "1":
            (save_dir / "session_manager.py").write_text(artifacts["code"], encoding="utf-8")
        console.print(f"\n[green]✔ Saved artifacts to:[/green] {save_dir.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="LLM Harness Engineering Runner - Software Engineering Domain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fast out-of-the-box run using Mock provider (zero config, zero keys):
  python main.py --provider mock

  # Run using local Ollama model (e.g. gemma4:12b or qwen2.5:32b):
  python main.py --provider local --model gemma4:12b

  # Run using OpenAI API:
  python main.py --provider openai --model gpt-4o-mini
        """,
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "local", "openai"],
        default=settings.provider.value,
        help="LLM backend provider (default: mock)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (default: 'gemma4:12b' for local, 'gpt-4o-mini' for openai)",
    )
    parser.add_argument(
        "--case",
        choices=["1", "2", "all"],
        default="1",
        help="Test case to execute (default: 1)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save generated solution and test files to ./output directory",
    )
    parser.add_argument(
        "--request",
        type=str,
        default=None,
        help="Custom user requirement string instead of predefined test cases",
    )

    args = parser.parse_args()

    # Determine provider & model
    provider_enum = LLMProvider(args.provider)
    active_model = args.model
    if not active_model:
        if provider_enum == LLMProvider.LOCAL:
            active_model = settings.local_model
        elif provider_enum == LLMProvider.OPENAI:
            active_model = settings.openai_model
        else:
            active_model = "deterministic-mock-v1"

    # Setup UI Logger
    logger = HarnessConsoleLogger(console)
    logger.log_header(
        provider=provider_enum.value,
        model=active_model,
        domain="Software Engineering (Code Gen, OWASP Audit, Pytest TDD)",
    )

    # Initialize Registry & LLM
    registry = SkillRegistry()
    available_skills = registry.list_skills()
    console.print(
        f"[dim]Loaded {len(available_skills)} modular skills from /skills catalog: "
        f"{', '.join([s.name for s in available_skills])}[/dim]\n"
    )

    llm_client = create_llm_client(
        provider=provider_enum,
        model=active_model,
    )

    dispatcher = DispatcherAgent(
        llm_client=llm_client,
        skills_registry=registry,
        max_feedback_iterations=settings.max_feedback_iterations,
    )

    save_dir = Path("output") if args.save else None

    try:
        if args.request:
            console.print(f"\n[bold green]▶ EXECUTING CUSTOM REQUEST[/bold green]")
            artifacts = dispatcher.run_harness(args.request, on_event=logger.on_event)
            console.print("\n[bold cyan]=== FINAL CODE ===[/bold cyan]")
            console.print(Syntax(artifacts["code"], "python", theme="monokai", line_numbers=True))
            console.print("\n[bold cyan]=== FINAL TESTS ===[/bold cyan]")
            console.print(Syntax(artifacts["tests"], "python", theme="monokai", line_numbers=True))
        elif args.case == "all":
            for c in ["1", "2"]:
                run_case(c, dispatcher, logger, save_dir)
        else:
            run_case(args.case, dispatcher, logger, save_dir)

    except KeyboardInterrupt:
        console.print("\n[yellow]Execution interrupted by user.[/yellow]")
        sys.exit(130)
    except ConnectionError as exc:
        console.print(
            Panel(
                f"[bold red]LLM CONNECTION ERROR[/bold red]\n\n{exc}",
                border_style="red",
            )
        )
        sys.exit(1)
    except Exception as exc:
        console.print(
            Panel(
                f"[bold red]EXECUTION ERROR[/bold red]\n\n{exc}",
                border_style="red",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
