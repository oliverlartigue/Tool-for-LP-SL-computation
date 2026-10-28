# Oliver lartigue - Sep 2026
### Compare SL hours by splitweek by asset computed by Python script with the SL from Live Parameters and compare with the SL Auto Forward Adjustment from LP

import pandas as pd
import os

def split_LP_AutoFA_by_splitweek(df_LP_FA, df_calendar):  
### Input is a table with all auto froward adjustments for all assets from LP, output is a table with the FXP SL Forward adjustments with a value for each split week.
### Note LP FA table has start date and end date which corresponds already to a Split week bondary, however LP roll up forward adjustment when FA value is the same for multiple spLit weekS, the following procedure create a row for each split week / asset
    # Filter LP Forward Adjustments for FXP SL
    df_LP_FA = df_LP_FA[
        (df_LP_FA['assetClass'].isin(['Plant','Primary Crusher','Ship Loader','Car Dumper'])) & 
        (df_LP_FA['metricName'] == 'Scheduled Loss Planned Percentage')
        ]
    # Select and rename colomn in LP Forward Adjustments 
    df_LP_FA = df_LP_FA[[
        "assetGroup",
        "metricValue",
        "fromDate",            
        "toDate"
        ]].rename(
            columns={
                "assetGroup": "asset",
                "metricValue": "SLPct_LP_AutoFA"
            }
        )    
    # Keep one row per split week
    df_splitweeks = df_calendar[
        [
            "SplitWeekCode",
            "SplitWeekStartDate",
            "SplitWeekEndDate"
        ]].drop_duplicates()
    # Cross join LP rows with split weeks
    df_split = df_LP_FA.merge(
        df_splitweeks,
        how="cross"
        )
    # Keep split weeks inside each LP period
    df_split = df_split[
        (df_split["SplitWeekStartDate"] >= df_split["fromDate"])
        &
        (df_split["SplitWeekEndDate"] <= df_split["toDate"])
        ]
    # SELECT AND ORDER THE FINAL COLUMNS
    df_split = df_split[
        [
            "asset",
            "SplitWeekStartDate",            
            "SplitWeekEndDate",
            "SLPct_LP_AutoFA"            
        ]].sort_values(['asset', 'SplitWeekStartDate']).reset_index(drop=True)
    return df_split


