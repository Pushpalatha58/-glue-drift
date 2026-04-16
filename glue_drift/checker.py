"""
checker.py
----------
Core drift detection logic.
Compares expected YAML configs against live AWS Glue job configs.
"""

from dataclasses import dataclass, field
from typing import Any

import yaml

from glue_drift.normalizer import normalize_job, to_comparable_json
from glue_drift.fetcher import fetch_live_jobs, get_glue_client


@dataclass
class FieldDrift:
    """Represents a single field that has drifted."""
    field: str
    expected: Any
    actual: Any


@dataclass
class JobDriftResult:
    """Drift result for a single Glue job."""
    job_name: str
    status: str                        # "ok" | "drifted" | "missing"
    drifts: list[FieldDrift] = field(default_factory=list)
    error: str | None = None

    @property
    def has_drift(self) -> bool:
        return self.status != "ok"


def load_yaml_config(config_path: str) -> dict:
    """Load and parse the source-of-truth YAML config file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _compare_jobs(expected: dict, actual: dict) -> list[FieldDrift]:
    """
    Compare expected vs actual job configs field by field.
    Returns a list of FieldDrift for every field that differs.
    """
    drifts = []

    all_keys = set(expected.keys()) | set(actual.keys())

    for key in sorted(all_keys):
        exp_val = expected.get(key)
        act_val = actual.get(key)

        # Normalize nested dicts to stable JSON for comparison
        if isinstance(exp_val, dict) or isinstance(act_val, dict):
            exp_str = to_comparable_json(exp_val or {})
            act_str = to_comparable_json(act_val or {})
            if exp_str != act_str:
                drifts.append(FieldDrift(field=key, expected=exp_val, actual=act_val))
        else:
            if exp_val != act_val:
                drifts.append(FieldDrift(field=key, expected=exp_val, actual=act_val))

    return drifts


def check_all_jobs(
    config_path: str,
    region: str = "us-east-2",
    profile: str = None,
) -> list[JobDriftResult]:
    """
    Main entrypoint: load YAML, fetch live configs, compare all jobs.
    Returns a list of JobDriftResult (one per job in YAML).
    """
    config = load_yaml_config(config_path)
    jobs_config: dict = config.get("jobs", {})

    if not jobs_config:
        raise ValueError("No 'jobs' key found in YAML config.")

    client = get_glue_client(region=region, profile=profile)
    live_jobs = fetch_live_jobs(list(jobs_config.keys()), client)

    results = []

    for job_name, expected_config in jobs_config.items():
        live_config = live_jobs.get(job_name)

        # Job doesn't exist in AWS at all
        if live_config is None:
            results.append(
                JobDriftResult(
                    job_name=job_name,
                    status="missing",
                    error=f"Job '{job_name}' not found in AWS Glue.",
                )
            )
            continue

        # Normalize both sides before comparison
        normalized_expected = normalize_job(expected_config)
        normalized_actual = normalize_job(live_config)

        drifts = _compare_jobs(normalized_expected, normalized_actual)

        results.append(
            JobDriftResult(
                job_name=job_name,
                status="drifted" if drifts else "ok",
                drifts=drifts,
            )
        )

    return results
