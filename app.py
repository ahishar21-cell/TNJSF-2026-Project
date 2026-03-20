import streamlit as st

st.set_page_config(
    page_title="Depression Treatment Recommender",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1180px;
}

html, body, [class*="css"] {
    font-family: "Aptos", "Inter", "Segoe UI", sans-serif;
}

.main-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #355C7D;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.subtitle {
    font-size: 1.05rem;
    color: #4B5563;
    margin-bottom: 1.3rem;
}

.hero-box {
    background: linear-gradient(135deg, #EEF4F9 0%, #F8FBFD 100%);
    border: 1px solid #DCE6EF;
    padding: 1.4rem;
    border-radius: 20px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 14px rgba(53, 92, 125, 0.06);
}

.info-card {
    background: #FCFDFE;
    border: 1px solid #DCE6EF;
    padding: 1rem 1.1rem;
    border-radius: 18px;
    box-shadow: 0 3px 10px rgba(53, 92, 125, 0.05);
    margin-bottom: 0.9rem;
}

.card-title {
    color: #355C7D;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.small-muted {
    color: #5F6B7A;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧠 Personalized Depression Treatment Recommender</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">PHQ-9–centered prototype for symptom-level treatment personalization</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="hero-box">
<b style="color:#355C7D;">What this app does</b><br>
Uses PHQ-9 symptom patterns and baseline clinical context to compare estimated remission probabilities across candidate treatments.
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-card">
        <div class="card-title">1. Enter symptom profile</div>
        <div class="small-muted">Input PHQ-9 item-level symptoms and baseline clinical context.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <div class="card-title">2. Compare treatments</div>
        <div class="small-muted">Generate counterfactual remission probabilities for each treatment option.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-card">
        <div class="card-title">3. Review recommendation</div>
        <div class="small-muted">See which option has the highest predicted probability in the prototype.</div>
    </div>
    """, unsafe_allow_html=True)

st.info("Research prototype only. Not for clinical use.")
