"""
reporter.py
-----------
Handles output: colored terminal report and optional JSON file report.
"""

import json
import sys
from typing import List

from glue_drift.checker import JobDriftResult

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _color(text: str, code: str) -> str:
    if _supports_color():
        return f"{code}{text}{RESET}"
    return text


def print_terminal_report(results: List[JobDriftResult]) -> None:
    """Print a human-readable colored drift report to stdout."""

    total = len(results)
    ok = sum(1 for r in results if r.status == "ok")
    drifted = sum(1 for r in results if r.status == "drifted")
    missing = sum(1 for r in results if r.status == "missing")

    print()
    print(_color("=" * 60, BOLD))
    print(_color("  GLUE DRIFT REPORT", BOLD))
    print(_color("=" * 60, BOLD))
    print(f"  Jobs checked : {total}")
    print(f"  {_color('OK', GREEN)}       : {ok}")
    print(f"  {_color('Drifted', RED)}  : {drifted}")
    print(f"  {_color('Missing', YELLOW)}  : {missing}")
    print(_color("=" * 60, BOLD))
    print()

    for result in results:
        if result.status == "ok":
            print(f"  {_color('✔', GREEN)}  {result.job_name}")

        elif result.status == "missing":
            print(f"  {_color('✘', YELLOW)}  {result.job_name}  {_color('[MISSING in AWS]', YELLOW)}")
            if result.error:
                print(f"      {result.error}")

        elif result.status == "drifted":
            print(f"  {_color('✘', RED)}  {result.job_name}  {_color('[DRIFTED]', RED)}")
            for drift in result.drifts:
                print(f"      {_color('Field:', CYAN)} {drift.field}")
                print(f"        {_color('Expected:', GREEN)} {drift.expected}")
                print(f"        {_color('Actual:  ', RED)} {drift.actual}")

        print()

    print(_color("=" * 60, BOLD))

    if drifted > 0 or missing > 0:
        print(_color("  ❌ Drift detected! Review the above jobs.", RED))
    else:
        print(_color("  ✅ All jobs are in sync with source-of-truth.", GREEN))

    print(_color("=" * 60, BOLD))
    print()


def write_json_report(results: List[JobDriftResult], output_path: str) -> None:
    """Write a machine-readable JSON drift report to a file."""

    report = {
        "summary": {
            "total": len(results),
            "ok": sum(1 for r in results if r.status == "ok"),
            "drifted": sum(1 for r in results if r.status == "drifted"),
            "missing": sum(1 for r in results if r.status == "missing"),
        },
        "jobs": [],
    }

    for result in results:
        job_entry = {
            "job_name": result.job_name,
            "status": result.status,
            "drifts": [
                {
                    "field": d.field,
                    "expected": d.expected,
                    "actual": d.actual,
                }
                for d in result.drifts
            ],
        }
        if result.error:
            job_entry["error"] = result.error

        report["jobs"].append(job_entry)

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"JSON report written to: {output_path}")
