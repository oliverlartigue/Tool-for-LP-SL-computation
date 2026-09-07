# Script import shut data from MSF, LP MSF mapping, and return SL a LP would compute the forward adjustments


import pandas as pd
from generate_calendar import build_split_week_calendar
from split_shuts import split_shuts_periods, split_shuts_period_all_asset

# GET DATA _ v1
# get LP MSF mapping
df_mapping = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\LP MSF mapping.xlsx')
# get MSF shut
df_rawshuts = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\MSF shuts.xlsx')
df_rawshuts = df_rawshuts[['SourceIdentifier_AssetCode','MaintenanceShutdown_BK','MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
# join mapping to MSF shuts
df_shuts = df_rawshuts.merge(  # add asset group and percentage impact
    df_mapping, 
    left_on='SourceIdentifier_AssetCode',right_on='MSFName',how='left')
df_shuts = df_shuts.dropna(subset=['assetGroupingName'])  # remove row which do not have an assetgroupname from the mapping
df_shuts = df_shuts.drop(columns=['SourceIdentifier_AssetCode'])  #remove col
df_shuts.insert(0, 'index', range(1, len(df_shuts) + 1))  #insert an index starting at 1 as the first column

# print (df_shuts.head(1000))

# write an excel file with the MSF shut and the LP mapping
output_file_1 = r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\shuts_after_mapping.xlsx"
df_shuts.to_excel(output_file_1, index=False)
print(f"Saved to: {output_file_1}")

# GET DATA _ v2
# df_shuts_2 = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\INPUT_shuts_after_mapping.xlsx')


# Run Function to split overlapping shuts
############################################################
df_to_be_split = (df_shuts[['index','MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
    .rename(columns={
        'index': 'index',
        'MaintenanceShutdownPlannedFeedOff': 'startdate',        
        'MaintenanceShutdownPlannedFeedOn': 'enddate'
    })
)
df_split = split_shuts_period_all_asset(df_to_be_split)
# Run Function to generate a calendar and split all shuts at daily level (with days starting at 6am and linked to split week)
df_calendar = build_split_week_calendar("2026-10-25","2027-11-08")

output_file_2 = r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\shutdown_analysis2.xlsx"
df_split.to_excel(output_file_2, index=False)
print(f"Saved to: {output_file_2}")




