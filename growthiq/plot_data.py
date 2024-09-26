
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Plot fundamental data with price overlay
def plot_fundamentals(fundamental_timeseries, historical_data):
    # Create figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar traces for Revenue, Net Income, Free Cash Flow
    fig.add_trace(
        go.Bar(
            x=fundamental_timeseries.index,
            y=fundamental_timeseries['Revenue'],
            name='Revenue',
            marker_color='blue',
            opacity=0.6
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=fundamental_timeseries.index,
            y=fundamental_timeseries['Net Income'],
            name='Net Income',
            marker_color='green',
            opacity=0.6
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=fundamental_timeseries.index,
            y=fundamental_timeseries['Free Cash Flow'],
            name='Free Cash Flow',
            marker_color='purple',
            opacity=0.6
        ),
        secondary_y=False,
    )

    # Overlay price data
    price_data = historical_data['Close']
    # Resample price data to match fundamental data frequency
    price_data = price_data.resample('Q').last()
    fig.add_trace(
        go.Scatter(
            x=price_data.index,
            y=price_data.values,
            name='Close Price',
            mode='lines',
            line=dict(color='royalblue', width=2),
            opacity=0.7
        ),
        secondary_y=True,
    )

    # Update layout
    fig.update_layout(
        title="Fundamental Data with Price Overlay",
        xaxis_title='Date',
        yaxis_title='Fundamental Metrics',
        yaxis2_title='Close Price',
        legend=dict(x=0, y=1.1, orientation='h'),
        height=600,
        barmode='group',
    )

    return fig

# Plot comprehensive technical chart
def plot_technical_chart(historical_data):
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.4, 0.2, 0.2, 0.2],
    )

    # Price with SMA50 and SMA200
    fig.add_trace(
        go.Scatter(
            x=historical_data.index,
            y=historical_data['Close'],
            name='Close Price',
            line=dict(color='blue')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=historical_data.index,
            y=historical_data['SMA_50'],
            name='SMA 50',
            line=dict(color='orange')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=historical_data.index,
            y=historical_data['SMA_200'],
            name='SMA 200',
            line=dict(color='green')
        ),
        row=1, col=1
    )

    # Volume
    fig.add_trace(
        go.Bar(
            x=historical_data.index,
            y=historical_data['Volume'],
            name='Volume',
            marker_color='gray',
            opacity=0.5
        ),
        row=2, col=1
    )

    # RSI
    fig.add_trace(
        go.Scatter(
            x=historical_data.index,
            y=historical_data['RSI'],
            name='RSI',
            line=dict(color='purple')
        ),
        row=3, col=1
    )
    # Add overbought/oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # MACD Histogram
    fig.add_trace(
        go.Bar(
            x=historical_data.index,
            y=historical_data['MACD_Hist'],
            name='MACD Histogram',
            marker_color='red',
        ),
        row=4, col=1
    )

    # Update layout
    fig.update_layout(
        height=900,
        title="Technical Analysis Chart",
        xaxis_title='Date',
        legend=dict(orientation='h', x=0, y=1.02),
    )

    # Update y-axes titles
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_yaxes(title_text="MACD Hist", row=4, col=1)

    return fig
