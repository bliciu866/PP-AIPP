from __future__ import annotations

import html
import json
from pathlib import Path

from .models import VerificationReport


def write_json(report: VerificationReport, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def write_markdown(report: VerificationReport, target: Path) -> Path:
    lines = [
        "# PP-AIPP Verification Report",
        "",
        f"**Version:** {report.version}",
        f"**Status:** {report.status}",
        f"**Started:** {report.started_at}",
        f"**Finished:** {report.finished_at}",
        "",
        "| Check | Status | Duration (s) | Return code |",
        "|---|---:|---:|---:|",
    ]
    for check in report.checks:
        lines.append(f"| {check.name} | {check.status.value} | {check.duration_seconds:.4f} | {check.return_code if check.return_code is not None else '—'} |")
    lines.extend(["", "## Environment", ""])
    for key, value in report.environment.items():
        lines.append(f"- **{key}:** `{value}`")
    lines.extend(["", "## Check details", ""])
    for check in report.checks:
        lines.extend([f"### {check.name}", "", f"Status: **{check.status.value}**", ""])
        if check.details:
            lines.extend(["```json", json.dumps(check.details, indent=2, ensure_ascii=False), "```", ""])
        if check.stdout:
            lines.extend(["<details><summary>stdout</summary>", "", "```text", check.stdout, "```", "</details>", ""])
        if check.stderr:
            lines.extend(["<details><summary>stderr</summary>", "", "```text", check.stderr, "```", "</details>", ""])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def write_html(report: VerificationReport, target: Path) -> Path:
    rows = "".join(
        f"<tr><td>{html.escape(c.name)}</td><td>{c.status.value}</td><td>{c.duration_seconds:.4f}</td><td>{c.return_code if c.return_code is not None else '—'}</td></tr>"
        for c in report.checks
    )
    page = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>PP-AIPP Verification</title>
<style>body{{font-family:system-ui,sans-serif;max-width:980px;margin:40px auto;padding:0 20px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}.PASSED{{color:#176b2c}}.FAILED{{color:#a40000}}</style></head>
<body><h1>PP-AIPP Verification Report</h1><p>Version: <strong>{html.escape(report.version)}</strong></p><p>Status: <strong class=\"{report.status}\">{report.status}</strong></p>
<table><thead><tr><th>Check</th><th>Status</th><th>Duration (s)</th><th>Return code</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return target
