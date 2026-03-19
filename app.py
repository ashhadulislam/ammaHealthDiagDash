import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt

# ---------- LOAD DATA ----------
with open("allPagesDiag.json") as f:
    data = json.load(f)

patient = data["patient"]
reports = data["reports"]
summary = data["clinical_summary"]

# ---------- CONFIG ----------
st.set_page_config(layout="wide", page_title="Patient Health Dashboard")

# ---------- COLOR HELPERS ----------
def risk_color(value, good_range=None, warning_range=None):
    if good_range and good_range[0] <= value <= good_range[1]:
        return "green"
    elif warning_range and warning_range[0] <= value <= warning_range[1]:
        return "orange"
    else:
        return "red"

# ---------- HEADER ----------
st.title("🩺 Patient Health Dashboard")

st.subheader("👤 Patient Details")
col1, col2, col3 = st.columns(3)

col1.metric("Name", patient["name"])
col2.metric("Age", patient["age"])
col3.metric("Gender", patient["gender"])

st.markdown(f"""
**Patient ID:** {patient['id']}  
**Address:** {patient['address']}  
**Referred By:** {patient['referred_by']}  
""")

st.divider()

# ---------- IMPORTANT DATES ----------
st.subheader("📅 Test Dates")

dates = {
    "Liver Elastography": reports["liver_elastography"]["dates"]["test_date"]
}

st.table(pd.DataFrame(dates.items(), columns=["Test", "Date"]))

st.divider()

# ---------- CARDIAC ----------
st.header("❤️ Cardiac Health")

cardiac = reports["cardiac"]

col1, col2, col3 = st.columns(3)

ef = cardiac["echocardiography"]["measurements"]["lvef_percent"]
ntprobnp = cardiac["biomarker"]["nt_probnp_pg_ml"]

col1.metric("Ejection Fraction (%)", ef, delta="Normal", delta_color="normal")
col2.metric("NT-proBNP", ntprobnp, delta="Good", delta_color="normal")

lvh = cardiac["echocardiography"]["structure"]["lvh"]
col3.metric("LVH", lvh)

st.markdown("### 🫀 Valve Status")
valves = cardiac["echocardiography"]["valves"]

for valve, details in valves.items():
    if isinstance(details, dict):
        st.write(f"**{valve.capitalize()} Valve:** {details}")
    else:
        st.write(f"**{valve.capitalize()} Valve:** {details}")

# ---------- LIVER ----------
st.header("🧬 Liver Health")

liver = reports["liver_elastography"]

col1, col2 = st.columns(2)

fibrosis_stage = liver["classification"]["fibrosis"]["stage"]
steatosis = liver["classification"]["steatosis"]["level"]

col1.metric("Fibrosis Stage", fibrosis_stage)
col2.metric("Steatosis Level", steatosis)

# Bar chart for liver severity
labels = ["Fibrosis", "Steatosis"]
values = [4, 2]  # F4, S2

fig, ax = plt.subplots()
ax.bar(labels, values)
ax.set_title("Liver Severity Scale")
st.pyplot(fig)

# ---------- KIDNEY ----------
st.header("🧪 Kidney Function")

renal = reports["renal_function"]
acr = renal["albumin_creatinine_ratio"]["value"]

color = risk_color(acr, good_range=(0, 30), warning_range=(30, 300))

st.metric(
    "Albumin-Creatinine Ratio",
    acr,
    delta=renal["albumin_creatinine_ratio"]["category"],
    delta_color="inverse" if color == "red" else "normal"
)

# ---------- BODY ----------
st.header("⚖️ Body Composition")

body = reports["body_composition"]

bmi = body["measurements"]["bmi"]
fat = body["body_metrics"]["body_fat_percent"]
visceral = body["body_metrics"]["visceral_fat_level"]

col1, col2, col3 = st.columns(3)

col1.metric("BMI", bmi)
col2.metric("Body Fat %", fat)
col3.metric("Visceral Fat", visceral)

# Pie chart
labels = ["Fat", "Muscle"]
sizes = [fat, body["body_metrics"]["muscle_percent"]]

fig2, ax2 = plt.subplots()
ax2.pie(sizes, labels=labels, autopct='%1.1f%%')
ax2.set_title("Body Composition")
st.pyplot(fig2)

# ---------- SUMMARY ----------
st.header("📊 Clinical Summary")

st.subheader("🚨 Major Diagnoses")
for d in summary["major_diagnoses"]:
    st.error(d)

st.subheader("✅ Positive Findings")
for p in summary["important_positives"]:
    st.success(p)

st.subheader("⚠️ Risk Profile")
for r in summary["risk_profile"]:
    st.warning(r)

# ---------- PRIORITY ----------
st.header("🎯 Clinical Priorities")

for p in data["clinical_priority"]:
    st.info(p)