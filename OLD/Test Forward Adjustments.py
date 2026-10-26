# Oliver lartigue - Oct 2026
### Prepare table with FXP SL auto froward adjustment by slsit week

import pandas as pd
import os

### Input is a table with all auto froward adjustments for all assets from LP, output is a table with the FXP SL Forward adjustments with a value for each split week.
### Note LP FA table has start date and end date which corresponds already to a Split week bondary, however LP roll up forward adjustment when FA value is the same for multiple spLit weekS, the following procedure create a row for each split week / asset

def split_LP_AutoFA_by_splitweek(df_LP_FA, df_calendar):  

    # Filter LP Forward Adjustments for FXP SL
    df_LP_FA = df_LP_FA[
        (df_LP_FA['assetClass'].isin(['Plant','Primary Crusher'])) & 
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
        ]
    ].drop_duplicates()

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


### Test script compare_output_with_LP
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files'
    df_LP_FA = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_LP auto_forward_adjustments.xlsx'))
    df_calendar = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_calendar.xlsx'))
    df_comparison = split_LP_AutoFA_by_splitweek(df_LP_FA, df_calendar)
    output_file = os.path.join(main_folder_path, 'output_for_testing_forward_adjustment.xlsx')
    df_comparison.to_excel(output_file, index=False)
### End Test script

###     END of script