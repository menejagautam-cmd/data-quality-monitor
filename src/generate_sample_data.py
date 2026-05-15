"""
generate_sample_data.py
Generates synthetic maintenance work order data with intentional quality issues.
Simulates real-world data from an HVAC/mechanical services company where
data entry is manual and quality control is minimal.

Run this to create test data: python src/generate_sample_data.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

np.random.seed(42)

NUM_RECORDS = 500
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)

TECHNICIANS = [
    "Alex Rivera", "Jordan Smith", "Casey Martinez", "Morgan Lee",
    "Taylor Brown", "Jamie Wilson", "Riley Anderson", "Dakota Chen",
    "Avery Thomas", "Quinn Jackson"
]

CUSTOMERS = [
    "Riverside Medical Center", "Henrico County Schools", "Capital One HQ",
    "VCU Health System", "Richmond Convention Center", "Dominion Energy",
    "CarMax Corporate", "Altria Group", "Markel Corporation",
    "West Creek Business Park", "Innsbrook Office Complex", "Short Pump Mall"
]

LOCATIONS = [
    "Richmond - Downtown", "Richmond - West End", "Henrico", "Chesterfield",
    "Glen Allen", "Midlothian", "Short Pump", "Mechanicsville"
]

SERVICE_TYPES = [
    "HVAC Repair", "HVAC Installation", "Plumbing Repair",
    "Plumbing Installation", "Preventive Maintenance", "Emergency Service",
    "Electrical", "General Maintenance"
]

PRIORITIES = ["Low", "Medium", "High", "Emergency"]
STATUSES = ["Open", "In Progress", "Completed", "Cancelled"]


def random_dates(n, start, end):
    """Generate n random dates between start and end."""
    days_range = (end - start).days
    return [start + timedelta(days=np.random.randint(0, days_range)) for _ in range(n)]


def generate_clean_data(n):
    """Generate the base clean dataset."""
    submit_dates = random_dates(n, START_DATE, END_DATE)
    
    data = {
        "work_order_id": [f"WO-{5000 + i}" for i in range(n)],
        "date_submitted": [d.strftime("%Y-%m-%d") for d in submit_dates],
        "date_completed": [
            (d + timedelta(days=np.random.randint(1, 30))).strftime("%Y-%m-%d")
            if np.random.random() > 0.15 else None
            for d in submit_dates
        ],
        "customer": np.random.choice(CUSTOMERS, n),
        "location": np.random.choice(LOCATIONS, n),
        "service_type": np.random.choice(SERVICE_TYPES, n),
        "priority": np.random.choice(PRIORITIES, n, p=[0.3, 0.35, 0.25, 0.1]),
        "status": np.random.choice(STATUSES, n, p=[0.1, 0.15, 0.65, 0.1]),
        "technician": np.random.choice(TECHNICIANS, n),
        "temperature": np.round(np.random.uniform(55, 85, n), 1),
        "runtime_hours": np.round(np.random.uniform(100, 5000, n), 0),
        "cost": np.round(np.random.uniform(150, 12000, n), 2),
        "response_time_hours": np.round(np.random.uniform(0.5, 72, n), 1),
        "notes": np.random.choice(
            ["Routine service", "Parts replaced", "Follow-up needed",
             "Customer satisfied", "Warranty claim", "Urgent request",
             "Scheduled maintenance", "Callback required", ""], n
        )
    }
    return pd.DataFrame(data)


def inject_quality_issues(df):
    """
    Inject realistic data quality problems that mirror what happens
    when data entry is manual and there's no validation in place.
    """
    n = len(df)
    
    # --- COMPLETENESS ISSUES (missing values) ---
    # 8% of customers missing
    mask = np.random.random(n) < 0.08
    df.loc[mask, "customer"] = np.nan
    
    # 6% of locations missing
    mask = np.random.random(n) < 0.06
    df.loc[mask, "location"] = np.nan
    
    # 4% of technician names missing
    mask = np.random.random(n) < 0.04
    df.loc[mask, "technician"] = np.nan
    
    # 10% of costs missing
    mask = np.random.random(n) < 0.10
    df.loc[mask, "cost"] = np.nan
    
    # --- VALIDITY ISSUES (out-of-range values) ---
    # Negative costs (data entry errors)
    df.loc[15, "cost"] = -350.00
    df.loc[89, "cost"] = -1200.50
    
    # Impossible temperature readings
    df.loc[42, "temperature"] = -50.0
    df.loc[200, "temperature"] = 350.0
    
    # Negative response times
    df.loc[77, "response_time_hours"] = -4.5
    
    # Runtime hours exceeding a year
    df.loc[150, "runtime_hours"] = 10000
    
    # --- UNIQUENESS ISSUES (duplicates) ---
    # Add 5 exact duplicate rows
    dupes = df.sample(5, random_state=42)
    df = pd.concat([df, dupes], ignore_index=True)
    
    # Add 3 rows with duplicate work order IDs but different data
    df.loc[n, "work_order_id"] = df.loc[0, "work_order_id"]
    df.loc[n + 1, "work_order_id"] = df.loc[1, "work_order_id"]
    df.loc[n + 2, "work_order_id"] = df.loc[2, "work_order_id"]
    
    # --- CONSISTENCY ISSUES (format problems) ---
    # Mix date formats
    format_mask = np.random.random(len(df)) < 0.15
    for idx in df[format_mask].index:
        if pd.notna(df.loc[idx, "date_submitted"]):
            try:
                d = datetime.strptime(str(df.loc[idx, "date_submitted"]), "%Y-%m-%d")
                df.loc[idx, "date_submitted"] = d.strftime("%m/%d/%Y")
            except (ValueError, TypeError):
                pass
    
    # Inconsistent capitalization in service types
    cap_mask = np.random.random(len(df)) < 0.08
    df.loc[cap_mask, "service_type"] = df.loc[cap_mask, "service_type"].apply(
        lambda x: x.lower() if pd.notna(x) else x
    )
    
    # Inconsistent priority values
    df.loc[30, "priority"] = "HIGH"
    df.loc[55, "priority"] = "low"
    df.loc[100, "priority"] = "Med"
    df.loc[180, "priority"] = "EMERGENCY"
    df.loc[250, "priority"] = "Urgent"
    
    # Extra whitespace in names
    space_mask = np.random.random(len(df)) < 0.06
    df.loc[space_mask, "technician"] = df.loc[space_mask, "technician"].apply(
        lambda x: f"  {x}  " if pd.notna(x) else x
    )
    
    # --- TIMELINESS ISSUES ---
    # Future dates
    df.loc[10, "date_submitted"] = "2027-06-15"
    df.loc[25, "date_submitted"] = "2028-01-01"
    
    # Very old dates
    df.loc[60, "date_submitted"] = "2019-03-15"
    
    # Completion date before submission date
    df.loc[90, "date_submitted"] = "2025-08-15"
    df.loc[90, "date_completed"] = "2025-07-01"
    
    # --- EMPTY ROWS (manual Excel entry artifact) ---
    empty_rows = pd.DataFrame({col: [np.nan] for col in df.columns})
    df = pd.concat([df.iloc[:250], empty_rows, empty_rows, empty_rows, df.iloc[250:]], ignore_index=True)
    
    return df


def main():
    """Generate sample data with quality issues and save to Excel."""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "input")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating synthetic maintenance work order data...\n")
    
    # Generate and inject issues
    df = generate_clean_data(NUM_RECORDS)
    df = inject_quality_issues(df)
    
    # Save
    output_path = os.path.join(output_dir, "maintenance_work_orders.xlsx")
    df.to_excel(output_path, index=False)
    
    print(f"Generated {len(df)} records with intentional quality issues")
    print(f"Saved to: {output_path}")
    
    # Print summary of injected issues
    print(f"\nInjected issues:")
    print(f"  Missing values: ~{df.isnull().sum().sum()} nulls across all columns")
    print(f"  Duplicate rows: {df.duplicated().sum()}")
    print(f"  Mixed date formats: ~15% of date_submitted")
    print(f"  Out-of-range values: 6 invalid numeric entries")
    print(f"  Inconsistent categories: 5 non-standard priority values")
    print(f"  Empty rows: 3 completely blank rows")


if __name__ == "__main__":
    main()
