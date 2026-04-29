import streamlit as st
import os
from supabase import create_client

# -----------------------------
# INIT
# -----------------------------
def get_client():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"]
    )

supabase = get_client()

st.title("🧹 Patient Reconciliation")

# -----------------------------
# LOAD USERS (caretakers)
# -----------------------------
users = supabase.table("users").select("*").execute().data

user_map = {u["name"]: u["user_id"] for u in users}
user_names = list(user_map.keys())

selected_user = st.selectbox("Select Caretaker", user_names)

# -----------------------------
# LOAD PATIENTS FOR USER
# -----------------------------
if selected_user:
    user_id = user_map[selected_user]

    user_patients = supabase.table("user_patients") \
        .select("patient_id") \
        .eq("user_id", user_id) \
        .execute().data

    patient_ids = [p["patient_id"] for p in user_patients]

    patients = supabase.table("patients") \
        .select("patient_id, name") \
        .in_("patient_id", patient_ids) \
        .execute().data

    patient_map = {f"{p['name']} ({p['patient_id'][:6]})": p["patient_id"] for p in patients}

    # -----------------------------
    # SELECT PATIENTS TO MERGE
    # -----------------------------
    selected = st.multiselect(
        "Select patients to merge",
        list(patient_map.keys())
    )

    if len(selected) >= 2:

        selected_ids = [patient_map[s] for s in selected]

        # Choose target
        target_label = st.selectbox(
            "Select primary patient (target)",
            selected
        )

        target_id = patient_map[target_label]

        new_name = st.text_input("New merged patient name")

        if st.button("🚨 Merge Patients"):

            if not new_name:
                st.error("Please enter a new name")
            else:
                supabase.rpc(
                    "merge_patients",
                    {
                        "target_patient": target_id,
                        "source_patients": selected_ids,
                        "new_name": new_name
                    }
                ).execute()

                # 👉 cleanup duplicates

                supabase.rpc("cleanup_user_patients_duplicates").execute()

                st.success("Patients merged and cleaned successfully!")   
                st.rerun()             

                

st.markdown("---")
st.subheader("🧪 Test Reconciliation")
# -----------------------------
# CONTROLS
# -----------------------------
search = st.text_input("🔍 Filter tests")

query = supabase.table("tests") \
    .select("test_id, test_name, canonical_name, report_id, reports(source_file)") \
    .order("test_name") \
    .limit(200)
# Search filter only
if search:
    query = query.ilike("test_name", f"%{search}%")
tests = query.execute().data
# -----------------------------
# DISPLAY COUNT
# -----------------------------
st.caption(f"Showing {len(tests)} tests")
# -----------------------------
# LOAD MEASUREMENTS
# -----------------------------
if tests:
    test_ids = [t["test_id"] for t in tests]
    measurements = supabase.table("measurements") \
        .select("test_id, value_numeric, value_text, unit") \
        .in_("test_id", test_ids) \
        .execute().data
    meas_map = {m["test_id"]: m for m in measurements}


    st.write("Select tests to standardize:")

    selected_test_ids = []

    # Header row
    col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 2, 2])
    col1.markdown("**Select**")
    col2.markdown("**Test Name**")
    col3.markdown("**Canonical**")
    col4.markdown("**Value**")
    col5.markdown("**Unit**")

    st.markdown("---")

    # Rows
    for t in tests:

        m = meas_map.get(t["test_id"], {})

        value = m.get("value_numeric") or m.get("value_text") or ""

        unit = m.get("unit") or ""

        canonical = t.get("canonical_name") or "—"

        # 👇 get S3 link safely

        report_url = (t.get("reports") or {}).get("source_file")

        col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 3, 2, 2, 2])

        checked = col1.checkbox("", key=f"test_{t['test_id']}")

        col2.write(t["test_name"])

        col3.write(canonical)

        col4.write(value)

        col5.write(unit)

        # 👇 clickable link

        if report_url:

            col6.markdown(f"[Open]({report_url})")

        else:

            col6.write("—")

        if checked:

            selected_test_ids.append(t["test_id"])

    # -----------------------------
    # APPLY UPDATE
    # -----------------------------
    if selected_test_ids:
        st.markdown("---")
        new_name = st.text_input("New canonical test name")
        if st.button("🧹 Apply Test Standardization"):
            if not new_name:
                st.error("Please enter a name")
            else:
                supabase.rpc(
                    "update_tests_canonical",
                    {
                        "test_ids": selected_test_ids,
                        "new_name": new_name
                    }
                ).execute()
                
                st.success("Test names updated!")
                st.rerun()