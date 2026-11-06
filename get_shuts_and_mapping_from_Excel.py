# Procedure to get shut data and mapping data from Excel Inputs

import pandas as pd
import os

from requests import head


def get_shuts_from_excel_input(main_folder_path, input_folder, inputfile_name): 
    # get MSF shut 
    df_rawshuts = pd.read_excel(os.path.join(main_folder_path, input_folder, inputfile_name))
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
def get_LP_MSF_mapping_from_excel_input(main_folder_path,input_folder, inputfile_name):
    # get LP MSF mapping
    df_mapping = pd.read_excel(os.path.join(main_folder_path, input_folder, inputfile_name))
    # df_mapping example: [assetGroupingPK:1, assetGroupingName:B4 Plant, planningGroupName:Brockman 4, assetClassName:Plant, MSFName:BM4PLT, percentageImpact:1]    
    return df_mapping 

### Test script compare_output_with_LP
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation'
    output_folder = 'Testing Input and Output Files'
    input_folder = output_folder
    inputfile_name_shuts = 'input_for_testing_MSF_shuts.xlsx'
    inputfile_name_mapping = 'input_for_testing_LP_MSF_mapping.xlsx'
    # df_input_shuts = pd.read_excel(os.path.join(main_folder_path, input_folder, inputfile_name_shuts))
    # df_input_mapping = pd.read_excel(os.path.join(main_folder_path, input_folder, inputfile_name_mapping))
    df_shuts = get_shuts_from_excel_input(main_folder_path, input_folder, inputfile_name_shuts)
    print(df_shuts.head(5))
    df_mapping = get_LP_MSF_mapping_from_excel_input(main_folder_path, input_folder, inputfile_name_mapping)
    print(df_mapping.head(5))
### End Test script



