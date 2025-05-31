import os
import pandas as pd
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

def calculate_profit(df, efficiency, grid_fee_per_mwh, degradation_cost_per_mwh):
    # Calculate profits
    df["revenue"] = df["discharge_mwh"] * efficiency * df["price_eur_per_mwh"]
    df["cost"] = df['charge_mwh'] * (df['price_eur_per_mwh'] + grid_fee_per_mwh)
    df["degradation"] = degradation_cost_per_mwh * (df['charge_mwh'] + df['discharge_mwh'])
    df['interval_profit'] = df['revenue'] - df['cost'] - df['degradation']
    df['cumulative_profit'] = df['interval_profit'].cumsum()
    return df

def save_results_to_csv(df, model_name, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{model_name.replace(' ', '_')}_results.csv")
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
