# PP-AIPP Verification Report

**Version:** 3.0.0-alpha.6
**Status:** PASSED
**Started:** 2026-08-03T18:01:41.361058+00:00
**Finished:** 2026-08-03T18:01:45.302891+00:00

| Check | Status | Duration (s) | Return code |
|---|---:|---:|---:|
| compile | PASSED | 0.5772 | 0 |
| unit_and_integration_tests | PASSED | 2.1684 | 0 |
| gold_master_integration | PASSED | 1.1934 | 0 |

## Environment

- **python:** `3.13.5`
- **platform:** `Linux-6.12.13-x86_64-with-glibc2.41`
- **executable:** `/opt/pyvenv/bin/python`

## Check details

### compile

Status: **PASSED**

### unit_and_integration_tests

Status: **PASSED**

<details><summary>stdout</summary>

```text
.....................                                                    [100%]

```
</details>

### gold_master_integration

Status: **PASSED**

```json
{
  "source": "[CONTROLLED GOLD MASTER DOCX]",
  "report": "./reports/production/gold_master/import_report.json",
  "import_summary": {
    "book_id": "verification-book",
    "parsed_recipes": 80,
    "imported_recipes": 80,
    "ingredients": 589,
    "method_steps": 183,
    "conditional_pass": 11,
    "errors": 0,
    "warnings": 50
  }
}
```

Production import executed successfully; detailed controlled-source logs remain outside the public repository.
