import streamlit as st
import pandas as pd
import os
from supabase import create_client
import altair as alt
# -----------------------------
# INIT SUPABASE
# -----------------------------
#@st.cache_resource
def get_client():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"]
    )
supabase = get_client()
st.title("📊 Medista - Patient Test Progression")
# -----------------------------
# 👤 LOAD ALL PATIENTS
# -----------------------------
# @st.cache_data
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
# @st.cache_data
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
print(df)
print(df.columns)
if df.empty:
    st.warning("No data found")
    st.stop()
# -----------------------------
# 🧪 SELECT TESTS
# -----------------------------
if st.button("🧹 Normalize Test Names"):
    supabase.rpc("normalize_all_tests").execute()
    st.success("Normalization complete!")

test_options = sorted(df["canonical_name"].unique())
selected_tests = st.multiselect(
    "Select tests",
    test_options
)


# -----------------------------
# 📊 PROCESS DATA
# -----------------------------
if selected_tests:
    df = df[df["canonical_name"].isin(selected_tests)]
    print(df.shape)
    
    # Clean numeric values
    df["value"] = pd.to_numeric(
        df["value_numeric"].fillna(
            df["value_text"].astype(str).str.replace(",", "")
        ),
        errors="coerce"
    )
    
    df["report_date"] = pd.to_datetime(df["report_date"])
    print(df[["canonical_name","value","value_numeric","value_text","report_date"]])
    st.subheader("📈 Test Trends Over Time")
    # -----------------------------
    # 📈 CHARTS (ONE PER TEST)
    # -----------------------------
    for test in selected_tests:
        test_df = df[df["canonical_name"] == test].copy()
        test_df = test_df.sort_values("report_date")
        st.write(f"### {test}")
        chart = alt.Chart(test_df).mark_line(point=True).encode(
#            x=alt.X("report_date:T", title="Date"),

            x=alt.X(
                "report_date:T",
                title="Date",
                scale=alt.Scale(padding=30)
            ),            
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


# st.markdown("---")
# st.markdown("<h3 style='text-align: center;'>Meet the team</h3>", unsafe_allow_html=True)

# col1, col2, col3 = st.columns(3)


# with col1:
#     st.image("images/fatima.png", width=120)    
#     st.markdown("""
#     **Fatima Zaman**  
#     Final-year Software Engineering student at the University of Management and Technology, Lahore. 
#     Focused on applied AI, including deep learning, NLP, and agentic systems, with experience in 
#     Android and web application development.
#     """)

# with col2:
#     st.image("images/muntaha.png", width=120)    
#     st.markdown("""
#     **Muntaha Sheikh**  
#     Public Policy & Governance graduate working at the intersection of AI governance and ethical AI. 
#     Currently transitioning into the tech domain with a focus on AI development, supported by hands-on 
#     learning, hackathons, and practical exposure to real-world innovation challenges.
#     """)


# with col3:
#     st.image("images/ashhad.png", width=120)    
#     st.markdown("""
#     **Ashhadul Islam**  
#     Postdoctoral Researcher at KTH Royal Institute of Technology, Sweden. His research spans machine 
#     learning, deep learning, and AI-driven healthcare systems, including physiological modeling and 
#     digital twins, with prior experience in building scalable industry-grade ML solutions.
#     """)