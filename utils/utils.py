import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "browser"

def load_price_data(file_path):
    df = pd.read_csv(file_path, low_memory=False, usecols=[0,1,2])
    try:
        df['Start date'] = pd.to_datetime(df['Start date'], format="%b %d, %Y %I:%M %p")
        df['End date'] = pd.to_datetime(df['End date'], format="%b %d, %Y %I:%M %p")
        # df['Start date'] = pd.to_datetime(df['Start date'])
        # df['End date'] = pd.to_datetime(df['End date'])
    except Exception as e:
        print(e)

    df = df.rename(columns={"Germany/Luxembourg [€/MWh]": "price_eur_per_mwh"})
    # df['price_eur_per_kwh'] = df['price_eur_per_mwh'] * 1000

    # Assuming start time as the timestamp
    df['timestamp'] = df['Start date']
    return df

def get_results_path(model_name: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    return os.path.join(results_dir, f"{model_name.replace(' ', '_')}_results.csv")

def calculate_profit(df, efficiency, grid_fee_per_mwh, degradation_cost_per_mwh, pv_setup_cost_eur):
    df["revenue"] = df["discharge_mwh"] * efficiency * df["price_eur_per_mwh"]
    df["cost"] = df["from_grid_mwh"] * (df["price_eur_per_mwh"] + grid_fee_per_mwh)
    df["degradation"] = degradation_cost_per_mwh * (df["charge_mwh"] + df["discharge_mwh"])
    df["interval_profit"] = df["revenue"] - df["cost"] - df["degradation"]

    # Deduct setup cost once at the start
    if pv_setup_cost_eur > 0:
        df.at[0, "interval_profit"] -= pv_setup_cost_eur

    df["cumulative_profit"] = df["interval_profit"].cumsum()
    return df

def save_results_to_csv(df, file_path, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(file_path, index=False)
    print(f"Saved results to {file_path}")

def plot_results(df, title, output_dir="results"):
    fig = go.Figure()

    # Add price trace (left y-axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["price_eur_per_mwh"],
        name="Price per MWh",
        yaxis="y1",
        mode="lines"
    ))

    # Add soc trace (right y-axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["soc"],
        name="State of Charge (SOC)",
        yaxis="y2",
        mode="lines"
    ))

    # Update layout with two y-axes
    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Time",
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis=dict(
            title="Price per MWh",
            side="left"
        ),
        yaxis2=dict(
            title="SOC",
            overlaying="y",
            side="right"
        ),
        legend_title="Metric",
        height=500,
        width=1000
    )

    # Save plot as HTML
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{title.replace(' ', '_')}.html")
    fig.write_html(filename)
    print(f"Saved plot to {filename}")

    fig.show()

def simulate_pv_generation(df: pd.DataFrame, capacity_mw: float = 5.0) -> pd.Series:
    """
    Simulate PV generation [MWh per 15-min interval] for a given timestamped DataFrame.
    """
    timestamps = df["timestamp"]
    pv_output = []

    for ts in timestamps:
        hour = ts.hour + ts.minute / 60
        doy = ts.timetuple().tm_yday

        # Daily irradiance profile (0 at night, peak at noon)
        daylight_factor = max(0, np.sin(np.pi * (hour - 6) / 12))  # peak at 12:00
        seasonal_scaling = 0.9 + 0.1 * np.cos(2 * np.pi * (doy - 173) / 365)  # max in June

        # Simulated output power [MW]
        power_mw = capacity_mw * daylight_factor * seasonal_scaling

        # Convert to MWh over 15-minute period
        energy_mwh = power_mw * 0.25
        pv_output.append(energy_mwh)

    return pd.Series(pv_output, index=df.index, name="pv_generation_mwh")

def simulate_load_series(df: pd.DataFrame, peak_mw: float = 8.0) -> pd.Series:
    """
    Simulate non-shiftable load demand [MWh per 15-min interval] with a peak of 8 MW.
    Includes weekday/weekend variation and typical daily profile.
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
