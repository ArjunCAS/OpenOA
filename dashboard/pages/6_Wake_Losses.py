"""Page 6 — Wake Loss Estimation."""

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data
from backend.analysis_runner import run_wake_losses

st.set_page_config(page_title="Wake Losses", layout="wide")
st.title("Wake Loss Estimation")

plant = load_plant_data()

# --- Sidebar controls ---
st.sidebar.header("Parameters")
UQ = st.sidebar.checkbox("Uncertainty Quantification", value=True)
num_sim = st.sidebar.slider("Number of simulations", 1, 200, 50, step=5, disabled=not UQ)
wd_bin_width = st.sidebar.slider("Wind direction bin width (°)", 1.0, 30.0, 5.0, step=1.0)
fs_min = st.sidebar.number_input("Freestream sector width min (°)", 10.0, 180.0, 50.0, step=5.0)
fs_max = st.sidebar.number_input("Freestream sector width max (°)", 10.0, 180.0, 110.0, step=5.0)

reanalysis_options = list(plant.reanalysis.keys())
reanalysis_products = st.sidebar.multiselect("Reanalysis products", reanalysis_options, default=reanalysis_options)

run_btn = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

if run_btn:
    try:
        freestream_sector_width = (fs_min, fs_max) if UQ else fs_min
        res = run_wake_losses(
            plant,
            UQ=UQ,
            num_sim=num_sim if UQ else 1,
            wd_bin_width=wd_bin_width,
            freestream_sector_width=freestream_sector_width,
            reanalysis_products=reanalysis_products or None,
        )

        # --- Summary metrics ---
        st.header("Summary")
        c1, c2 = st.columns(2)
        c1.metric("POR Wake Loss", f"{res['por_mean']:.1f}%")
        c2.metric("Long-Term Wake Loss", f"{res['lt_mean']:.1f}%")

        # --- Distribution ---
        if UQ and len(res["wake_losses_por"]) > 1:
            import plotly.express as px

            st.header("Wake Loss Distributions")
            col1, col2 = st.columns(2)
            with col1:
                fig_por = px.histogram(
                    x=np.array(res["wake_losses_por"]).flatten() * 100,
                    nbins=30,
                    labels={"x": "POR Wake Loss (%)"},
                    title="Period of Record",
                    color_discrete_sequence=["#7570B3"],
                )
                fig_por.update_layout(height=350)
                st.plotly_chart(fig_por, use_container_width=True)
            with col2:
                fig_lt = px.histogram(
                    x=np.array(res["wake_losses_lt"]).flatten() * 100,
                    nbins=30,
                    labels={"x": "Long-Term Wake Loss (%)"},
                    title="Long-Term Corrected",
                    color_discrete_sequence=["#E7298A"],
                )
                fig_lt.update_layout(height=350)
                st.plotly_chart(fig_lt, use_container_width=True)

        # --- Wake efficiency by wind direction ---
        st.header("Wake Efficiency by Wind Direction")
        por_wd = res.get("wake_losses_por_wd")
        if por_wd is not None and len(por_wd) > 0:
            wd_data = np.array(por_wd)
            if wd_data.ndim == 2:
                mean_eff = (1 - np.nanmean(wd_data, axis=0)) * 100
            else:
                mean_eff = (1 - wd_data) * 100
            n_bins = len(mean_eff)
            wd_centers = np.linspace(0, 360, n_bins, endpoint=False) + wd_bin_width / 2

            fig_wd = go.Figure()
            fig_wd.add_trace(go.Scatterpolar(
                r=mean_eff,
                theta=wd_centers,
                mode="lines+markers",
                name="POR Efficiency",
                line=dict(color="#1B9E77"),
            ))
            fig_wd.update_layout(
                polar=dict(radialaxis=dict(title="Efficiency (%)", range=[min(50, mean_eff.min() - 5), 105])),
                title="Wake Efficiency vs Wind Direction",
                height=500,
            )
            st.plotly_chart(fig_wd, use_container_width=True)

    except Exception as e:
        st.error(f"Wake losses analysis failed: {e}")
else:
    st.info("Configure parameters in the sidebar, then click **Run Analysis**.")
