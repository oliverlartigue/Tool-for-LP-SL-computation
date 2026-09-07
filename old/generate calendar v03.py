import pandas as pd

def build_split_week_calendar(start_date, end_date):

    df = pd.DataFrame({
        "Date": pd.date_range(start_date, end_date, freq="D")
    })

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month

    iso = df["Date"].dt.isocalendar()
    df["ISOYear"] = iso.year
    df["WeekNumber"] = iso.week

    # Build split week start/end dates
    rows = []

    for (year, month), group in df.groupby(["Year", "Month"], sort=False):

        month_start = group["Date"].min()
        month_end = group["Date"].max()

        current_start = month_start

        while current_start <= month_end:

            week_end = current_start + pd.Timedelta(
                days=(6 - current_start.weekday())
            )
            week_end = min(week_end, month_end)

            for d in pd.date_range(current_start, week_end, freq="D"):
                rows.append({
                    "Date": d,
                    "SplitWeekStart": current_start,
                    "SplitWeekEnd": week_end
                })

            current_start = week_end + pd.Timedelta(days=1)

    split_df = pd.DataFrame(rows)

    df = df.merge(split_df, on="Date", how="left")

    # Determine if ISO week spans multiple months
    week_info = (
        df.groupby(["ISOYear", "WeekNumber"])
          .agg(
              FirstMonth=("Month", "min"),
              LastMonth=("Month", "max")
          )
          .reset_index()
    )

    df = df.merge(
        week_info,
        on=["ISOYear", "WeekNumber"],
        how="left"
    )

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

    return df[
        [
            "Date",
            "Year",
            "Month",
            "WeekNumber",
            "SplitWeekNumber",
            "SplitWeekStart",
            "SplitWeekEnd"
        ]
    ]


df_calendar = build_split_week_calendar(
    "2026-10-25",
    "2027-11-08"
)


output_file = (
    r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents"
    r"\31. Tool for LP SL computation\calendar.xlsx"
)

df_calendar.to_excel(output_file, index=False)
print(f"Saved to: {output_file}")