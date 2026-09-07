import pandas as pd



df_mapping = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\LP MSF mapping.xlsx')
# print (df_mapping.head(10))
df_rawshuts = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\MSF shuts.xlsx')
df_rawshuts = df_rawshuts[['SourceIdentifier_AssetCode','MaintenanceShutdown_BK','MaintenanceShutdownPlannedFeedOff','MaintenanceShutdownPlannedFeedOn']]
# print (df_rawshuts.head(10))

df_shuts = df_rawshuts.merge(  # add asset group and percentage impact
    df_mapping, 
    left_on='SourceIdentifier_AssetCode',right_on='MSFName',how='left')
df_shuts = df_shuts.dropna(subset=['assetGroupingName'])  # remove row which do not have an assetgroupname from the mapping
df_shuts = df_shuts.drop(columns=['SourceIdentifier_AssetCode'])  #remove col
print (df_shuts.head(1000))


###     START: Split rows for overlapping shuts
"""
# split plit row when there is an overalapping period as defined by MaintenanceShutdownPlannedFeedOff and MaintenanceShutdownPlannedFeedOn for each assetGroupingName 
# for example, a CL Plant Shutdown runs from 16/11/2026 01:00 to 21/11/2026 11:00
# If another CL Plant shutdown overlaps part of that range, for example from 19/11/2026 06:00 to 20/11/2026 18:00
# the first shutdown is split into:
# - 16/11/2026 01:00 to 19/11/2026 06:00
# - 19/11/2026 06:00 to 20/11/2026 18:00
#  -20/11/2026 18:00 to 21/11/2026 11:00
# During the middle segment, both active shutdown rows will appear. Each of your equipment mappings, such as CLAPLT, CLASCSCCT01, and CLATCSCCT03, remains a separate row.

"""


def split_shuts_periods(df):
    # df is a dataframe with at least these cols: MaintenanceShutdownPlannedFeedOn, MaintenanceShutdownPlannedFeedOff
    # Split shutdown rows at every FeedOff or FeedOn boundary - will be used for one assetGroupingName 

    start_col = 'MaintenanceShutdownPlannedFeedOff'
    end_col = 'MaintenanceShutdownPlannedFeedOn'

    # Create the ordered boundary timestamps
    boundaries = (pd.concat([
            df[start_col],
            df[end_col]
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
            (df[start_col] < split_end)
            & (df[end_col] > split_start)
        ]

        if active_rows.empty:
            continue

        for _, original_row in active_rows.iterrows():
            new_row = original_row.copy()

            # Preserve the unsplit source period
            new_row['OriginalFeedOff'] = original_row[start_col]
            new_row['OriginalFeedOn'] = original_row[end_col]

            # Replace the period with the split segment
            new_row[start_col] = split_start
            new_row[end_col] = split_end

            split_rows.append(new_row)

    if not split_rows:
        return pd.DataFrame(columns=[
            *df.columns,
            'OriginalFeedOff',
            'OriginalFeedOn'
        ])

    return pd.DataFrame(split_rows)


def split_shuts_period_all_asset(df):
    # split shuts for overlapping period for each for different assetGroupingName
    # df has at least these cols: assetGroupingName, MaintenanceShutdownPlannedFeedOn, MaintenanceShutdownPlannedFeedOff, MaintenanceShutdown_BK, MSFName

    start_col = 'MaintenanceShutdownPlannedFeedOff'
    end_col = 'MaintenanceShutdownPlannedFeedOn'
    group_col = 'assetGroupingName'

    # Ensure the period columns are datetimes
    df[start_col] = pd.to_datetime(df[start_col],errors='coerce')
    df[end_col] = pd.to_datetime(df[end_col],errors='coerce')

    # Remove invalid periods           ########## ADD A CHECK TO SEE INVALID DATA IF ANY
    df = df.dropna(subset=[group_col, start_col, end_col])
    df = df[df[end_col] > df[start_col]].copy()

    # Split independently for every assetGroupingName
    split_parts = []

    for asset_grouping_name, df_for_asset_grouping_name in df.groupby(
        group_col,
        dropna=False,
        sort=False
    ):
        split_parts.append(
            split_shuts_periods(df_for_asset_grouping_name)
        )

    df_split = pd.concat(
        split_parts,
        ignore_index=True
    )

    # Number of different shutdowns active in each split period
    segment_keys = [
        'assetGroupingName',
        'MaintenanceShutdownPlannedFeedOff',
        'MaintenanceShutdownPlannedFeedOn'
    ]

    overlap_summary = (
        df_split
        .groupby(segment_keys, as_index=False)
        .agg(
            activeShutdownCount=(
                'MaintenanceShutdown_BK',
                'nunique'
            ),
            activeShutdowns=(
                'MaintenanceShutdown_BK',
                lambda values: ', '.join(
                    sorted(
                        values.dropna()
                            .astype(str)
                            .unique()
                    )
                )
            )
        )
    )

    df_split = df_split.merge(
        overlap_summary,
        on=segment_keys,
        how='left'
    )

    df_split['isOverlap'] = (
        df_split['activeShutdownCount'] > 1
    )

    df_split['splitDurationHours'] = (
        df_split['MaintenanceShutdownPlannedFeedOn']
        - df_split['MaintenanceShutdownPlannedFeedOff']
    ).dt.total_seconds() / 3600

    # Arrange the output
    df_split = (
        df_split
        .sort_values([
            'assetGroupingName',
            'MaintenanceShutdownPlannedFeedOff',
            'MaintenanceShutdownPlannedFeedOn',
            'MaintenanceShutdown_BK',
            'MSFName'
        ])
        .reset_index(drop=True)
    )

    return df_split

###     END: Split rows for overlapping shuts 

df_split = split_shuts_period_all_asset(df_shuts)



output_file = r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\shutdown_analysis2.xlsx"
df_split.to_excel(output_file, index=False)
print(f"Saved to: {output_file}")




