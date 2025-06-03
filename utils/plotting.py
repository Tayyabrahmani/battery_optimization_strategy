import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import os

def plot_prices(df, title='Average Electricity Prices', y_column='price_eur_per_mwh', tickformat="%b %d\n%Y"):
    """
    Plot average electricity prices with consistent formatting.

    Parameters:
        df (pd.DataFrame): DataFrame indexed by timestamp with a column for price.
        title (str): Plot title.
        y_column (str): Name of the column containing price data.
    """
    fig = px.line(
        df,
        x=df.index,
        y=y_column,
        title=title,
        labels={'x': 'Date', y_column: 'Electricity Price [€/MWh]'}
    )

    # Dark yellow line
    fig.update_traces(line=dict(color='#f1c40f'))
   
    # Layout updates
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='black', family='Arial')
        ),
        xaxis=dict(
            title='Start Timestamp',
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=3, label="3d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            showgrid=True,
            tickformat=tickformat,
            tickangle=90
        ),
        yaxis=dict(
            title='Price [€/MWh]',
            showgrid=True,
        ),
        margin=dict(l=50, r=50, t=60, b=40),
        height=500,
        template='plotly_white'
    )

    return fig

def plot_boxplot_by_time_unit(df, time_unit='hour', price_col='price_eur_per_mwh', range_yaxis=[-200, 400]):
    """
    Plot a boxplot showing price distribution by hour of the day.

    Parameters:
        df (pd.DataFrame): DataFrame with a datetime index or column and a price column.
        timestamp_col (str): Name of the datetime column if not set as index.
        price_col (str): Name of the price column.
    """
    # Ensure timestamp is in a column for plotting

    # Add grouping variable
    if time_unit == 'hour':
        df['TimeGroup'] = df.index.hour
        x_label = 'Hour of Day'
        title = 'Price Distribution by Hour of Day'
    elif time_unit == 'weekday':
        df['TimeGroup'] = df.index.dayofweek
        df['TimeGroup'] = df['TimeGroup'].map({
            0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'
        })
        x_label = 'Day of Week'
        title = 'Price Distribution by Day of Week'
    else:
        raise ValueError("time_unit must be either 'hour' or 'weekday'")

    # Create the plot
    fig = px.box(
        df,
        x='TimeGroup',
        y=price_col,
        color='TimeGroup',
        title=title,
        labels={'TimeGroup': x_label, price_col: 'Price [€/MWh]'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    # Update layout
    fig.update_layout(
        title=dict(
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='black', family='Arial')
        ),
        xaxis=dict(
            title=dict(
                text="Start Timestamp",
                font=dict(size=14, color='black', family='Arial')
            ),
            tickfont=dict(size=12, color='black', family='Arial'),
            tickangle=90,
            showgrid=True,
            tickmode='linear',
            dtick=1,
        ),
        yaxis=dict(
            title=dict(
                text="Price [€/MWh]",
                font=dict(size=14, color='black', family='Arial')
            ),
            tickfont=dict(size=12, color='black', family='Arial'),
            showgrid=True,
            range=range_yaxis,
        ),
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=60, b=40)
    )

    return fig

def plot_charge_discharge_vs_price(df):
    fig = go.Figure()

    # Price (left axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["price_eur_per_mwh"],
        name="Price (€/MWh)",
        yaxis="y1",
        line=dict(color="black", width=2)
    ))

    # Charge (right axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["charge_mwh"] * 1000 / 0.25,
        name="Charge Power (kW)",
        yaxis="y2",
        line=dict(color="blue", width=2)
    ))

    # Discharge (right axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=-df["discharge_mwh"] * 1000 / 0.25,
        name="Discharge Power (kW)",
        yaxis="y2",
        line=dict(color="red", width=2)
    ))

    fig.update_layout(
        title=dict(
            text="⚡ Battery Charging/Discharging vs Market Price",
            x=0.5,
            xanchor="center",
            font=dict(size=18, family="Arial Black", color="black")
        ),
        font=dict(size=14, color="black"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                x=0.5,
                xanchor="center",
                font=dict(color="black"),
                bgcolor="rgba(0,0,0,0)"
            ),
        xaxis=dict(
            title=dict(text="Time", font=dict(color="black")),
            linecolor="black",
            linewidth=2,
            showgrid=True,
            gridcolor="#eee",
            tickfont=dict(color="black")
        ),
        yaxis=dict(
            title=dict(text="Price (€/MWh)", font=dict(color="black")),
            linecolor="black",
            linewidth=2,
            showgrid=True,
            gridcolor="#eee",
            tickfont=dict(color="black"),
            side="left"
        ),
        yaxis2=dict(
            title=dict(text="Power (kW)", font=dict(color="black")),
            linecolor="black",
            linewidth=2,
            showgrid=False,
            tickfont=dict(color="black"),
            overlaying="y",
            side="right"
        ),
        margin=dict(l=60, r=60, t=60, b=100),
        height=500
    )

    fig.show()

