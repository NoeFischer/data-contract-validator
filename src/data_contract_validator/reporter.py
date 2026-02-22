from __future__ import annotations

import json
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from data_contract_validator.models.report import ValidationReport


def print_report(report: ValidationReport, console: Console | None = None) -> None:
    c = console or Console()

    passed = report.passed
    status = "[bold green]PASSED[/]" if passed else "[bold red]FAILED[/]"
    border = "green" if passed else "red"

    c.print(Panel(
        f"Contract:  [bold]{report.contract_name}[/] v{report.contract_version}\n"
        f"Data file: {report.data_file}\n"
        f"Rows:      {report.total_rows}\n"
        f"Status:    {status}",
        title="Data Contract Validation",
        border_style=border,
    ))

    if not report.violations:
        c.print("[green]No violations found.[/]\n")
        return

    table = Table(
        title=f"{len(report.violations)} violation(s)",
        box=box.ROUNDED,
        border_style="red",
        show_lines=True,
        expand=False,
    )
    table.add_column("Rule", style="bold")
    table.add_column("Column")
    table.add_column("Row", justify="right")
    table.add_column("Message", max_width=60)

    for v in report.violations:
        table.add_row(
            v.rule,
            v.column or "—",
            str(v.row) if v.row is not None else "—",
            v.message,
        )

    c.print(table)
    c.print()


def export_json(report: ValidationReport, output_path: str) -> None:
    path = Path(output_path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2)
