import streamlit as st
import pandas as pd

st.title("Treatment Comparison")

if "patient_dict" not in st.session_state:
    st.warning("Go to Patient Input first.")
    st.stop()

patient = st.session_state["patient_dict"]

treatments = [
    "bupropion SR",
    "citalopram + bupropion SR",
    "citalopram + buspirone",
    "sertraline",
    "venlafaxine XR",
]


def symptom_personalized_probability(patient_dict, treatment):
    """
    Prototype logic:
    final score = predicted remission probability - access/dropout penalties
    PHQ-9 drives symptom matching
    clinical/demographic features adjust feasibility and overall success
    """

    # STAR*D-inspired starting points
    base_probs = {
        "bupropion SR": 0.25,
        "citalopram + bupropion SR": 0.29,
        "citalopram + buspirone": 0.28,
        "sertraline": 0.24,
        "venlafaxine XR": 0.25,
    }

    p = base_probs[treatment]

    # PHQ-9
    phq1 = patient_dict.get("phq1", 0)  # anhedonia
    phq2 = patient_dict.get("phq2", 0)  # depressed mood
    phq3 = patient_dict.get("phq3", 0)  # sleep
    phq4 = patient_dict.get("phq4", 0)  # fatigue
    phq5 = patient_dict.get("phq5", 0)  # appetite
    phq6 = patient_dict.get("phq6", 0)  # guilt
    phq7 = patient_dict.get("phq7", 0)  # concentration
    phq8 = patient_dict.get("phq8", 0)  # psychomotor
    phq9 = patient_dict.get("phq9", 0)  # suicidality

    total = patient_dict.get("baseline_QIDS_SR16", 0)

    energy_concentration = phq1 + phq4 + phq7
    sleep_psychomotor = phq3 + phq8
    guilt_suicidality = phq6 + phq9
    mood_appetite_fatigue = phq2 + phq4 + phq5

    # ----------------------------
    # Symptom-driven treatment matching
    # ----------------------------

    # low-energy / anhedonic profile
    if energy_concentration >= 6:
        if treatment == "bupropion SR":
            p += 0.07
        elif treatment == "citalopram + bupropion SR":
            p += 0.05
        elif treatment == "sertraline":
            p -= 0.01

    # sleep + psychomotor burden
    if sleep_psychomotor >= 4:
        if treatment == "sertraline":
            p += 0.06
        elif treatment == "venlafaxine XR":
            p += 0.05
        elif treatment == "bupropion SR":
            p -= 0.02

    # anxiety / guilt / internal distress
    if patient_dict.get("anxiety_disorder", 0) == 1 or guilt_suicidality >= 3:
        if treatment == "citalopram + buspirone":
            p += 0.07
        elif treatment == "citalopram + bupropion SR":
            p += 0.02

    # broader depressive burden
    if mood_appetite_fatigue >= 6:
        if treatment == "venlafaxine XR":
            p += 0.05
        elif treatment == "citalopram + bupropion SR":
            p += 0.04
        elif treatment == "citalopram + buspirone":
            p += 0.02

    # higher suicidality -> favor augmentation-type options a bit
    if phq9 >= 2:
        if treatment in ["bupropion SR", "sertraline"]:
            p -= 0.02
        elif treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            p += 0.02

    # overall symptom severity
    if total >= 18:
        p -= 0.03
        if treatment in ["citalopram + bupropion SR", "venlafaxine XR"]:
            p += 0.02
    elif total <= 9:
        p += 0.03

    # ----------------------------
    # Clinical risk factors affecting all options
    # ----------------------------

    if patient_dict.get("chronic_episode_gt_2y", 0) == 1:
        p -= 0.04

    if patient_dict.get("recurrent_mdd", 0) == 1:
        p -= 0.02

    if patient_dict.get("substance_use_disorder", 0) == 1:
        p -= 0.04

    p -= 0.01 * min(patient_dict.get("medical_comorbidity_count", 0), 5)

    if patient_dict.get("baseline_function_score", 50) < 40:
        p -= 0.03
    elif patient_dict.get("baseline_function_score", 50) > 70:
        p += 0.02

    if patient_dict.get("baseline_qol_score", 50) < 40:
        p -= 0.03
    elif patient_dict.get("baseline_qol_score", 50) > 70:
        p += 0.02

    if patient_dict.get("level1_response", 0) == 0:
        p -= 0.03

    if patient_dict.get("level1_remission", 0) == 1:
        p += 0.02

    # ----------------------------
    # Practical barriers / dropout risk / feasibility
    # These affect treatment recommendation through utility, not just raw efficacy
    # ----------------------------

    feasibility_penalty = 0.0

    low_income = patient_dict.get("income_band", "middle") == "low"
    public_insurance = patient_dict.get("insurance_type", "private") == "public"
    unemployed = patient_dict.get("employed", 0) == 0
    low_resources = low_income or public_insurance or unemployed

    # More complex augmentation can be harder to sustain with financial / logistical barriers
    if low_resources:
        if treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            feasibility_penalty += 0.03

    # Lower education / functioning may increase adherence burden for more complex regimens
    if patient_dict.get("college_grad", 0) == 0 and patient_dict.get("baseline_function_score", 50) < 40:
        if treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            feasibility_penalty += 0.02

    # Higher medical comorbidity slightly penalizes more complex augmentation
    if patient_dict.get("medical_comorbidity_count", 0) >= 3:
        if treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            feasibility_penalty += 0.01

    # Severe anxiety may make buspirone augmentation more feasible / relevant
    if patient_dict.get("anxiety_disorder", 0) == 1 and treatment == "citalopram + buspirone":
        feasibility_penalty -= 0.01

    # Final utility-like score
    final_score = p - feasibility_penalty
    final_score = max(0.05, min(0.60, final_score))

    return round(final_score, 3), round(p, 3), round(feasibility_penalty, 3)


