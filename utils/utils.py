import pandas as pd
import plotly.graph_objects as go

def load_price_data(file_path):
    df = pd.read_csv(file_path)
    df = df[['Start date', 'End date', 'Germany/Luxembourg [€/MWh]']]
    df['Start date'] = pd.to_datetime(df['Start date'], format="%b %d, %Y %I:%M %p")
    df['End date'] = pd.to_datetime(df['End date'], format="%b %d, %Y %I:%M %p")
    df = df.rename(columns={"Germany/Luxembourg [€/MWh]": "price_eur_per_mwh"})
    df['price_eur_per_kwh'] = df['price_eur_per_mwh'] * 1000

    # Assuming start time as the timestamp
    df['timestamp'] = df['Start date']
    return df

def plot_results(df):
    fig = go.Figure()

    # Add price trace (left y-axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["price"],
        name="Price",
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
        title="Battery Operation: State of Charge and Price",
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
            title="Price",
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

    fig.show()
