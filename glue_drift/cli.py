"""
cli.py
------
CLI entrypoint for glue-drift.
Usage: glue-drift check --config jobs.yaml
"""

import sys
import click

from glue_drift.checker import check_all_jobs
from glue_drift.reporter import print_terminal_report, write_json_report


@click.group()
@click.version_option(package_name="glue-drift")
def cli():
    """glue-drift: Detect configuration drift in AWS Glue jobs."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to the source-of-truth YAML config file.",
)
@click.option(
    "--region",
    "-r",
    default="us-east-2",
    show_default=True,
    help="AWS region where Glue jobs are deployed.",
)
@click.option(
    "--profile",
    "-p",
    default=None,
    help="AWS CLI profile name to use (optional).",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Optional path to write JSON report (e.g. report.json).",
)
@click.option(
    "--fail-on-drift",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any drift or missing jobs are found (useful for CI/CD).",
)
def check(config, region, profile, output, fail_on_drift):
    """
    Compare live AWS Glue job configs against a source-of-truth YAML.

    Example:

        glue-drift check --config jobs.yaml

        glue-drift check --config jobs.yaml --output report.json --fail-on-drift
    """
    click.echo(f"Loading config: {config}")
    click.echo(f"AWS Region   : {region}")
    if profile:
        click.echo(f"AWS Profile  : {profile}")
    click.echo("Fetching live Glue job configs from AWS...")

    try:
        results = check_all_jobs(config_path=config, region=region, profile=profile)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(2)

    print_terminal_report(results)

    if output:
        write_json_report(results, output)

    if fail_on_drift:
        has_issues = any(r.status != "ok" for r in results)
        if has_issues:
            sys.exit(1)
