# Oliver lartigue - Oct 2026
# Script import shut data from an MSF snapshot in ORDW

import pyodbc
import pandas as pd
from datetime import datetime

# query return shuts from the MSF snapshot as follows, eg 
# VersionName:2027 January QF - Final Maintenance Snapshot, MaintenanceShutdown_BK:28403, MaintenanceShutdownTypeName: Scheduled, MaintenanceShutdownStatusName:Approved,  
# ... SourceIdentifier_AssetCode: BM4TLO, MaintenanceShutdownPlannedFeedOff: 2027-02-14 04:00:00, MaintenanceShutdownPlannedFeedOn: 2027-02-14 16:00:00
query_get_MSF_snapshot = """
SELECT 
    DMSS.[VersionName]
    ,FMSS.[SourceIdentifier_ShutId] AS 'MaintenanceShutdown_BK'
	,DMST.[MaintenanceShutdownTypeName]
	,DMSST.[MaintenanceShutdownStatusName]
    ,FMSS.[SourceIdentifier_AssetCode]
    ,FMSS.[PlannedFeedOffDate] AS 'MaintenanceShutdownPlannedFeedOff'
    ,FMSS.[PlannedFeedOnDate] AS 'MaintenanceShutdownPlannedFeedOn'
  FROM [ORDW].[public_v2].[fact_MaintenanceShutdownSnapshot] AS FMSS
  LEFT JOIN [ORDW].[public_v2].[dim_MaintenanceShutdownSnapshot] AS DMSS ON DMSS.[MaintenanceShutdownSnapshot_SK] = FMSS.[MaintenanceShutdownSnapshot_SK]  -- JOIN to get snapshot [VersionName]
  LEFT JOIN (  -- JOIN  to get [MaintenanceShutdownType_SK] and [MaintenanceShutdownStatus_SK] -- USING a GROUP BY to make sure that FMSD.[MaintenanceShutdownType_SK] and [MaintenanceShutdownStatus_SK] are unique to a [SourceIdentifier_ShutId] when joining  
	SELECT 
		LEFT(FMSD.[SourceIdentifier_EquipmentMaintenanceShutdownPK],CHARINDEX('_',FMSD.[SourceIdentifier_EquipmentMaintenanceShutdownPK])-1) AS [SourceIdentifier_ShutId],  -- [SourceIdentifier_ShutId]
		MAX(FMSD.[MaintenanceShutdownType_SK]) AS [MaintenanceShutdownType_SK],
		MAX(FMSD.[MaintenanceShutdownStatus_SK]) AS [MaintenanceShutdownStatus_SK]
	FROM [ORDW].[public_v2].[fact_MaintenanceShutdown] AS FMSD
	GROUP BY LEFT(FMSD.[SourceIdentifier_EquipmentMaintenanceShutdownPK],CHARINDEX('_',FMSD.[SourceIdentifier_EquipmentMaintenanceShutdownPK])-1)
	) AS FMSDU ON FMSDU.[SourceIdentifier_ShutId] = FMSS.[SourceIdentifier_ShutId]
  LEFT JOIN [ORDW].[public_v2].[dim_MaintenanceShutdownType] AS DMST ON DMST.[MaintenanceShutdownType_SK] = FMSDU.[MaintenanceShutdownType_SK]  -- JOIN  to get [MaintenanceShutdownTypeName]
  LEFT JOIN [ORDW].[public_v2].[dim_MaintenanceShutdownStatus] AS DMSST ON DMSST.[MaintenanceShutdownStatus_SK] = FMSDU.[MaintenanceShutdownStatus_SK]  -- JOIN  to get [MaintenanceShutdownStatusName]
  WHERE DMSS.[VersionName] = ?
"""

# run ORDW query and store result in a dataframe
def get_unprocessed_shuts_from_MSFsnapshot_in_ORDW(snapshot_name):
    # Connect to ORDW
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=ORDW;"
        r"DATABASE=ORDW;"
        r"Trusted_Connection=yes;"
        r"Encrypt=no;"
    )
    df_shuts = pd.read_sql(
        query_get_MSF_snapshot,
        conn,
        params=[snapshot_name])
    conn.close()
    run_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    df_shuts['VersionName'] = f"{snapshot_name} - ORDW query run at {run_datetime}"
    return df_shuts

# get raw shuts (excluding shuts with 'Shut type' = 'Site Constraint')
# output has columns: ['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
def get_shuts_from_MSFsnapshot_in_ORDW(snapshot_name): 
    df_rawshuts = get_unprocessed_shuts_from_MSFsnapshot_in_ORDW(snapshot_name)
    df_rawshuts = df_rawshuts[df_rawshuts['MaintenanceShutdownTypeName'] != 'Site Constraint']  # filter out shuts when Shut type = Site Constraint 
    df_rawshuts['MaintenanceShutdownStatusName'] = df_rawshuts['MaintenanceShutdownStatusName'].replace('Approved Status', 'Approved')  # replace 'Approved Status' by 'Approved' (so that it is consistnet with the API which has 'Approved')     
    df_rawshuts = df_rawshuts[
        ['VersionName','SourceIdentifier_AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
        ].rename(
            columns={
                "VersionName": "MSFSourceData",
                "SourceIdentifier_AssetCode": "AssetCode"
            }
        )
    # df_rawshuts row example: [MSFSourceData:2027 January QF - Final Maintenance Snapshot, MaintenanceShutdown_BK:41667, MaintenanceShutdownTypeName:Scheduled, 
    # ... MaintenanceShutdownStatusName:Approved, AssetCode:BM4PLT, MaintenanceShutdownPlannedFeedOff:26/11/2026  7:00:00 AM, 
    # ... MaintenanceShutdownPlannedFeedOn:26/11/2026]  9:00:00 AM]
    return df_rawshuts



### Test script 
snapshot_name_for_testing_1 = "2027 January QF - Final Maintenance Snapshot"
snapshot_name_for_testing_2 = "2026 October QF - Final Maintenance Snapshot"
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    df_shuts_1 = get_shuts_from_MSFsnapshot_in_ORDW(snapshot_name_for_testing_1)
    print(df_shuts_1.head())
    print(df_shuts_1.shape)
    df_shuts_2 = get_shuts_from_MSFsnapshot_in_ORDW(snapshot_name_for_testing_2)
    print(df_shuts_2.head())
    print(df_shuts_2.shape)
### End Test script

###     END of script


