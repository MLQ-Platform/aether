from rich.console import Console
from rich.theme import Theme

aether_theme = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "stage": "bold magenta",
        "dim": "dim white",
        "header": "bold blue",
        "metric": "bold cyan",
    }
)

console = Console(theme=aether_theme, highlight=False)
