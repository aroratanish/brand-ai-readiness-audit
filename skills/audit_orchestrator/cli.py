import argparse
import json

from .orchestrator import audit_site_report
from shared.report_formatter import format_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Brand AI Readiness Audit.")
    parser.add_argument("url", help="Public HTTP(S) website URL to audit")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Report output format (default: json)",
    )
    args = parser.parse_args()

    report = audit_site_report(args.url)
    if args.format == "text":
        print(format_report(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())