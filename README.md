# glue-drift

**Detect configuration drift in AWS Glue jobs.**

`glue-drift` compares your live AWS Glue job configurations against a source-of-truth YAML file and reports exactly what has drifted — field by field.

Built for data engineering teams managing multi-environment Glue deployments (DEV / QA / UAT / PROD).

---

## Why glue-drift?

AWS Glue jobs can drift from their intended configuration due to:
- Manual edits in the AWS Console
- Failed or partial deployments
- Auto-injected AWS keys polluting comparisons
- Key-order differences creating false positives

`glue-drift` handles all of these correctly.

---

## Installation

```bash
pip install glue-drift
```

---

## Quickstart

**1. Create your source-of-truth `jobs.yaml`:**

```yaml
jobs:
  my-glue-job:
    Name: my-glue-job
    Role: arn:aws:iam::123456789012:role/my-glue-role
    GlueVersion: "4.0"
    WorkerType: G.1X
    NumberOfWorkers: 2
    Timeout: 120
    MaxRetries: 0
    Command:
      Name: glueetl
      ScriptLocation: s3://my-bucket/scripts/my_script.py
      PythonVersion: "3"
    DefaultArguments:
      --enable-metrics: "true"
      --TempDir: s3://my-temp-bucket/
```

**2. Run the drift check:**

```bash
glue-drift check --config jobs.yaml
```

**3. Example output:**

```
============================================================
  GLUE DRIFT REPORT
============================================================
  Jobs checked : 3
  OK       : 1
  Drifted  : 1
  Missing  : 1
============================================================

  ✔  my-glue-job-ok

  ✘  my-glue-job-drifted  [DRIFTED]
      Field: WorkerType
        Expected: G.1X
        Actual:   G.2X

  ✘  my-glue-job-missing  [MISSING in AWS]
      Job 'my-glue-job-missing' not found in AWS Glue.

============================================================
  ❌ Drift detected! Review the above jobs.
============================================================
```

---

## CLI Options

```
glue-drift check --config jobs.yaml [OPTIONS]

Options:
  -c, --config PATH       Path to source-of-truth YAML config  [required]
  -r, --region TEXT       AWS region  [default: us-east-2]
  -p, --profile TEXT      AWS CLI profile name (optional)
  -o, --output PATH       Write JSON report to file (e.g. report.json)
  --fail-on-drift         Exit code 1 if drift found (for CI/CD pipelines)
  --version               Show version and exit
  --help                  Show this message and exit
```

---

## CI/CD Integration

Use `--fail-on-drift` to block deployments when drift is detected:

```yaml
# In your buildspec.yaml or GitHub Actions workflow:
- name: Check Glue job drift
  run: glue-drift check --config jobs.yaml --output drift-report.json --fail-on-drift
```

---

## Python API

Use `glue-drift` programmatically:

```python
from glue_drift import check_all_jobs, print_terminal_report

results = check_all_jobs(config_path="jobs.yaml", region="us-east-2")
print_terminal_report(results)

for result in results:
    if result.has_drift:
        print(f"Job {result.job_name} has drifted!")
        for drift in result.drifts:
            print(f"  {drift.field}: expected={drift.expected}, actual={drift.actual}")
```

---

## What glue-drift normalizes automatically

- **AWS auto-injected keys** stripped: `--job-language`, `--class`
- **AWS managed metadata** ignored: `CreatedOn`, `LastModifiedOn`, `LastModifiedBy`
- **JSON key ordering** normalized — no false positives from key-order differences

---

## Authentication

`glue-drift` uses standard boto3 credential resolution:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. IAM role (recommended for EC2 / Lambda / CI runners)
3. AWS CLI profile via `--profile`

---

## Development

```bash
git clone https://github.com/Pushpalatha58/glue-drift
cd glue-drift
pip install -e ".[dev]"
pytest
```

---

## License

MIT
