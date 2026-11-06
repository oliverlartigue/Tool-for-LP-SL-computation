

import pandas as pd

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