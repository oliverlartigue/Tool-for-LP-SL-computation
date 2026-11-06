import streamlit as st
import io
from contextlib import redirect_stdout
from main_LP_SL_computation import main_LP_SL_computation

st.set_page_config(layout="wide")
st.title("Scheduled Loss Computation - with Live Parameters methodology")

source = st.radio(
    "MSF shutdown source",
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
                results = main_LP_SL_computation(choice)

        st.success("Completed")

        st.subheader("Shuts")
        st.dataframe(results["Shuts"], width="stretch", height=600)

        st.subheader("Annual comparison of Annual SL with LP")
        st.dataframe(
            results["comparison_annual"][[
                "asset",
                "Year",
                "YearStartDate",
                "YearEndDate",
                "SLHours_Output",
                "SLHours_LP_AutoFA",
                "SLHours_Output_less_LP_AutoFA"]],
            width="stretch", height=600)

        st.subheader("Run log")
        st.code(output.getvalue())

    except Exception as e:
        st.exception(e)

