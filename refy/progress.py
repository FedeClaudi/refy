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


class FileNameColumn(TextColumn):
    _renderable_cache = {}

    def __init__(self, *args):
        pass

    def render(self, task):
        try:
            return f"[bold {orange}]{task.fields['filename']}"
        except (AttributeError, TypeError):
            return ""


class LossColumn(TextColumn):
    _renderable_cache = {}

    def __init__(self, *args):
        pass

    def render(self, task):
        try:
            return f"[{amber_light}]curr. loss: [bold {orange}]{task.fields['loss']:.3f}"
        except (AttributeError, TypeError):
            return ""


# ------------------------------- progress bars ------------------------------ #
# general porpuse progress
progress = Progress(
    "[progress.description]{task.description}",
    "•",
    TextColumn("[bold magenta]Completed {task.completed}/{task.total}"),
    "•",
    BarColumn(bar_width=None),
    "•",
    TextColumn("Time remaining: ", justify="right"),
    TimeRemainingColumn(),
)

train_progress = Progress(
    "[progress.description]{task.description}",
    "•",
    TextColumn("[bold magenta]Completed {task.completed}/{task.total}"),
    "•",
    LossColumn(),
    "•",
    BarColumn(bar_width=None),
    "•",
    TextColumn("Time remaining: ", justify="right"),
    TimeRemainingColumn(),
)


# Overall progress bar for suggestions
suggest_progress = Progress(
    "[progress.description]{task.description}",
    "•",
    TextColumn("[bold magenta]Completed {task.completed}/{task.total}"),
    "•",
    CurrentTaskColumn(),
    "•",
    BarColumn(bar_width=None),
    "•",
    TextColumn("Time remaining: ", justify="right"),
    TimeRemainingColumn(),
)


http_retrieve_progress = Progress(
    TextColumn("[bold]Downloading: ", justify="right"),
    FileNameColumn(),
    BarColumn(bar_width=None),
    "{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "• speed:",
    TransferSpeedColumn(),
    "• ETA:",
    TimeRemainingColumn(),
)
