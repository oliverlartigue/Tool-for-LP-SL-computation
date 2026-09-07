import pandas as pd
import os

main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation'


# Assumptions:
df_SL_splitWeek = pd.read_excel(os.path.join(main_folder_path, 'Output_SL_hours_splitWeek.xlsx'))
df_LP = pd.read_csv(os.path.join(main_folder_path, 'Input Files\LP SL.csv'))

# -----------------------------------------------------------------------------
# PREPARE JOIN FIELDS
# -----------------------------------------------------------------------------

# Convert SplitWeekStartDate6am to date-only
df_SL_splitWeek["joinDate"] = pd.to_datetime(
    df_SL_splitWeek["SplitWeekStartDate6am"],
    errors="coerce"
).dt.normalize()

# Convert LP fromDate to date-only
df_LP["joinDate"] = pd.to_datetime(
    df_LP["fromDate"],
    errors="coerce"
).dt.normalize()

# Ensure metricValue is numeric
df_LP["metricValue"] = pd.to_numeric(
    df_LP["metricValue"],
    errors="coerce"
)


# -----------------------------------------------------------------------------
# FILTER AND PIVOT LP DATA
# -----------------------------------------------------------------------------

required_metrics = [
    "Calendar Time",
    "Scheduled Loss",
    "Scheduled Loss Percentage",
]

df_LP_metrics = (
    df_LP.loc[
        df_LP["metricName"].isin(required_metrics),
        ["Circuit_Name", "joinDate", "metricName", "metricValue"]
    ]
    .pivot_table(
        index=["Circuit_Name", "joinDate"],
        columns="metricName",
        values="metricValue",
        aggfunc="first"
    )
    .reset_index()
    .rename(
        columns={
            "Calendar Time": "LP_CalendarHours",
            "Scheduled Loss": "LP_SLHours",
            "Scheduled Loss Percentage": "LP_SLPct",
        }
    )
)

# Convert percentage from values such as 3.125 to 0.03125
df_LP_metrics["LP_SLPct"] = (
    df_LP_metrics["LP_SLPct"] / 100
)


# -----------------------------------------------------------------------------
# JOIN LP VALUES TO THE FIRST DATAFRAME
# -----------------------------------------------------------------------------

df_comparison = df_SL_splitWeek.merge(
    df_LP_metrics,
    left_on=["asset", "joinDate"],
    right_on=["Circuit_Name", "joinDate"],
    how="left",
    validate="many_to_one"
)

# Remove temporary and duplicate join columns
df_comparison = df_comparison.drop(
    columns=["Circuit_Name", "joinDate"]
)


# -----------------------------------------------------------------------------
# OPTIONAL: SELECT AND ORDER THE FINAL COLUMNS
# -----------------------------------------------------------------------------

df_comparison = df_comparison[
    [
        "asset",
        "SplitWeekCode",
        "SplitWeekStartDate6am",
        "SplitWeekEndDate6am",
        "CalendarHours",
        "SLHours",
        "SLPct",
        "LP_CalendarHours",
        "LP_SLHours",
        "LP_SLPct",
    ]
]

print(df_comparison)
output_file = os.path.join(main_folder_path, 'Output_SL_comparison_for testing.xlsx')
df_comparison.to_excel(output_file, index=False)
print(f"Saved to: {output_file}")