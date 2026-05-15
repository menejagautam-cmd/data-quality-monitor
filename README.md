# Data Quality Monitor

An automated data quality assessment tool that scans incoming datasets, evaluates them across five quality dimensions, calculates a weighted quality score (0–100 with letter grade), and generates a professional HTML report with findings and actionable recommendations.

**AImed at solving a real problem:** Organizations with manual data entry processes often don't know their data has quality issues until a dashboard shows wrong numbers or a decision is made on bad information. This tool catches problems at the source — before they propagate downstream.

![Report Preview](screenshots/report_preview.png)

## What It Does

1. **Scans** incoming Excel or CSV files from an input directory
2. **Checks** five quality dimensions: Completeness, Uniqueness, Validity, Consistency, and Timeliness
3. **Scores** each dimension from 0–100 using configurable weights
4. **Grades** overall quality (A through F) based on weighted scores
5. **Generates** an HTML report with a visual scorecard, detailed findings, and prioritized recommendations
6. **Logs** every check for full auditability

## Quality Dimensions

| Dimension | What It Checks | Weight |
|-----------|---------------|--------|
| **Completeness** | Missing/null values per column | 30% |
| **Validity** | Values within expected numeric ranges, unexpected categories | 25% |
| **Uniqueness** | Duplicate rows and duplicate values in key columns | 20% |
| **Consistency** | Mixed date formats, whitespace issues, capitalization variants | 15% |
| **Timeliness** | Future dates, impossibly old dates, completion-before-submission | 10% |

## Quick Start

```bash
git clone https://github.com/menejagautam-cmd/data-quality-monitor.git
cd data-quality-monitor
pip install -r requirements.txt
python src/monitor.py --generate-data
```

Then open `data/reports/quality_report_maintenance_work_orders.html` in your browser.

## Output

- `data/reports/quality_report_*.html` — visual quality scorecard and findings
- `logs/quality_check_*.log` — full audit trail of every check

## Project Structure

```
data-quality-monitor/
├── config/
│   └── quality_rules.json         # Thresholds, ranges, weights (fully configurable)
├── src/
│   ├── monitor.py                 # Main orchestrator
│   ├── generate_sample_data.py    # Creates realistic test data with quality issues
│   ├── quality_checks.py          # Five quality check categories
│   ├── scoring.py                 # Weighted scoring and grading engine
│   └── reporting.py               # HTML report generator
├── data/
│   ├── input/                     # Drop files here to scan
│   └── reports/                   # Auto-generated quality reports
└── logs/                          # Audit trail
```

## Configuration

All rules, thresholds, and weights live in `config/quality_rules.json`. No code changes needed to adjust quality standards. Examples:

- Change the acceptable range for a numeric field
- Add new expected categorical values
- Adjust dimension weights (e.g., make completeness worth 40% instead of 30%)
- Change grade thresholds (e.g., require 95+ for an A)

## Tech Stack

- **Python 3.10+**
- **pandas** — data manipulation and analysis
- **openpyxl** — Excel file I/O
- **JSON** — configurable quality rules

## Context

This project was inspired by real data quality challenges encountered during project working with financial records and operational data. In organizations transitioning from manual processes to data-driven decision-making, the first step is understanding the quality of the data you already have — before building dashboards or models on top of it.
