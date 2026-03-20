import streamlit as st
import pandas as pd

st.markdown("""
<style>
.card {
    background: #FCFDFE;
    border: 100px solid #DCE6EF;
    padding: 1.1rem 1.2rem;
    border-radius: 20px;
    box-shadow: 0 3px 12px rgba(53, 92, 125, 0.05);
    margin-bottom: 1rem;
}

.recommend-box {
    background: linear-gradient(135deg, #EEF4F9 0%, #F8FBFD 100%);
    border: 1px solid #DCE6EF;
    padding: 1.1rem 1.2rem;
    border-radius: 20px;
    margin-bottom: 1rem;
    box-shadow: 0 4px 14px rgba(53, 92, 125, 0.06);
}

.reason-box {
    background: linear-gradient(135deg, #F3F1FB 0%, #FBFAFE 100%);
    border: 1px solid #E4DFF3;
    padding: 1rem 1.1rem;
    border-radius: 18px;
    margin-bottom: 0.8rem;
}

.rank-pill {
    display: inline-block;
    background: #EAF4F3;
    color: #355C7D;
    border: 1px solid #D9ECE8;
    border-radius: 999px;
    padding: 0.22rem 0.65rem;
    font-size: 0.86rem;
    font-weight: 700;
    margin-bottom: 0.45rem;
}
</style>
""", unsafe_allow_html=True)

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
    base_probs = {
        "bupropion SR": 0.25,
        "citalopram + bupropion SR": 0.29,
        "citalopram + buspirone": 0.28,
        "sertraline": 0.24,
        "venlafaxine XR": 0.25,
    }

    p = base_probs[treatment]

    phq1 = patient_dict.get("phq1", 0)
    phq2 = patient_dict.get("phq2", 0)
    phq3 = patient_dict.get("phq3", 0)
    phq4 = patient_dict.get("phq4", 0)
    phq5 = patient_dict.get("phq5", 0)
    phq6 = patient_dict.get("phq6", 0)
    phq7 = patient_dict.get("phq7", 0)
    phq8 = patient_dict.get("phq8", 0)
    phq9 = patient_dict.get("phq9", 0)

    total = patient_dict.get("baseline_QIDS_SR16", 0)

    energy_concentration = phq1 + phq4 + phq7
    sleep_psychomotor = phq3 + phq8
    guilt_suicidality = phq6 + phq9
    mood_appetite_fatigue = phq2 + phq4 + phq5

    if energy_concentration >= 6:
        if treatment == "bupropion SR":
            p += 0.07
        elif treatment == "citalopram + bupropion SR":
            p += 0.05
        elif treatment == "sertraline":
            p -= 0.01

    if sleep_psychomotor >= 4:
        if treatment == "sertraline":
            p += 0.06
        elif treatment == "venlafaxine XR":
            p += 0.05
        elif treatment == "bupropion SR":
            p -= 0.02

    if patient_dict.get("anxiety_disorder", 0) == 1 or guilt_suicidality >= 3:
        if treatment == "citalopram + buspirone":
            p += 0.07
        elif treatment == "citalopram + bupropion SR":
            p += 0.02

    if mood_appetite_fatigue >= 6:
        if treatment == "venlafaxine XR":
            p += 0.05
        elif treatment == "citalopram + bupropion SR":
            p += 0.04
        elif treatment == "citalopram + buspirone":
            p += 0.02

    if phq9 >= 2:
        if treatment in ["bupropion SR", "sertraline"]:
            p -= 0.02
        elif treatment in ["citalopram + bupropion SR", "citalopram + buspirone"]:
            p += 0.02

    if total >= 18:
        p -= 0.03
        if treatment in ["citalopram + bupropion SR", "venlafaxine XR"]:
            p += 0.02
    elif total <= 9:
        p += 0.03
        if treatment == "sertraline":
            p += 0.01

    if patient.get("chronic_episode_gt_2y", 0) == 1:
        p -= 0.04
    if patient.get("substance_use_disorder", 0) == 1:
        p -= 0.04

    p -= 0.01 * min(patient.get("medical_comorbidity_count", 0), 5)

    if patient.get("baseline_function_score", 50) < 40:
        p -= 0.03
    elif patient.get("baseline_function_score", 50) > 70:
        p += 0.02

    if patient.get("baseline_qol_score", 50) < 40:
        p -= 0.03
    elif patient.get("baseline_qol_score", 50) > 70:
        p += 0.02

    if patient.get("level1_response", 0) == 0:
        p -= 0.03

    p = max(0.05, min(0.60, p))
    return round(p, 3)

results = []
for tx in treatments:
    results.append({
        "Treatment": tx,
        "Predicted Remission Probability": symptom_personalized_probability(patient, tx)
    })

results_df = pd.DataFrame(results).sort_values(
    "Predicted Remission Probability",
    ascending=False
).reset_index(drop=True)

best = results_df.iloc[0]

st.markdown(f"""
<div class="recommend-box">
    <div style="font-size:0.95rem;color:#5F6B7A;">Recommended treatment</div>
    <div style="font-size:1.7rem;font-weight:800;color:#355C7D;">{best['Treatment']}</div>
    <div style="font-size:1.05rem;color:#4B5563;margin-top:0.25rem;">
        Predicted remission probability: <b>{best['Predicted Remission Probability']:.3f}</b>
    </div>
</div>
""", unsafe_allow_html=True)

