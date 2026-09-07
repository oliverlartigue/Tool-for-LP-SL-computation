# Oliver lartigue - Sep 2026
# Split rows into mutliple rows for the overlapping events of an asset


# Function 'split_events_for_an_asset' split overlapping events (such as shuts) of each asset
# INPUT : dataframe with at least 3 columns: asset, startDate, endDate. 
# In practice, each row represent a shut for an asset with an asset code and a shut startDate and endDate
# Dataframe can have additional columns such as index, an MSFcode and other columns, for example it could have : index, asset, MSFcode, startDate, endDate :
# - index is unique
# - multiple assets
# - each asset has muliple MSFcode
# - each MSF code has multiple shuts (muliple rows of a shut startDate and endDate)
# Note code does not look at cleaning data (if the same shut is a doulbe up the code will still run
# OUTPUT : dataframe with at least 3 columns: asset, startDate, endDate.
# In practice, output could have 5+ columns, for example : index, asset, MSFcode, startDate, endDate. 
# Each row would represent a unique combination of shut for an asset with an MSFcode and a shut startDate and endDate :
# - index is not unique anymore (but can be useful for other transformation and join)
# - multiple assets
# - each asset has muliple MSFcode
# - each MSF code has multiple shuts (muliple rows of a shut startDate and endDate)
# for EXAMPLE, if a dataframe has 2 rows with :
# - a "CL Plant" shut runs from 16/11/2026 01:00 to 21/11/2026 11:00 (with an MSFcode for example CLAPLT)
# - another "CL Plant" shut overlapping part of that range (it does not matter if the shut has the same MSFcode CLAPLT or a different MSFCode such as CLATCSCCT03). 
# For example, if the other shut runs from 19/11/2026 06:00 to 20/11/2026 18:00, then the first shut is split into 3 rows:
# - 16/11/2026 01:00 to 19/11/2026 06:00
# - 19/11/2026 06:00 to 20/11/2026 18:00
#  -20/11/2026 18:00 to 21/11/2026 11:00
# During the middle segment, both active shutdown rows will appear.
# The output will have 4 rows :
# - CL Plant 19/11/2026 06:00 to 20/11/2026 18:00
# - CL Plant 16/11/2026 01:00 to 19/11/2026 06:00
# - CL Plant 19/11/2026 06:00 to 20/11/2026 18:00
# - CL Plant 20/11/2026 18:00 to 21/11/2026 11:00

# Function 'split_events_all_assets' iterates the function 'split_events_for_an_asset' to process the dataframe which contains all the assets and shuts

import pandas as pd
import os



def split_events_for_an_asset(df):
    # Function Parameter is df with at least 3 cols : asset, startDate, endDate
    # Split shutdown rows at every startDate or endDate boundary
    # script deal with all the events of one unique asset 

    # Create the ordered boundary timestamps
    boundaries = (pd.concat([
            df['startDate'],
            df['endDate']
        ])
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    split_rows = []

    # Create intervals between consecutive boundaries
    for split_start, split_end in zip(
        boundaries[:-1],
        boundaries[1:]
    ):
        # Half-open interval logic:
        # original_start < split_end
        # original_end   > split_start
        active_rows = df[
            (df['startDate'] < split_end)
            & (df['endDate'] > split_start)
        ]

        if active_rows.empty:
            continue

        for _, original_row in active_rows.iterrows():
            new_row = original_row.copy()

            # Replace the period with the split segment
            new_row['startDate'] = split_start
            new_row['endDate'] = split_end

            split_rows.append(new_row)

    if not split_rows: return pd.DataFrame(columns=[*df.columns])

    return pd.DataFrame(split_rows)


def split_events_all_assets(df):
  # Function Parameter is df with at least 3 cols : asset, startDate, endDate
    # split shuts for overlapping period for each for different asset

    # Ensure the period columns are datetimes
    df['startDate'] = pd.to_datetime(df['startDate'],errors='coerce')
    df['endDate'] = pd.to_datetime(df['endDate'],errors='coerce')

    # Remove invalid periods           ########## ADD A CHECK TO SEE INVALID DATA IF ANY
    df = df.dropna(subset=['asset', 'startDate', 'endDate'])
    df = df[df['endDate'] > df['startDate']].copy()

    # Split independently for every asset
    split_parts = []

    for asset_name, df_for_asset in df.groupby(
        'asset',
        dropna=False,
        sort=False
    ):
        split_parts.append(
            split_events_for_an_asset(df_for_asset)
        )

    df_split = pd.concat(
        split_parts,
        ignore_index=True
    )

    # Arrange the output
    df_split = (
        df_split
        .sort_values([
            'asset',
            'startDate',
            'endDate',
        ])
        .reset_index(drop=True)
    )

    return df_split

### Test script split_by_overlappingPeriod
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files'
    df_in = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_split_by_overlappingPeriod.xlsx'))
    df_in = df_in.rename(columns={
            'index': 'index',
            'assetGroupingName': 'asset',
            'MaintenanceShutdownPlannedFeedOff': 'startDate',        
            'MaintenanceShutdownPlannedFeedOn': 'endDate'
        })
    df_out = split_events_all_assets(df_in)
    output_file_1 = os.path.join(main_folder_path, 'output_for_testing_split_by_overlappingPeriod.xlsx')
    df_out.to_excel(output_file_1, index=False)
    print(f"Saved to: {output_file_1}")
### End Test script

###     END of script 
