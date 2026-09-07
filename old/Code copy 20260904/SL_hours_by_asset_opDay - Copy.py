# Oliver lartige - Sep 2026
### Compute SL hours by asset by operatingDay from multiple sliced shuts period within an opertating day for an asset


import pandas as pd

def effective_hours_by_asset_by_startEndDate(df):
    # Function Parameter is df with at least 5 cols : startDate, endDate, operatingDay, asset, percentageImpact
    # for each unique combination of asset startdate enddate, compute an effective SL duration in hours bycomputing : 
    # (a) an effective percentage impact which is the sum of percentage impact capped at 1
    # (b)  a gross duration which is the time in hour beteen startdate enddate 
    # (c) an effective duration which is the gross duration times the effective percentage impact - which is the SL hour for the [asset,startDate, endDate, operatingDay] combination.
    # Function return columns : asset, operatingDay, effectiveDurationHours - for computing SL downstream    
    # Function return also columns : startDate, endDate, maintenanceShutdownBKs,effectivePercentageImpact - for analytical / testing purpose

    group_cols = ['asset', 'startDate', 'endDate','operatingDay']

    result = (
        df.groupby(group_cols, as_index=False)
        .agg(
            effectivePercentageImpact=(
                'percentageImpact',
                lambda x: min(x.sum(), 1.0)
            ),
            maintenanceShutdownBKs=(
                'MaintenanceShutdown_BK',
                lambda x: '|'.join(
                    map(str, sorted(x.unique()))
                )
            )
        )
    )

    result['grossDurationHours'] = (
        (result['endDate'] - result['startDate'])
        .dt.total_seconds() / 3600
    )

    result['effectiveDurationHours'] = (
        result['grossDurationHours']
        * result['effectivePercentageImpact']
    )

    result = result[
        [
            'asset',
            'effectiveDurationHours',
            'startDate',
            'endDate',
            'operatingDay',
            'maintenanceShutdownBKs',
            'effectivePercentageImpact',
            'grossDurationHours'
        ]
    ]
    return result

def SL_hours_by_asset_by_operating_day(df):

    group_cols = ['asset', 'operatingDay']

    result = (
        df.groupby(group_cols, as_index=False)
        .agg(
            SLHours=(
                'effectiveDurationHours','sum')
            )
        )
    
    result = result[
        [
            'asset',
            'operatingDay',            
            'SLHours'

        ]
    ]

    return result

if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    # GET DATA _
    df = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Output_splitShuts.xlsx')

    df_temp = effective_hours_by_asset_by_startEndDate(df)
    df_out = SL_hours_by_asset_by_operating_day(df_temp)

    print(type(df_out))
    print(df_out)

    output_file_1 = r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Output_for_testing_SL.xlsx"
    df_out.to_excel(output_file_1, index=False)
    print(f"Saved to: {output_file_1}")


###     END of script