def compare_SL_output_with_LP_weekly (df_SL_output, df_SL_LP, df_autoFA_LP):
### Input are a table with computed SL hours by asset / split week to be compared, a table with SL by asset / split week  from Live Parameters, and a table with SL Auto Forward Adjustment by asset / split week  from LP 
### Output is a table with a row for each asset / split week with columns with SL hours, SL %, SL Auto FA from Live Parameters and from a computation by a Python script and difference columns.
    # PREPARE JOIN FIELDS
    # Convert LP fromDate to date-only
    df_SL_LP["fromDate"] = pd.to_datetime(df_SL_LP["fromDate"],errors="coerce").dt.normalize()
    # Ensure metricValue is numeric
    df_SL_LP["metricValue"] = pd.to_numeric(df_SL_LP["metricValue"],errors="coerce")
    # FILTER AND PIVOT df_SL_LP
    required_metrics = [
        "Calendar Time",
        "Scheduled Loss",
        "Scheduled Loss Percentage",
        ]
    df_SL_LP_pivoted = (
        df_SL_LP.loc[
            df_SL_LP["metricName"].isin(required_metrics),
            ["Circuit_Name", "fromDate", "metricName", "metricValue"]
            ]
        .pivot_table(
            index=["Circuit_Name", "fromDate"],
            columns="metricName",
            values="metricValue",
            aggfunc="first"
            )
        .reset_index()
        .rename(
            columns={
                "Circuit_Name": "asset",
                "fromDate": "SplitWeekStartDate",
                "Calendar Time": "CalendarHours_LP",
                "Scheduled Loss": "SLHours_LP_AllSL",
                "Scheduled Loss Percentage": "SLPct_LP_AllSL"
                }
            )
        )
    # Convert percentage from values such as 3.125 to 0.03125
    if "SLPct_LP_AllSL" in df_SL_LP_pivoted.columns:  # check that 'SLPct_LP_AllSL' exist before making a computation
        df_SL_LP_pivoted["SLPct_LP_AllSL"] = df_SL_LP_pivoted["SLPct_LP_AllSL"] / 100
    else:
        print("WARNING: SLPct_LP_AllSL (aka Scheduled Loss Percentage) column is missing in LP data source")

    # Keep only the required Auto FA columns 
    df_autoFA_LP = df_autoFA_LP[ ["asset","SplitWeekStartDate","SLPct_LP_AutoFA"]]
    # JOIN LP Auto FA to LP SL
    df_LP = df_SL_LP_pivoted.merge(
        df_autoFA_LP,
        on=["asset", "SplitWeekStartDate"],
        how="left",
        validate="one_to_one"
        )
    # Calculate weighted Auto FA SL
    # CalendarHours_LP is used because Auto FA comes from Live Parameters
    if "SLPct_LP_AutoFA" in df_LP.columns:
        df_LP["SLHours_LP_AutoFA"] = (df_LP["CalendarHours_LP"] * df_LP["SLPct_LP_AutoFA"])
    else:
        print("WARNING: SLPct_LP_AutoFA is missing - annual Auto FA comparison not calculated")
        df_LP["SLHours_LP_AutoFA"] = pd.NA
    # Reanme some df_SL_output
    df_SL_output = df_SL_output.rename(
            columns={
                "CalendarHours": "CalendarHours_Output",
                "SLHours": "SLHours_Output",
                "SLPct": "SLPct_Output",
            }
        )
    # JOIN LP VALUES TO OUTPUT VALUES
    df_comparison = df_SL_output.merge(
        df_LP,
        on=["asset", "SplitWeekStartDate"],
        how="left",
        validate="many_to_one"
        )
    # compute diff
    df_comparison['CTHours_Output_less_LP'] = (df_comparison['CalendarHours_Output'] - df_comparison['CalendarHours_LP']).round(2)  # round(2) : round to have zero when diff is less than 2 decimals
    df_comparison['SLHours_Output_less_LP_AllSL'] = (df_comparison['SLHours_Output'] - df_comparison['SLHours_LP_AllSL']).round(2)  # round(2) : round to have zero when diff is less than 2 decimals
    df_comparison['SLHours_Output_less_LP_AutoFA'] = (df_comparison['SLHours_Output'] - df_comparison['SLHours_LP_AutoFA']).round(2)  # round(2) : round to have zero when diff is less than 2 decimals
    if "SLPct_LP_AllSL" in df_comparison.columns:      # SLPct LP AllSL comparison
        df_comparison['SLPct_Output_less_LP_AllSL'] = (df_comparison['SLPct_Output'] - df_comparison['SLPct_LP_AllSL']).round(5)
    else:
        print("WARNING: SLPct_LP_AllSL is missing - comparison not calculated")
        df_comparison['SLPct_LP_AllSL'] = pd.NA
        df_comparison['SLPct_Output_less_LP_AllSL'] = pd.NA
    if "SLPct_LP_AutoFA" in df_comparison.columns:      # SLPct LP AutoFA comparison
        df_comparison['SLPct_Output_less_LP_AutoFA'] = (df_comparison['SLPct_Output'] - df_comparison['SLPct_LP_AutoFA']).round(5)
    else:
        print("WARNING: SLPct_LP_AutoFA is missing - comparison not calculated")
        df_comparison['SLPct_LP_AutoFA'] = pd.NA
        df_comparison['SLPct_Output_less_LP_AutoFA'] = pd.NA
    # SELECT AND ORDER THE FINAL COLUMNS
    df_comparison = df_comparison[[
            "asset",
            "SplitWeekCode",
            "SplitWeekStartDate",
            "SplitWeekEndDate",            
            "CalendarHours_Output",
            "SLHours_Output",
            "SLPct_Output",
            "CalendarHours_LP",
            "SLHours_LP_AllSL",
            "SLPct_LP_AllSL",
            "SLHours_LP_AutoFA",
            "SLPct_LP_AutoFA",
            'CTHours_Output_less_LP',
            'SLHours_Output_less_LP_AllSL',
            'SLPct_Output_less_LP_AllSL',
            'SLHours_Output_less_LP_AutoFA',
            'SLPct_Output_less_LP_AutoFA'
        ]]
    return df_comparison

