# Oliver lartigue - Oct 2026
# Script import shut data from MSF, LP MSF mapping, and return SL a LP would compute the forward adjustments


import pandas as pd
import os
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime
from generate_calendar import build_split_week_calendar
from split_by_overlappingPeriod import split_events_all_assets
from split_by_operatingDay import split_periods_by_operating_day
from SL_hours_by_asset_opDay import SL_hours_by_asset_by_operating_day, effective_hours_by_asset_by_startEndDate
from SL_hours_by_asset_splitWeek  import SL_hours_by_asset_by_split_week
from compare_output_with_LP import split_LP_AutoFA_by_splitweek, compare_SL_output_with_LP_weekly, compare_SL_output_with_LP_annual
from get_shuts_from_API import get_shuts_approved_only_from_MSF_API, get_shuts_including_pending_from_MSF_API    
from get_shuts_from_ORDW import get_shuts_from_MSFsnapshot_in_ORDW
from get_shuts_and_mapping_from_Excel import get_shuts_from_excel_input, get_LP_MSF_mapping_from_excel_input
from merge_rawshuts_with_mapping import merge_rawshuts_with_mapping
from write_output_in_excel import write_output_SL_and_shuts_in_excel

pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)


period_start_date = "2027-01-01"
period_end_date = "2027-12-31"
snapshot_name = "2027 January QF - Final Maintenance Snapshot"
main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation'
main_output_folder = 'Main Output Files'
main_input_folder = 'Main Input Files'
inputfile_name_shuts = 'MSF shuts.xlsx'
inputfile_name_mapping = 'LP MSF mapping.xlsx'



# Run Function to generate a calendar and split all shuts at daily level (with days starting at 6am and linked to split week)
df_calendar = build_split_week_calendar(period_start_date,period_end_date)
run_datetime = datetime.now().strftime("%Y-%m-%d %Hh%M")


### GET DATA
df_mapping = get_LP_MSF_mapping_from_excel_input(main_folder_path, main_input_folder, inputfile_name_mapping)
df_rawshuts_excel = get_shuts_from_excel_input(main_folder_path, main_input_folder, inputfile_name_shuts)
# Shuts from MSF API
# Output has columns: ['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
df_rawshuts_API_approved_only = get_shuts_approved_only_from_MSF_API() 
df_rawshuts_API_including_pending = get_shuts_including_pending_from_MSF_API()
# Shuts from MSF snaphot in ORDW
# output has columns: ['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
df_rawshuts_ORDW_snapshot = get_shuts_from_MSFsnapshot_in_ORDW(snapshot_name)

# Ask user which source to use
print("\nSelect shutdown source:")
print("1 - Excel Input")
print("2 - MSF API (Approved Only)")
print("3 - MSF API (Including Pending)")
print("4 - ORDW Snapshot")

choice = input("Enter choice (1/2/3/4): ").strip()

if choice == "1":
    df_rawshuts = df_rawshuts_excel
    source_name = "Excel Input"
elif choice == "2":
    df_rawshuts = df_rawshuts_API_approved_only
    source_name = "MSF API (Approved Only)"
elif choice == "3":
    df_rawshuts = df_rawshuts_API_including_pending
    source_name = "MSF API (Including Pending)"
elif choice == "4":
    df_rawshuts = df_rawshuts_ORDW_snapshot
    source_name = "ORDW Snapshot"
else:
    raise ValueError("Invalid choice. Please enter 1, 2, 3 or 4.")

print(f"\nUsing shutdown source: {source_name}")

### PROCESS DATA
# merge raw shuts with mapping
df_shuts = merge_rawshuts_with_mapping(df_rawshuts, df_mapping)
df_shuts["index"] = range(1, len(df_shuts) + 1)
print("shuts returned:")
print(df_shuts.head(5))
# run Function to split overlapping shuts
df_to_be_split = (df_shuts[['index', 'assetGroupingName','MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
    .rename(columns={
        'index': 'index',
        'assetGroupingName': 'asset',
        'MaintenanceShutdownPlannedFeedOff': 'startDate',        
        'MaintenanceShutdownPlannedFeedOn': 'endDate'
    }))
df_split_overlapping = split_events_all_assets(df_to_be_split)
# run Function to split by operating days and join with df_shuts data (col MSFcode...) thanks to index
df_split_days = split_periods_by_operating_day(df_split_overlapping)
df_split = df_split_days.merge( 
    df_shuts, 
    left_on='index',right_on='index',how='left')
#run Functions to compute SL hours by asset and by operating day, then to group by split week
df_SL_opDay = SL_hours_by_asset_by_operating_day(effective_hours_by_asset_by_startEndDate(df_split))
df_SL_splitWeek = SL_hours_by_asset_by_split_week(df_SL_opDay, df_calendar)

### COMPARE OUTPUT WITH LP
# get LP total SL from excel file 
LP_SL_file_path = os.path.join(main_folder_path, 'Main Input Files','LP SL.xlsx')
LP_SL_file_modified_datetime = datetime.fromtimestamp(os.path.getmtime(LP_SL_file_path))
df_LP_SL = pd.read_excel(LP_SL_file_path)
df_LP_SL[['LP_SL_data_source']] = os.path.basename(LP_SL_file_path) +' - file dated ' + LP_SL_file_modified_datetime.strftime("%Y-%m-%d %H:%M")   # add data source 
# get LP Auto Forward Adjustments for SL 
LP_FA_file_path = os.path.join(main_folder_path, 'Main Input Files','LP Auto Forward Adjustments.xlsx')
LP_FA_file_modified_datetime = datetime.fromtimestamp(os.path.getmtime(LP_FA_file_path))
df_LP_FA = pd.read_excel(LP_FA_file_path)   # get LP FA
df_LP_FA[['LP_FA_data_source']] = os.path.basename(LP_FA_file_path) +' - file dated ' + LP_FA_file_modified_datetime.strftime("%Y-%m-%d %H:%M")   # add data source 
df_autoFA_split_LP = split_LP_AutoFA_by_splitweek(df_LP_FA, df_calendar)
# run comparison
df_comparison_SL_weekly = compare_SL_output_with_LP_weekly(df_SL_splitWeek ,df_LP_SL,df_autoFA_split_LP)
df_comparison_SL_annual = compare_SL_output_with_LP_annual(df_comparison_SL_weekly)


# write an excel file with the MSF shut
outputfile_name_shuts = 'output_SL_and_shuts.xlsx'
write_output_SL_and_shuts_in_excel(df_comparison_SL_annual, df_comparison_SL_weekly, df_shuts, df_split, df_SL_opDay, df_SL_splitWeek, period_start_date, period_end_date, main_folder_path, main_output_folder, outputfile_name_shuts)

              
###     END of script