def plot_soc(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["soc"],
        mode="lines",
        name="State of Charge (MWh)",
        line=dict(color="green")
    ))

    fig.update_layout(
        title=dict(
            text="Battery SoC Over Time",
            x=0.5,
            xanchor="center",
            font=dict(size=18, color="black")
        ),
        xaxis=dict(
            title="Time",
            linecolor="black",
            tickfont=dict(color="black"),
            showgrid=True,
            gridcolor="#e5e5e5"
        ),
        yaxis=dict(
            title="SoC (MWh)",
            linecolor="black",
            tickfont=dict(color="black"),
            showgrid=True,
            gridcolor="#e5e5e5"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        margin=dict(l=50, r=50, t=50, b=50),
        height=400
    )

    fig.show()

def plot_monthly_cycles(df: pd.DataFrame, soc_max: float = None):
    """
    Plots monthly full equivalent battery cycles.

    Parameters:
    - df: DataFrame with 'timestamp', 'discharge_mwh', and 'soc' columns
    - soc_max: Optional, maximum SoC (defaults to max(df['soc']))
    """
    if soc_max is None:
        soc_max = df["soc"].max()

    df = df.copy()
    df['month'] = df['timestamp'].dt.to_period('M')

    monthly_discharge = df.groupby('month')["discharge_mwh"].sum()
    monthly_cycles = monthly_discharge / soc_max

    monthly_cycles.plot(kind="bar", title="Monthly Full Equivalent Cycles")
    plt.ylabel("Full Equivalent Cycles")
    plt.xlabel("Month")
    plt.tight_layout()
    plt.show()

    return monthly_cycles

def plot_line_over_time_by_category(
    df: pd.DataFrame,
    time_col: str = "timestamp",
    value_col: str = "cumulative_profit",
    model_col: str = "Model_Name",
    title: str = "Cumulative Profit Over Time"
):
    fig = go.Figure()

    for model in df[model_col].unique():
        model_df = df[df[model_col] == model]
        fig.add_trace(go.Scatter(
            x=model_df[time_col],
            y=model_df[value_col],
            mode="lines",
            name=str(model),
            hovertemplate=f"{model_col}: %{{text}}<br>{time_col}: %{{x}}<br>{value_col}: %{{y:.2f}}",
            text=[model] * len(model_df)
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=18, color="black")),
        xaxis=dict(
            title=time_col.capitalize(),
            linecolor="black",
            tickfont=dict(color="black"),
            showgrid=True,
            gridcolor="#eee"
        ),
        yaxis=dict(
            title=f"{value_col.replace('_', ' ').capitalize()}",
            linecolor="black",
            tickfont=dict(color="black"),
            showgrid=True,
            gridcolor="#eee"
        ),
        legend=dict(
            x=1.0,
            y=1.0,
            xanchor="right",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
        margin=dict(l=50, r=120, t=50, b=50),
        font=dict(color="black")
    )

    return fig

def plot_sensitivity_analysis(
    x_values,
    y_values,
    x_label="X Axis",
    y_label="Y Axis",
    title="Sensitivity Analysis",
    marker_color="blue",
    line_color="black"
):
    fig = go.Figure()

    # Add main line plot
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode="lines+markers",
        line=dict(color=line_color, width=2),
        marker=dict(color=marker_color, size=8),
        name="KPI"
    ))

    # Highlight max and min points
    max_idx = y_values.index(max(y_values))
    min_idx = y_values.index(min(y_values))

    fig.add_trace(go.Scatter(
        x=[x_values[max_idx]],
        y=[y_values[max_idx]],
        mode='markers+text',
        marker=dict(color='green', size=10),
        text=["Max"],
        textposition="top center",
        name="Max Profit"
    ))

    fig.add_trace(go.Scatter(
        x=[x_values[min_idx]],
        y=[y_values[min_idx]],
        mode='markers+text',
        marker=dict(color='red', size=10),
        text=["Min"],
        textposition="bottom center",
        name="Min Profit"
    ))

    # Layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=18, color="black")
        ),
        xaxis=dict(
            title=x_label,
            linecolor="black",
            tickfont=dict(color="black"),
            # titlefont=dict(color="black"),
            showgrid=True,
            gridcolor="#eee"
        ),
        yaxis=dict(
            title=y_label,
            linecolor="black",
            tickfont=dict(color="black"),
            # titlefont=dict(color="black"),
            showgrid=True,
            gridcolor="#eee"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(x=0.99, y=0.5, xanchor="right", yanchor="top"),
        height=500,
        margin=dict(l=60, r=60, t=60, b=60)
    )

    return fig

def plot_results(df, title, output_dir="results"):
    fig = go.Figure()

    # Add price trace (left y-axis)
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["cumulative_profit"],
        name="Cumulative Profit (€)",
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
            title="Cumulative Profit (€)",
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
    return fig
