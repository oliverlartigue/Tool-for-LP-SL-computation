import pandas as pd

def build_split_week_calendar(start_date, end_date):
    # Daily calendar
    df = pd.DataFrame({
        "Date": pd.date_range(start_date, end_date, freq="D")
    })

    # ISO week/year
    iso = df["Date"].dt.isocalendar()
    df["ISOYear"] = iso.year
    df["WeekNumber"] = iso.week

    # Basic date attributes
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.strftime("%B")
    df["IsMonthEnd"] = df["Date"].dt.is_month_end

    # Split-week numbering within each month
    split_rows = []

    for (year, month), group in df.groupby(["Year", "Month"], sort=False):
        month_start = group["Date"].min()
        month_end = group["Date"].max()

        current_start = month_start
        split_week = 1

        while current_start <= month_end:
            week_end = current_start + pd.Timedelta(days=6 - current_start.weekday())
            week_end = min(week_end, month_end)

            dates = pd.date_range(current_start, week_end, freq="D")
            days = len(dates)

            for d in dates:
                split_rows.append({
                    "Date": d,
                    "SplitWeek": split_week,
                    "SplitWeekStart": current_start,
                    "SplitWeekEnd": week_end,
                    "DaysInSplitWeek": days,
                    "FractionOfSplitWeek": 1 / days
                })

            split_week += 1
            current_start = week_end + pd.Timedelta(days=1)

    split_df = pd.DataFrame(split_rows)

    # Merge split-week details back
    df = df.merge(split_df, on="Date", how="left")

    # Build A/B week numbering where ISO week crosses month boundary
    week_info = (
        df.groupby(["ISOYear", "WeekNumber"])
          .agg(
              FirstMonth=("Month", "min"),
              LastMonth=("Month", "max")
          )
          .reset_index()
    )

    df = df.merge(week_info, on=["ISOYear", "WeekNumber"], how="left")

    df["SplitWeekNumber"] = df["WeekNumber"].astype(str)

    mask = df["FirstMonth"] != df["LastMonth"]

    df.loc[
        mask & (df["Month"] == df["FirstMonth"]),
        "SplitWeekNumber"
    ] = df["WeekNumber"].astype(str) + "A"

    df.loc[
        mask & (df["Month"] == df["LastMonth"]),
        "SplitWeekNumber"
    ] = df["WeekNumber"].astype(str) + "B"

    return df.drop(columns=["FirstMonth", "LastMonth"])


# Usage
df_calendar = build_split_week_calendar(
    "2026-10-25",
    "2027-11-08"
)

print(df_calendar)

output_file = (
    r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents"
    r"\31. Tool for LP SL computation\calendar.xlsx"
)

df_calendar.to_excel(output_file, index=False)
print(f"Saved to: {output_file}")