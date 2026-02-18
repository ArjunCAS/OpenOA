"""
Data loading backend — adapted from examples/project_ENGIE.py.

Loads the ENGIE La Haute Borne dataset and returns a validated PlantData object.
Uses @st.cache_resource so data is loaded once per server session.
"""

from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import streamlit as st

# Ensure the repo root is on sys.path so openoa is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import openoa.utils.unit_conversion as un
import openoa.utils.met_data_processing as met
from openoa.plant import PlantData
from openoa.utils import filters

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _extract_data(path: Path) -> None:
    """Extract the zip archive if the folder doesn't exist yet."""
    if not path.exists():
        with ZipFile(path.with_suffix(".zip")) as zf:
            zf.extractall(path)


def _clean_scada(scada_file: Path) -> pd.DataFrame:
    """Read and clean SCADA data."""
    scada_freq = "10min"
    scada_df = pd.read_csv(scada_file)

    scada_df["Date_time"] = pd.to_datetime(scada_df["Date_time"], utc=True).dt.tz_localize(None)
    scada_df = scada_df.drop_duplicates(subset=["Date_time", "Wind_turbine_name"], keep="first")

    # Remove extreme temperatures
    scada_df = scada_df[(scada_df["Ot_avg"] >= -15.0) & (scada_df["Ot_avg"] <= 45.0)]

    # Flag unresponsive sensors
    turbine_ids = scada_df.Wind_turbine_name.unique()
    sensor_cols = ["Ba_avg", "P_avg", "Ws_avg", "Va_avg", "Ot_avg", "Ya_avg", "Wa_avg"]
    for t_id in turbine_ids:
        ix_turbine = scada_df["Wind_turbine_name"] == t_id
        ix_flag = filters.unresponsive_flag(scada_df.loc[ix_turbine], 3, col=["Va_avg"])
        scada_df.loc[ix_flag.loc[ix_flag["Va_avg"]].index, sensor_cols] = np.nan
        ix_flag = filters.unresponsive_flag(scada_df.loc[ix_turbine], 20, col=["Ot_avg"])
        scada_df.loc[ix_flag.loc[ix_flag["Ot_avg"]].index, "Ot_avg"] = np.nan

    # Convert pitch to [-180, 180]
    scada_df.loc[:, "Ba_avg"] = scada_df["Ba_avg"] % 360
    ix_gt_180 = scada_df["Ba_avg"] > 180.0
    scada_df.loc[ix_gt_180, "Ba_avg"] = scada_df.loc[ix_gt_180, "Ba_avg"] - 360.0

    # Energy production
    scada_df["energy_kwh"] = un.convert_power_to_energy(scada_df.P_avg * 1000, scada_freq) / 1000

    return scada_df


@st.cache_resource(show_spinner="Loading La Haute Borne dataset…")
def load_plant_data() -> PlantData:
    """Load and return a validated PlantData object (cached per server session)."""
    path = DATA_DIR / "la_haute_borne"
    _extract_data(path)

    # --- SCADA ---
    scada_df = _clean_scada(path / "la-haute-borne-data-2014-2015.csv")

    # --- Meter ---
    meter_curtail_df = pd.read_csv(path / "plant_data.csv")
    meter_df = meter_curtail_df.copy()
    meter_df["time"] = pd.to_datetime(meter_df.time_utc).dt.tz_localize(None)
    meter_df.drop(["time_utc", "availability_kwh", "curtailment_kwh"], axis=1, inplace=True)

    # --- Curtailment ---
    curtail_df = meter_curtail_df.copy()
    curtail_df["time"] = pd.to_datetime(curtail_df.time_utc).dt.tz_localize(None)
    curtail_df.drop(["time_utc"], axis=1, inplace=True)

    # --- Reanalysis: MERRA2 ---
    re_merra2 = pd.read_csv(path / "merra2_la_haute_borne.csv")
    re_merra2["datetime"] = pd.to_datetime(re_merra2["datetime"], utc=True).dt.tz_localize(None)
    re_merra2["winddirection_deg"] = met.compute_wind_direction(re_merra2["u_50"], re_merra2["v_50"])
    re_merra2.drop(["Unnamed: 0"], axis=1, inplace=True, errors="ignore")

    # --- Reanalysis: ERA5 ---
    re_era5 = pd.read_csv(path / "era5_wind_la_haute_borne.csv")
    re_era5 = re_era5.loc[:, ~re_era5.columns.duplicated()].copy()
    re_era5["datetime"] = pd.to_datetime(re_era5["datetime"], utc=True).dt.tz_localize(None)
    re_era5 = re_era5.set_index(pd.DatetimeIndex(re_era5.datetime)).asfreq("1h")
    re_era5["datetime"] = re_era5.index
    re_era5["winddirection_deg"] = met.compute_wind_direction(
        re_era5["u_100"], re_era5["v_100"]
    ).values
    re_era5.drop(["Unnamed: 0"], axis=1, inplace=True, errors="ignore")

    # --- Asset ---
    asset_df = pd.read_csv(path / "la-haute-borne_asset_table.csv")
    asset_df["type"] = "turbine"

    # --- Build PlantData ---
    plant = PlantData(
        analysis_type="MonteCarloAEP",
        metadata=DATA_DIR / "plant_meta.yml",
        scada=scada_df,
        meter=meter_df,
        curtail=curtail_df,
        asset=asset_df,
        reanalysis={"era5": re_era5, "merra2": re_merra2},
    )
    return plant
