"""
OpenOA Wind Energy Analysis Dashboard
======================================
Streamlit multi-page app showcasing OpenOA analysis methods
using the ENGIE La Haute Borne example dataset.
"""

import streamlit as st

st.set_page_config(
    page_title="OpenOA Dashboard",
    page_icon="💨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("OpenOA Wind Energy Analysis Dashboard")

st.markdown(
    """
Welcome to the **OpenOA** analysis dashboard. This application demonstrates
the six operational analysis methods provided by the
[OpenOA library](https://github.com/NREL/OpenOA) using the **ENGIE La Haute Borne**
example wind farm dataset.

### Wind Farm Summary

| Parameter | Value |
|---|---|
| **Farm Name** | La Haute Borne |
| **Location** | 48.45° N, 5.59° E (Meuse, France) |
| **Capacity** | 8.2 MW |
| **Turbines** | 4 × Senvion MM82 (2.05 MW each) |
| **Data Period** | Jan 2014 – Dec 2015 (10-min SCADA) |

### Analysis Pages

Use the **sidebar** to navigate between pages:

1. **Plant Overview** — Wind farm map, asset table, and SCADA data explorer
2. **AEP Analysis** — Monte Carlo annual energy production estimation
3. **Turbine Gross Energy** — Long-term gross energy per turbine
4. **Electrical Losses** — Electrical loss estimation
5. **EYA Gap Analysis** — Energy yield assessment gap waterfall
6. **Wake Losses** — Wake loss estimation by wind direction
7. **Yaw Misalignment** — Static yaw misalignment detection

---
*Powered by [OpenOA](https://github.com/NREL/OpenOA) and
[Streamlit](https://streamlit.io)*
"""
)
