import pandas as pd
import os
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime

# write an excel file with the MSF shut
def write_output_SL_and_shuts_in_excel(df_comparison_SL_annual, df_comparison_SL_weekly, df_shuts, df_split, df_SL_opDay, df_SL_splitWeek, period_start_date, period_end_date, main_folder_path, output_folder, outputfile_name):
    run_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = os.path.join(main_folder_path, output_folder, f'run {run_datetime} - {outputfile_name}')
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # create sheets with comparison SL annual and weekly
        df_comparison_SL_annual.to_excel(writer, sheet_name="Annual Comparison", index=False, startrow=2)
        df_comparison_SL_weekly.to_excel(writer, sheet_name="SplitWeek Comparison", index=False, startrow=2)
        # Get distinct MSFSourceData values - should be unique, but getting a list just in case there is an inconsistency
        MSFSourceDataNames = ", ".join(df_shuts["MSFSourceData"].dropna().astype(str).unique())
        # foramt sheets with comparison SL annual and weekly 
        for sheet_name in ["SplitWeek Comparison", "Annual Comparison"]: # loop to format excel output
            ws = writer.sheets[sheet_name]
            ws["A1"] = "SL output computed from shuts in '" + MSFSourceDataNames + "' and compared with Live Parameters" # Print info on first row          
            for cell in ws[3]:      # Wrap column names
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            for col in ws.iter_cols():
                if col[2].value in ["SplitWeekStartDate", "SplitWeekEndDate", "YearStartDate", "YearEndDate" ]:
                    ws.column_dimensions[get_column_letter(col[2].column)].width = 11  # set column width at 11
                    for cell in col[1:]:
                        cell.number_format = "d/mm/yyyy"  # Format datetime columns
        ws.freeze_panes = "A4"  # freeze first 3 rows          
        # write a sheet e with the MSF shut and the LP mapping
        df_shuts.drop(columns=['MSFSourceData', 'assetGroupingPK']).to_excel(writer, index=False, sheet_name="MSF_shuts_after_mapping", startrow=2)
        ws = writer.sheets["MSF_shuts_after_mapping"]
        ws["A1"] = 'shuts from MSF - one row for each combination of MSF shut & MSFName (aka MSF asset code). Show percentage impact of MSFName on asset (assetGroupingName) as defined in Live Parameters MSF mapping' # Print info on first row      
        ws["A2"] = 'source: ' + df_shuts['MSFSourceData'].iloc[0] # Print info on second row
        for cell in ws[3]:     
            cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
        for col in ws.iter_cols():
            if col[2].value in ['MaintenanceShutdownPlannedFeedOff', 'MaintenanceShutdownPlannedFeedOn']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy h:mm"     # Format datetime columns 
        ws.freeze_panes = "A4"  # freeze first 3 rows                
        # write a sheet  with the split Shuts
        df_split.drop(columns=['MSFSourceData', 'assetGroupingPK']).to_excel(writer, index=False, sheet_name='split Shuts by OperatingDay', startrow=2)
        df_split = df_split[(df_split['operatingDay'] >= period_start_date) & (df_split['operatingDay'] <= period_end_date)].copy()  # only show operation within the period of interest
        ws = writer.sheets['split Shuts by OperatingDay']
        ws["A1"] = 'shuts from MSF split by Day (from 6am to 6am) - one row for each combination of OperatingDay & MSF shut & MSFName (aka MSF asset code). SartDate and EndDate of the portion of the shut in the OperatingDay' # Print info on first row      
        ws["A2"] = 'shut source: ' + df_split['MSFSourceData'].iloc[0] # Print info on second row
        for cell in ws[3]:     
            cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
        for col in ws.iter_cols():
            if col[2].value in ['startDate', 'endDate', 'MaintenanceShutdownPlannedFeedOff', 'MaintenanceShutdownPlannedFeedOn']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy h:mm"     # Format datetime columns 
            if col[2].value in ['operatingDay']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 14  # set column width at 14
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy"     # Format datetime columns  
        ws.freeze_panes = "A4"  # freeze first 3 row                                   
        # write a sheet  with SL by asset, by Operating Day
        df_SL_opDay.to_excel(writer, index=False, sheet_name='SL by OperatingDay', startrow=2)
        ws = writer.sheets['SL by OperatingDay']
        ws["A1"] = 'Scheduled Loss (SL) as computed in Live Parameters by asset, by Operating Day' # Print info on first row      
        ws["A2"] = 'shut source: ' + df_split['MSFSourceData'].iloc[0] # Print info on second row
        for cell in ws[3]:     
            cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
        for col in ws.iter_cols():
            if col[2].value in ['operatingDay']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 14  # set column width at 14
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy"     # Format datetime columns            
            if col[2].value in ['maintenanceShutdownBKss']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
        ws.freeze_panes = "A4"  # freeze first 3 row    
        # write a sheet  with SL by asset, by Split Week
        df_SL_splitWeek.to_excel(writer, index=False, sheet_name='SL by Split Week', startrow=2)
        ws = writer.sheets['SL by Split Week']
        ws["A1"] = 'Scheduled Loss (SL) by asset, by Split Week, computed with the same methodology as Live Parameters auto forward adjustments ' # Print info on first row      
        ws["A2"] = 'shut source: ' + df_split['MSFSourceData'].iloc[0] # Print info on second row
        for cell in ws[3]:     
            cell.alignment = Alignment(wrap_text=True, vertical="top") # Wrap column names
        for col in ws.iter_cols():
            if col[2].value in ['SplitWeekStartDate', 'SplitWeekEndDate']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 14  # set column width at 14
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy"     # Format datetime columns    
            if col[2].value in ['SplitWeekStartDate6am', 'SplitWeekEndDate6am']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
                for cell in col[1:]:
                    cell.number_format = "d/mm/yyyy h:mm"     # Format datetime columns                           
            if col[2].value in ['maintenanceShutdownBKss']:
                ws.column_dimensions[get_column_letter(col[2].column)].width = 18  # set column width at 18
        ws.freeze_panes = "A4"  # freeze first 3 row                 
    print(f"Saved to: {output_file}")
    return ()


