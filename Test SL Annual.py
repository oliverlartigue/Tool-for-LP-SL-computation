# Create annual comparison
df_comparison_annual = compare_SL_annual(df_comparison)

# Write split-week and annual results into separate tabs
with pd.ExcelWriter(output_file,engine="openpyxl") as writer:
    df_comparison.to_excel(
        writer,
        sheet_name="SplitWeek Comparison",
        index=False
    )
    df_comparison_annual.to_excel(
        writer,
        sheet_name="Annual Comparison",
        index=False
    )