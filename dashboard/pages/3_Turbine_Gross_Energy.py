"""Page 3 — Turbine Long-Term Gross Energy."""

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data
from backend.analysis_runner import run_turbine_gross_energy

st.set_page_config(page_title="Turbine Gross Energy", layout="wide")
st.title("Turbine Long-Term Gross Energy")

plant = load_plant_data()

# --- Sidebar controls ---
st.sidebar.header("Parameters")
UQ = st.sidebar.checkbox("Uncertainty Quantification", value=False)
num_sim = st.sidebar.slider("Number of simulations", 1, 500, 100 if UQ else 1, step=10, disabled=not UQ)

run_btn = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

if run_btn:
    try:
        res = run_turbine_gross_energy(
            plant,
            UQ=UQ,
            num_sim=num_sim if UQ else 1,
        )

        # --- Filtered power curves ---
        st.header("Filtered Power Curves")
        st.pyplot(res["fig_power_curves"])

        # --- Gross energy bar chart ---
        st.header("Long-Term Gross Energy by Turbine")
        turb_gross = res["turb_lt_gross"]
        turbine_ids = res["turbine_ids"]

        if not turb_gross.empty:
            # Each column is a turbine, each row is a simulation
            mean_gross = turb_gross.mean()
            std_gross = turb_gross.std() if UQ else turb_gross.mean() * 0

            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=mean_gross.index.astype(str),
                y=mean_gross.values / 1e3,
                error_y=dict(type="data", array=std_gross.values / 1e3, visible=UQ),
                marker_color="#1B9E77",
            ))
            fig.update_layout(
                xaxis_title="Turbine",
                yaxis_title="Gross Energy (MWh)",
                title="Mean Long-Term Gross Energy per Turbine",
                height=450,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            st.header("Summary Statistics")
            summary = turb_gross.describe().T
            summary.index.name = "Turbine"
            st.dataframe(summary, use_container_width=True)

    except Exception as e:
        st.error(f"Turbine gross energy analysis failed: {e}")
else:
    st.info("Configure parameters in the sidebar, then click **Run Analysis**.")
