# Oliver lartigue - Oct 2026
# Script import LP MSF mapping data from LiveParameters-Prod database
# it works fine, just it needs me enter my authorization code in the pop-up window to connect to the database
import pyodbc
import pandas as pd
from datetime import datetime

# query return maapin, eg 
# 
query_get_mapping = """
    SELECT 
        DISTINCT (AMFP.[assetGroupingPK])
        ,AG.[assetGroupingName]
        ,PG.[planningGroupName]
        ,AMFP.[assetClassName]
            ,AMFP.[MSFName]
            ,AMFP.[percentageImpact]
    FROM [dbo].[vw_assetsManagement_fixedPlantAsset] AS AMFP
    LEFT JOIN [dbo].[assetGrouping] AS AG ON AG.[assetGroupingPK] = AMFP.[assetGroupingPK]
    LEFT JOIN [dbo].[planningGroup] AS PG ON PG.[planningGroupPK] = AMFP.[planningGroupPK]
    WHERE 
        AMFP.[assetClassName] IN ('Plant','Primary Crusher') AND AG.[assetGroupingName] NOT IN ('Dummy RVY MA Wet Plant') OR
        AG.[assetGroupingName] IN ('CD2E', 'CD3P', 'CD4P', 'CD2C', 'CD5C', 'CD6C', 'CD7C', 'SL1E', 'SL2P', 'SL3P', 'SL2C', 'SL3C', 'SL11C', 'SL12C')
    ORDER BY AMFP.[assetClassName], PG.[planningGroupName], AG.[assetGroupingName]
"""

# run  query and store result in a dataframe
def get_mapping():
    # Connect to LiveParameters-Prod
    conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=tcp:sql-rt-iprd-liveparams-prod.database.windows.net,1433;"
    r"DATABASE=LiveParameters-Prod;"
    r"Authentication=ActiveDirectoryInteractive;"
    r"Encrypt=yes;",
    timeout=30
    )
    try:
        df_mapping= pd.read_sql(
            query_get_mapping,
            conn)
    finally:
        conn.close()
    run_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    df_mapping['VersionName'] = f" query run at {run_datetime}"
    return df_mapping



### Test script 
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    df_mapping = get_mapping()
    print(df_mapping.head())
    print(df_mapping.shape)
    df_mapping.to_excel(
        r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files\test_output_LP_MSF_mapping.xlsx',
        index=False,
        engine="openpyxl"
        )
    print(f"Saved to: test_output_LP_MSF_mapping.xlsx")
### End Test script

###     END of script


