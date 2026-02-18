"""Page 5 — EYA Gap Analysis (Waterfall)."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data
from backend.analysis_runner import run_eya_gap_analysis

st.set_page_config(page_title="EYA Gap Analysis", layout="wide")
st.title("EYA Gap Analysis")

plant = load_plant_data()

st.markdown(
    """
This page compares an Energy Yield Assessment (EYA) prediction against
Operational Assessment (OA) results. Enter your EYA estimates and OA
results below, then run the analysis to see a waterfall chart.
"""
)

# --- EYA Estimates ---
st.header("EYA Estimates")
col1, col2, col3 = st.columns(3)
with col1:
    eya_aep = st.number_input("EYA AEP (GWh/yr)", 0.0, 100.0, 17.0, step=0.5)
    eya_gross = st.number_input("Gross Energy (GWh/yr)", 0.0, 100.0, 22.0, step=0.5)
with col2:
    eya_avail = st.number_input("Availability Losses", 0.0, 0.99, 0.05, step=0.01, format="%.2f")
    eya_elec = st.number_input("Electrical Losses", 0.0, 0.99, 0.02, step=0.01, format="%.2f")
with col3:
    eya_turbine = st.number_input("Turbine Losses", 0.0, 0.99, 0.03, step=0.01, format="%.2f")
    eya_blade = st.number_input("Blade Degradation Losses", 0.0, 0.99, 0.01, step=0.01, format="%.2f")
    eya_wake = st.number_input("Wake Losses", 0.0, 0.99, 0.08, step=0.01, format="%.2f")

# --- OA Results ---
st.header("OA Results")
col_a, col_b = st.columns(2)
with col_a:
    oa_aep = st.number_input("OA AEP (GWh/yr)", 0.0, 100.0, 15.5, step=0.5)
    oa_tie = st.number_input("Turbine Ideal Energy (GWh/yr)", 0.0, 100.0, 18.0, step=0.5)
with col_b:
    oa_avail = st.number_input("OA Availability Losses", 0.0, 0.99, 0.06, step=0.01, format="%.2f")
    oa_elec = st.number_input("OA Electrical Losses", 0.0, 0.99, 0.02, step=0.01, format="%.2f")

run_btn = st.button("Run Gap Analysis", type="primary")

if run_btn:
    try:
        eya_estimates = {
            "aep": eya_aep,
            "gross_energy": eya_gross,
            "availability_losses": eya_avail,
            "electrical_losses": eya_elec,
            "turbine_losses": eya_turbine,
            "blade_degradation_losses": eya_blade,
            "wake_losses": eya_wake,
        }
        oa_results = {
            "aep": oa_aep,
            "availability_losses": oa_avail,
            "electrical_losses": oa_elec,
            "turbine_ideal_energy": oa_tie,
        }

        res = run_eya_gap_analysis(plant, eya_estimates, oa_results)

        st.header("Waterfall Chart")
        st.pyplot(res["fig_waterfall"])

        st.header("Gap Breakdown")
        labels = ["EYA AEP", "TIE Diff", "Availability Diff", "Electrical Diff", "Unaccounted"]
        data = res["compiled_data"]
        for label, val in zip(labels, data):
            st.write(f"**{label}:** {val:.3f} GWh/yr")

    except Exception as e:
        st.error(f"EYA gap analysis failed: {e}")
