"""Page 2 — Monte Carlo AEP Analysis."""

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data
from backend.analysis_runner import run_aep_analysis

st.set_page_config(page_title="AEP Analysis", layout="wide")
st.title("AEP Analysis (Monte Carlo)")

plant = load_plant_data()

# --- Sidebar controls ---
st.sidebar.header("AEP Parameters")
num_sim = st.sidebar.slider("Number of simulations", 10, 2000, 500, step=10)
time_resolution = st.sidebar.selectbox("Time resolution", ["MS", "D"], index=0)
reg_model = st.sidebar.selectbox("Regression model", ["lin", "gbm", "etr", "gam"], index=0)
reg_temperature = st.sidebar.checkbox("Include temperature", value=False)
reg_wind_direction = st.sidebar.checkbox("Include wind direction", value=False)
reanalysis_options = list(plant.reanalysis.keys())
reanalysis_products = st.sidebar.multiselect("Reanalysis products", reanalysis_options, default=reanalysis_options)

run_btn = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

if run_btn:
    try:
        res = run_aep_analysis(
            plant,
            num_sim=num_sim,
            reanalysis_products=reanalysis_products or None,
            time_resolution=time_resolution,
            reg_model=reg_model,
            reg_temperature=reg_temperature,
            reg_wind_direction=reg_wind_direction,
        )

        # --- Summary metrics ---
        st.header("Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean AEP", f"{res['mean_aep']:.2f} GWh/yr")
        c2.metric("Uncertainty", f"{res['uncertainty_pct']:.1f}%")
        c3.metric("Availability Loss", f"{res['mean_avail_loss']:.1f}%")
        c4.metric("Curtailment Loss", f"{res['mean_curtail_loss']:.1f}%")

        results = res["results"]

        # --- AEP distribution histogram ---
        st.header("AEP Distribution")
        fig_hist = px.histogram(
            results,
            x="aep_GWh",
            nbins=40,
            labels={"aep_GWh": "AEP (GWh/yr)"},
            title="Monte Carlo AEP Distribution",
            color_discrete_sequence=["#1B9E77"],
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

        # --- Results table ---
        st.header("Results Summary")
        summary = results.describe().T
        st.dataframe(summary, use_container_width=True)

    except Exception as e:
        st.error(f"AEP analysis failed: {e}")
else:
    st.info("Configure parameters in the sidebar, then click **Run Analysis**.")
