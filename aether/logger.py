from loguru import logger
from aether.display import console

_sink_id = None
_cli_mode = False


def _script_sink(message):
    """Default sink for script/entrypoint mode: standard format."""
    record = message.record
    level = record["level"].name
    name = record["extra"].get("name", record["module"])
    time_str = record["time"].strftime("%H:%M:%S")
    style = {
        "DEBUG": "dim",
        "INFO": "info",
        "WARNING": "warning",
        "ERROR": "error",
    }.get(level, "info")
    console.print(
        f"[dim]{time_str}[/dim] [{style}]{level:<7}[/{style}] [cyan]{name}[/cyan] {record['message']}"
    )


def _cli_sink(message):
    """CLI verbose sink: tree-style format with │ prefix."""
    record = message.record
    name = record["extra"].get("name", record["module"])
    time_str = record["time"].strftime("%H:%M:%S")
    console.print(
        f" [dim]│[/dim]  [dim]{time_str}[/dim] [cyan]{name:<10}[/cyan] {record['message']}"
    )


def _cli_warn_sink(message):
    """CLI default sink: tree-style for WARNING/ERROR only."""
    record = message.record
    level = record["level"].name
    marker = "\u26a0" if level == "WARNING" else "\u2716"
    style = "warning" if level == "WARNING" else "error"
    console.print(f" [dim]│[/dim]  [{style}]{marker} {record['message']}[/{style}]")


def _cli_info_sink(message):
    """CLI default sink: INFO updates the live display sub-text; WARNING suppressed; ERROR printed."""
    from aether.display import get_active_display

    record = message.record
    level = record["level"].name
    if level == "WARNING":
        return
    if level in ("ERROR", "CRITICAL"):
        console.print(f" [dim]│[/dim]  [error]✖ {record['message']}[/error]")
        return
    # INFO: update the live display sub-text, or print as dim line if no display active
    display = get_active_display()
    if display is not None:
        display.update(record["message"])
    else:
        console.print(f" [dim]│[/dim]  [dim]{record['message']}[/dim]")


# Default: script mode (INFO level, standard format)
logger.remove()
_sink_id = logger.add(_script_sink, level="INFO", colorize=False)


def init_cli(verbose: bool = False):
    """Initialize logger for CLI mode. Call this from cli.py callback."""
    global _sink_id, _cli_mode
    _cli_mode = True
    logger.remove()
    if verbose:
        _sink_id = logger.add(_cli_sink, level="DEBUG", colorize=False)
    else:
        _sink_id = logger.add(_cli_info_sink, level="INFO", colorize=False)


def get_logger(name: str, level: str = "INFO"):
    """Loguru-based logger factory."""
    return logger.bind(name=name)
