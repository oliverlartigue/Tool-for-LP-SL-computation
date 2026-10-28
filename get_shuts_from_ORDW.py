# Oliver lartigue - Oct 2026
# Script import shut data from MSF inORDW

import pyodbc
import pandas as pd

# Connect to ORDW
conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=ORDW;"
    r"DATABASE=ORDW;"
    r"Trusted_Connection=yes;"
    r"Encrypt=no;"
)

snapshot_name = "2027 January QF - Final Maintenance Snapshot"


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

df = pd.read_sql(
    query_get_MSF_snapshot,
    conn,
    params=[snapshot_name])
conn.close()


### Test script 
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    # ...
    print(df.head())
    print(df.shape) 
### End Test script

###     END of script


