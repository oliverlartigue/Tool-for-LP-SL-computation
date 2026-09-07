# Oliver lartige - Sep 2026
### Split one row with a date range into multiple daily segments (note operting day start at 6am)

import pandas as pd

def split_periods_by_operating_day(df):
    # Function Parameter is df with at least 2 cols : startDate, endDate
    # Function Parameter split event by oerating days (note operting day start at 6am)
    # Output has at least 3 cols : startDate, endDate, operatingDay

    split_rows = []

    for _, row in df.iterrows():

        start = row['startDate']
        end = row['endDate']

        # Find first 6am boundary after the period start
        first_boundary = (
            start.normalize() + pd.Timedelta(hours=6)
        )

        if first_boundary <= start:
            first_boundary += pd.Timedelta(days=1)

        # Build all boundaries
        boundaries = [start]

        current = first_boundary

        while current < end:
            boundaries.append(current)
            current += pd.Timedelta(days=1)

        boundaries.append(end)

        # Create split periods
        for split_start, split_end in zip(
            boundaries[:-1],
            boundaries[1:]
        ):
            new_row = row.copy()
            new_row['startDate'] = split_start
            new_row['endDate'] = split_end
            new_row['operatingDay'] = (split_start - pd.Timedelta(hours=6)).normalize() # Operating day runs from 06:00 to next day 06:00

            split_rows.append(new_row)

    return pd.DataFrame(split_rows).reset_index(drop=True)


# GET DATA _
df = pd.read_excel(r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\data_for_testing.xlsx')

df_out = split_periods_by_operating_day(df)

output_file_1 = r"C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation\output_for_testing.xlsx"
df_out.to_excel(output_file_1, index=False)
print(f"Saved to: {output_file_1}")


###     END of script