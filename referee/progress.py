from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
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
)


def step_suggest_progress(progress, taskid, newtask, n_completed):
    n_completed += 1
    progress.update(
        taskid, current_task=newtask, completed=n_completed,
    )

    return n_completed
