import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt
# -----------------------------
# INIT SUPABASE
# -----------------------------
@st.cache_resource
def get_client():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"]
    )
supabase = get_client()
st.title("📊 Patient Test Progression")
# -----------------------------
# 👤 LOAD ALL PATIENTS
# -----------------------------
@st.cache_data
def get_all_patients():
    res = supabase.table("patients") \
        .select("patient_id, name") \
        .order("name") \
        .execute()
    return res.data
patients = get_all_patients()
patient_map = {p["name"]: p["patient_id"] for p in patients}
patient_names = list(patient_map.keys())
# -----------------------------
# 👤 SELECT PATIENT
# -----------------------------
selected_patient_name = st.selectbox(
    "Select patient",
    patient_names
)
selected_patient_id = patient_map[selected_patient_name]
# -----------------------------
# 📥 FETCH DATA
# -----------------------------
@st.cache_data
def fetch_data(patient_id):
    reports = supabase.table("reports") \
        .select("*") \
        .eq("patient_id", patient_id) \
        .execute().data
    if not reports:
        return pd.DataFrame()
    report_ids = [r["report_id"] for r in reports]
    tests = supabase.table("tests") \
        .select("*") \
        .in_("report_id", report_ids) \
        .execute().data
    if not tests:
        return pd.DataFrame()
    test_ids = [t["test_id"] for t in tests]
    measurements = supabase.table("measurements") \
        .select("*") \
        .in_("test_id", test_ids) \
        .execute().data
    df_reports = pd.DataFrame(reports)
    df_tests = pd.DataFrame(tests)
    df_meas = pd.DataFrame(measurements)
    df = df_tests.merge(df_reports, on="report_id") \
                 .merge(df_meas, on="test_id")
    return df

df = fetch_data(selected_patient_id)
if df.empty:
    st.warning("No data found")
    st.stop()
# -----------------------------
# 🧪 SELECT TESTS
# -----------------------------
test_options = sorted(df["test_name"].unique())
selected_tests = st.multiselect(
    "Select tests",
    test_options
)
# -----------------------------
# 📊 PROCESS DATA
# -----------------------------
if selected_tests:
    df = df[df["test_name"].isin(selected_tests)]
    # Clean numeric values
    df["value"] = pd.to_numeric(
        df["value_numeric"].fillna(
            df["value_text"].astype(str).str.replace(",", "")
        ),
        errors="coerce"
    )
    df["report_date"] = pd.to_datetime(df["report_date"])
    st.subheader("📈 Test Trends Over Time")
    # -----------------------------
    # 📈 CHARTS (ONE PER TEST)
    # -----------------------------
    for test in selected_tests:
        test_df = df[df["test_name"] == test].copy()
        test_df = test_df.sort_values("report_date")
        st.write(f"### {test}")
        chart = alt.Chart(test_df).mark_line(point=True).encode(
            x=alt.X("report_date:T", title="Date"),
            y=alt.Y("value:Q", title=f"Value ({test_df['unit'].iloc[0]})"),
            tooltip=["report_date", "value"]
        ).properties(
            width=700,
            height=300
        )
        st.altair_chart(chart, use_container_width=True)
        # -----------------------------
        # 📄 TABLE
        # -----------------------------
        display_df = test_df[
            ["report_date", "value", "unit", "source_file"]
        ].copy()
        display_df["report_link"] = display_df["source_file"].apply(
            lambda x: f"[Open Report]({x})" if x else ""
        )
        st.dataframe(display_df)