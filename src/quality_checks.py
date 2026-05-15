"""
quality_checks.py
Core data quality checking engine. Runs five categories of checks
against any incoming dataset and returns detailed findings.

Quality Dimensions:
    1. Completeness — Are there missing values?
    2. Uniqueness — Are there duplicates?
    3. Validity — Do values fall within expected ranges?
    4. Consistency — Are formats and categories uniform?
    5. Timeliness — Are dates reasonable and current?
"""

import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================
# 1. COMPLETENESS CHECKS
# ============================================================

def check_completeness(df):
    """
    Check each column for missing/null values.
    Returns a dict with per-column null counts and percentages.
    """
    logger.info("Running completeness checks...")
    
    results = {
        "total_rows": len(df),
        "empty_rows": int(df.isnull().all(axis=1).sum()),
        "columns": {}
    }
    
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = round(null_count / len(df) * 100, 2) if len(df) > 0 else 0
        
        results["columns"][col] = {
            "null_count": null_count,
            "null_percentage": null_pct,
            "status": "PASS" if null_pct == 0 else ("WARNING" if null_pct < 5 else "FAIL")
        }
    
    total_nulls = sum(v["null_count"] for v in results["columns"].values())
    results["total_nulls"] = total_nulls
    
    logger.info(f"  Total nulls found: {total_nulls}")
    logger.info(f"  Empty rows: {results['empty_rows']}")
    
    return results


# ============================================================
# 2. UNIQUENESS CHECKS
# ============================================================

def check_uniqueness(df, key_columns=None):
    """
    Check for exact duplicate rows and duplicate values in key columns.
    Key columns should contain unique values (like work order IDs).
    """
    logger.info("Running uniqueness checks...")
    
    results = {
        "exact_duplicates": int(df.duplicated().sum()),
        "key_column_duplicates": {}
    }
    
    if key_columns:
        for col in key_columns:
            if col in df.columns:
                dupes = df[col].dropna().duplicated()
                dupe_count = int(dupes.sum())
                dupe_values = df[col].dropna()[dupes].unique().tolist()[:10]
                
                results["key_column_duplicates"][col] = {
                    "duplicate_count": dupe_count,
                    "sample_duplicates": dupe_values,
                    "status": "PASS" if dupe_count == 0 else "FAIL"
                }
    
    logger.info(f"  Exact duplicate rows: {results['exact_duplicates']}")
    for col, info in results["key_column_duplicates"].items():
        logger.info(f"  Duplicates in '{col}': {info['duplicate_count']}")
    
    return results


# ============================================================
# 3. VALIDITY CHECKS
# ============================================================

def check_validity(df, numeric_ranges=None, categorical_values=None):
    """
    Check that values fall within expected ranges (numeric)
    and match expected categories (categorical).
    """
    logger.info("Running validity checks...")
    
    results = {
        "numeric_issues": {},
        "categorical_issues": {}
    }
    
    # Numeric range checks
    if numeric_ranges:
        for col, bounds in numeric_ranges.items():
            if col not in df.columns:
                continue
            
            col_data = pd.to_numeric(df[col], errors="coerce")
            min_val = bounds.get("min")
            max_val = bounds.get("max")
            
            below_min = int((col_data < min_val).sum()) if min_val is not None else 0
            above_max = int((col_data > max_val).sum()) if max_val is not None else 0
            
            invalid_values = []
            if below_min > 0:
                invalid_values.extend(col_data[col_data < min_val].dropna().tolist()[:5])
            if above_max > 0:
                invalid_values.extend(col_data[col_data > max_val].dropna().tolist()[:5])
            
            total_invalid = below_min + above_max
            results["numeric_issues"][col] = {
                "below_minimum": below_min,
                "above_maximum": above_max,
                "total_invalid": total_invalid,
                "expected_range": f"{min_val} to {max_val}",
                "sample_invalid": invalid_values[:5],
                "status": "PASS" if total_invalid == 0 else "FAIL"
            }
            
            if total_invalid > 0:
                logger.warning(f"  {col}: {total_invalid} values outside range [{min_val}, {max_val}]")
    
    # Categorical value checks
    if categorical_values:
        for col, expected in categorical_values.items():
            if col not in df.columns:
                continue
            
            actual = df[col].dropna().unique()
            expected_lower = [v.lower().strip() for v in expected]
            
            unexpected = []
            for val in actual:
                if str(val).lower().strip() not in expected_lower:
                    unexpected.append(str(val))
            
            results["categorical_issues"][col] = {
                "unexpected_count": len(unexpected),
                "unexpected_values": unexpected[:10],
                "expected_values": expected,
                "status": "PASS" if len(unexpected) == 0 else "WARNING"
            }
            
            if unexpected:
                logger.warning(f"  {col}: {len(unexpected)} unexpected values found")
    
    return results


# ============================================================
# 4. CONSISTENCY CHECKS
# ============================================================

