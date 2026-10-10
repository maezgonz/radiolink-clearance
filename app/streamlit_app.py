"""Streamlit dashboard for interactive radiolink clearance analysis."""

from __future__ import annotations

import streamlit as st

from radiolink import RadioLinkEngine, TowerOptimizer, plot_link_profile
from radiolink.io import load_profile_from_csv

st.set_page_config(page_title="RadioLink Clearance", layout="wide")
st.title("RadioLink Clearance Suite")
st.markdown(
    "Microwave radiolink clearance analysis — ITU-R P.530-18 compliant. "
    "Load a terrain profile and adjust the parameters interactively."
)

with st.sidebar:
    st.header("Terrain profile")
    profile_path = st.text_input("CSV profile path", value="data/sample_profile.csv")

    st.header("Link parameters")
    freq = st.slider("Frequency (GHz)", 1.0, 42.0, 7.0, 0.1)
    h1 = st.slider("TX antenna height h1 (m)", 10.0, 150.0, 60.0, 1.0)
    h2 = st.slider("RX antenna height h2 (m)", 10.0, 150.0, 80.0, 1.0)
    k_factor = st.selectbox("Atmospheric factor K", [4.0 / 3.0, 1.0, 0.8, 2.0 / 3.0], index=0, format_func=lambda v: f"{v:.2f}")
    target_ratio = st.slider("Compliance target C/R1", 0.1, 1.0, 0.60, 0.05)

if st.sidebar.button("Analyse"):
    df = load_profile_from_csv(profile_path)
    engine = RadioLinkEngine(df, freq, h1, h2, k_factor, target_ratio)
    summary = engine.get_summary()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Path length", f"{summary.d_total_km:.2f} km")
    c2.metric("Critical obstacle", f"km {summary.crit_dist_km:.2f}")
    c3.metric("Net clearance", f"{summary.crit_clearance_m:.2f} m")
    c4.metric("Ratio C/R1", f"{summary.crit_ratio * 100:.1f}%")

    if summary.is_compliant:
        st.success(f"Status: {summary.status_label}")
    else:
        st.error(f"Status: {summary.status_label}")
        if st.sidebar.button("Optimize towers"):
            h1_opt, h2_opt = TowerOptimizer(engine).solve()
            st.info(f"Optimized towers: h1 = {h1_opt:.1f} m, h2 = {h2_opt:.1f} m")

    fig, _ = plot_link_profile(engine, show_k_variations=st.sidebar.checkbox("K variations", True), save_path=None)
    st.pyplot(fig)

    st.download_button(
        "Download profile table (CSV)",
        data=engine.df.to_csv(index=False),
        file_name="profile_table.csv",
        mime="text/csv",
    )
