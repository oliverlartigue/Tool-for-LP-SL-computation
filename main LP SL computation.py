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
from get_shuts_from_ORDW import get_raw_shuts_from_MSFsnapshot_in_ORDW

pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)


period_start_date = "2027-01-01"
period_end_date = "2027-12-31"
snapshot_name = "2027 January QF - Final Maintenance Snapshot"
main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation'



# Run Function to generate a calendar and split all shuts at daily level (with days starting at 6am and linked to split week)
df_calendar = build_split_week_calendar(period_start_date,period_end_date)
run_datetime = datetime.now().strftime("%Y-%m-%d %Hh%M")


# Procedure to get shut data from Excel Inputs
def get_raw_shut_from_excel_input(): 
    # get MSF shut 
    df_rawshuts = pd.read_excel(os.path.join(main_folder_path,'Main Input Files','MSF shuts.xlsx'))
     # df_rawshuts row example: [VersionName:2027 January QF - Final Maintenance Snapshot, MSFSourceData: 2027 January QF - Final Maintenance Snapshot - excel input run at 2026-11-02 08:21:15,  
     # ... MaintenanceShutdown_BK:41667, MaintenanceShutdownTypeName:Scheduled, MaintenanceShutdownStatusName:Approved Status, SourceIdentifier_AssetCode:BM4PLT,
     # ... MaintenanceShutdownPlannedFeedOff:26/11/2026,  7:00:00 AM, MaintenanceShutdownPlannedFeedOn:26/11/2026]  9:00:00 AM]  
    df_rawshuts = df_rawshuts[df_rawshuts['MaintenanceShutdownTypeName'] != 'Site Constraint']  # filter out shuts when Shut type = Site Constraint 
    df_rawshuts['MaintenanceShutdownStatusName'] = df_rawshuts['MaintenanceShutdownStatusName'].replace('Approved Status', 'Approved')  # replace 'Approved Status' by 'Approved' (so that it is consistnet with the API which has 'Approved')     
    # df_rawshuts['VersionName'] = f"df_rawshuts['VersionName'] - ORDW query run at {run_datetime}"
    df_rawshuts = df_rawshuts[
        ['MSFSourceData','SourceIdentifier_AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
        ].rename(
            columns={
                "SourceIdentifier_AssetCode": "AssetCode"
            }
        )
    # df_rawshuts row example: [2027 January QF - Final Maintenance Snapshot - excel input run at 2026-11-02 08:21:15, MaintenanceShutdown_BK:41667, MaintenanceShutdownTypeName:Scheduled, 
    # ... MaintenanceShutdownStatusName:Approved, AssetCode:BM4PLT, MaintenanceShutdownPlannedFeedOff:26/11/2026  7:00:00 AM, MaintenanceShutdownPlannedFeedOn:26/11/2026]  9:00:00 AM]
    return df_rawshuts


# Procedure to get shut mapping from Excel Inputs
def get_LP_MSF_mapping_from_excel_input(): 
    # get LP MSF mapping
    df_mapping = pd.read_excel(os.path.join(main_folder_path,'Main Input Files','LP MSF mapping.xlsx'))
    # df_mapping example: [assetGroupingPK:1, assetGroupingName:B4 Plant, planningGroupName:Brockman 4, assetClassName:Plant, MSFName:BM4PLT, percentageImpact:1]    
    return df_mapping 

# Procedure to merge shut data and mapping
def merge_rawshuts_with_mapping(df_rawshuts, df_mapping):  # join LP MSF mapping to MSF shuts
    # join mapping to MSF shuts
    df_shuts = df_rawshuts.merge(  # add asset group and percentage impact
        df_mapping, 
        left_on='AssetCode',right_on='MSFName',how='left')
    df_shuts = df_shuts.dropna(subset=['assetGroupingName'])  # remove row which do not have an assetgroupname from the mapping
    df_shuts = df_shuts.drop(columns=['AssetCode'])  #remove col
    df_shuts = df_shuts.sort_values(by=["assetGroupingName", "MaintenanceShutdownPlannedFeedOff", "MSFName"]).reset_index(drop=True)
    df_shuts.insert(0, 'index', range(1, len(df_shuts) + 1))  #insert an index starting at 1 as the first column
    return df_shuts

### GET DATA
df_mapping = get_LP_MSF_mapping_from_excel_input()
df_rawshuts_excel = get_raw_shut_from_excel_input()
# Shuts from MSF API
# Output has columns: ['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
df_rawshuts_API_approved_only = get_shuts_approved_only_from_MSF_API() 
df_rawshuts_API_including_pending = get_shuts_including_pending_from_MSF_API()
# Shuts from MSF snaphot in ORDW
# output has columns: ['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
df_rawshuts_ORDW_snapshot = get_raw_shuts_from_MSFsnapshot_in_ORDW(snapshot_name)

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

df_shuts = merge_rawshuts_with_mapping(df_rawshuts, df_mapping)

df_shuts["index"] = range(1, len(df_shuts) + 1)
print("shuts returned:")
print(df_shuts.head(5))


### PROCESS DATA
# Run Function to split overlapping shuts
df_to_be_split = (df_shuts[['index', 'assetGroupingName','MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
    .rename(columns={
        'index': 'index',
        'assetGroupingName': 'asset',
        'MaintenanceShutdownPlannedFeedOff': 'startDate',        
        'MaintenanceShutdownPlannedFeedOn': 'endDate'
    })
)
df_split_overlapping = split_events_all_assets(df_to_be_split)
# Run Function to split by operating days
df_split_days = split_periods_by_operating_day(df_split_overlapping)
# join with df_shuts data (col MSFcode...) thanks to index
df_split = df_split_days.merge( 
    df_shuts, 
    left_on='index',right_on='index',how='left')


# for col in df_split.columns:
#     if "datetime64" in str(df_split[col].dtype):
#         print(col, df_split[col].dtype)


df_SL_opDay = SL_hours_by_asset_by_operating_day(effective_hours_by_asset_by_startEndDate(df_split))
# sum SL hours by assets and by split week
df_SL_splitWeek = SL_hours_by_asset_by_split_week(df_SL_opDay, df_calendar)

### WRITE OUTPUT IN EXCEL

# write an excel file with the MSF shut
output_file_1 = os.path.join(main_folder_path,'Main Output Files',f'run {run_datetime} - output_MSF_shuts.xlsx')
with pd.ExcelWriter(output_file_1, engine="openpyxl") as writer:
    # write a sheet e with the MSF shut and the LP mapping
    df_shuts.drop(columns=['MSFSourceData', 'assetGroupingPK']).to_excel(writer, index=False, sheet_name="MSF_shuts_after_mapping", startrow=2)
    ws = writer.sheets["MSF_shuts_after_mapping"]
    ws["A1"] = 'shuts from MSF - one row for each combination of MSF shut & MSFName (aka MSF asset code). Show percentage impact of MSFName on asset (assetGroupingName) as defined in Live Parameters MSF mapping' # Print info on first row      
    ws["A2"] = 'source: ' + df_shuts['MSFSourceData'].iloc[0] # Print info on second row
    for cell in ws[3]:     
        cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
    for col in ws.iter_cols():
        if col[2].value in ['MaintenanceShutdownPlannedFeedOff', 'MaintenanceShutdownPlannedFeedOn']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
            for cell in col[1:]:
                cell.number_format = "d/mm/yyyy h:mm"     # Format datetime columns 
    ws.freeze_panes = "A4"  # freeze first 3 rows                
    # write a sheet  with the split Shuts
    df_split.drop(columns=['MSFSourceData', 'assetGroupingPK']).to_excel(writer, index=False, sheet_name='split Shuts by OperatingDay', startrow=2)
    df_split = df_split[(df_split['operatingDay'] >= period_start_date) & (df_split['operatingDay'] <= period_end_date)].copy()  # only show operation within the period of interest
    ws = writer.sheets['split Shuts by OperatingDay']
    ws["A1"] = 'shuts from MSF split by Day (from 6am to 6am) - one row for each combination of OperatingDay & MSF shut & MSFName (aka MSF asset code). SartDate and EndDate of the portion of the shut in the OperatingDay' # Print info on first row      
    ws["A2"] = 'shut source: ' + df_split['MSFSourceData'].iloc[0] # Print info on second row
    for cell in ws[3]:     
        cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
    for col in ws.iter_cols():
        if col[2].value in ['startDate', 'endDate', 'MaintenanceShutdownPlannedFeedOff', 'MaintenanceShutdownPlannedFeedOn']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
            for cell in col[1:]:
                cell.number_format = "d/mm/yyyy h:mm"     # Format datetime columns 
        if col[2].value in ['operatingDay']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 14  # set column width at 14
            for cell in col[1:]:
                cell.number_format = "d/mm/yyyy"     # Format datetime columns  
    ws.freeze_panes = "A4"  # freeze first 3 row                                   
    # write a sheet  with SL by asset, by Operating Day
    df_SL_opDay.to_excel(writer, index=False, sheet_name='SL by OperatingDay', startrow=2)
    ws = writer.sheets['SL by OperatingDay']
    ws["A1"] = 'Scheduled Loss (SL) as computed in Live Parameters by asset, by Operating Day' # Print info on first row      
    ws["A2"] = 'shut source: ' + df_split['MSFSourceData'].iloc[0] # Print info on second row
    for cell in ws[3]:     
        cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
    for col in ws.iter_cols():
        if col[2].value in ['operatingDay']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 14  # set column width at 14
            for cell in col[1:]:
                cell.number_format = "d/mm/yyyy"     # Format datetime columns            
        if col[2].value in ['maintenanceShutdownBKss']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
    ws.freeze_panes = "A4"  # freeze first 3 row    
    # write a sheet  with SL by asset, by Split Week
    df_SL_splitWeek.to_excel(writer, index=False, sheet_name='SL by Split Week', startrow=2)
    ws = writer.sheets['SL by Split Week']
    ws["A1"] = 'Scheduled Loss (SL) by asset, by Split Week, computed with the same methodology as Live Parameters auto forward adjustments ' # Print info on first row      
    ws["A2"] = 'shut source: ' + df_split['MSFSourceData'].iloc[0] # Print info on second row
    for cell in ws[3]:     
        cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
    for col in ws.iter_cols():
        if col[2].value in ['SplitWeekStartDate', 'SplitWeekEndDate']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 14  # set column width at 14
            for cell in col[1:]:
                cell.number_format = "d/mm/yyyy"     # Format datetime columns    
        if col[2].value in ['SplitWeekStartDate6am', 'SplitWeekEndDate6am']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
            for cell in col[1:]:
                cell.number_format = "d/mm/yyyy h:mm"     # Format datetime columns                           
        if col[2].value in ['maintenanceShutdownBKss']:
            ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
    ws.freeze_panes = "A4"  # freeze first 3 row                
print(f"Saved to: {output_file_1}")


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
output_file_5 = os.path.join(main_folder_path, 'Main Output Files',f'run {run_datetime} - output_SL_comparison_with LP.xlsx')

# Get distinct MSFSourceData values - should be unique, but getting a list just in case there is an inconsistency
MSFSourceDataNames = ", ".join(df_shuts["MSFSourceData"].dropna().astype(str).unique())

# Write split-week and annual results into separate tabs
with pd.ExcelWriter(output_file_5, engine="openpyxl") as writer:
    df_comparison_SL_annual.to_excel(writer, sheet_name="Annual Comparison", index=False, startrow=2)
    df_comparison_SL_weekly.to_excel(writer, sheet_name="SplitWeek Comparison", index=False, startrow=2)
    for sheet_name in ["SplitWeek Comparison", "Annual Comparison"]: # loop to format excel output
        ws = writer.sheets[sheet_name]
        ws["A1"] = "SL output computed from shuts in '" + MSFSourceDataNames + "' and compared with Live Parameters" # Print info on first row          
        for cell in ws[3]:      # Wrap column names
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        for col in ws.iter_cols():
            if col[2].value in ["SplitWeekStartDate", "SplitWeekEndDate", "YearStartDate", "YearEndDate" ]:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 11  # set column width at 11
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy"  # Format datetime columns
    ws.freeze_panes = "A4"  # freeze first 3 rows                          
print(f"Saved to: {output_file_5}")
              
###     END of script
