# Oliver lartigue - Sep 2026
### sum SL hours by asset by splitweek from SL hours by asset by operatingDay


import pandas as pd
import numpy as np
import os


def SL_hours_by_asset_by_split_week(df_sl, df_calendar):

    # Aggregate SL hours by split week
    df = df_sl.merge(
        df_calendar[
            [
                'Date',
                'SplitWeekCode',
                'SplitWeekStartDate6am',
                'SplitWeekEndDate6am'
            ]
        ],
        left_on='operatingDay',
        right_on='Date',
        how='left'
    )

    df_sl_week = (
        df.groupby(
            [
                'asset',
                'SplitWeekCode',
                'SplitWeekStartDate6am',
                'SplitWeekEndDate6am'
            ],
            as_index=False
        )
        .agg(
            SLHours=('SLHours', 'sum')
        )
    )

    # Complete list of assets
    assets = pd.DataFrame(
        {
            'asset': sorted(df_sl['asset'].unique())
        }
    )

    # Complete list of split weeks
    split_weeks = (
        df_calendar[
            [
                'SplitWeekCode',
                'SplitWeekStartDate6am',
                'SplitWeekEndDate6am'
            ]
        ]
        .drop_duplicates()
        .sort_values('SplitWeekStartDate6am')
    )

    # Cartesian product asset x split week
    assets['_tmp'] = 1
    split_weeks['_tmp'] = 1

    result = (
        assets.merge(
            split_weeks,
            on='_tmp'
        )
        .drop(columns='_tmp')
    )

    # Bring in SL hours
    result = result.merge(
        df_sl_week,
        on=[
            'asset',
            'SplitWeekCode',
            'SplitWeekStartDate6am',
            'SplitWeekEndDate6am'
        ],
        how='left'
    )

    # Missing weeks get zero SL hours
    result['SLHours'] = (
        result['SLHours']
        .fillna(0)
    )

    # Calendar hours
    result['CalendarHours'] = (
        result['SplitWeekEndDate6am']
        - result['SplitWeekStartDate6am']
    ).dt.total_seconds() / 3600

    # SL %
    result['SLPct'] = np.where(
        result['CalendarHours'] == 0,
        0,
        result['SLHours']
        / result['CalendarHours']
    )

    result = result[
        [
            'asset',
            'SplitWeekCode',
            'SplitWeekStartDate6am',
            'SplitWeekEndDate6am',
            'CalendarHours',
            'SLHours',
            'SLPct'
        ]
    ]

    result = result.sort_values(
        [
            'asset',
            'SplitWeekStartDate6am'
        ]
    )

    return result

### Test script SL_hours_by_asset_splitWeek
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Files Input and Output'
    df_in_sl = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_SL_hours_by_asset_splitWeek_sl.xlsx'))
    df_in_calendar = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_SL_hours_by_asset_splitWeek_calendar.xlsx'))
    df_out = SL_hours_by_asset_by_split_week(df_in_sl, df_in_calendar)
    output_file_1 = os.path.join(main_folder_path, 'output_for_testing_SL_hours_by_asset_splitWeek.xlsx')
    df_out.to_excel(output_file_1, index=False)
    print(f"Saved to: {output_file_1}")
### End Test script

###     END of script


