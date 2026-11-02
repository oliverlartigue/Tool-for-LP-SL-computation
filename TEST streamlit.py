import streamlit as st
import pandas as pd

from generate_calendar import build_split_week_calendar
from split_by_overlappingPeriod import split_events_all_assets
from split_by_operatingDay import split_periods_by_operating_day
from SL_hours_by_asset_opDay import (
    SL_hours_by_asset_by_operating_day,
    effective_hours_by_asset_by_startEndDate
)
from SL_hours_by_asset_splitWeek import SL_hours_by_asset_by_split_week
from compare_output_with_LP import (
    split_LP_AutoFA_by_splitweek,
    compare_SL_output_with_LP_weekly,
    compare_SL_output_with_LP_annual
)
from get_shuts_from_API import (
    get_shuts_approved_only_from_MSF_API,
    get_shuts_including_pending_from_MSF_API
)
from get_shuts_from_ORDW import get_raw_shuts_from_MSFsnapshot_in_ORDW


st.title("LP Scheduled Loss Computation")

# -----------------------------
# Select shutdown source
# -----------------------------

source = st.radio(
    "MSF shutdown source",
    [
        "MSF API - approved only",
        "MSF API - including pending",
        "ORDW"
    ]
)


# -----------------------------
# Run
# -----------------------------

if st.button("Run"):

    try:

        with st.spinner("Getting MSF shutdown data..."):

            if source == "MSF API - approved only":
                df_rawshuts = get_shuts_approved_only_from_MSF_API()

            elif source == "MSF API - including pending":
                df_rawshuts = get_shuts_including_pending_from_MSF_API()

            elif source == "ORDW":
                df_rawshuts = get_raw_shuts_from_MSFsnapshot_in_ORDW()

        st.success("MSF data loaded")

        st.write("Number of raw shutdown rows:", len(df_rawshuts))

        st.dataframe(
            df_rawshuts,
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)