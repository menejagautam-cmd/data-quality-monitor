"""
reporting.py
Generates a professional HTML quality report with a scorecard,
dimension breakdowns, and actionable recommendations.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

COLORS = {
    "PASS": "#2CA58D", "WARNING": "#F4A940", "FAIL": "#E8614D",
    "A": "#2CA58D", "B": "#6CC4A1", "C": "#F4A940", "D": "#E88B4D", "F": "#E8614D",
    "navy": "#1B2A4A", "teal": "#2CA58D", "coral": "#E8614D", "gold": "#F4A940"
}


def grade_color(grade):
    return COLORS.get(grade, "#636E72")


def status_badge(status):
    color = COLORS.get(status, "#636E72")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600">{status}</span>'


def generate_recommendations(check_results, scorecard):
    """Generate actionable recommendations based on findings."""
    recs = []
    dims = scorecard.get("dimensions", {})
    
    if dims.get("completeness", {}).get("score", 100) < 80:
        worst_cols = sorted(
            check_results.get("completeness", {}).get("columns", {}).items(),
            key=lambda x: x[1]["null_percentage"], reverse=True
        )[:3]
        cols_str = ", ".join([f"<strong>{c}</strong> ({v['null_percentage']}%)" for c, v in worst_cols if v["null_percentage"] > 0])
        recs.append(f"<strong>Fix missing data:</strong> Columns with highest null rates: {cols_str}. Add required-field validation at the point of entry.")
    
    if dims.get("uniqueness", {}).get("score", 100) < 80:
        dupes = check_results.get("uniqueness", {}).get("exact_duplicates", 0)
        recs.append(f"<strong>Remove duplicates:</strong> Found {dupes} exact duplicate rows. Implement unique constraints on key columns like work_order_id.")
    
    if dims.get("validity", {}).get("score", 100) < 80:
        recs.append("<strong>Add range validation:</strong> Out-of-range values detected in numeric fields. Add min/max validation rules at data entry.")
    
    if dims.get("consistency", {}).get("score", 100) < 80:
        recs.append("<strong>Standardize formats:</strong> Mixed date formats and inconsistent capitalization found. Use dropdown menus and date pickers instead of free-text entry.")
    
    if dims.get("timeliness", {}).get("score", 100) < 80:
        recs.append("<strong>Validate dates:</strong> Future dates and logically impossible date sequences found. Add date range validation at entry.")
    
    if not recs:
        recs.append("Data quality is strong across all dimensions. Continue monitoring to maintain standards.")
    
    return recs


def generate_html_report(check_results, scorecard, output_path):
    """Generate the full HTML quality report."""
    logger.info("Generating quality report...")
    
    overall = scorecard["overall_score"]
    grade = scorecard["grade"]
    dims = scorecard["dimensions"]
    recs = generate_recommendations(check_results, scorecard)
    dataset_info = check_results.get("dataset_info", {})
    
    # Dimension score bars
    dim_bars = ""
    for dim_name, dim_info in dims.items():
        score = dim_info["score"]
        color = grade_color(dim_info["grade"])
        weight = f"{dim_info['weight']:.0%}"
        dim_bars += f'''
        <div style="margin-bottom:16px">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span style="font-weight:600;text-transform:capitalize">{dim_name}</span>
                <span>{score}/100 ({dim_info["grade"]}) — weight: {weight}</span>
            </div>
            <div style="background:#e9ecef;border-radius:8px;height:24px;overflow:hidden">
                <div style="background:{color};height:100%;width:{score}%;border-radius:8px;transition:width 0.5s"></div>
            </div>
        </div>'''
    
    # Completeness detail table
    comp_rows = ""
    for col, info in sorted(
        check_results.get("completeness", {}).get("columns", {}).items(),
        key=lambda x: x[1]["null_percentage"], reverse=True
    ):
        if info["null_count"] > 0:
            comp_rows += f'<tr><td>{col}</td><td>{info["null_count"]}</td><td>{info["null_percentage"]}%</td><td>{status_badge(info["status"])}</td></tr>'
    
    # Validity detail
    validity_rows = ""
    for col, info in check_results.get("validity", {}).get("numeric_issues", {}).items():
        if info["total_invalid"] > 0:
            samples = ", ".join([str(v) for v in info["sample_invalid"][:3]])
            validity_rows += f'<tr><td>{col}</td><td>{info["expected_range"]}</td><td>{info["total_invalid"]}</td><td>{samples}</td><td>{status_badge("FAIL")}</td></tr>'
    
    # Recommendations
    rec_html = "".join([f'<li style="margin-bottom:10px;line-height:1.6">{r}</li>' for r in recs])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Quality Report</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',Tahoma,sans-serif; background:#f5f6fa; color:#2d3436; }}
        .header {{ background:linear-gradient(135deg,{COLORS["navy"]},{COLORS["teal"]}); color:white; padding:40px; text-align:center; }}
        .header h1 {{ font-size:28px; margin-bottom:8px; }}
        .header p {{ opacity:0.85; font-size:14px; }}
        .container {{ max-width:1100px; margin:0 auto; padding:30px 20px; }}
        .grade-card {{ background:white; border-radius:16px; padding:40px; text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.1); margin-bottom:30px; }}
        .grade-circle {{ width:120px; height:120px; border-radius:50%; background:{grade_color(grade)}; color:white; display:inline-flex; align-items:center; justify-content:center; font-size:48px; font-weight:700; margin-bottom:16px; }}
        .score-text {{ font-size:24px; font-weight:600; color:{COLORS["navy"]}; }}
        .section {{ background:white; border-radius:10px; padding:30px; margin-bottom:20px; box-shadow:0 2px 10px rgba(0,0,0,0.08); }}
        .section h2 {{ font-size:20px; color:{COLORS["navy"]}; margin-bottom:20px; padding-bottom:10px; border-bottom:2px solid {COLORS["teal"]}; }}
        table {{ width:100%; border-collapse:collapse; margin-top:15px; }}
        th {{ background:{COLORS["navy"]}; color:white; padding:12px 16px; text-align:left; font-size:13px; text-transform:uppercase; }}
        td {{ padding:10px 16px; border-bottom:1px solid #eee; font-size:14px; }}
        tr:hover {{ background:#f8f9fa; }}
        .rec-list {{ padding-left:20px; }}
        .footer {{ text-align:center; padding:30px; color:#636e72; font-size:12px; }}
        .info-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:30px; }}
        .info-card {{ background:white; border-radius:10px; padding:20px; text-align:center; box-shadow:0 2px 10px rgba(0,0,0,0.08); }}
        .info-card .value {{ font-size:28px; font-weight:700; color:{COLORS["navy"]}; }}
        .info-card .label {{ font-size:12px; color:#636e72; text-transform:uppercase; margin-top:4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Quality Report</h1>
        <p>Generated {datetime.now().strftime("%B %d, %Y at %I:%M %p")} | {dataset_info.get("rows", 0):,} rows analyzed | {dataset_info.get("columns", 0)} columns</p>
    </div>
    <div class="container">
        <div class="grade-card">
            <div class="grade-circle">{grade}</div>
            <div class="score-text">{overall} / 100</div>
            <p style="color:#636e72;margin-top:8px">Overall Data Quality Score</p>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <div class="value">{check_results.get("completeness",{}).get("total_nulls",0):,}</div>
                <div class="label">Missing Values</div>
            </div>
            <div class="info-card">
                <div class="value">{check_results.get("uniqueness",{}).get("exact_duplicates",0)}</div>
                <div class="label">Duplicate Rows</div>
            </div>
            <div class="info-card">
                <div class="value">{sum(v.get("total_invalid",0) for v in check_results.get("validity",{}).get("numeric_issues",{}).values())}</div>
                <div class="label">Invalid Values</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Quality Score Breakdown</h2>
            {dim_bars}
        </div>
        
        <div class="section">
            <h2>Completeness — Missing Data</h2>
            {"<table><thead><tr><th>Column</th><th>Null Count</th><th>Null %</th><th>Status</th></tr></thead><tbody>" + comp_rows + "</tbody></table>" if comp_rows else "<p style='color:#2CA58D;font-weight:600'>All columns are 100% complete.</p>"}
        </div>
        
        <div class="section">
            <h2>Validity — Out-of-Range Values</h2>
            {"<table><thead><tr><th>Column</th><th>Expected Range</th><th>Invalid Count</th><th>Sample Values</th><th>Status</th></tr></thead><tbody>" + validity_rows + "</tbody></table>" if validity_rows else "<p style='color:#2CA58D;font-weight:600'>All values within expected ranges.</p>"}
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ol class="rec-list">{rec_html}</ol>
        </div>
        
        <div class="section">
            <h2>Report Details</h2>
            <p style="color:#636e72;line-height:1.8">
                <strong>Dimensions checked:</strong> Completeness, Uniqueness, Validity, Consistency, Timeliness<br>
                <strong>Configuration:</strong> quality_rules.json (weights and thresholds are fully configurable)<br>
                <strong>Dataset:</strong> {dataset_info.get("rows",0):,} rows × {dataset_info.get("columns",0)} columns
            </p>
        </div>
    </div>
    <div class="footer">Data Quality Monitor | Built with Python, pandas</div>
</body>
</html>'''
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    
    logger.info(f"Report saved to: {output_path}")
    return output_path
