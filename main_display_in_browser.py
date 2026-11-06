import streamlit as st
import pandas as pd
import altair as alt
import io
from contextlib import redirect_stdout
from main_LP_SL_computation import main_LP_SL_computation

st.set_page_config(layout="wide")
st.title("Scheduled Loss (SL) computation - with Live Parameters (LP) methodology")

source = st.radio(
    "Select MSF shutdown source",
    ["1 - Excel Input",
     "2 - MSF API - approved only",
     "3 - MSF API - including pending",
     "4 - ORDW snapshot"]
)

choice = source[0]

if st.button("Run"):
    try:
        output = io.StringIO()
        with st.spinner("Running..."):
            with redirect_stdout(output):
                st.session_state.results = main_LP_SL_computation(choice)
        st.session_state.run_log = output.getvalue()
        st.success("Completed")
    except Exception as e:
        st.exception(e)


if "results" in st.session_state:
    results = st.session_state.results
    ## main header
    st.header("Computed SL results")
    # get MSF source data from the results
    df_display_shuts = results["shuts"].copy()
    st.write("MSF Source Data:", df_display_shuts["MSFSourceData"].iloc[0]) # display MSF source data 
    ## display annual SL
    st.subheader("Comparison of computed annual SL with LP Auto SL")
    df_display_annual_SL = results["comparison_annual"].copy()
    df_display_annual_SL = df_display_annual_SL.rename(columns={  # rename columns for better display in chart
        "SLHours_Output": "SL hours computed",
        "SLHours_LP_AutoFA": "Live Parameters Auto SL hours",
        "SLHours_Output_less_LP_AutoFA": "Difference"})
    df_display_annual_SL[""] = "" # add an empty column for better visualization
    display_cols = ["asset", "Year", "YearStartDate", "YearEndDate", "SL hours computed", "Live Parameters Auto SL hours","Difference", ""]
    df_display_annual_SL[["SL hours computed", "Live Parameters Auto SL hours", "Difference"]] = df_display_annual_SL[["SL hours computed", "Live Parameters Auto SL hours", "Difference"]].astype("Float64") # this keeps missing value as blank/<NA>, not 0
    st.dataframe(
        df_display_annual_SL[display_cols],
        column_config={
            "asset": st.column_config.TextColumn(width="small"),
            "Year": st.column_config.NumberColumn(width="small"),
            "YearStartDate": st.column_config.DateColumn(format="YYYY-MM-DD", width="small"),
            "YearEndDate": st.column_config.DateColumn(format="YYYY-MM-DD", width="small"),
            "SL hours computed": st.column_config.NumberColumn(width="small"),
            "Live Parameters Auto SL hours": st.column_config.NumberColumn(width="small"),
            "Difference": st.column_config.NumberColumn(width="small"),
            "": st.column_config.TextColumn(width=10)},
        width="stretch",
        height=600)

    ## display Weekly chart
    st.subheader("Weekly Scheduled Loss")
    df_chart_weekly = results["comparison_weekly"].copy()
    assets = sorted(df_chart_weekly["asset"].dropna().unique())
    default_index = assets.index("B4 Plant") if "B4 Plant" in assets else 0
    selected_asset = st.selectbox(
        "Select asset",
        assets,
        index=default_index)
    df_chart_weekly = df_chart_weekly[df_chart_weekly ["asset"] == selected_asset]
    df_chart_weekly["SL hours computed"] = pd.to_numeric(df_chart_weekly["SLHours_Output"], errors="coerce")
    df_chart_weekly["Live Parameters Auto SL hours"] = pd.to_numeric(df_chart_weekly["SLHours_LP_AutoFA"], errors="coerce")

    df_chart_weekly = df_chart_weekly.melt(
        id_vars=["SplitWeekStartDate"],
        value_vars=["SL hours computed", "Live Parameters Auto SL hours"],
        var_name="Source",
        value_name="SLHours")
    # df_chart_weekly["Source"] = df_chart_weekly["Source"].replace({  # rename columns for better display in chart
    #     "SLHours_Output": "SL hours computed",
    #     "SLHours_LP_AutoFA": "Live Parameters Auto SL hours"})
    df_chart_weekly["SplitWeek"] = df_chart_weekly["SplitWeekStartDate"].dt.strftime("%Y-%m-%d")
    df_chart_weekly = alt.Chart(df_chart_weekly  ).mark_bar().encode(
        x=alt.X("SplitWeek:N", title="Split Week", sort=None),
        xOffset=alt.XOffset("Source:N"),
        y=alt.Y("SLHours:Q", title="SL Hours"),
        color=alt.Color(
            "Source:N",
            scale=alt.Scale(
                domain=["SL hours computed", "Live Parameters Auto SL hours"],
                range=["#0078D4", "#87CEEB"])),
        tooltip=["SplitWeek:N", "Source:N", "SLHours:Q"]
    ).properties(height=500)
    st.altair_chart(df_chart_weekly, width="stretch")

    ## Display Shuts
    st.subheader("Shuts (after mapping) used for SL computation")
    # df_display_shuts = results["shuts"].copy()
    st.write("MSF Source Data:", df_display_shuts["MSFSourceData"].iloc[0]) # display MSF source data 
    display_cols = ["MaintenanceShutdown_BK", "MaintenanceShutdownTypeName", "MaintenanceShutdownStatusName", "MaintenanceShutdownPlannedFeedOff", "MaintenanceShutdownPlannedFeedOn", "assetGroupingName", "MSFName", "percentageImpact"]
    # df_display_shuts[["SLHours_Output", "SLHours_LP_AutoFA", "SLHours_Output_less_LP_AutoFA"]] = df_display_shuts[["SLHours_Output", "SLHours_LP_AutoFA", "SLHours_Output_less_LP_AutoFA"]].astype("Float64") # this keeps missing value as blank/<NA>, not 0
    st.dataframe(
        df_display_shuts[display_cols],
        column_config={
            "MaintenanceShutdown_BK": st.column_config.TextColumn(width="small"),
            "MaintenanceShutdownTypeName": st.column_config.TextColumn(width="small"),
            "MaintenanceShutdownStatusName": st.column_config.TextColumn(width="small"),
            "MaintenanceShutdownPlannedFeedOff": st.column_config.DateColumn(format="YYYY-MM-DD", width="small"),
            "MaintenanceShutdownPlannedFeedOn": st.column_config.DateColumn(format="YYYY-MM-DD", width="small"),
            "assetGroupingName": st.column_config.TextColumn(width="small"),
            "MSFName": st.column_config.TextColumn(width="small"),
            "percentageImpact": st.column_config.NumberColumn(width="small")},
        width="stretch",
        height=600)

    ## Dispaly Log
    st.subheader("Run log")
    st.code(st.session_state.run_log)
