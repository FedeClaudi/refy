from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

from myterial import (
    orange,
    amber_light,
)


# ---------------------------------- columns --------------------------------- #


class CurrentTaskColumn(TextColumn):
    _renderable_cache = {}

    def __init__(self, *args):
        pass

    def render(self, task):
        try:
            return f"[{amber_light}]curr. task: [bold {orange}]{task.fields['current_task']}"
        except (AttributeError, TypeError):
            return ""


# ------------------------------- progress bars ------------------------------ #
# Overall progress bar for suggestions
suggest_progress = Progress(
    "[progress.description]{task.description}",
    "•",
    TextColumn("[bold magenta]Step {task.completed}/{task.total}"),
    CurrentTaskColumn(),
    "•",
    BarColumn(bar_width=None),
    "•",
    TextColumn("Time remaining: ", justify="right"),
    TimeRemainingColumn(),
)


http_retrieve_progress = Progress(
    TextColumn("[bold]Downloading: ", justify="right"),
    TextColumn("[bold magenta]Step {task.filename}"),
    BarColumn(bar_width=None),
    "{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "• speed:",
    TransferSpeedColumn(),
    "• ETA:",
    TimeRemainingColumn(),
    transient=True,
)
