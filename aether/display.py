import time
from contextlib import contextmanager
from aether.console import console

VERSION = "0.2.0"
BAR = "[dim]│[/dim]"


def show_header(**context):
    """Display clack-style header with optional context key-value pairs.

    Usage:
        show_header(model="deepseek/deepseek-v3.2-exp", ticker="BTCUSDT")
    """
    console.print(f" [bold blue]┌[/bold blue]  [bold]AETHER[/bold] v{VERSION}")
    console.print(f" {BAR}")
    if context:
        for key, value in context.items():
            console.print(f" {BAR}  [cyan]{key:<8}[/cyan] {value}")
        console.print(f" {BAR}")


class StepContext:
    """Collects detail lines and allows live status updates."""

    def __init__(self, status, label: str):
        self._details: list[str] = []
        self._status = status
        self._label = label

    def update(self, text: str):
        """Update the spinner text in real-time."""
        self._status.update(f" [dim]◇[/dim]  {self._label}  [dim]{text}[/dim]")

    def detail(self, text: str):
        self._details.append(text)


@contextmanager
def step_progress(label: str):
    """Context manager that shows a spinner during work, then a completed step.

    Usage:
        with step_progress("Building Clause Graph") as ctx:
            for i in range(10):
                ctx.update(f"{i} edges")   # live update next to spinner
            ctx.detail("42 nodes, 18 edges")  # shown after completion
    """
    start = time.time()
    try:
        with console.status(f" [dim]◇[/dim]  {label}...", spinner="dots") as status:
            ctx = StepContext(status, label)
            yield ctx
    except Exception:
        elapsed = time.time() - start
        console.print(f" [red]✖[/red]  {label}  [dim]{elapsed:.1f}s[/dim]")
        raise
    elapsed = time.time() - start
    console.print(f" [bold blue]◆[/bold blue]  {label}  [dim]{elapsed:.1f}s[/dim]")
    for d in ctx._details:
        console.print(f" {BAR}  [dim]{d}[/dim]")
    console.print(f" {BAR}")


def show_error_block(title: str, message: str):
    """Display a clack-style error block."""
    console.print(f" {BAR}")
    console.print(f" [red]✖[/red]  [bold red]{title}[/bold red]")
    console.print(f" {BAR}")
    console.print(f" {BAR}  [red]{message}[/red]")
    console.print(f" {BAR}")
    console.print(" [dim]└[/dim]  [dim]Aborted[/dim]")


def show_closer(text: str):
    """Display the closing line."""
    console.print(f" [dim]└[/dim]  {text}")


def show_config_display(config_dict: dict):
    """Display config in tree style.

    Usage:
        show_config_display({"llm": {"model": "...", ...}, "pipeline": {...}})
    """
    sections = list(config_dict.items())
    for i, (section, values) in enumerate(sections):
        is_last = i == len(sections) - 1
        branch = "\u2514" if is_last else "\u251c"
        console.print(f" [bold blue]{branch}[/bold blue]  [bold]{section}[/bold]")
        if isinstance(values, dict):
            for key, val in values.items():
                console.print(f" {BAR}  [cyan]{key:<24}[/cyan] {val}")
        else:
            console.print(f" {BAR}  {values}")
        if not is_last:
            console.print(f" {BAR}")
