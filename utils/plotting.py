import plotly.express as px

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

    fig.show()

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

    fig.show()