def check_consistency(df, date_columns=None):
    """
    Check for format consistency within columns:
    - Mixed date formats
    - Inconsistent capitalization
    - Leading/trailing whitespace
    """
    logger.info("Running consistency checks...")
    
    results = {
        "date_format_issues": {},
        "whitespace_issues": {},
        "capitalization_issues": {}
    }
    
    # Date format consistency
    if date_columns:
        for col in date_columns:
            if col not in df.columns:
                continue
            
            non_null = df[col].dropna().astype(str)
            
            # Detect format patterns
            iso_pattern = r"^\d{4}-\d{2}-\d{2}$"
            us_pattern = r"^\d{2}/\d{2}/\d{4}$"
            dash_pattern = r"^\d{2}-\d{2}-\d{4}$"
            
            iso_count = int(non_null.str.match(iso_pattern).sum())
            us_count = int(non_null.str.match(us_pattern).sum())
            dash_count = int(non_null.str.match(dash_pattern).sum())
            other_count = int(len(non_null) - iso_count - us_count - dash_count)
            
            formats_found = {}
            if iso_count > 0: formats_found["YYYY-MM-DD"] = iso_count
            if us_count > 0: formats_found["MM/DD/YYYY"] = us_count
            if dash_count > 0: formats_found["MM-DD-YYYY"] = dash_count
            if other_count > 0: formats_found["other"] = other_count
            
            is_consistent = len(formats_found) <= 1
            results["date_format_issues"][col] = {
                "formats_found": formats_found,
                "is_consistent": is_consistent,
                "status": "PASS" if is_consistent else "FAIL"
            }
            
            if not is_consistent:
                logger.warning(f"  {col}: Multiple date formats detected: {formats_found}")
    
    # Whitespace issues
    text_cols = df.select_dtypes(include=["object"]).columns
    for col in text_cols:
        non_null = df[col].dropna().astype(str)
        has_leading = int(non_null.str.startswith(" ").sum())
        has_trailing = int(non_null.str.endswith(" ").sum())
        total = has_leading + has_trailing
        
        if total > 0:
            results["whitespace_issues"][col] = {
                "leading_spaces": has_leading,
                "trailing_spaces": has_trailing,
                "total_affected": total,
                "status": "WARNING"
            }
    
    # Capitalization consistency in categorical columns
    for col in text_cols:
        non_null = df[col].dropna().astype(str)
        unique_raw = non_null.nunique()
        unique_lower = non_null.str.lower().str.strip().nunique()
        
        if unique_lower < unique_raw:
            diff = unique_raw - unique_lower
            results["capitalization_issues"][col] = {
                "unique_values": unique_raw,
                "unique_after_normalization": unique_lower,
                "variants_reducible": diff,
                "status": "WARNING"
            }
    
    return results


# ============================================================
# 5. TIMELINESS CHECKS
# ============================================================

def check_timeliness(df, date_columns=None, max_future_days=7, max_past_days=730):
    """
    Check that dates are reasonable — not in the far future or distant past.
    Also checks for logical issues like completion before submission.
    """
    logger.info("Running timeliness checks...")
    
    results = {
        "date_range_issues": {},
        "logical_issues": {}
    }
    
    now = datetime.now()
    
    if date_columns:
        for col in date_columns:
            if col not in df.columns:
                continue
            
            parsed = pd.to_datetime(df[col], format="mixed", errors="coerce")
            
            future_cutoff = now + timedelta(days=max_future_days)
            past_cutoff = now - timedelta(days=max_past_days)
            
            future_dates = int((parsed > future_cutoff).sum())
            old_dates = int((parsed < past_cutoff).sum())
            
            results["date_range_issues"][col] = {
                "future_dates": future_dates,
                "old_dates": old_dates,
                "total_issues": future_dates + old_dates,
                "status": "PASS" if (future_dates + old_dates) == 0 else "WARNING"
            }
            
            if future_dates > 0:
                logger.warning(f"  {col}: {future_dates} dates in the future")
            if old_dates > 0:
                logger.warning(f"  {col}: {old_dates} dates older than {max_past_days} days")
    
    # Check completion before submission
    if "date_submitted" in df.columns and "date_completed" in df.columns:
        submitted = pd.to_datetime(df["date_submitted"], format="mixed", errors="coerce")
        completed = pd.to_datetime(df["date_completed"], format="mixed", errors="coerce")
        
        both_valid = submitted.notna() & completed.notna()
        backwards = int((completed[both_valid] < submitted[both_valid]).sum())
        
        results["logical_issues"]["completion_before_submission"] = {
            "count": backwards,
            "status": "PASS" if backwards == 0 else "FAIL"
        }
        
        if backwards > 0:
            logger.warning(f"  {backwards} records where completion date is before submission date")
    
    return results


# ============================================================
# RUN ALL CHECKS
# ============================================================

def run_all_checks(df, config):
    """
    Execute all five quality check categories and return combined results.
    """
    rules = config.get("quality_rules", {})
    
    logger.info("=" * 60)
    logger.info("DATA QUALITY ASSESSMENT — STARTING")
    logger.info(f"Dataset: {len(df)} rows × {len(df.columns)} columns")
    logger.info("=" * 60)
    
    results = {
        "dataset_info": {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        },
        "completeness": check_completeness(df),
        "uniqueness": check_uniqueness(
            df,
            key_columns=rules.get("uniqueness", {}).get("key_columns", [])
        ),
        "validity": check_validity(
            df,
            numeric_ranges=rules.get("validity", {}).get("numeric_ranges"),
            categorical_values=rules.get("validity", {}).get("categorical_values")
        ),
        "consistency": check_consistency(
            df,
            date_columns=rules.get("consistency", {}).get("date_columns")
        ),
        "timeliness": check_timeliness(
            df,
            date_columns=rules.get("consistency", {}).get("date_columns"),
            max_future_days=rules.get("timeliness", {}).get("max_future_days", 7),
            max_past_days=rules.get("timeliness", {}).get("max_past_days", 730)
        )
    }
    
    logger.info("\nAll quality checks complete.")
    return results
