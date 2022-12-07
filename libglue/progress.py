"""libGlue progress library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn
)
from rich.table import Table


def create_overall_progress():
    """Overall progress template."""
    return Progress(
        "{task.description} {task.percentage:>3.0f}%",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage] [{task.completed:05}/{task.total}]"),
        TimeRemainingColumn(),
    )


def create_job_progress():
    """Job progress template."""
    return Progress("[{task.completed:03}/{task.total:03}] {task.description}")


def create_download_progress(transient: bool = True):
    """Download progress template."""
    return Progress(
        TextColumn("[bold blue]{task.fields[file_name]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        transient=transient,
    )


def create_progress_table(total: int):
    """Progress table template."""
    overall_progress = create_overall_progress()
    overall_task_id = overall_progress.add_task("🕵️", total=total)
    job_progress = create_job_progress()

    progress_table = Table.grid()

    progress_table.add_row(
        Panel(overall_progress, title="Overall Progress", border_style="green", padding=(2, 2), height=8),
        Panel(job_progress, title="[b]Threads", border_style="red", padding=(1, 2), height=8, width=100),
    )

    return job_progress, overall_task_id, overall_progress, progress_table


def create_download_progress_table(total: int):
    """Download progress table template."""
    overall_progress = create_overall_progress()
    overall_task_id = overall_progress.add_task("🕵️", total=total)
    job_progress = create_download_progress()

    progress_table = Table.grid()

    progress_table.add_row(
        Panel(overall_progress, title="Overall Progress", border_style="green", padding=(2, 2), height=8),
        Panel(job_progress, title="[b]Threads", border_style="red", padding=(1, 2), height=8, width=100),
    )

    return job_progress, overall_task_id, overall_progress, progress_table
