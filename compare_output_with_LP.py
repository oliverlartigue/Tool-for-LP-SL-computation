# Oliver lartigue - Sep 2026
### Compare SL hours by splitweek by asset computed by Python script with the SL from Live Parameters

import pandas as pd
import os


def compare_SL_output_with_LP (df_SL_output, df_SL_LP):


    # PREPARE JOIN FIELDS
    # Convert SplitWeekStartDate6am to date-only
    df_SL_output["SplitWeekStartDate"] = pd.to_datetime(df_SL_output["SplitWeekStartDate6am"],errors="coerce").dt.normalize()
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
                "Calendar Time": "LP_CalendarHours",
                "Scheduled Loss": "LP_SLHours",
                "Scheduled Loss Percentage": "LP_SLPct",
            }
        )
    )

    # Convert percentage from values such as 3.125 to 0.03125
    df_SL_LP_pivoted ["LP_SLPct"] = (df_SL_LP_pivoted ["LP_SLPct"] / 100)

    # JOIN LP VALUES TO OUTPUT VALUES
    df_comparison = df_SL_output.merge(
        df_SL_LP_pivoted,
        left_on=["asset", "SplitWeekStartDate"],
        right_on=["Circuit_Name", "fromDate"],
        how="left",
        validate="many_to_one"
    )

    # Remove temporary and duplicate join columns
    df_comparison = df_comparison.drop(columns=["Circuit_Name", "SplitWeekStartDate"])

    # compute diff
    df_comparison['CTHours_Output_less_LP'] = (df_comparison['CalendarHours'] - df_comparison['LP_CalendarHours']).round(2)  # round(2) : round to have zero when diff is less than 2 decimals
    df_comparison['SLHours_Output_less_LP'] = (df_comparison['SLHours'] - df_comparison['LP_SLHours']).round(2)  # round(2) : round to have zero when diff is less than 2 decimals
    df_comparison['SLPct_Output_less_LP'] = (df_comparison['SLPct'] - df_comparison['LP_SLPct']).round(5) # round(5) : round to have zero when diff is less than 5 decimals

    
    # SELECT AND ORDER THE FINAL COLUMNS
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
            'CTHours_Output_less_LP',
            'SLHours_Output_less_LP',
            'SLPct_Output_less_LP'
        ]
    ]

    return df_comparison



### Test script compare_output_with_LP
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files'
    df_SL_splitWeek = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_compare_output_with_LP_outputsl.xlsx'))
    df_LP = pd.read_csv(os.path.join(main_folder_path, 'input_for_testing_compare_output_with_LP_lpsl.csv'))
    df_comparison = compare_SL_output_with_LP(df_SL_splitWeek,df_LP)
    output_file = os.path.join(main_folder_path, 'output_for_testing_compare_output_with_LP.xlsx')
    df_comparison.to_excel(output_file, index=False)
### End Test script

###     END of script