results = []
for tx in treatments:
    final_prob, raw_prob, penalty = symptom_personalized_probability(patient, tx)
    results.append({
        "Treatment": tx,
        "Raw Predicted Remission": raw_prob,
        "Feasibility / Dropout Penalty": penalty,
        "Final Recommended Score": final_prob,
    })

results_df = pd.DataFrame(results).sort_values(
    "Final Recommended Score",
    ascending=False
).reset_index(drop=True)

best = results_df.iloc[0]

st.subheader("Counterfactual Treatment Predictions")
st.caption(
    "Final recommended score combines symptom-matched remission probability with feasibility/dropout penalties based on clinical and demographic risk factors."
)
st.dataframe(results_df, use_container_width=True)

st.success(
    f"Recommended treatment: {best['Treatment']} "
    f"(final score {best['Final Recommended Score']:.3f})"
)

st.subheader("Why the recommendation changed")

top_reasons = []

energy_concentration = patient.get("phq1", 0) + patient.get("phq4", 0) + patient.get("phq7", 0)
sleep_psychomotor = patient.get("phq3", 0) + patient.get("phq8", 0)
guilt_suicidality = patient.get("phq6", 0) + patient.get("phq9", 0)
mood_appetite_fatigue = patient.get("phq2", 0) + patient.get("phq4", 0) + patient.get("phq5", 0)

best_treatment = best["Treatment"]

if best_treatment == "bupropion SR" and energy_concentration >= 6:
    top_reasons.append(
        "High anhedonia (PHQ-1), fatigue (PHQ-4), and concentration difficulty (PHQ-7) shifted the recommendation toward bupropion SR."
    )

if best_treatment == "sertraline" and sleep_psychomotor >= 4:
    top_reasons.append(
        "Sleep disturbance (PHQ-3) and psychomotor symptoms (PHQ-8) shifted probability toward sertraline."
    )

if best_treatment == "venlafaxine XR" and mood_appetite_fatigue >= 6:
    top_reasons.append(
        "Broader depressive burden across mood (PHQ-2), fatigue (PHQ-4), and appetite change (PHQ-5) favored venlafaxine XR."
    )

if best_treatment == "citalopram + buspirone" and (
    patient.get("anxiety_disorder", 0) == 1 or guilt_suicidality >= 3
):
    top_reasons.append(
        "Higher anxiety burden and elevated guilt / suicidality increased the relative fit of buspirone augmentation."
    )

if best_treatment == "citalopram + bupropion SR" and (
    energy_concentration >= 6 or mood_appetite_fatigue >= 6
):
    top_reasons.append(
        "A mixed profile spanning mood, energy, and cognition favored a combined augmentation strategy."
    )

# Clinical / demographic context explanations
if patient.get("income_band", "middle") == "low":
    top_reasons.append(
        "Low income increased the penalty on more complex regimens because cost and adherence burden can reduce real-world treatment success."
    )

if patient.get("insurance_type", "private") == "public":
    top_reasons.append(
        "Public insurance increased feasibility concerns for more complex treatment pathways, which affected the final ranking."
    )

if patient.get("employed", 1) == 0:
    top_reasons.append(
        "Not being employed increased practical risk for treatment disengagement, which lowered the final score of more demanding options."
    )

if patient.get("chronic_episode_gt_2y", 0) == 1:
    top_reasons.append(
        "A chronic episode lowered expected remission across all options."
    )

if patient.get("recurrent_mdd", 0) == 1:
    top_reasons.append(
        "Recurrent depression lowered overall remission probability."
    )

if patient.get("medical_comorbidity_count", 0) >= 3:
    top_reasons.append(
        "Higher medical comorbidity reduced the expected success of treatment overall and slightly penalized more complex regimens."
    )

if patient.get("baseline_function_score", 50) < 40:
    top_reasons.append(
        "Lower baseline functioning reduced remission probability and increased adherence risk."
    )

if patient.get("baseline_qol_score", 50) < 40:
    top_reasons.append(
        "Lower baseline quality of life reduced expected remission probability."
    )

if not top_reasons:
    top_reasons.append(
        "The recommendation was driven by both PHQ-9 symptom pattern and broader clinical feasibility factors."
    )

for reason in top_reasons:
    st.write(f"- {reason}")

with st.expander("Current patient inputs"):
    st.dataframe(pd.DataFrame([patient]), use_container_width=True)
