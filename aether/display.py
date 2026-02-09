import time
from contextlib import contextmanager
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from aether.console import console

VERSION = "0.2.0"
BAR = "[dim]│[/dim]"

_active_display = None


def get_active_display():
    """Return the currently active _ElapsedDisplay, or None."""
    return _active_display


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


def show_system_info(config):
    """Display concurrency and system info from config."""
    console.print(
        f" {BAR}  [dim]semaphore      {config.pipeline.max_concurrent_requests}[/dim]"
    )
    console.print(f" {BAR}  [dim]threads        1 (tool executor)[/dim]")
    console.print(f" {BAR}  [dim]timeout        {config.llm.timeout}s[/dim]")
    console.print(f" {BAR}  [dim]max_retries    {config.llm.max_retries}[/dim]")
    console.print(f" {BAR}  [dim]parse_retries  {config.llm.parse_retries}[/dim]")
    console.print(f" {BAR}")


def show_run_plan(
    stage: str,
    parallel: int = 1,
    iter_count: int = 1,
    skip_confirm: bool = False,
) -> bool:
    """Display run plan and confirmation prompt. Returns True to proceed, False to cancel."""
    total = parallel * iter_count
    console.print(f" [bold blue]◇[/bold blue]  [bold]{stage}[/bold]")
    if parallel > 1:
        console.print(f" {BAR}  [cyan]parallel[/cyan]  {parallel}")
    if iter_count > 1:
        console.print(f" {BAR}  [cyan]iter[/cyan]      {iter_count}")
    if total > 1:
        console.print(f" {BAR}  [cyan]total[/cyan]     {total}")
    console.print(f" {BAR}")

    if skip_confirm:
        return True

    answer = console.input(f" {BAR}  Proceed? [bold]\\[Y/n][/bold] ").strip().lower()
    console.print(f" {BAR}")
    return answer in ("", "y", "yes")


class _ElapsedDisplay:
    """Rich renderable that shows spinner + label + sub-text + live elapsed time."""

    def __init__(self, label: str):
        self._label = label
        self._sub_text = ""
        self._start = time.time()
        self._spinner = Spinner("dots", style="green")

    def update(self, sub_text: str):
        self._sub_text = sub_text

    @property
    def elapsed(self) -> float:
        return time.time() - self._start

    def __rich_console__(self, console, options):
        elapsed = self.elapsed
        suffix = f"  [dim]{self._sub_text}[/dim]" if self._sub_text else ""
        text = Text.from_markup(f"  {self._label}{suffix}  [dim]{elapsed:.1f}s[/dim]")
        self._spinner.update(text=text)
        yield self._spinner


class StepContext:
    """Collects detail lines and allows live status updates."""

    def __init__(self, display: _ElapsedDisplay):
        self._details: list[str] = []
        self._display = display

    def update(self, text: str):
        """Update the sub-text displayed next to the label."""
        self._display.update(text)

    def detail(self, text: str):
        self._details.append(text)


@contextmanager
def step_progress(label: str, iter_label: str = None):
    """Context manager that shows a live elapsed timer during work, then a completed step.

    Usage:
        with step_progress("Building Clause Graph") as ctx:
            for i in range(10):
                ctx.update(f"{i} edges")   # live update next to label
            ctx.detail("42 nodes, 18 edges")  # shown after completion

        with step_progress("Generating Theses", iter_label="Iter 1/3") as ctx:
            ...
    """
    global _active_display
    prefix = f"{iter_label}  " if iter_label else ""
    display_label = f"{prefix}{label}"
    display = _ElapsedDisplay(display_label)
    ctx = StepContext(display)
    try:
        with Live(display, refresh_per_second=8, console=console, transient=True):
            _active_display = display
            yield ctx
    except Exception:
        console.print(
            f" [red]✖[/red]  {display_label}  [dim]{display.elapsed:.1f}s[/dim]"
        )
        raise
    finally:
        _active_display = None
    console.print(
        f" [bold blue]◆[/bold blue]  {display_label}  [dim]{display.elapsed:.1f}s[/dim]"
    )
    for d in ctx._details:
        console.print(f" {BAR}  [dim]{d}[/dim]")
    console.print(f" {BAR}")


def show_step_result(text: str):
    """Display a single result line after a step completes. e.g. '✓ 2 theses generated'"""
    console.print(f" {BAR}  [green]✓[/green] {text}")


def show_summary(lines: list[tuple[str, str]]):
    """Display a summary panel inside the clack flow.

    Args:
        lines: [("Total", "6 theses"), ("Time", "37.2s (12.4s/iter)"), ("Output", "database/thesis/")]
    """
    content = "\n".join(f"  [cyan]{k:<8}[/cyan] {v}" for k, v in lines)
    panel = Panel(
        content, title="Summary", border_style="dim", expand=False, padding=(0, 1)
    )

    with console.capture() as capture:
        console.print(panel)
    for line in capture.get().rstrip("\n").split("\n"):
        console.print(f" {BAR}  {line}")
    console.print(f" {BAR}")


def show_error_block(title: str, message: str):
    """Display a clack-style error block."""
    console.print(f" {BAR}")
    console.print(f" [red]✖[/red]  [bold red]{title}[/bold red]")
    console.print(f" {BAR}")
    console.print(f" {BAR}  [red]{message}[/red]")
    console.print(f" {BAR}")
    console.print(" [dim]└[/dim]  [dim]Aborted[/dim]")


def show_closer(text: str = "Done"):
    """Display the closing line."""
    console.print(f" [dim]└[/dim]  {text} [green]✓[/green]")


def show_config_display(config_dict: dict):
    """Display config as a Rich Tree inside the clack flow."""
    from rich.tree import Tree

    tree = Tree("[bold]config[/bold]", guide_style="dim")
    for section, values in config_dict.items():
        branch = tree.add(f"[bold]{section}[/bold]")
        if isinstance(values, dict):
            for key, val in values.items():
                branch.add(f"[cyan]{key}[/cyan] = {val}")
        else:
            branch.add(str(values))

    with console.capture() as capture:
        console.print(tree)
    for line in capture.get().rstrip("\n").split("\n"):
        console.print(f" {BAR}  {line}")
