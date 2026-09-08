# Oliver lartige - Sep 2026
### Compute SL hours by asset by operatingDay from multiple sliced shuts period within an opertating day for an asset



import pandas as pd
import os

def effective_hours_by_asset_by_startEndDate(df):
    # Function Parameter is df with at least 6 cols : startDate, endDate, operatingDay, asset, MSFName, percentageImpact
    # for each unique combination of asset, MSFName, startdate enddate, compute an effective SL duration in hours by computing : 
    # (a) an effective percentage impact which is the sum of percentage impact capped at 1 for the [asset, startdate enddate] combination (note before that there is a grouping by [asset, MSFName, startdate, enddate] to remove duplicate in case there was two shuts againt the same MSFName at the same start-end date)
    # (b)  a gross duration which is the time in hour between startdate enddate for the asset
    # (c) an effective duration which is the gross duration times the effective percentage impact - which is the SL hour for the [asset,startDate, endDate, operatingDay] combination.
    # Function return columns : asset, operatingDay, effectiveDurationHours - for computing SL downstream    
    # Function return also columns : startDate, endDate, MSFName, maintenanceShutdownBKs,effectivePercentageImpact - for analytical / testing purpose


    # Compute  percentage impact at asset/MSFName/start/end/day level
    df_msfcode = (
        df.groupby(['asset', 'MSFName', 'startDate', 'endDate', 'operatingDay'], as_index=False)
        .agg(
            percentageImpact=('percentageImpact', 'max'),
            maintenanceShutdownBKs=('MaintenanceShutdown_BK', lambda x: '|'.join(map(str, sorted(x.unique()))))
        )
    )

    # compute effective impact at asset/start/end/day level : sum impacts across MSFNames and cap at 1 
    result = (
        df_msfcode.groupby(['asset', 'startDate', 'endDate', 'operatingDay'], as_index=False)
        .agg(
            effectivePercentageImpact=(
                'percentageImpact',
                lambda x: min(x.sum(), 1.0)
            ),
            maintenanceShutdownBKss=(
                'maintenanceShutdownBKs',
                lambda x: '|'.join(
                    sorted(
                        {
                            bk
                            for s in x.dropna()
                            for bk in str(s).split('|')
                        }
                    )
                )
            )
        )
    )            


    # compute gross duration as duration btw start-end date
    result['grossDurationHours'] = (
        (result['endDate'] - result['startDate'])
        .dt.total_seconds() / 3600
    )
    # compute effectiveDurationHours  as duration btw start-end date time the effectivePercentageImpact : this is the SL for the asset for the start-enddate period 
    result['effectiveDurationHours'] = (
        result['grossDurationHours']
        * result['effectivePercentageImpact']
    )

    result = result[
        [
            'asset',
            'startDate',
            'endDate',           
            'operatingDay',
            'maintenanceShutdownBKss',
            'effectivePercentageImpact',
            'grossDurationHours',
            'effectiveDurationHours',
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

### Test script SL_hours_by_asset_opDay
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\Testing Input and Output Files'
    df_in = pd.read_excel(os.path.join(main_folder_path, 'input_for_testing_SL_hours_by_asset_opDay.xlsx'))
    df_out = SL_hours_by_asset_by_operating_day(effective_hours_by_asset_by_startEndDate(df_in))
    output_file_1 = os.path.join(main_folder_path, 'output_for_testing_SL_hours_by_asset_opDay.xlsx')
    df_out.to_excel(output_file_1, index=False)
    print(f"Saved to: {output_file_1}")
### End Test script

###     END of script