st.subheader("Counterfactual Treatment Predictions")
st.caption("Estimated remission probability for the same patient under each candidate treatment.")

for i, row in results_df.iterrows():
    rank = i + 1
    st.markdown(f"""
    <div class="reason-box">
        <div class="rank-pill">Rank {rank}</div>
        <div style="font-size:1.05rem;font-weight:700;color:#355C7D;">{row['Treatment']}</div>
        <div style="font-size:1rem;color:#4B5563;margin-top:0.2rem;">
            Predicted remission probability: <b>{row['Predicted Remission Probability']:.3f}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.subheader("Neurobiological Reason for Recommendation")

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

best_treatment = best["Treatment"]

# ---- DOPAMINE / MOTIVATION CIRCUIT ----
if best_treatment == "bupropion SR" and (phq1 + phq4 + phq7) >= 6:
    top_reasons.append(
        "Elevated anhedonia (PHQ-1), fatigue (PHQ-4), and concentration impairment (PHQ-7) suggest reduced mesolimbic dopamine signaling (VTA → nucleus accumbens → prefrontal cortex). "
        "Bupropion, a norepinephrine–dopamine reuptake inhibitor (NDRI), enhances dopaminergic tone, targeting reward processing and cognitive energy deficits."
    )

# ---- COMBINATION: BROAD CIRCUIT COVERAGE ----
if best_treatment == "citalopram + bupropion SR" and (
    (phq1 + phq4 + phq7) >= 5 or (phq2 + phq5 + phq4) >= 6
):
    top_reasons.append(
        "Concurrent mood disturbance (PHQ-2), anhedonia (PHQ-1), fatigue (PHQ-4), and appetite disruption (PHQ-5) indicate dysregulation across both serotonergic (raphe nuclei) and dopaminergic circuits. "
        "Citalopram (SSRI) increases serotonin to stabilize mood and affect, while bupropion enhances dopamine and norepinephrine, improving motivation and executive function."
    )

# ---- ANXIETY / LIMBIC HYPERACTIVITY ----
if best_treatment == "citalopram + buspirone" and (phq6 + phq9 >= 3 or patient.get("anxiety_disorder", 0) == 1):
    top_reasons.append(
        "Elevated guilt/worthlessness (PHQ-6) and suicidal ideation (PHQ-9), along with anxiety features, suggest hyperactivity in limbic circuits (amygdala–ventromedial prefrontal cortex). "
        "Buspirone (5-HT1A partial agonist) reduces excessive serotonergic firing and anxiety reactivity, while citalopram increases overall serotonergic tone to stabilize mood."
    )

# ---- SEROTONIN / SLEEP + PSYCHOMOTOR ----
if best_treatment == "sertraline" and (phq3 + phq8) >= 4:
    top_reasons.append(
        "Sleep disturbance (PHQ-3) and psychomotor changes (PHQ-8) reflect serotonergic dysregulation affecting circadian and motor systems. "
        "Sertraline, an SSRI, increases serotonin availability in the dorsal raphe–cortical pathways, improving sleep regulation and psychomotor stability."
    )

# ---- SNRI / BROAD SEVERITY + ENERGY ----
if best_treatment == "venlafaxine XR" and ((phq2 + phq4 + phq5) >= 6 or (phq3 + phq8) >= 4):
    top_reasons.append(
        "Combined mood disturbance (PHQ-2), fatigue (PHQ-4), appetite dysregulation (PHQ-5), and sleep/psychomotor disruption (PHQ-3, PHQ-8) indicate widespread monoaminergic dysfunction. "
        "Venlafaxine (SNRI) enhances both serotonin and norepinephrine transmission, supporting mood regulation, arousal, and energy through dual-pathway modulation."
    )

# ---- SUICIDALITY ADJUSTMENT ----
if phq9 >= 2:
    top_reasons.append(
        "Elevated suicidal ideation (PHQ-9) is associated with dysregulation in prefrontal–limbic inhibitory control circuits. "
        "Treatments with stronger serotonergic stabilization were prioritized due to their role in improving impulse control and emotional regulation."
    )

# ---- GLOBAL SEVERITY ----
if patient.get("baseline_QIDS_SR16", 0) >= 18:
    top_reasons.append(
        "Higher overall symptom severity reflects broader network-level dysfunction across mood, reward, and cognitive systems, reducing baseline remission probability and favoring treatments with multi-pathway coverage."
    )

if not top_reasons:
    top_reasons.append(
        "The recommendation is driven by the interaction between individual PHQ-9 symptom patterns and baseline clinical features, rather than total severity alone."
    )

for reason in top_reasons:
    st.markdown(f"""
    <div class="reason-box">
        {reason}
    </div>
    """, unsafe_allow_html=True)

st.caption("Symptom-level neurobiological interpretation for demonstration purposes.")
st.markdown('</div>', unsafe_allow_html=True)
st.caption("Prototype explanation for demonstration only.")
st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Current patient inputs"):
    st.dataframe(pd.DataFrame([patient]), use_container_width=True)
