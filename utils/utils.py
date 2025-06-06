import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import rainflow

pio.renderers.default = "browser"


def load_price_data(file_path):
    """
    Load electricity price data from a CSV file and convert timestamps.

    Args:
        file_path (str): Path to the CSV file with columns 'Start date', 'End date',
                         and 'Germany/Luxembourg [€/MWh]'.

    Returns:
        pd.DataFrame: DataFrame with 'timestamp' and 'price_eur_per_mwh' columns.
    """
    df = pd.read_csv(file_path, low_memory=False, usecols=[0, 1, 2])
    try:
        df["Start date"] = pd.to_datetime(df["Start date"], format="%b %d, %Y %I:%M %p")
        df["End date"] = pd.to_datetime(df["End date"], format="%b %d, %Y %I:%M %p")
    except Exception as e:
        print(e)

    df = df.rename(columns={"Germany/Luxembourg [€/MWh]": "price_eur_per_mwh"})

    # Assuming start time as the timestamp
    df["timestamp"] = df["Start date"]
    return df


def get_results_path(model_name: str) -> str:
    """
    Construct a results CSV file path for a model based on project root.

    Args:
        model_name (str): Name of the simulation model.

    Returns:
        str: Absolute file path to the results CSV file.
    """
    cwd = os.getcwd()

    # Look for marker file or directory
    while True:
        if "pyproject.toml" in os.listdir(cwd) or ".git" in os.listdir(cwd):
            base_dir = cwd
            break
        parent = os.path.dirname(cwd)
        if parent == cwd:
            raise FileNotFoundError(
                "Could not find project root (pyproject.toml or .git)."
            )
        cwd = parent

    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    filename = f"{model_name.replace(' ', '_')}_results.csv"
    return os.path.join(results_dir, filename)


def calculate_profit(
    df, efficiency, grid_fee_per_mwh, degradation_cost_per_mwh, pv_setup_cost_eur
):
    """
    Compute interval-wise and cumulative financial metrics for battery simulation.

    Args:
        df (pd.DataFrame): DataFrame with charge/discharge data and prices.
        efficiency (float): Round-trip battery efficiency (0–1).
        grid_fee_per_mwh (float): Grid usage cost per MWh.
        degradation_cost_per_mwh (float): Battery degradation cost per MWh throughput.
        pv_setup_cost_eur (float): One-time capital cost of PV installation.

    Returns:
        pd.DataFrame: Updated DataFrame with financial metrics columns.
    """
    # Battery discharge revenue
    df["revenue_battery"] = df["discharge_mwh"] * efficiency * df["price_eur_per_mwh"]

    # PV export revenue
    df["revenue_pv_export"] = df.get("pv_export_mwh", 0.0) * df["price_eur_per_mwh"]

    # Total revenue
    df["revenue"] = df["revenue_battery"] + df["revenue_pv_export"]

    # Grid energy cost
    df["cost"] = df["from_grid_mwh"] * (df["price_eur_per_mwh"] + grid_fee_per_mwh)

    # Battery degradation cost
    df["degradation"] = degradation_cost_per_mwh * (
        df["charge_mwh"] + df["discharge_mwh"]
    )

    # Interval profit
    df["interval_profit"] = df["revenue"] - df["cost"] - df["degradation"]

    # Deduct PV setup cost once, if any
    if pv_setup_cost_eur > 0:
        df.at[0, "interval_profit"] -= pv_setup_cost_eur

    # Cumulative metrics
    df["cumulative_profit"] = df["interval_profit"].cumsum()
    df["cumulative_degradation"] = df["degradation"].cumsum()
    df["cumulative_grid_cost"] = df["cost"].cumsum()
    df["cumulative_pv_revenue"] = df["revenue_pv_export"].cumsum()

    return df


def save_results_to_csv(df, file_path, output_dir="results"):
    """
    Save DataFrame to a CSV file inside the given output directory.

    Args:
        df (pd.DataFrame): DataFrame to save.
        file_path (str): Output file path including filename.
        output_dir (str): Directory to save the file (default: "results").
    """
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(file_path, index=False)


def simulate_pv_generation(df: pd.DataFrame, capacity_mw: float = 5.0) -> pd.Series:
    """
    Simulate PV generation (MWh per 15-minute interval) based on hour and season.

    Args:
        df (pd.DataFrame): Must include a 'timestamp' column.
        capacity_mw (float): Installed PV capacity in MW.

    Returns:
        pd.Series: Simulated PV energy generation series indexed by timestamp.
    """
    timestamps = df["timestamp"]
    pv_output = []

    for ts in timestamps:
        hour = ts.hour + ts.minute / 60
        doy = ts.timetuple().tm_yday

        # Daily irradiance profile (0 at night, peak at noon)
        daylight_factor = max(0, np.sin(np.pi * (hour - 6) / 12))  # peak at 12:00
        seasonal_scaling = 0.9 + 0.1 * np.cos(
            2 * np.pi * (doy - 173) / 365
        )  # max in June

        # Simulated output power [MW]
        power_mw = capacity_mw * daylight_factor * seasonal_scaling

        # Convert to MWh over 15-minute period
        energy_mwh = power_mw * 0.25
        pv_output.append(energy_mwh)

    return pd.Series(pv_output, index=df.index, name="pv_generation_mwh")


