"""Page 7 — Static Yaw Misalignment Detection."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data
from backend.analysis_runner import run_yaw_misalignment

st.set_page_config(page_title="Yaw Misalignment", layout="wide")
st.title("Static Yaw Misalignment Detection")

plant = load_plant_data()

# --- Sidebar controls ---
st.sidebar.header("Parameters")
UQ = st.sidebar.checkbox("Uncertainty Quantification", value=True)
num_sim = st.sidebar.slider("Number of simulations", 1, 200, 50, step=5, disabled=not UQ)
pitch_thresh = st.sidebar.slider("Pitch threshold (deg)", 0.0, 5.0, 0.5, step=0.1)

ws_bin_str = st.sidebar.text_input("Wind speed bins (comma-separated)", "5.0, 6.0, 7.0, 8.0")
try:
    ws_bins = [float(x.strip()) for x in ws_bin_str.split(",")]
except ValueError:
    ws_bins = [5.0, 6.0, 7.0, 8.0]
    st.sidebar.warning("Invalid wind speed bins, using defaults.")

run_btn = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

if run_btn:
    try:
        res = run_yaw_misalignment(
            plant,
            UQ=UQ,
            num_sim=num_sim if UQ else 1,
            ws_bins=ws_bins,
            pitch_thresh=pitch_thresh,
            max_power_filter=(0.92, 0.98) if UQ else 0.95,
        )

        turbine_ids = res["turbine_ids"]
        ws_bins_used = res["ws_bins"]

        st.header("Yaw Misalignment Results")

        # --- Per wind-speed-bin table ---
        # yaw_misalignment_ws shape: (num_sim, n_turbines, n_ws_bins) if UQ else (n_turbines, n_ws_bins)
        yaw_ws = np.array(res["yaw_misalignment_ws"])
        if yaw_ws.ndim == 3:
            mean_yaw_ws = np.nanmean(yaw_ws, axis=0)
        else:
            mean_yaw_ws = yaw_ws

        ws_labels = [f"{ws:.1f} m/s" for ws in ws_bins_used]
        summary_df = pd.DataFrame(mean_yaw_ws, index=turbine_ids, columns=ws_labels)

        # Overall average per turbine
        yaw_overall = np.array(res["yaw_misalignment"])
        if yaw_overall.ndim == 2:
            mean_overall = np.nanmean(yaw_overall, axis=0)
        else:
            mean_overall = yaw_overall
        summary_df["Mean (deg)"] = mean_overall

        st.dataframe(summary_df.style.format("{:.2f}"), use_container_width=True)

        # --- Heatmap ---
        st.header("Misalignment Heatmap")
        fig_heat = px.imshow(
            mean_yaw_ws,
            x=ws_labels,
            y=[str(t) for t in turbine_ids],
            labels=dict(x="Wind Speed Bin", y="Turbine", color="Misalignment (deg)"),
            color_continuous_scale="RdBu_r",
            color_continuous_midpoint=0,
            aspect="auto",
            title="Yaw Misalignment by Turbine and Wind Speed",
        )
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)

        # --- Bar chart per turbine ---
        st.header("Mean Misalignment per Turbine")
        fig_bar = px.bar(
            x=[str(t) for t in turbine_ids],
            y=mean_overall,
            labels={"x": "Turbine", "y": "Mean Misalignment (deg)"},
            title="Average Yaw Misalignment",
            color_discrete_sequence=["#D95F02"],
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Yaw misalignment analysis failed: {e}")
else:
    st.info("Configure parameters in the sidebar, then click **Run Analysis**.")