def compare_SL_output_with_LP_annual(df_comparison):
    """
    Input:
        Split-week comparison output from compare_SL_output_with_LP().

    Output:
        One row per asset / year with annual Calendar Hours, SL Hours,
        SL percentages, LP Auto FA and annual differences.
    """
    df_annual_source = df_comparison.copy()
    # Create calendar year
    df_annual_source["Year"] = (df_annual_source["SplitWeekStartDate"].dt.year)
    # # Calculate weighted Auto FA SL before grouping
    # # CalendarHours_LP is used because Auto FA comes from Live Parameters
    # if "SLPct_LP_AutoFA" in df_annual_source.columns:
    #     df_annual_source["SLHours_LP_AutoFA"] = (df_annual_source["CalendarHours_LP"]* df_annual_source["SLPct_LP_AutoFA"])
    # else:
    #     print("WARNING: SLPct_LP_AutoFA is missing - annual Auto FA comparison not calculated")
    #     df_annual_source["SLHours_LP_AutoFA_Equivalent"] = pd.NA
    # Sum hours by asset and year
    df_annual = (
        df_annual_source.groupby(
            ["asset", "Year"],
            as_index=False
            )
        .agg(
            SplitWeekStartDate=("SplitWeekStartDate", "min"),
            SplitWeekEndDate=("SplitWeekEndDate", "max"),
            CalendarHours_Output=("CalendarHours_Output", "sum"),
            SLHours_Output=("SLHours_Output", "sum"),
            CalendarHours_LP=("CalendarHours_LP", "sum"),
            SLHours_LP_AllSL=("SLHours_LP_AllSL", "sum"),
            SLHours_LP_AutoFA=("SLHours_LP_AutoFA","sum")
            )
        ).rename(
            columns={
                "SplitWeekStartDate": "YearStartDate",
                "SplitWeekEndDate": "YearEndDate"
                }
            )
    # Calculate annual percentages from annual hours
    df_annual["SLPct_Output"] = (df_annual["SLHours_Output"] / df_annual["CalendarHours_Output"])
    df_annual["SLPct_LP_AllSL"] = (df_annual["SLHours_LP_AllSL"] / df_annual["CalendarHours_LP"])
    df_annual["SLPct_LP_AutoFA"] = (df_annual["SLHours_LP_AutoFA"]/ df_annual["CalendarHours_LP"])
    # Calculate annual differences
    df_annual["CTHours_Output_less_LP"] = (df_annual["CalendarHours_Output"] - df_annual["CalendarHours_LP"]).round(2)
    df_annual["SLHours_Output_less_LP_AllSL"] = (df_annual["SLHours_Output"] - df_annual["SLHours_LP_AllSL"]).round(2)
    df_annual["SLHours_Output_less_LP_AutoFA"] = (df_annual["SLHours_Output"] - df_annual["SLHours_LP_AutoFA"]).round(2)
    df_annual["SLPct_Output_less_LP_AllSL"] = (df_annual["SLPct_Output"] - df_annual["SLPct_LP_AllSL"]).round(5)
    df_annual["SLPct_Output_less_LP_AutoFA"] = (df_annual["SLPct_Output"]- df_annual["SLPct_LP_AutoFA"]).round(5)
    # Select and order final columns
    df_annual = df_annual[
        [
            "asset",
            "Year",
            "YearStartDate",
            "YearEndDate",
            "CalendarHours_Output",
            "SLHours_Output",
            "SLPct_Output",
            "CalendarHours_LP",
            "SLHours_LP_AllSL",
            "SLPct_LP_AllSL",
             "SLHours_LP_AutoFA",           
            "SLPct_LP_AutoFA",
            "CTHours_Output_less_LP",
            "SLHours_Output_less_LP_AllSL",           
            "SLPct_Output_less_LP_AllSL",
            "SLHours_Output_less_LP_AutoFA",            
            "SLPct_Output_less_LP_AutoFA"
        ]
    ].sort_values(
        ["asset", "Year"]
    ).reset_index(drop=True)

    return df_annual





### Test script compare_output_with_LP
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files'
    df_Output_SL = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_compare_output_with_LP_outputsl.xlsx'))
    df_LP_SL = pd.read_csv(os.path.join(main_folder_path, 'input_for_testing_compare_output_with_LP_lpsl.csv'))
    df_calendar = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_calendar.xlsx'))    
    df_LP_FA = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_LP auto_forward_adjustments.xlsx'))
    df_autoFA_split_LP = split_LP_AutoFA_by_splitweek(df_LP_FA, df_calendar)
    df_comparison_weekly = compare_SL_output_with_LP_weekly(df_Output_SL ,df_LP_SL,df_autoFA_split_LP)
    df_comparison_annual = compare_SL_output_with_LP_annual(df_comparison_weekly)
    output_file = os.path.join(main_folder_path, 'output_for_testing_compare_output_with_LP.xlsx')
    # Write weekly and annual results into separate tabs
    with pd.ExcelWriter(output_file,engine="openpyxl") as writer:
        df_comparison_weekly.to_excel(
            writer,
            sheet_name="SplitWeek Comparison",
            index=False
        )
        df_comparison_annual.to_excel(
            writer,
            sheet_name="Annual Comparison",
            index=False
        )
### End Test script

###     END of script