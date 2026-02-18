"""Page 4 — Electrical Loss Estimation."""

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data
from backend.analysis_runner import run_electrical_losses

st.set_page_config(page_title="Electrical Losses", layout="wide")
st.title("Electrical Loss Estimation")

plant = load_plant_data()

# --- Sidebar controls ---
st.sidebar.header("Parameters")
UQ = st.sidebar.checkbox("Uncertainty Quantification", value=False)
num_sim = st.sidebar.slider("Number of simulations", 1, 10000, 3000 if UQ else 1, step=100, disabled=not UQ)
uncertainty_meter = st.sidebar.number_input("Meter uncertainty", 0.0, 0.1, 0.005, step=0.001, format="%.3f")
uncertainty_scada = st.sidebar.number_input("SCADA uncertainty", 0.0, 0.1, 0.005, step=0.001, format="%.3f")

run_btn = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

if run_btn:
    try:
        res = run_electrical_losses(
            plant,
            UQ=UQ,
            num_sim=num_sim if UQ else 1,
            uncertainty_meter=uncertainty_meter,
            uncertainty_scada=uncertainty_scada,
        )

        # --- Summary ---
        st.header("Summary")
        c1, c2 = st.columns(2)
        c1.metric("Mean Electrical Loss", f"{res['mean_loss_pct']:.2f}%")
        c2.metric("Std. Deviation", f"{res['std_loss_pct']:.2f}%")

        # --- Monthly losses chart ---
        st.header("Monthly Electrical Losses")
        st.pyplot(res["fig_monthly"])

        # --- Distribution histogram ---
        if UQ and len(res["electrical_losses"]) > 1:
            st.header("Loss Distribution")
            losses = res["electrical_losses"].flatten() * 100
            fig_hist = px.histogram(
                x=losses,
                nbins=40,
                labels={"x": "Electrical Loss (%)"},
                title="Electrical Loss Distribution",
                color_discrete_sequence=["#D95F02"],
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)

    except Exception as e:
        st.error(f"Electrical losses analysis failed: {e}")
else:
    st.info("Configure parameters in the sidebar, then click **Run Analysis**.")
