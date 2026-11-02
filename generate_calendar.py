import pandas as pd
import os

def build_split_week_calendar(start_date, end_date):
# call the fuction : df_calendar = build_split_week_calendar("2026-10-25","2027-11-08")
# function output a dataframe with rows for each date and has columns for date, year, month, week, day and for split weeek (SplitWeekCode, SplitWeekStartDate6am,SplitWeekEndDate6am)
# split week Monday to Sunday, unless start/end of month
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    df = pd.DataFrame({"Date": pd.date_range(start_date - pd.Timedelta(days=7),end_date,freq="D")})  #create a dataframe with all dates from 7 days before the requested start date so that the split weeek code are correct for the first week of the requested period 
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
                    "SplitWeekStartDate": current_start,
                    "SplitWeekEndDate": week_end
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

    # Default week code
    df["SplitWeekCode"] = df["WeekNumber"].astype(str)

    # Find split periods within each ISO week
    split_periods = (
        df.groupby(
            ["ISOYear", "WeekNumber", "SplitWeekStartDate"],
            as_index=False
        )
        .agg(
            FirstDate=("Date", "min")
        )
    )

    # Earliest split period = A
    split_periods["MinSplitWeekStartDate"] = (
        split_periods.groupby(
            ["ISOYear", "WeekNumber"]
        )["SplitWeekStartDate"]
        .transform("min")
    )

    # Latest split period = B
    split_periods["MaxSplitWeekStartDate"] = (
        split_periods.groupby(
            ["ISOYear", "WeekNumber"]
        )["SplitWeekStartDate"]
        .transform("max")
    )

    split_periods["Suffix"] = ""

    split_periods.loc[
        split_periods["SplitWeekStartDate"]
        ==
        split_periods["MinSplitWeekStartDate"],
        "Suffix"
    ] = "A"

    split_periods.loc[
        split_periods["SplitWeekStartDate"]
        ==
        split_periods["MaxSplitWeekStartDate"],
        "Suffix"
    ] = "B"

    # Weeks not split should have blank suffix
    split_counts = (
        split_periods.groupby(
            ["ISOYear", "WeekNumber"]
        )["SplitWeekStartDate"]
        .nunique()
        .reset_index(name="NumPeriods")
    )

    split_periods = split_periods.merge(
        split_counts,
        on=["ISOYear", "WeekNumber"],
        how="left"
    )

    split_periods.loc[
        split_periods["NumPeriods"] == 1,
        "Suffix"
    ] = ""

    df = df.merge(
        split_periods[
            [
                "ISOYear",
                "WeekNumber",
                "SplitWeekStartDate",
                "Suffix"
            ]
        ],
        on=[
            "ISOYear",
            "WeekNumber",
            "SplitWeekStartDate"
        ],
        how="left"
    )

    df["SplitWeekCode"] = (
        df["WeekNumber"].astype(str)
        + df["Suffix"]
    )



    # 6am versions
    df["Date6am"] = (
        df["Date"]
        + pd.Timedelta(hours=6)
    )

    df["SplitWeekStartDate6am"] = (
        df["SplitWeekStartDate"]
        + pd.Timedelta(hours=6)
    )

    df["SplitWeekEndDate6am"] = (
        df["SplitWeekEndDate"]
        + pd.Timedelta(days=1,hours=6)
    )

    df = df[
        (df["Date"] >= start_date) &
        (df["Date"] <= end_date)
    ].copy()


    return df[
        [
            "Date",
            "Date6am",
            "Year",
            "MonthNumber",
            "Day",
            "WeekNumber",
            "SplitWeekCode",
            "SplitWeekStartDate",
            "SplitWeekEndDate",            
            "SplitWeekStartDate6am",
            "SplitWeekEndDate6am"
        ]
    ]


### Test script generate_calendar
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files'
    period_start_date = "2026-10-01"
    period_end_date = "2027-12-31"
    df_out = build_split_week_calendar(period_start_date,period_end_date)
    output_file_1 = os.path.join(main_folder_path, 'output_for_testing_generate_calendar.xlsx')
    df_out.to_excel(output_file_1, index=False)
    print(f"Saved to: {output_file_1}")
### End of Test


###     END of script
