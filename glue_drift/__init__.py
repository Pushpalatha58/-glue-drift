"""
glue-drift
----------
Detect configuration drift in AWS Glue jobs.
Compare live job configs against a source-of-truth YAML.
"""

__version__ = "0.1.0"
__author__ = "Pushpalatha58"

from glue_drift.checker import check_all_jobs, JobDriftResult
from glue_drift.reporter import print_terminal_report, write_json_report

__all__ = [
    "check_all_jobs",
    "JobDriftResult",
    "print_terminal_report",
    "write_json_report",
]
