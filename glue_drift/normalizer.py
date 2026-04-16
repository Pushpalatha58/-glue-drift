"""
normalizer.py
-------------
Strips AWS auto-injected keys and normalizes Glue job configs
for fair comparison. Based on real buildspec drift-detection logic.
"""

import json

# Keys AWS auto-injects into DefaultArguments — not user-controlled
AWS_AUTO_INJECTED_ARGS = {
    "--job-language",
    "--class",
}

# Top-level Glue job keys AWS manages internally — skip in comparison
AWS_MANAGED_KEYS = {
    "CreatedOn",
    "LastModifiedOn",
    "LastModifiedBy",
    "JobRunQueuingEnabled",
    "SourceControlDetails",
    "ProfileName",
}


def normalize_arguments(args: dict) -> dict:
    """Remove AWS auto-injected keys from DefaultArguments."""
    return {k: v for k, v in args.items() if k not in AWS_AUTO_INJECTED_ARGS}


def normalize_job(job: dict) -> dict:
    """
    Normalize a Glue job config dict for comparison.
    - Removes AWS-managed top-level keys
    - Strips auto-injected DefaultArguments keys
    - Sorts all keys for stable JSON comparison
    """
    normalized = {k: v for k, v in job.items() if k not in AWS_MANAGED_KEYS}

    if "DefaultArguments" in normalized:
        normalized["DefaultArguments"] = normalize_arguments(
            normalized["DefaultArguments"]
        )

    return normalized


def to_comparable_json(job: dict) -> str:
    """Convert a normalized job dict to a stable JSON string for diffing."""
    return json.dumps(job, sort_keys=True, separators=(",", ":"), default=str)
