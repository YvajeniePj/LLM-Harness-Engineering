"""Rich-based console UI and logger for LLM Harness execution."""

from __future__ import annotations

import sys
from typing import Any, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

from src.schema import ExecutionPlan, ReviewReport, ReviewSeverity

console = Console(legacy_windows=False)


class HarnessConsoleLogger:
    """Renders formatted execution traces and multi-agent interaction logs."""

    def __init__(self, console_instance: Console = console):
        self.console = console_instance

    def log_header(self, provider: str, model: str, domain: str = "Software Engineering"):
        """Print startup banner."""
        table = Table(show_header=False, box=None)
        table.add_row("[bold cyan]Project:[/bold cyan]", "Talent Hub LLM Harness Engineering")
        table.add_row("[bold cyan]Target Domain:[/bold cyan]", f"[bold yellow]{domain}[/bold yellow]")
        table.add_row("[bold cyan]LLM Provider:[/bold cyan]", f"[green]{provider.upper()}[/green]")
        table.add_row("[bold cyan]Active Model:[/bold cyan]", f"[magenta]{model}[/magenta]")
        table.add_row("[bold cyan]AI Core:[/bold cyan]", "Hierarchical Sub-Agents & Dynamic Skills Injection")

        self.console.print(
            Panel(
                table,
                title="[bold blue]=== LLM HARNESS EXECUTION ENVIRONMENT ===[/bold blue]",
                border_style="blue",
            )
        )

    def on_event(self, event_type: str, data: Dict[str, Any]):
        """Event dispatcher callback invoked by DispatcherAgent."""
        if event_type == "HARNESS_STARTED":
            self.console.print(f"\n[bold yellow]>>> New Task Received:[/bold yellow] {data['request']}")

        elif event_type == "PLANNING_COMPLETED":
            plan: ExecutionPlan = data["plan"]
            table = Table(title="[bold green]Root Orchestrator Execution Plan[/bold green]")
            table.add_column("Step", justify="center", style="cyan", no_wrap=True)
            table.add_column("Subagent Role", style="magenta")
            table.add_column("Dynamically Injected Skills", style="yellow")
            table.add_column("Step Objective", style="white")

            for step in plan.steps:
                skills_str = ", ".join(step.skill_names) if step.skill_names else "[dim]None[/dim]"
                table.add_row(str(step.step_id), step.role.value.upper(), skills_str, step.title)

            self.console.print(table)
            self.console.print(f"[dim]Rationale: {plan.rationale}[/dim]\n")

        elif event_type == "SKILL_INJECTION":
            agent = data["agent"]
            skills = data["skills"]
            skills_txt = ", ".join([f"[bold yellow]{s}[/bold yellow]" for s in skills])
            self.console.print(
                Panel(
                    f"⚡ [bold cyan]Runtime Skill Injection[/bold cyan] -> Target: [bold magenta]{agent}[/bold magenta]\n"
                    f"   Active Skill Guidelines: {skills_txt}",
                    border_style="yellow",
                    padding=(0, 2),
                )
            )

        elif event_type == "STEP_STARTED":
            agent = data.get("agent")
            iter_info = f" (Iteration {data['iteration']})" if "iteration" in data else ""
            self.console.print(f"  [blue]▶[/blue] Executing [bold]{agent}[/bold]{iter_info}...")

        elif event_type == "STEP_COMPLETED":
            agent = data.get("agent")
            res = data.get("result")
            self.console.print(f"  [green]✔[/green] Finished [bold]{agent}[/bold] in {res.execution_time_sec}s")

        elif event_type == "REVIEW_COMPLETED":
            report: ReviewReport = data["report"]
            iteration = data["iteration"]
            if report.is_approved:
                self.console.print(
                    Panel(
                        f"[bold green]✔ CODE REVIEW PASSED (Iteration {iteration})[/bold green]\n{report.summary}",
                        border_style="green",
                    )
                )
            else:
                issues_tbl = Table(show_header=True, header_style="bold red")
                issues_tbl.add_column("Severity", justify="center", style="bold")
                issues_tbl.add_column("Skill / Rule Violated", style="yellow")
                issues_tbl.add_column("Issue Description", style="white")
                issues_tbl.add_column("Recommendation", style="green")

                for issue in report.issues:
                    sev_style = "bold red" if issue.severity == ReviewSeverity.CRITICAL else "bold yellow"
                    issues_tbl.add_row(
                        Text(issue.severity.upper(), style=sev_style),
                        issue.rule_violated,
                        issue.description,
                        issue.suggestion,
                    )

                self.console.print(
                    Panel(
                        issues_tbl,
                        title=f"[bold red]✘ REVIEW REJECTED: ISSUES FOUND (Iteration {iteration})[/bold red]",
                        subtitle=report.summary,
                        border_style="red",
                    )
                )

        elif event_type == "FEEDBACK_LOOP_TRIGGERED":
            iteration = data["iteration"]
            self.console.print(
                f"[bold magenta]↺ [Feedback Loop][/bold magenta] Dispatcher detected critical issues. "
                f"Returning code and review findings to [bold]DeveloperAgent[/bold] for remediation pass #{iteration}...\n"
            )

        elif event_type == "CODE_REVISED":
            self.console.print("  [green]✔[/green] DeveloperAgent applied remediation. Re-submitting to ReviewerAgent...")

        elif event_type == "HARNESS_COMPLETED":
            artifacts = data["artifacts"]
            dur = artifacts["metrics"].get("total_duration_sec", 0.0)
            self.console.print(
                Panel(
                    f"[bold green]✔ HARNESS PIPELINE EXECUTION SUCCESSFUL[/bold green]\n"
                    f"Total Duration: {dur}s | Code Review History: {len(artifacts['review_history'])} round(s)\n"
                    f"Generated Code: {len(artifacts['code'])} chars | Tests: {len(artifacts['tests'])} chars",
                    border_style="green",
                )
            )
