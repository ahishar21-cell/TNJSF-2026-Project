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
    final score = symptom-matched remission probability - feasibility/dropout penalties

    - PHQ-9 symptom patterns drive treatment matching
    - broader clinical factors modify overall remission probability
    - demographic/access variables affect feasibility and dropout burden
    - prototype only; not a validated clinical recommendation system
    """

    # STAR*D-inspired starting rates
    base_probs = {
        "bupropion SR": 0.25,
        "citalopram + bupropion SR": 0.29,
        "citalopram + buspirone": 0.28,
        "sertraline": 0.24,
        "venlafaxine XR": 0.25,
    }

    p = base_probs[treatment]

    # ----------------------------
    # PHQ-9 symptom inputs
    # ----------------------------
    phq1 = patient_dict.get("phq1", 0)  # anhedonia
    phq2 = patient_dict.get("phq2", 0)  # depressed mood
    phq3 = patient_dict.get("phq3", 0)  # sleep disturbance
    phq4 = patient_dict.get("phq4", 0)  # fatigue / low energy
    phq5 = patient_dict.get("phq5", 0)  # appetite change
    phq6 = patient_dict.get("phq6", 0)  # guilt / worthlessness
    phq7 = patient_dict.get("phq7", 0)  # concentration difficulty
    phq8 = patient_dict.get("phq8", 0)  # psychomotor change
    phq9 = patient_dict.get("phq9", 0)  # suicidal ideation

    total = patient_dict.get("baseline_QIDS_SR16", 0)

    # Symptom clusters
    energy_concentration = phq1 + phq4 + phq7
    sleep_psychomotor = phq3 + phq8
    guilt_suicidality = phq6 + phq9
    mood_appetite_fatigue = phq2 + phq4 + phq5

    # ----------------------------
    # Symptom-driven treatment matching
    # ----------------------------

    # Low-energy / reward-deficit / cognitive-effort profile
    if energy_concentration >= 6:
        if treatment == "bupropion SR":
            p += 0.07
        elif treatment == "citalopram + bupropion SR":
            p += 0.05
        elif treatment == "sertraline":
            p -= 0.01

    # Sleep / psychomotor burden
    if sleep_psychomotor >= 4:
        if treatment == "sertraline":
            p += 0.06
        elif treatment == "venlafaxine XR":
            p += 0.05
        elif treatment == "bupropion SR":
            p -= 0.02

    # Anxiety / distress / guilt-heavy presentation
    if patient_dict.get("anxiety_disorder", 0) == 1 or guilt_suicidality >= 3:
        if treatment == "citalopram + buspirone":
            p += 0.07
        elif treatment == "citalopram + bupropion SR":
            p += 0.02

    # Broad depressive burden across affect + somatic symptoms
    if mood_appetite_fatigue >= 6:
        if treatment == "venlafaxine XR":
            p += 0.05
        elif treatment == "citalopram + bupropion SR":
            p += 0.04
        elif treatment == "citalopram + buspirone":
            p += 0.02

    # Higher suicidality slightly favors augmentation over simple switch
    if phq9 >= 2:
        if treatment in ["bupropion SR", "sertraline"]:
            p -= 0.02
        elif treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            p += 0.02

    # Overall severity
    if total >= 18:
        p -= 0.03
        if treatment in ["citalopram + bupropion SR", "venlafaxine XR"]:
            p += 0.02
    elif total <= 9:
        p += 0.03

    # ----------------------------
    # Clinical risk modifiers
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
    # Feasibility / dropout penalties
    # ----------------------------
    feasibility_penalty = 0.0

    low_income = patient_dict.get("income_band", "middle") == "low"
    public_insurance = patient_dict.get("insurance_type", "private") == "public"
    unemployed = patient_dict.get("employed", 1) == 0
    low_education = patient_dict.get("college_grad", 1) == 0
    low_resources = low_income or public_insurance or unemployed

    # More complex regimens can be harder to sustain in lower-resource settings
    if low_resources:
        if treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            feasibility_penalty += 0.03

    # Lower education + lower functioning may increase adherence burden for complex augmentation
    if low_education and patient_dict.get("baseline_function_score", 50) < 40:
        if treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            feasibility_penalty += 0.02

    # More medical complexity slightly penalizes more complicated regimens
    if patient_dict.get("medical_comorbidity_count", 0) >= 3:
        if treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            feasibility_penalty += 0.01

    # Anxiety may make buspirone augmentation relatively more feasible
    if patient_dict.get("anxiety_disorder", 0) == 1 and treatment == "citalopram + buspirone":
        feasibility_penalty -= 0.01

    final_score = p - feasibility_penalty
    final_score = max(0.05, min(0.60, final_score))

    return round(final_score, 3), round(p, 3), round(feasibility_penalty, 3)


results = []
for tx in treatments:
    final_score, raw_prob, penalty = symptom_personalized_probability(patient, tx)
    results.append({
        "Treatment": tx,
        "Raw Predicted Remission": raw_prob,
        "Feasibility / Dropout Penalty": penalty,
        "Final Recommended Score": final_score,
    })

results_df = pd.DataFrame(results).sort_values(
    "Final Recommended Score",
    ascending=False
).reset_index(drop=True)

best = results_df.iloc[0]

st.subheader("Counterfactual Treatment Predictions")
st.caption(
    "Final recommended score combines symptom-matched remission probability with feasibility and dropout penalties based on broader clinical context."
)
st.dataframe(results_df, use_container_width=True)

st.success(
    f"Recommended treatment: {best['Treatment']} "
    f"(final score {best['Final Recommended Score']:.3f})"
)

# ============================
# MODEL-BASED EXPLANATION
# ============================

st.subheader("Model-Based Recommendation (Neurobiological Interpretation)")

top_reasons = []

phq1 = patient.get("phq1", 0)
phq2 = patient.get("phq2", 0)
phq3 = patient.get("phq3", 0)
phq4 = patient.get("phq4", 0)
phq5 = patient.get("phq5", 0)
phq6 = patient.get("phq6", 0)
phq7 = patient.get("phq7", 0)
phq8 = patient.get("phq8", 0)
phq9 = patient.get("phq9", 0)

energy_concentration = phq1 + phq4 + phq7
sleep_psychomotor = phq3 + phq8
guilt_suicidality = phq6 + phq9
mood_appetite_fatigue = phq2 + phq4 + phq5

best_treatment = best["Treatment"]

if best_treatment == "bupropion SR" and energy_concentration >= 6:
    top_reasons.append(
        "Elevated anhedonia (PHQ-1), fatigue (PHQ-4), and concentration impairment (PHQ-7) suggest a reward-deficit and low-motivation phenotype. "
        "This pattern is consistent with reduced dopaminergic signaling in mesolimbic pathways and reduced engagement of frontoparietal cognitive control networks. "
        "Because bupropion is a norepinephrine–dopamine reuptake inhibitor, it is better aligned with restoring reward sensitivity, motivation, and cognitive effort."
    )

if best_treatment == "citalopram + bupropion SR" and (
    energy_concentration >= 6 or mood_appetite_fatigue >= 6 or guilt_suicidality >= 3
):
    top_reasons.append(
        "The symptom profile spans multiple domains, including mood disturbance (PHQ-2), fatigue (PHQ-4), appetite change (PHQ-5), anhedonia (PHQ-1), and/or concentration deficits (PHQ-7). "
        "This suggests combined disruption across serotonergic affect-regulation systems and catecholaminergic reward and executive-function networks. "
        "Augmentation with both an SSRI and a norepinephrine–dopamine agent may better address this multi-network dysfunction."
    )

if best_treatment == "citalopram + buspirone" and (
    patient.get("anxiety_disorder", 0) == 1 or guilt_suicidality >= 3
):
    top_reasons.append(
        "Elevated guilt (PHQ-6), suicidal ideation (PHQ-9), or comorbid anxiety suggest a high internal-distress phenotype involving hyperactivity in amygdala–medial prefrontal circuits. "
        "Buspirone modulates 5-HT1A receptors and may help regulate serotonergic tone in these circuits, so the prototype increases its score in anxiety-weighted or distress-heavy presentations."
    )

if best_treatment == "sertraline" and sleep_psychomotor >= 4:
    top_reasons.append(
        "Prominent sleep disturbance (PHQ-3) and psychomotor changes (PHQ-8) suggest dysregulation in arousal systems and motor-affective pacing. "
        "These features are associated here with serotonergic dysfunction affecting sleep–wake regulation and behavioral activation, so sertraline receives a higher score."
    )

if best_treatment == "venlafaxine XR" and (
    sleep_psychomotor >= 4 or mood_appetite_fatigue >= 6
):
    top_reasons.append(
        "A broader symptom burden across mood (PHQ-2), fatigue (PHQ-4), appetite (PHQ-5), and sleep/psychomotor domains (PHQ-3, PHQ-8) suggests more diffuse monoaminergic dysregulation. "
        "This includes both serotonergic and noradrenergic systems affecting affective tone, autonomic function, and energy regulation, making venlafaxine XR more competitive."
    )

if patient.get("baseline_QIDS_SR16", 0) >= 18:
    top_reasons.append(
        "Higher overall symptom severity indicates more distributed dysfunction across affective, reward, autonomic, and executive-control networks, "
        "which increases the relative value of broader or combination-based treatment strategies."
    )

if phq9 >= 2:
    top_reasons.append(
        "Elevated suicidal ideation suggests greater prefrontal–limbic dysregulation and clinical complexity, which shifts the model toward augmentation strategies rather than simpler switch options."
    )

if not top_reasons:
    top_reasons.append(
        "The recommendation is driven by the interaction between PHQ-9 symptom structure and inferred neurobiological patterns rather than total severity alone."
    )

for reason in top_reasons:
    st.write(f"- {reason}")

st.caption(
    "This section reflects a symptom-level, neuroscience-informed interpretation of treatment selection based on PHQ-9 structure."
)

# ============================
# REAL-WORLD CONSTRAINTS BOX
# ============================

st.subheader("Real-World Constraints & Risk Factors")

warnings = []

if patient.get("income_band", "middle") == "low":
    warnings.append("Lower income may introduce financial barriers to sustained treatment adherence.")

if patient.get("insurance_type", "private") == "public":
    warnings.append("Insurance limitations may affect medication access, provider availability, or follow-up care.")

if patient.get("employed", 1) == 0:
    warnings.append("Unemployment may increase risk of treatment disengagement or inconsistent follow-up.")

if patient.get("chronic_episode_gt_2y", 0) == 1:
    warnings.append("Chronic depression is associated with reduced remission probability across treatments.")

if patient.get("recurrent_mdd", 0) == 1:
    warnings.append("Recurrent depressive episodes suggest increased baseline treatment resistance.")

if patient.get("substance_use_disorder", 0) == 1:
    warnings.append("Substance use may interfere with both treatment response and adherence.")

if patient.get("medical_comorbidity_count", 0) >= 3:
    warnings.append("Higher medical comorbidity may complicate treatment selection and reduce response rates.")

if patient.get("baseline_function_score", 50) < 40:
    warnings.append("Lower baseline functioning increases risk of disengagement and poorer outcomes.")

if patient.get("baseline_qol_score", 50) < 40:
    warnings.append("Lower quality of life is associated with reduced likelihood of remission.")

if patient.get("level1_response", 0) == 0:
    warnings.append("Lack of response to initial treatment suggests need for more complex or multi-step care.")

if warnings:
    st.markdown("""
    <div style="
        background: #F8FAFC;
        border: 1px solid #CBD5F5;
        padding: 1rem;
        border-radius: 15px;
        margin-top: 0.5rem;
    ">
    <b style="color:#3730A3;">⚠️ Contextual factors that may influence real-world outcomes</b><br><br>
    """, unsafe_allow_html=True)

    for w in warnings:
        st.markdown(f"- {w}")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No major real-world risk factors identified.")
    
with st.expander("Current patient inputs"):
    st.dataframe(pd.DataFrame([patient]), use_container_width=True)
