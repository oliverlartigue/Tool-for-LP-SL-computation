import pandas as pd
import os

def build_split_week_calendar(start_date, end_date):
# call the fuction : df_calendar = build_split_week_calendar("2026-10-25","2027-11-08")
# function output a dataframe with rows for each date and has columns for date, year, month, week, day and for split weeek (SplitWeekCode, SplitWeekStartDate6am,SplitWeekEndDate6am)
# split week Monday to Sunday, unless start/end of month
    df = pd.DataFrame({
        "Date": pd.date_range(start_date, end_date, freq="D")
    })

    df["Year"] = df["Date"].dt.year
    df["MonthNumber"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day

    iso = df["Date"].dt.isocalendar()
    df["ISOYear"] = iso.year
    df["WeekNumber"] = iso.week

    # Build split-week start/end dates
    rows = []

    for (year, month), group in df.groupby(
        ["Year", "MonthNumber"],
        sort=False
    ):

        month_start = group["Date"].min()
        month_end = group["Date"].max()

        current_start = month_start

        while current_start <= month_end:

            week_end = current_start + pd.Timedelta(
                days=(6 - current_start.weekday())
            )
            week_end = min(week_end, month_end)

            for d in pd.date_range(
                current_start,
                week_end,
                freq="D"
            ):
                rows.append({
                    "Date": d,
                    "SplitWeekStart": current_start,
                    "SplitWeekEnd": week_end
                })

            current_start = (
                week_end + pd.Timedelta(days=1)
            )

    split_df = pd.DataFrame(rows)

    df = df.merge(
        split_df,
        on="Date",
        how="left"
    )

    # Identify ISO weeks that span two months
    week_info = (
        df.groupby(
            ["ISOYear", "WeekNumber"]
        )
        .agg(
            FirstMonth=("MonthNumber", "min"),
            LastMonth=("MonthNumber", "max")
        )
        .reset_index()
    )

    df = df.merge(
        week_info,
        on=["ISOYear", "WeekNumber"],
        how="left"
    )

    # Default week code
    df["SplitWeekCode"] = (
        df["WeekNumber"].astype(str)
    )

    # Apply A/B suffix when ISO week crosses month end
    mask = (
        df["FirstMonth"]
        !=
        df["LastMonth"]
    )

    df.loc[
        mask &
        (
            df["MonthNumber"]
            ==
            df["FirstMonth"]
        ),
        "SplitWeekCode"
    ] = (
        df["WeekNumber"].astype(str)
        + "A"
    )

    df.loc[
        mask &
        (
            df["MonthNumber"]
            ==
            df["LastMonth"]
        ),
        "SplitWeekCode"
    ] = (
        df["WeekNumber"].astype(str)
        + "B"
    )

    # 6am versions
    df["Date6am"] = (
        df["Date"]
        + pd.Timedelta(hours=6)
    )

    df["SplitWeekStartDate6am"] = (
        df["SplitWeekStart"]
        + pd.Timedelta(hours=6)
    )

    df["SplitWeekEndDate6am"] = (
        df["SplitWeekEnd"]
        + pd.Timedelta(days=1,hours=6)
    )

    return df[
        [
            "Date",
            "Date6am",
            "Year",
            "MonthNumber",
            "Day",
            "WeekNumber",
            "SplitWeekCode",
            "SplitWeekStartDate6am",
            "SplitWeekEndDate6am"
        ]
    ]


### Test script generate_calendar
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Files Input and Output'
    period_start_date = "2026-10-01"
    period_end_date = "2027-12-31"
    df_out = build_split_week_calendar(period_start_date,period_end_date)
    output_file_1 = os.path.join(main_folder_path, 'output_for_testing_generate_calendar.xlsx')
    df_out.to_excel(output_file_1, index=False)
    print(f"Saved to: {output_file_1}")
### End of Test


###     END of script