### Test script compare_output_with_LP
if __name__ == "__main__":  # the if condition prevent the above code from failing when called by another python file, but enable the following test code to run if exectuted from the current file
    main_folder_path = r'C:\Users\oliver.lartigue\OneDrive - Rio Tinto\Documents\31. Tool for LP SL computation'
    output_folder = 'Testing Input and Output Files'
    input_folder = output_folder
    outputfile_name = 'output_for_testing_write_SL_and_shuts.xlsx'
    period_start_date = "2027-01-01"
    period_end_date = "2027-12-31"
    df_shuts = pd.read_excel(os.path.join(main_folder_path, input_folder, 'input_for_testing_df_shuts_from_main.xlsx'))
    df_split = pd.read_excel(os.path.join(main_folder_path, input_folder, 'input_for_testing_df_split_from_main.xlsx'))
    df_SL_opDay = pd.read_excel(os.path.join(main_folder_path, input_folder, 'input_for_testing_df_SL_opDay_from_main.xlsx'))
    df_SL_splitWeek = pd.read_excel(os.path.join(main_folder_path, input_folder, 'input_for_testing_df_SL_splitWeek_from_main.xlsx'))
    df_comparison_SL_weekly = pd.read_excel(os.path.join(main_folder_path, input_folder, 'input_for_testing_df_comparison_SL_weekly_from_main.xlsx'))
    df_comparison_SL_annual = pd.read_excel(os.path.join(main_folder_path, input_folder, 'input_for_testing_df_comparison_SL_annual_from_main.xlsx'))
    write_output_SL_and_shuts_in_excel(df_comparison_SL_annual, df_comparison_SL_weekly, df_shuts, df_split, df_SL_opDay, df_SL_splitWeek,period_start_date, period_end_date, main_folder_path, output_folder, outputfile_name)
### End Test script
