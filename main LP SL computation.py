# Oliver lartigue - Sep 2026
# Script import shut data from MSF, LP MSF mapping, and return SL a LP would compute the forward adjustments


import pandas as pd
import os
from generate_calendar import build_split_week_calendar
from split_by_overlappingPeriod import split_events_all_assets
from split_by_operatingDay import split_periods_by_operating_day
from SL_hours_by_asset_opDay import SL_hours_by_asset_by_operating_day, effective_hours_by_asset_by_startEndDate
from SL_hours_by_asset_splitWeek  import SL_hours_by_asset_by_split_week
from compare_output_with_LP import compare_SL_output_with_LP

period_start_date = "2026-10-01"
period_end_date = "2027-12-31"
main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation'


# Run Function to generate a calendar and split all shuts at daily level (with days starting at 6am and linked to split week)
df_calendar = build_split_week_calendar(period_start_date,period_end_date)


### GET DATA
# get LP MSF mapping
df_mapping = pd.read_excel(os.path.join(main_folder_path,'Main Input Files\LP MSF mapping.xlsx'))
# df_mapping example: [assetGroupingPK:1, assetGroupingName:B4 Plant, planningGroupName:Brockman 4, assetClassName:Plant, MSFName:BM4PLT, percentageImpact:1]     
# get MSF shut
df_rawshuts = pd.read_excel(os.path.join(main_folder_path,'Main Input Files\MSF shuts.xlsx'))
df_rawshuts = df_rawshuts[['SourceIdentifier_AssetCode','MaintenanceShutdown_BK','MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
# df_rawshuts example: [SourceIdentifier_AssetCode:BM4PLT, MaintenanceShutdown_BK:41667, MaintenanceShutdownPlannedFeedOff:26/11/2026  7:00:00 AM, MaintenanceShutdownPlannedFeedOn:26/11/2026]  9:00:00 AM
# join mapping to MSF shuts
df_shuts = df_rawshuts.merge(  # add asset group and percentage impact
    df_mapping, 
    left_on='SourceIdentifier_AssetCode',right_on='MSFName',how='left')
df_shuts = df_shuts.dropna(subset=['assetGroupingName'])  # remove row which do not have an assetgroupname from the mapping
df_shuts = df_shuts.drop(columns=['SourceIdentifier_AssetCode'])  #remove col
df_shuts.insert(0, 'index', range(1, len(df_shuts) + 1))  #insert an index starting at 1 as the first column


# write an excel file with the MSF shut and the LP mapping
output_file_1 = os.path.join(main_folder_path,'Main Output Files\output_MSF_shuts_after_mapping.xlsx')
df_shuts.to_excel(output_file_1, index=False)
print(f"Saved to: {output_file_1}")

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
df_SL_opDay = SL_hours_by_asset_by_operating_day(effective_hours_by_asset_by_startEndDate(df_split))
# sum SL hours by assets and by split week
df_SL_splitWeeek = SL_hours_by_asset_by_split_week(df_SL_opDay, df_calendar)

### WRITE OUTPUT IN EXCEL
output_file_2 = os.path.join(main_folder_path,'Main Output Files\output_splitShuts.xlsx')
df_split.to_excel(output_file_2, index=False)
print(f"Saved to: {output_file_2}")
output_file_3 = os.path.join(main_folder_path, 'Main Output Files\output_SL_hours_opDay.xlsx')
df_SL_opDay.to_excel(output_file_3, index=False)
print(f"Saved to: {output_file_3}")
output_file_4 = os.path.join(main_folder_path, 'Main Output Files\output_SL_hours_splitWeek.xlsx')
df_SL_splitWeeek.to_excel(output_file_4, index=False)
print(f"Saved to: {output_file_4}")


### COMPARE OUTPUT WITH LP
df_LP = pd.read_csv(os.path.join(main_folder_path, 'Main Input Files\LP SL.csv'))  # get LP SL
df_comparison = compare_SL_output_with_LP(df_SL_splitWeeek,df_LP)
output_file_5 = os.path.join(main_folder_path, 'Main Output Files\output_SL_comparison_for testing.xlsx')
df_comparison.to_excel(output_file_5, index=False)
              


###     END of script
