import streamlit as st
import pandas as pd

st.title("Patient Input")

# -------------------- PHQ-9 --------------------
st.subheader("PHQ-9 Symptom Profile")

col1, col2 = st.columns(2)

with col1:
    phq1 = st.selectbox("PHQ-1: Little interest or pleasure", [0, 1, 2, 3], index=1)
    phq2 = st.selectbox("PHQ-2: Feeling down or hopeless", [0, 1, 2, 3], index=1)
    phq3 = st.selectbox("PHQ-3: Sleep problems", [0, 1, 2, 3], index=1)
    phq4 = st.selectbox("PHQ-4: Low energy", [0, 1, 2, 3], index=1)
    phq5 = st.selectbox("PHQ-5: Appetite issues", [0, 1, 2, 3], index=1)

with col2:
    phq6 = st.selectbox("PHQ-6: Feeling bad about themself", [0, 1, 2, 3], index=1)
    phq7 = st.selectbox("PHQ-7: Trouble concentrating", [0, 1, 2, 3], index=1)
    phq8 = st.selectbox("PHQ-8: Psychomotor changes", [0, 1, 2, 3], index=1)
    phq9 = st.selectbox("PHQ-9: Suicidal thoughts", [0, 1, 2, 3], index=0)

phq_total = phq1 + phq2 + phq3 + phq4 + phq5 + phq6 + phq7 + phq8 + phq9

st.metric("PHQ-9 Total Score", phq_total)

# -------------------- CLINICAL FEATURES --------------------
st.subheader("Clinical & Demographic Features")

a, b, c = st.columns(3)

# ---------- COLUMN A ----------
with a:
    site_type = st.selectbox("Site Type", ["psychiatric", "primary_care"])

    age = st.slider("Age", 18, 75, 40)

    sex = st.selectbox("Sex", ["Female", "Male"])

    race_ethnicity = st.selectbox(
        "Race/Ethnicity",
        ["White_non_Hispanic", "Black", "Hispanic", "Other"]
    )

    insurance_type = st.selectbox(
        "Insurance Type",
        ["Private", "Public", "None"]
    )

    college_grad_ui = st.selectbox("College Graduate", ["No", "Yes"])
    college_grad = 1 if college_grad_ui == "Yes" else 0

    employed_ui = st.selectbox("Employed", ["No", "Yes"])
    employed = 1 if employed_ui == "Yes" else 0

# ---------- COLUMN B ----------
with b:
    income_band = st.selectbox("Income Band", ["Low", "Middle", "High"])

    baseline_hamd17 = st.slider("Baseline HAMD-17", 14, 35, 22)

    chronic_ui = st.selectbox("Chronic Episode > 2 Years", ["No", "Yes"])
    chronic_episode_gt_2y = 1 if chronic_ui == "Yes" else 0

    recurrent_ui = st.selectbox("Recurrent MDD", ["No", "Yes"])
    recurrent_mdd = 1 if recurrent_ui == "Yes" else 0

    anxiety_ui = st.selectbox("Anxiety Disorder", ["No", "Yes"])
    anxiety_disorder = 1 if anxiety_ui == "Yes" else 0

    substance_ui = st.selectbox("Substance Use Disorder", ["No", "Yes"])
    substance_use_disorder = 1 if substance_ui == "Yes" else 0

    medical_comorbidity_count = st.slider("Medical Comorbidity Count", 0, 10, 2)

# ---------- COLUMN C ----------
with c:
    suicide_attempt_ui = st.selectbox("Past Suicide Attempt", ["No", "Yes"])
    past_suicide_attempt = 1 if suicide_attempt_ui == "Yes" else 0

    onset_ui = st.selectbox("Onset Before Age 18", ["No", "Yes"])
    onset_before_18 = 1 if onset_ui == "Yes" else 0

    baseline_function_score = st.slider("Baseline Function Score", 0, 100, 50)

    baseline_qol_score = st.slider("Baseline Quality of Life Score", 0, 100, 50)

    response_ui = st.selectbox("Level 1 Response", ["No", "Yes"])
    level1_response = 1 if response_ui == "Yes" else 0

    remission_ui = st.selectbox("Level 1 Remission", ["No", "Yes"])
    level1_remission = 1 if remission_ui == "Yes" else 0

# -------------------- DATA DICTIONARY --------------------
patient_dict = {
    "phq1": phq1,
    "phq2": phq2,
    "phq3": phq3,
    "phq4": phq4,
    "phq5": phq5,
    "phq6": phq6,
    "phq7": phq7,
    "phq8": phq8,
    "phq9": phq9,
    "site_type": site_type,
    "age": age,
    "sex": sex.lower(),
    "race_ethnicity": race_ethnicity,
    "insurance_type": insurance_type.lower(),
    "college_grad": college_grad,
    "employed": employed,
    "income_band": income_band.lower(),
    "baseline_HAMD17": baseline_hamd17,
    "baseline_QIDS_SR16": phq_total,
    "chronic_episode_gt_2y": chronic_episode_gt_2y,
    "recurrent_mdd": recurrent_mdd,
    "anxiety_disorder": anxiety_disorder,
    "substance_use_disorder": substance_use_disorder,
    "medical_comorbidity_count": medical_comorbidity_count,
    "past_suicide_attempt": past_suicide_attempt,
    "onset_before_18": onset_before_18,
    "baseline_function_score": baseline_function_score,
    "baseline_qol_score": baseline_qol_score,
    "level1_response": level1_response,
    "level1_remission": level1_remission,
}

# -------------------- PREVIEW --------------------
with st.expander("Current Patient Record"):
    st.dataframe(pd.DataFrame([patient_dict]), use_container_width=True)

st.session_state["patient_dict"] = patient_dict