def simulate_load_series(df: pd.DataFrame, peak_mw: float = 8.0) -> pd.Series:
    """
    Simulate time-varying load demand with weekday and time-of-day effects.

    Args:
        df (pd.DataFrame): Must include a 'timestamp' column.
        peak_mw (float): Maximum load demand in MW.

    Returns:
        pd.Series: Simulated load demand in MWh per 15-minute interval.
    """
    timestamps = df["timestamp"]
    load_output = []

    for ts in timestamps:
        hour = ts.hour + ts.minute / 60
        day_of_week = ts.weekday()  # 0 = Monday, ..., 6 = Sunday

        # Daily demand shape: peaks in morning (~8am) and evening (~6pm)
        morning_peak = np.sin(np.pi * (hour - 6) / 16) ** 2
        evening_peak = np.sin(np.pi * (hour - 17) / 10) ** 2

        # Weekday/weekend adjustment
        weekday_factor = 1.0 if day_of_week < 5 else 0.75

        # Compute power (MW), capped by peak_mw
        power_mw = peak_mw * (morning_peak + evening_peak) * 0.5 * weekday_factor

        # Convert to MWh for 15-minute period
        energy_mwh = power_mw * 0.25
        load_output.append(energy_mwh)

    return pd.Series(load_output, index=df.index, name="load_demand_mwh")


def count_battery_cycles(soc_series: pd.Series, resolution_hours=0.25) -> pd.DataFrame:
    """
    Count full and partial battery charge cycles using rainflow analysis.

    Args:
        soc_series (pd.Series): State of charge time series.
        resolution_hours (float): Duration of each timestep in hours.

    Returns:
        pd.DataFrame: DataFrame with columns: ['depth', 'count', 'energy_mwh'].
    """
    cycles = rainflow.count_cycles(soc_series.values)
    df = pd.DataFrame(cycles, columns=["depth", "count"])
    df["energy_mwh"] = df["depth"] * df["count"] * resolution_hours
    return df


def calculate_utilization(df):
    """
    Calculate key battery utilization KPIs from simulation data.

    Args:
        df (pd.DataFrame): Must include 'discharge_mwh' and 'soc' columns.

    Returns:
        pd.DataFrame: Transposed DataFrame with metrics like FEC, average DoD, etc.
    """
    total_discharge = df["discharge_mwh"].sum()
    full_cycles = total_discharge / df["soc"].max()
    utilization = {
        "Full Equivalent Cycles": full_cycles,
        "Total Discharge (MWh)": total_discharge,
        "Avg Depth of Discharge per Action (MWh)": df["discharge_mwh"][
            df["discharge_mwh"] > 0
        ].mean(),
    }
    return pd.DataFrame([utilization], index=["Value"]).T


def summarize_simulation_operation_kpi(df: pd.DataFrame, model_col: str = "Model_Name"):
    """
    Summarize operational KPIs grouped by simulation model.

    Args:
        df (pd.DataFrame): Contains operation data by model.
        model_col (str): Column name indicating the model.

    Returns:
        pd.DataFrame: Summary DataFrame with metrics like energy import/export, SoC, etc.
    """
    grouped = df.groupby(model_col)
    summary = {}

    for model, group in grouped:
        summary[model] = {
            "Energy Imported (MWh)": group["from_grid_mwh"].sum(),
            "Energy Exported (MWh)": group["to_grid_mwh"].sum(),
            "Total Charge (MWh)": group["charge_mwh"].sum(),
            "Total Discharge (MWh)": group["discharge_mwh"].sum(),
            "Average SoC (MWh)": group["soc"].mean(),
        }

    return pd.DataFrame(summary)


def calculate_financial_kpis(
    df: pd.DataFrame,
    model_col: str = "Model_Name",
    initial_cost: float = None,
    power_mw: float = None,
) -> pd.DataFrame:
    """
    Calculate financial KPIs for each simulation model.

    Args:
        df (pd.DataFrame): Contains interval profit and cost data.
        model_col (str): Column name to group data by model.
        initial_cost (float): Initial investment cost in euros.
        power_mw (float): Battery power capacity in MW (for utilization metric).

    Returns:
        pd.DataFrame: Summary of financial KPIs for each model.
    """
    days = df["timestamp"].dt.date.nunique()

    grouped = df.groupby(model_col)
    summary = {}

    for model, group in grouped:
        revenue = group["revenue"].sum()
        cost = group["cost"].sum()
        degradation = group["degradation"].sum()
        total_profit = group["interval_profit"].sum()
        annualized_profit = total_profit / (len(group) * 0.25 / 24 / 365)
        payback_years = (
            initial_cost / annualized_profit if annualized_profit != 0 else float("inf")
        )
        roi = total_profit / initial_cost * 100
        energy_throughput = group["charge_mwh"].sum() + group["discharge_mwh"].sum()
        max_energy_possible = days * 24 * power_mw if power_mw else None

        kpis = {
            "Total Revenue (€)": revenue,
            "Total Grid Cost (€)": cost,
            "Total Degradation Cost (€)": degradation,
            "Total Profit (€)": total_profit,
            "Initial Cost (€)": initial_cost,
            "ROI (%)": roi,
            "Estimated Payback Time (Years)": payback_years,
            "Profit per MWh Cycled (€ / MWh)": (
                total_profit / energy_throughput if energy_throughput else None
            ),
            "Return on Energy (%)": ((revenue - cost) / cost) * 100 if cost else None,
            "Revenue-to-Cost Ratio": (
                revenue / (cost + degradation) if (cost + degradation) else None
            ),
            "Degradation Cost Share (%)": (
                (degradation / (cost + degradation)) * 100
                if (cost + degradation)
                else None
            ),
            "Energy Utilization (%)": (
                (energy_throughput / max_energy_possible) * 100
                if max_energy_possible
                else None
            ),
            "Average Daily Profit (€)": total_profit / days if days else None,
            "Profit Volatility (Std Dev)": group.groupby(group["timestamp"].dt.date)[
                "interval_profit"
            ]
            .sum()
            .std(),
        }

        summary[model] = kpis

    return pd.DataFrame(summary)
