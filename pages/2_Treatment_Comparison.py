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

# ----------------------------
# Explanation section
# ----------------------------
st.subheader("Neurobiological Interpretation of Recommendation")

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
        "High anhedonia (PHQ-1), fatigue (PHQ-4), and concentration impairment (PHQ-7) shifted the recommendation toward bupropion SR. "
        "This symptom combination can be interpreted as a reward-deficit / low-motivation profile involving mesolimbic dopamine pathways and frontoparietal cognitive-control systems. "
        "Because bupropion is a norepinephrine–dopamine reuptake inhibitor, this prototype gives it an advantage when the presentation is dominated by low energy, reduced drive, and impaired attention."
    )

if best_treatment == "citalopram + bupropion SR" and (
    energy_concentration >= 6 or mood_appetite_fatigue >= 6 or guilt_suicidality >= 3
):
    top_reasons.append(
        "The recommendation favored citalopram + bupropion SR because the symptom profile spans multiple domains: mood disturbance (PHQ-2), energy reduction (PHQ-4), appetite change (PHQ-5), anhedonia (PHQ-1), or concentration deficits (PHQ-7). "
        "In neuroscience terms, this suggests combined disruption across serotonergic affect-regulation systems and catecholaminergic reward / executive systems. "
        "This prototype therefore favors augmentation when both mood-stabilization and energy/cognitive restoration appear relevant."
    )

if best_treatment == "citalopram + buspirone" and (
    patient.get("anxiety_disorder", 0) == 1 or guilt_suicidality >= 3
):
    top_reasons.append(
        "The recommendation shifted toward citalopram + buspirone because guilt/worthlessness (PHQ-6), suicidal ideation (PHQ-9), or anxiety burden were elevated. "
        "This is treated as a high internal-distress profile involving amygdala–medial prefrontal circuitry and heightened affective salience. "
        "Buspirone is often framed around 5-HT1A receptor activity and anxiolytic serotonergic modulation, so the prototype increases its score when the phenotype is more anxiety-distress weighted."
    )

if best_treatment == "sertraline" and sleep_psychomotor >= 4:
    top_reasons.append(
        "The recommendation shifted toward sertraline because sleep disturbance (PHQ-3) and psychomotor symptoms (PHQ-8) were more prominent. "
        "This prototype interprets that cluster as more consistent with serotonergic dysregulation affecting arousal regulation, motor-affective pacing, and circadian symptom dimensions. "
        "Sertraline therefore receives a higher score when the presentation is driven more by sleep/psychomotor burden than by a pure reward-deficit phenotype."
    )

if best_treatment == "venlafaxine XR" and (
    sleep_psychomotor >= 4 or mood_appetite_fatigue >= 6
):
    top_reasons.append(
        "The recommendation favored venlafaxine XR because the symptom pattern reflects broader depressive burden involving depressed mood (PHQ-2), fatigue (PHQ-4), appetite change (PHQ-5), and/or sleep and psychomotor disruption (PHQ-3, PHQ-8). "
        "This prototype treats that as a more diffuse monoaminergic dysregulation profile spanning serotonergic and noradrenergic domains, so a dual-action SNRI becomes more competitive."
    )

if phq9 >= 2:
    top_reasons.append(
        "Elevated suicidal ideation (PHQ-9) increased the relative score of augmentation-based strategies. "
        "In this prototype, higher suicidality is treated as reflecting greater prefrontal–limbic dysregulation and clinical complexity, making broader stabilization strategies relatively more favorable than simpler switch options."
    )

if patient.get("baseline_QIDS_SR16", 0) >= 18:
    top_reasons.append(
        "Higher overall symptom severity reduced remission probability overall, while making broader-coverage treatments relatively more competitive. "
        "At a systems level, this is interpreted as more distributed dysfunction across affective, reward, autonomic, and executive-control networks."
    )

# Risk-factor / feasibility explanations
if patient.get("income_band", "middle") == "low":
    top_reasons.append(
        "Low income increased the penalty on more complex regimens because cost burden can reduce adherence and increase dropout risk in real-world care."
    )

if patient.get("insurance_type", "private") == "public":
    top_reasons.append(
        "Public insurance increased feasibility concerns for more complex treatment pathways, which lowered the final score of options with higher practical burden."
    )

if patient.get("employed", 1) == 0:
    top_reasons.append(
        "Not being employed increased practical disengagement risk, which reduced the final score of more demanding augmentation strategies."
    )

if patient.get("chronic_episode_gt_2y", 0) == 1:
    top_reasons.append(
        "A chronic depressive episode lowered predicted remission across all options, consistent with lower average remission in more persistent illness."
    )

if patient.get("recurrent_mdd", 0) == 1:
    top_reasons.append(
        "Recurrent depression lowered overall remission probability, reflecting a more treatment-resistant baseline profile."
    )

if patient.get("medical_comorbidity_count", 0) >= 3:
    top_reasons.append(
        "Higher medical comorbidity reduced the expected success of treatment overall and slightly penalized more complex regimens."
    )

if patient.get("baseline_function_score", 50) < 40:
    top_reasons.append(
        "Lower baseline functioning reduced remission probability and increased adherence vulnerability."
    )

if patient.get("baseline_qol_score", 50) < 40:
    top_reasons.append(
        "Lower baseline quality of life reduced expected remission probability across options."
    )

if not top_reasons:
    top_reasons.append(
        "The recommendation was driven by the interaction between PHQ-9 symptom structure and broader clinical feasibility factors rather than total severity alone."
    )

for reason in top_reasons:
    st.write(f"- {reason}")

st.caption(
    "These explanations are neuroscience-informed prototype interpretations for demonstration only and do not represent validated causal prescribing rules."
)

with st.expander("Current patient inputs"):
    st.dataframe(pd.DataFrame([patient]), use_container_width=True)
