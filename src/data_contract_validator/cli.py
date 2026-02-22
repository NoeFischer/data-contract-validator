from __future__ import annotations

import sys

import click

from data_contract_validator.loader import (
    ContractLoadError,
    DataLoadError,
    load_contract,
    load_csv,
)
from data_contract_validator.reporter import export_json, print_report
from data_contract_validator.validator import validate


@click.command()
@click.version_option(version="0.1.0", prog_name="validate-contract")
@click.option(
    "--contract", "-c",
    required=True,
    type=click.Path(dir_okay=False),
    help="Path to the YAML contract file.",
)
@click.option(
    "--data", "-d",
    required=True,
    type=click.Path(dir_okay=False),
    help="Path to the CSV data file.",
)
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Optional path to write a JSON report.",
)
def main(contract: str, data: str, output: str | None) -> None:
    """Validate a CSV file against a YAML data contract."""
    try:
        contract_model = load_contract(contract)
    except ContractLoadError as exc:
        click.echo(f"Error loading contract: {exc}", err=True)
        sys.exit(2)

    try:
        fieldnames, rows = load_csv(data)
    except DataLoadError as exc:
        click.echo(f"Error loading data: {exc}", err=True)
        sys.exit(2)

    report = validate(contract_model, fieldnames, rows, data)
    print_report(report)

    if output:
        export_json(report, output)
        click.echo(f"JSON report written to: {output}")

    if not report.passed:
        sys.exit(1)
