# Oliver lartige - Sep 2026
### sum SL hours by asset by splitweek from SL hours by asset by operatingDay



import pandas as pd
import numpy as np


def SL_hours_by_asset_by_split_week(df_sl, df_calendar):

    # Join calendar
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

    # Aggregate SL hours
    result = (
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

    # Compute calendar hours
    result['CalendarHours'] = (
        result['SplitWeekEndDate6am']
        - result['SplitWeekStartDate6am']
    ).dt.total_seconds() / 3600

    # Compute SL %
    result['SLPct'] = np.where(
        result['CalendarHours'] == 0,
        0,
        result['SLHours'] / result['CalendarHours']
    )

    return result[
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
