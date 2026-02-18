"""Page 1 — Plant Overview: map, asset table, SCADA explorer, data quality."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data_loader import load_plant_data

st.set_page_config(page_title="Plant Overview", layout="wide")
st.title("Plant Overview")

plant = load_plant_data()

# --- Asset table ---
st.header("Turbine Assets")
asset_df = plant.asset.reset_index()
display_cols = [c for c in asset_df.columns if c != "type"]
st.dataframe(asset_df[display_cols], use_container_width=True)

# --- Wind farm map ---
st.header("Wind Farm Map")
if "latitude" in asset_df.columns and "longitude" in asset_df.columns:
    fig_map = px.scatter_mapbox(
        asset_df,
        lat="latitude",
        lon="longitude",
        hover_name="asset_id",
        hover_data=["rated_power", "hub_height", "rotor_diameter"],
        color_discrete_sequence=["#1B9E77"],
        zoom=13,
        height=500,
    )
    fig_map.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

# --- SCADA data explorer ---
st.header("SCADA Data Explorer")
scada = plant.scada.reset_index()
turbine_ids = sorted(scada["asset_id"].unique())

col1, col2 = st.columns(2)
with col1:
    selected_turbine = st.selectbox("Select Turbine", turbine_ids)
with col2:
    y_var = st.selectbox("Y-axis variable", ["WTUR_W", "WMET_HorWdSpd", "WMET_EnvTmp", "WROT_BlPthAngVal"])

turbine_data = scada[scada["asset_id"] == selected_turbine].copy()

# Power curve scatter
st.subheader("Power Curve")
fig_pc = px.scatter(
    turbine_data,
    x="WMET_HorWdSpd",
    y="WTUR_W",
    opacity=0.3,
    labels={"WMET_HorWdSpd": "Wind Speed (m/s)", "WTUR_W": "Power (kW)"},
    title=f"Power Curve — {selected_turbine}",
    color_discrete_sequence=["#1B9E77"],
)
fig_pc.update_layout(height=400)
st.plotly_chart(fig_pc, use_container_width=True)

# Time series
st.subheader(f"{y_var} Time Series")
if "time" in turbine_data.columns:
    fig_ts = px.line(
        turbine_data.sort_values("time"),
        x="time",
        y=y_var,
        title=f"{y_var} — {selected_turbine}",
        color_discrete_sequence=["#1B9E77"],
    )
    fig_ts.update_layout(height=350)
    st.plotly_chart(fig_ts, use_container_width=True)

# --- Data quality metrics ---
st.header("Data Quality")
total_rows = len(scada)
nan_pct = scada.isnull().mean() * 100
quality_df = nan_pct[nan_pct > 0].sort_values(ascending=False).reset_index()
quality_df.columns = ["Column", "NaN %"]

col_a, col_b = st.columns(2)
with col_a:
    st.metric("Total SCADA Records", f"{total_rows:,}")
with col_b:
    n_turbines = scada["asset_id"].nunique()
    st.metric("Turbines", n_turbines)

if not quality_df.empty:
    st.dataframe(quality_df, use_container_width=True)
else:
    st.success("No missing values found in the SCADA data.")
