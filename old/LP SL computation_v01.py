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


shutdowns = df_shuts.copy()

start_col = 'MaintenanceShutdownPlannedFeedOff'
end_col = 'MaintenanceShutdownPlannedFeedOn'
group_col = 'assetGroupingName'

# Ensure the period columns are datetimes
shutdowns[start_col] = pd.to_datetime(shutdowns[start_col],errors='coerce')
shutdowns[end_col] = pd.to_datetime(shutdowns[end_col],errors='coerce')

# Remove invalid periods           ########## ADD A CHECK TO SEE INVALID DATA IF ANY
shutdowns = shutdowns.dropna(subset=[group_col, start_col, end_col])
shutdowns = shutdowns[shutdowns[end_col] > shutdowns[start_col]].copy()

def split_asset_group_periods(asset_group):
    #   Split shutdown rows at every FeedOff or FeedOn boundary within one assetGroupingName.

    # Create the ordered boundary timestamps for this asset group
    boundaries = (pd.concat([
            asset_group[start_col],
            asset_group[end_col]
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
        active_rows = asset_group[
            (asset_group[start_col] < split_end)
            & (asset_group[end_col] > split_start)
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
            *asset_group.columns,
            'OriginalFeedOff',
            'OriginalFeedOn'
        ])

    return pd.DataFrame(split_rows)


# Split independently for every assetGroupingName
split_parts = []

for asset_grouping_name, asset_group in shutdowns.groupby(
    group_col,
    dropna=False,
    sort=False
):
    split_parts.append(
        split_asset_group_periods(asset_group)
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

###     END: Split rows for overlapping shuts 



print(df_split[df_split['assetGroupingName']=='B4 Plant'])
print(df_split)


output_file = r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\shutdown_analysis.xlsx"
df_split.to_excel(output_file, index=False)
print(f"Saved to: {output_file}")




