"""
test_checker.py
---------------
Unit tests for glue-drift core logic.
No AWS credentials required — uses mocked Glue responses.
"""

import pytest
from unittest.mock import MagicMock, patch

from glue_drift.normalizer import normalize_job, normalize_arguments, to_comparable_json
from glue_drift.checker import _compare_jobs, JobDriftResult


# ─── Normalizer Tests ────────────────────────────────────────────────────────

class TestNormalizeArguments:

    def test_strips_auto_injected_keys(self):
        args = {
            "--job-language": "python",
            "--class": "GlueApp",
            "--enable-metrics": "true",
            "--TempDir": "s3://my-bucket/tmp/",
        }
        result = normalize_arguments(args)
        assert "--job-language" not in result
        assert "--class" not in result
        assert "--enable-metrics" in result
        assert "--TempDir" in result

    def test_empty_args(self):
        assert normalize_arguments({}) == {}

    def test_no_injected_keys_unchanged(self):
        args = {"--enable-metrics": "true"}
        assert normalize_arguments(args) == args


class TestNormalizeJob:

    def test_strips_managed_keys(self):
        job = {
            "Name": "my-job",
            "CreatedOn": "2024-01-01",
            "LastModifiedOn": "2024-06-01",
            "LastModifiedBy": "admin",
            "GlueVersion": "4.0",
        }
        result = normalize_job(job)
        assert "CreatedOn" not in result
        assert "LastModifiedOn" not in result
        assert "LastModifiedBy" not in result
        assert result["Name"] == "my-job"
        assert result["GlueVersion"] == "4.0"

    def test_normalizes_default_arguments(self):
        job = {
            "Name": "my-job",
            "DefaultArguments": {
                "--job-language": "python",
                "--enable-metrics": "true",
            },
        }
        result = normalize_job(job)
        assert "--job-language" not in result["DefaultArguments"]
        assert "--enable-metrics" in result["DefaultArguments"]


class TestToComparableJson:

    def test_stable_key_order(self):
        d1 = {"b": 1, "a": 2}
        d2 = {"a": 2, "b": 1}
        assert to_comparable_json(d1) == to_comparable_json(d2)

    def test_different_values_differ(self):
        d1 = {"a": 1}
        d2 = {"a": 2}
        assert to_comparable_json(d1) != to_comparable_json(d2)


# ─── Checker Tests ────────────────────────────────────────────────────────────

class TestCompareJobs:

    def test_no_drift(self):
        job = {"Name": "my-job", "GlueVersion": "4.0", "WorkerType": "G.1X"}
        drifts = _compare_jobs(job, job)
        assert drifts == []

    def test_detects_simple_drift(self):
        expected = {"WorkerType": "G.1X", "NumberOfWorkers": 2}
        actual = {"WorkerType": "G.2X", "NumberOfWorkers": 2}
        drifts = _compare_jobs(expected, actual)
        assert len(drifts) == 1
        assert drifts[0].field == "WorkerType"
        assert drifts[0].expected == "G.1X"
        assert drifts[0].actual == "G.2X"

    def test_detects_nested_dict_drift(self):
        expected = {"DefaultArguments": {"--enable-metrics": "true", "--TempDir": "s3://a/"}}
        actual = {"DefaultArguments": {"--enable-metrics": "true", "--TempDir": "s3://b/"}}
        drifts = _compare_jobs(expected, actual)
        assert len(drifts) == 1
        assert drifts[0].field == "DefaultArguments"

    def test_detects_missing_field_in_actual(self):
        expected = {"WorkerType": "G.1X", "Timeout": 120}
        actual = {"WorkerType": "G.1X"}
        drifts = _compare_jobs(expected, actual)
        assert any(d.field == "Timeout" for d in drifts)

    def test_detects_extra_field_in_actual(self):
        expected = {"WorkerType": "G.1X"}
        actual = {"WorkerType": "G.1X", "MaxRetries": 3}
        drifts = _compare_jobs(expected, actual)
        assert any(d.field == "MaxRetries" for d in drifts)

    def test_no_drift_with_key_order_difference(self):
        expected = {"DefaultArguments": {"--b": "2", "--a": "1"}}
        actual = {"DefaultArguments": {"--a": "1", "--b": "2"}}
        drifts = _compare_jobs(expected, actual)
        assert drifts == []


# ─── JobDriftResult Tests ─────────────────────────────────────────────────────

class TestJobDriftResult:

    def test_ok_has_no_drift(self):
        r = JobDriftResult(job_name="job-a", status="ok")
        assert not r.has_drift

    def test_drifted_has_drift(self):
        r = JobDriftResult(job_name="job-b", status="drifted")
        assert r.has_drift

    def test_missing_has_drift(self):
        r = JobDriftResult(job_name="job-c", status="missing")
        assert r.has_drift
