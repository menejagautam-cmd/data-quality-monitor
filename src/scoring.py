"""
scoring.py
Calculates an overall data quality score (0-100) based on weighted
results from all five quality dimensions.

Each dimension gets a score from 0-100, then they're combined using
configurable weights from quality_rules.json. The final score maps
to a letter grade (A through F).
"""

import logging

logger = logging.getLogger(__name__)


def score_completeness(results):
    """Score based on average completeness across all columns."""
    columns = results.get("columns", {})
    if not columns:
        return 100.0
    
    null_pcts = [v["null_percentage"] for v in columns.values()]
    avg_null_pct = sum(null_pcts) / len(null_pcts)
    
    # 0% nulls = 100 score, 20%+ nulls = 0 score
    score = max(0, 100 - (avg_null_pct * 5))
    return round(score, 1)


def score_uniqueness(results):
    """Score based on duplicate rate."""
    total_dupes = results.get("exact_duplicates", 0)
    key_dupes = sum(
        v.get("duplicate_count", 0) 
        for v in results.get("key_column_duplicates", {}).values()
    )
    
    total_issues = total_dupes + key_dupes
    
    if total_issues == 0:
        return 100.0
    elif total_issues < 5:
        return 85.0
    elif total_issues < 15:
        return 65.0
    elif total_issues < 30:
        return 40.0
    else:
        return 15.0


def score_validity(results):
    """Score based on numeric range violations and unexpected categories."""
    numeric_issues = sum(
        v.get("total_invalid", 0) 
        for v in results.get("numeric_issues", {}).values()
    )
    categorical_issues = sum(
        v.get("unexpected_count", 0) 
        for v in results.get("categorical_issues", {}).values()
    )
    
    total = numeric_issues + categorical_issues
    
    if total == 0:
        return 100.0
    elif total < 5:
        return 85.0
    elif total < 15:
        return 65.0
    elif total < 30:
        return 40.0
    else:
        return 15.0


def score_consistency(results):
    """Score based on format uniformity."""
    issues = 0
    
    # Date format inconsistencies
    for v in results.get("date_format_issues", {}).values():
        if not v.get("is_consistent", True):
            issues += len(v.get("formats_found", {})) - 1
    
    # Whitespace issues
    issues += len(results.get("whitespace_issues", {}))
    
    # Capitalization issues
    issues += sum(
        v.get("variants_reducible", 0) 
        for v in results.get("capitalization_issues", {}).values()
    )
    
    if issues == 0:
        return 100.0
    elif issues < 3:
        return 80.0
    elif issues < 8:
        return 60.0
    elif issues < 15:
        return 40.0
    else:
        return 20.0


def score_timeliness(results):
    """Score based on date reasonableness."""
    date_issues = sum(
        v.get("total_issues", 0) 
        for v in results.get("date_range_issues", {}).values()
    )
    logical_issues = sum(
        v.get("count", 0) 
        for v in results.get("logical_issues", {}).values()
    )
    
    total = date_issues + logical_issues
    
    if total == 0:
        return 100.0
    elif total < 3:
        return 80.0
    elif total < 10:
        return 60.0
    else:
        return 30.0


def calculate_overall_score(check_results, config):
    """
    Calculate weighted overall quality score and letter grade.
    """
    weights = config.get("scoring", {}).get("weights", {
        "completeness": 0.30,
        "uniqueness": 0.20,
        "validity": 0.25,
        "consistency": 0.15,
        "timeliness": 0.10
    })
    
    grade_thresholds = config.get("scoring", {}).get("grade_thresholds", {
        "A": 90, "B": 80, "C": 70, "D": 60, "F": 0
    })
    
    # Calculate individual dimension scores
    dimension_scores = {
        "completeness": score_completeness(check_results.get("completeness", {})),
        "uniqueness": score_uniqueness(check_results.get("uniqueness", {})),
        "validity": score_validity(check_results.get("validity", {})),
        "consistency": score_consistency(check_results.get("consistency", {})),
        "timeliness": score_timeliness(check_results.get("timeliness", {}))
    }
    
    # Calculate weighted overall score
    overall = sum(
        dimension_scores[dim] * weights.get(dim, 0.2)
        for dim in dimension_scores
    )
    overall = round(overall, 1)
    
    # Determine letter grade (check highest threshold first)
    grade = "F"
    for letter, threshold in sorted(grade_thresholds.items(), key=lambda x: x[1], reverse=True):
        if overall >= threshold:
            grade = letter
            break
    
    # Build scorecard
    scorecard = {
        "overall_score": overall,
        "grade": grade,
        "dimensions": {},
        "weights": weights
    }
    
    for dim, score in dimension_scores.items():
        dim_grade = "F"
        for letter, threshold in sorted(grade_thresholds.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                dim_grade = letter
                break
        
        scorecard["dimensions"][dim] = {
            "score": score,
            "grade": dim_grade,
            "weight": weights.get(dim, 0.2)
        }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"QUALITY SCORECARD")
    logger.info(f"{'='*60}")
    logger.info(f"Overall Score: {overall}/100 (Grade: {grade})")
    for dim, info in scorecard["dimensions"].items():
        logger.info(f"  {dim.capitalize():15s}: {info['score']:5.1f} ({info['grade']}) — weight: {info['weight']:.0%}")
    
    return scorecard
