"""
monitor.py
Main orchestrator for the Data Quality Monitor.

Scans incoming data files, runs five categories of quality checks,
calculates a weighted quality score, and generates an HTML report
with findings and recommendations.

Usage:
    python src/monitor.py                   # Run on existing data
    python src/monitor.py --generate-data   # Generate sample data first

This tool is designed as an early warning system — catch data quality
problems before they reach dashboards and business decisions.
"""

import pandas as pd
import os
import sys
import json
import logging
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.quality_checks import run_all_checks
from src.scoring import calculate_overall_score
from src.reporting import generate_html_report


def setup_logging():
    """Configure logging to file and console."""
    log_dir = os.path.join(PROJECT_ROOT, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"quality_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def load_config(config_path):
    """Load quality rules configuration."""
    with open(config_path, "r") as f:
        config = json.load(f)
    logging.info(f"Loaded quality rules from: {config_path}")
    return config


def load_data(data_dir):
    """Load all Excel/CSV files from the input directory."""
    dataframes = []
    
    for filename in sorted(os.listdir(data_dir)):
        filepath = os.path.join(data_dir, filename)
        
        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(filepath)
            logging.info(f"Loaded '{filename}': {len(df)} rows × {len(df.columns)} columns")
            dataframes.append((filename, df))
        elif filename.endswith(".csv"):
            df = pd.read_csv(filepath)
            logging.info(f"Loaded '{filename}': {len(df)} rows × {len(df.columns)} columns")
            dataframes.append((filename, df))
    
    if not dataframes:
        raise FileNotFoundError(f"No data files found in {data_dir}")
    
    return dataframes


def run_monitor():
    """
    Execute the full data quality monitoring pipeline.
    
    Steps:
        1. Load configuration and data files
        2. Run all five quality check categories
        3. Calculate weighted quality score and grade
        4. Generate HTML report with findings and recommendations
        5. Log everything for auditability
    """
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("DATA QUALITY MONITOR — START")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Paths
    data_dir = os.path.join(PROJECT_ROOT, "data", "input")
    reports_dir = os.path.join(PROJECT_ROOT, "data", "reports")
    config_path = os.path.join(PROJECT_ROOT, "config", "quality_rules.json")
    
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate sample data if needed
    if "--generate-data" in sys.argv or not os.path.exists(data_dir) or not os.listdir(data_dir):
        logger.info("Generating sample data...")
        from src.generate_sample_data import main as generate_data
        generate_data()
    
    # Load config
    config = load_config(config_path)
    
    # Load data
    logger.info(f"\nLoading data from: {data_dir}")
    data_files = load_data(data_dir)
    
    # Process each file
    for filename, df in data_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"ANALYZING: {filename}")
        logger.info(f"{'='*60}")
        
        # Run quality checks
        check_results = run_all_checks(df, config)
        
        # Calculate score
        scorecard = calculate_overall_score(check_results, config)
        
        # Generate report
        report_name = f"quality_report_{filename.rsplit('.', 1)[0]}.html"
        report_path = os.path.join(reports_dir, report_name)
        generate_html_report(check_results, scorecard, report_path)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"RESULTS FOR: {filename}")
        logger.info(f"{'='*60}")
        logger.info(f"Overall Score: {scorecard['overall_score']}/100 (Grade: {scorecard['grade']})")
        logger.info(f"Report: {report_path}")
    
    logger.info(f"\n{'='*60}")
    logger.info("DATA QUALITY MONITOR — COMPLETE")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    run_monitor()
