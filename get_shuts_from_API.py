# Oliver lartigue - Oct 2026
# Script import shut data from MSF API

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import jwt
import json
import pandas as pd
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from pathlib import Path
from datetime import datetime

pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)

key_file_path = Path(r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\000. Source Files\MSF API key.txt")

config = {}

with open(key_file_path, "r", encoding="utf-8-sig") as f:
    for line in f:
        if "=" not in line:
            continue
        key, value = [x.strip() for x in line.split("=", 1)]
        config[key] = value


CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")

TOKEN_URL = "https://login.microsoftonline.com/4341df80-fbe6-41bf-89b0-e6e2379c9c23/oauth2/v2.0/token"

API_ENDPOINT = "https://apim-icc-syd-prd.riotinto.org/MSF/data/v1/api/Shuts"
# SCOPE_KEY ="api://1d96a4d6-0a76-41e2-90e5-aac413a98a39/.default"

SUBSCRIPTION_KEY = "f65fbb6704404c1f916e7971cfb4e4db"

client = BackendApplicationClient(client_id=CLIENT_ID)

oauth = OAuth2Session(
    client=client,
    scope=["api://1d96a4d6-0a76-41e2-90e5-aac413a98a39/.default"]
)

token = oauth.fetch_token(
    token_url=TOKEN_URL,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope=["api://1d96a4d6-0a76-41e2-90e5-aac413a98a39/.default"]
)

access_token = token["access_token"]

# Parameters to query MSF API for pending shuts
params_pending = {
    "startDate": "2026-12-01", 
    "endDate": "2028-01-31",
    "includePendingApprovalVersions": "true",  # select pending shuts
    "currentPage": 1,
    "itemsPerPage": 1000,
    "itemsLimit": 100000
}

# Parameters to query MSF API for approved shuts
params_approved = {
    "startDate": "2026-12-01", 
    "endDate": "2028-01-31",
    "includePendingApprovalVersions": "false",  # select approved shuts
    "currentPage": 1,
    "itemsPerPage": 1000,
    "itemsLimit": 100000
}

def get_crude_shuts_from_MSF_API(params):  # query the API and get the shut data in a dataframe -- params is the variable which enable to get pending shuts or not
    response = requests.get(
        API_ENDPOINT,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
            "Accept": "application/json"
        },
        params=params,
        verify=False
    )

    data = response.json()
    df = pd.DataFrame(data["shuts"])
    df_versions = pd.json_normalize(df['versions'].str[0])  # Expand first item of the versions list
    df_versions = df_versions.add_prefix('version_')  # Add a prefix to avoid column name conflicts
    df = df.drop(columns=['versions']).join(df_versions)  # Join back to the original dataframe
    return df
 


def prepare_for_excel(value):
    if value is None:
        return None

    if isinstance(value, (dict, list)):
        value = json.dumps(
            value,
            ensure_ascii=False,
            default=str
        )

    if isinstance(value, str):
        value = ILLEGAL_CHARACTERS_RE.sub("", value)

    return value


def get_FXP_shuts_from_MSF_API(params): # get shuts  in a data frame
    df_shuts = get_crude_shuts_from_MSF_API(params)
    df_shuts = df_shuts[df_shuts['category'].apply(lambda x: x.get("name") == "Fixed Plant")].copy()  # filter only FXP Plant shuts (including Port FXP)
    required_columns = [
        'id',
        'version_startDatetimeLocal',
        'version_endDatetimeLocal',
        # 'version_durationHours',
        # 'version_description',
        # 'version_versionNumber',
        'version_equipment',
        'version_status.name',
        'version_type.name'
        ]   
    df_shuts = df_shuts[required_columns].rename(
            columns={
                "version_equipment": "AssetCode",                
                "id": "MaintenanceShutdown_BK",
                "version_startDatetimeLocal": "MaintenanceShutdownPlannedFeedOff",
                "version_endDatetimeLocal": "MaintenanceShutdownPlannedFeedOn",
                "version_status.name": "MaintenanceShutdownStatusName",
                "version_type.name": "MaintenanceShutdownTypeName"
            }
        )
    df_shuts["AssetCode"] = df_shuts["AssetCode"].apply(lambda x: x[0].get("code") if isinstance(x, list) and len(x) > 0 else None)  # get 'code' value from the dictionary in the 'AssetCode' col - API has one code per row, to avoid the code to fail in case of mutliple asset code in a row, select the first value
    for index, value in df_shuts["AssetCode"].items():
        if isinstance(value, list) and len(value) > 1:
            print(f"WARNING: Row {index} has multiple AssetCode values: {value}")  # print a warning message if a row has more than one asset code
    run_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    df_shuts['MSFSourceData'] = f"MSF API - FXP - including pending - run at {run_datetime}"  # create a 'MSFSourceData' column with value such as 'MSF API run at 2026-10-26 10:31'    
    for col in ["MaintenanceShutdownPlannedFeedOff","MaintenanceShutdownPlannedFeedOn"]:
        df_shuts[col] = pd.to_datetime(df_shuts[col]).dt.tz_localize(None)  # normalise the timestamps
    df_shuts = df_shuts[['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']
        ].sort_values(
            [
                'AssetCode',
                'MaintenanceShutdownPlannedFeedOff'
            ]
        )
    return df_shuts

def get_shuts_approved_only_from_MSF_API(): # get approved shuts and output them in a data frame
    df_shuts = get_FXP_shuts_from_MSF_API(params_approved)
    run_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    df_shuts['MSFSourceData'] = f"MSF API - FXP - approved only - run at {run_datetime}"  # create a 'MSFSourceData' column with value such as 'MSF API run at 2026-10-26 10:31'    
    df_shuts = df_shuts[['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
    return df_shuts 

def get_shuts_including_pending_from_MSF_API(): # get approved shuts and output them in a data frame
    df_shuts = get_FXP_shuts_from_MSF_API(params_pending)
    run_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    df_shuts['MSFSourceData'] = f"MSF API - FXP - including pending - run at {run_datetime}"  # create a 'MSFSourceData' column with value such as 'MSF API run at 2026-10-26 10:31'     df_shuts = df_shuts[['MSFSourceData','AssetCode','MaintenanceShutdown_BK', 'MaintenanceShutdownTypeName', 'MaintenanceShutdownStatusName', 'MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
    return df_shuts 

### Test script 
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    # get crude approved shuts in a dataframe and export in excel
    df_cruded_approved = get_crude_shuts_from_MSF_API(params_approved)
    df_cruded_approved.to_excel(
        r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files\Explore_API_crude_approved.xlsx',
        index=False,
        engine="openpyxl"
        )
    print(f"Saved to: Explore_API_crude_approved.xlsx")

    # get shuts including pending in a dataframe and export in excel
    df_pending = get_shuts_including_pending_from_MSF_API()  # get all shuts including pending - each shut is unique (it has the latest version whether approved or not)
    print(df_pending.head(5))
    df_pending_export = df_pending.map(prepare_for_excel)
    df_pending_export.to_excel(
        r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files\Explore_API_pending.xlsx',
        index=False,
        engine="openpyxl"
        )
    print(f"Saved to: Explore_API_pending.xlsx")

    # get approved shuts in a dataframe and export in excel
    df_approved = get_shuts_approved_only_from_MSF_API() # get approved only shuts - each shut is unique
    print(df_approved.head(5))
    df_approved_export = df_approved.map(prepare_for_excel)
    df_approved_export.to_excel(
        r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files\Explore_API_approved.xlsx',
        index=False,
        engine="openpyxl"
    )
    print(f"Saved to: Explore_API_approved.xlsx")


### End Test script

###     END of script
