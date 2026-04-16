"""
fetcher.py
----------
Fetches live Glue job configurations from AWS using boto3.
"""

import boto3
from botocore.exceptions import ClientError


def get_glue_client(region: str = "us-east-2", profile: str = None):
    """Create a boto3 Glue client. Uses default credentials (IAM role / env vars)."""
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("glue", region_name=region)


def fetch_live_job(job_name: str, client) -> dict | None:
    """
    Fetch a single Glue job config from AWS.
    Returns None if the job does not exist.
    """
    try:
        response = client.get_job(JobName=job_name)
        return response["Job"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityNotFoundException":
            return None
        raise


def fetch_live_jobs(job_names: list[str], client) -> dict[str, dict | None]:
    """
    Fetch multiple Glue job configs from AWS.
    Returns a dict: {job_name: job_config or None if not found}
    """
    results = {}
    for name in job_names:
        results[name] = fetch_live_job(name, client)
    return results
