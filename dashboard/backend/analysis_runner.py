"""
Analysis runner backend — wrappers for the six OpenOA analysis methods.

Each wrapper accepts a PlantData object and user-configurable parameters,
runs the analysis, and returns a results dict (+ matplotlib figures where available).
"""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from openoa.plant import PlantData
from openoa.analysis.aep import MonteCarloAEP
from openoa.analysis.electrical_losses import ElectricalLosses
from openoa.analysis.turbine_long_term_gross_energy import TurbineLongTermGrossEnergy
from openoa.analysis.eya_gap_analysis import EYAGapAnalysis, EYAEstimate, OAResults
from openoa.analysis.wake_losses import WakeLosses
from openoa.analysis.yaw_misalignment import StaticYawMisalignment


# ---------------------------------------------------------------------------
# AEP Analysis
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Running AEP analysis…")
def run_aep_analysis(
    _plant_data: PlantData,
    num_sim: int = 500,
    reanalysis_products: list[str] | None = None,
    time_resolution: str = "MS",
    reg_model: str = "lin",
    reg_temperature: bool = False,
    reg_wind_direction: bool = False,
) -> dict:
    """Run MonteCarloAEP and return results dict."""
    aep = MonteCarloAEP(
        plant=_plant_data,
        reg_temperature=reg_temperature,
        reg_wind_direction=reg_wind_direction,
        reanalysis_products=reanalysis_products,
        time_resolution=time_resolution,
        reg_model=reg_model,
    )
    aep.run(num_sim=num_sim)

    results = aep.results
    avail_losses, curtail_losses = aep.long_term_losses

    mean_aep = results["aep_GWh"].mean()
    std_aep = results["aep_GWh"].std()
    uncertainty_pct = (std_aep / mean_aep) * 100 if mean_aep else 0
    mean_avail = results["avail_pct"].mean() * 100 if "avail_pct" in results.columns else 0
    mean_curtail = results["curt_pct"].mean() * 100 if "curt_pct" in results.columns else 0

    return {
        "results": results,
        "avail_losses": avail_losses,
        "curtail_losses": curtail_losses,
        "aggregate": aep.aggregate,
        "mean_aep": mean_aep,
        "std_aep": std_aep,
        "uncertainty_pct": uncertainty_pct,
        "mean_avail_loss": mean_avail,
        "mean_curtail_loss": mean_curtail,
    }


# ---------------------------------------------------------------------------
# Turbine Long-Term Gross Energy
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Running turbine gross energy analysis…")
def run_turbine_gross_energy(
    _plant_data: PlantData,
    UQ: bool = False,
    num_sim: int = 100,
) -> dict:
    """Run TurbineLongTermGrossEnergy and return results dict."""
    tlg = TurbineLongTermGrossEnergy(
        plant=_plant_data,
        UQ=UQ,
        num_sim=num_sim,
    )
    tlg.run()

    fig_pc, ax_pc = tlg.plot_filtered_power_curves(return_fig=True)
    plt.close(fig_pc)

    return {
        "turb_lt_gross": tlg.turb_lt_gross,
        "turbine_ids": list(tlg.turbine_ids),
        "fig_power_curves": fig_pc,
    }


# ---------------------------------------------------------------------------
# Electrical Losses
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Running electrical losses analysis…")
def run_electrical_losses(
    _plant_data: PlantData,
    UQ: bool = False,
    num_sim: int = 3000,
    uncertainty_meter: float = 0.005,
    uncertainty_scada: float = 0.005,
) -> dict:
    """Run ElectricalLosses and return results dict."""
    el = ElectricalLosses(
        plant=_plant_data,
        UQ=UQ,
        num_sim=num_sim,
        uncertainty_meter=uncertainty_meter,
        uncertainty_scada=uncertainty_scada,
    )
    el.run()

    fig_monthly, ax_monthly = el.plot_monthly_losses(return_fig=True)
    plt.close(fig_monthly)

    mean_loss = np.mean(el.electrical_losses) * 100
    std_loss = np.std(el.electrical_losses) * 100

    return {
        "electrical_losses": el.electrical_losses,
        "mean_loss_pct": mean_loss,
        "std_loss_pct": std_loss,
        "fig_monthly": fig_monthly,
    }


# ---------------------------------------------------------------------------
# EYA Gap Analysis
# ---------------------------------------------------------------------------

def run_eya_gap_analysis(
    plant_data: PlantData,
    eya_estimates: dict,
    oa_results: dict,
) -> dict:
    """Run EYAGapAnalysis and return results dict + waterfall figure."""
    gap = EYAGapAnalysis(
        plant=plant_data,
        eya_estimates=eya_estimates,
        oa_results=oa_results,
    )
    gap.run()

    fig, ax = gap.plot_waterfall(return_fig=True)
    plt.close(fig)

    return {
        "compiled_data": gap.compiled_data,
        "fig_waterfall": fig,
    }


# ---------------------------------------------------------------------------
# Wake Losses
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Running wake losses analysis…")
def run_wake_losses(
    _plant_data: PlantData,
    UQ: bool = True,
    num_sim: int = 50,
    wd_bin_width: float = 5.0,
    freestream_sector_width: float | tuple = (50.0, 110.0),
    reanalysis_products: list[str] | None = None,
) -> dict:
    """Run WakeLosses and return results dict."""
    wl = WakeLosses(
        plant=_plant_data,
        UQ=UQ,
        num_sim=num_sim,
        wd_bin_width=wd_bin_width,
        freestream_sector_width=freestream_sector_width,
        reanalysis_products=reanalysis_products or ["merra2", "era5"],
    )
    wl.run()

    por_mean = np.mean(wl.wake_losses_por) * 100
    lt_mean = np.mean(wl.wake_losses_lt) * 100

    return {
        "wake_losses_por": wl.wake_losses_por,
        "wake_losses_lt": wl.wake_losses_lt,
        "por_mean": por_mean,
        "lt_mean": lt_mean,
        "wake_losses_por_wd": wl.wake_losses_por_wd,
        "wake_losses_lt_wd": wl.wake_losses_lt_wd,
        "wd_bin_width": wl.wd_bin_width,
    }


# ---------------------------------------------------------------------------
# Yaw Misalignment
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Running yaw misalignment analysis…")
def run_yaw_misalignment(
    _plant_data: PlantData,
    UQ: bool = True,
    num_sim: int = 50,
    ws_bins: list[float] | None = None,
    ws_bin_width: float = 1.0,
    pitch_thresh: float = 0.5,
    max_power_filter: float | tuple = (0.92, 0.98),
) -> dict:
    """Run StaticYawMisalignment and return results dict."""
    if ws_bins is None:
        ws_bins = [5.0, 6.0, 7.0, 8.0]

    ym = StaticYawMisalignment(
        plant=_plant_data,
        UQ=UQ,
        num_sim=num_sim,
        ws_bins=ws_bins,
        ws_bin_width=ws_bin_width,
        pitch_thresh=pitch_thresh,
        max_power_filter=max_power_filter,
    )
    ym.run()

    return {
        "yaw_misalignment": ym.yaw_misalignment,
        "yaw_misalignment_ws": ym.yaw_misalignment_ws,
        "yaw_misalignment_avg": ym.yaw_misalignment_avg if hasattr(ym, "yaw_misalignment_avg") else None,
        "turbine_ids": list(ym.turbine_ids),
        "ws_bins": ws_bins,
        "UQ": UQ,
    }
