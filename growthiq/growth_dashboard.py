import logging
import os
import json
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from plot_data import plot_fundamentals, plot_technical_chart

logging.basicConfig(level=logging.INFO)
st.set_page_config(layout="wide")

#####################################
# Sidebar + User Input
#####################################
st.sidebar.header("Screening Criteria")

market_indices = ['S&P500 Index', 'Dow Jones Industrial Index', 'NASDAQ Composite']
selected_market = st.sidebar.selectbox("Select Market Index", market_indices)

growth_type = st.sidebar.selectbox("Select Growth Type", ['QoQ', 'YoY'])

st.sidebar.subheader("Set Growth Thresholds (%) for Metrics")
revenue_growth_threshold = st.sidebar.number_input("Revenue Growth Threshold (%)", min_value=0, max_value=100, value=10, step=5)
net_income_growth_threshold = st.sidebar.number_input("Net Income Growth Threshold (%)", min_value=0, max_value=100, value=10, step=5)
fcf_growth_threshold = st.sidebar.number_input("Free Cash Flow Growth (%)", min_value=0, max_value=100, value=10, step=5)

rs_threshold = st.sidebar.slider("Relative Strength Threshold (%)", -50, 50, 0)
filter_logic = st.sidebar.selectbox("Screening Logic", ['ALL', 'ANY'])
run_screening = st.sidebar.button("RUN SCREENING")

index_file_map = {
    "S&P500 Index": "./growthiq/s&p500_index_data.json",
    "NASDAQ Composite": "./nasdaq_composite_data.json",
    "Dow Jones Industrial Index": "./dow_jones_industrial_index_data.json"
}

#####################################
# Ticker Utility Functions
#####################################
def get_tickers(market_index):
    """Scrape Wikipedia or CSV for your index components."""
    if market_index == 'S&P500 Index':
        comp_list = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        return comp_list
    elif market_index == 'Dow Jones Industrial Index':
        djia_tables = pd.read_html('https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average')
        comp_list = djia_tables[2]['Symbol'].tolist()
        return comp_list
    elif market_index == 'NASDAQ Composite':
        comp_list = pd.read_csv("nasdaq_components.csv")['Symbol'].to_list()
        return comp_list
    else:
        return []

def calculate_growth(series):
    """Compute QoQ & YoY growth from a sorted Series."""
    series = series.sort_index()
    qoQ_growth = series.pct_change(periods=1) * 100
    yoY_growth = series.pct_change(periods=4) * 100
    return qoQ_growth, yoY_growth

def calculate_relative_strength(stock_df, benchmark_df):
    """
    Calculate relative strength from 2 DataFrames with a 'Close' column.
    Both should have the same date index or be aligned.
    """
    stock_data, bench_data = stock_df.align(benchmark_df, join='inner', axis=0)
    if stock_data.empty or bench_data.empty:
        return None
    stock_return = (stock_data["Close"].iloc[-1] / stock_data["Close"].iloc[0]) - 1
    bench_return = (bench_data["Close"].iloc[-1] / bench_data["Close"].iloc[0]) - 1
    return (stock_return - bench_return) * 100.0

@st.cache_data(show_spinner=True)
def fetch_data_from_local_file(file_path):
    """Reads and returns JSON data from the specified local file path."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON file: {file_path}, {e}")
        return None

@st.cache_data(show_spinner=True)
def fetch_and_plot_data(ticker, period):
    """
    This function is still calling yfinance. 
    If you want 100% local data, remove yfinance calls 
    and load everything from your prefetched JSON instead.
    """
    stock = yf.Ticker(ticker)
    historical_data = stock.history(period=period)
    if historical_data.empty:
        return None, None

    # TA calculations
    historical_data['RSI'] = ta.rsi(historical_data['Close'])
    historical_data['SMA_20'] = ta.sma(historical_data['Close'], length=20)
    historical_data['SMA_50'] = ta.sma(historical_data['Close'], length=50)
    historical_data['SMA_200'] = ta.sma(historical_data['Close'], length=200)
    macd = ta.macd(historical_data['Close'])
    historical_data['MACD'] = macd['MACD_12_26_9']
    historical_data['MACD_Hist'] = macd['MACDh_12_26_9']

    financials = stock.quarterly_financials.T
    cashflow = stock.quarterly_cashflow.T

    financials.index = pd.to_datetime(financials.index, errors='coerce')
    cashflow.index = pd.to_datetime(cashflow.index, errors='coerce')

    fundamental_timeseries = pd.DataFrame(index=financials.index)
    fundamental_timeseries['Revenue'] = financials.get('Total Revenue')
    fundamental_timeseries['Net Income'] = financials.get('Net Income Common Stockholders')
    fundamental_timeseries['Free Cash Flow'] = cashflow.get('Free Cash Flow')
    fundamental_timeseries.dropna(how='all', inplace=True)

    if not historical_data.empty and not fundamental_timeseries.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_fundamentals = plot_fundamentals(fundamental_timeseries, historical_data)
            st.plotly_chart(fig_fundamentals, use_container_width=True)
        with col2:
            fig_technical = plot_technical_chart(historical_data)
            st.plotly_chart(fig_technical, use_container_width=True)
    else:
        st.warning("Data not available for this ticker.")

#####################################
# Main screening function
#####################################
@st.cache_data(show_spinner=True)
def fetch_and_process_data(
    tickers,
    growth_type,
    revenue_growth_threshold,
    net_income_growth_threshold,
    fcf_growth_threshold,
    rs_threshold,
    filter_logic,
    index_name="S&P500 Index"
):
    # 1. Load JSON
    data_file_path = index_file_map.get(index_name)
    if not data_file_path:
        st.error(f"No pre-fetched data file found for {index_name}.")
        return pd.DataFrame()

    data_list = fetch_data_from_local_file(data_file_path)
    if not data_list:
        st.error("No data available after fetching.")
        return pd.DataFrame()

    # 2. Separate out the benchmark (e.g. ^GSPC) from the data list
    #    This assumes you've appended ^GSPC in your prefetch script for S&P,
    #    ^IXIC for NASDAQ, ^DJI for Dow, etc.
    benchmark_ticker_map = {
        "S&P500 Index": "^GSPC",
        "NASDAQ Composite": "^IXIC",
        "Dow Jones Industrial Index": "^DJI"
    }
    bench_symbol = benchmark_ticker_map.get(index_name, None)

    benchmark_hist = None
    if bench_symbol:
        # find the benchmark item
        for item in data_list:
            if item["Ticker"] == bench_symbol:
                # build a DataFrame for the benchmark's historical data
                bm_df = pd.DataFrame(item["HistoricalData"]).set_index("Date")
                bm_df.index = pd.to_datetime(bm_df.index, errors="coerce")
                bm_df = bm_df[["Close"]].dropna()
                benchmark_hist = bm_df
                break

    # If we can't find or didn't fetch the benchmark, you can handle that:
    if benchmark_hist is None:
        st.warning("No local benchmark data found. Relative Strength can't be computed.")
        # We'll set a placeholder so we can skip the RS calculation

    # 3. Build results by filtering the relevant tickers
    results = []
    for entry in data_list:
        ticker = entry['Ticker']
        if ticker not in tickers:
            continue
        # Also skip if this is the benchmark itself
        if ticker == bench_symbol:
            continue

        company_name = entry['Info'].get('longName', ticker)

        # Convert financial data to DataFrames
        try:
            fin_df = pd.DataFrame(entry['Financials'])[['Total Revenue', 'Net Income']].dropna()
        except KeyError:
            logging.warning(f"Ticker {ticker}: missing 'Total Revenue'/'Net Income'. Skipping.")
            continue

        try:
            cf_df = pd.DataFrame(entry['Cashflow'])[['Free Cash Flow']].dropna()
        except KeyError:
            logging.warning(f"Ticker {ticker}: missing 'Free Cash Flow'. Skipping.")
            continue

        fin_df.index = pd.to_datetime(fin_df.index, errors='coerce')
        cf_df.index = pd.to_datetime(cf_df.index, errors='coerce')
        fin_df.dropna(inplace=True)
        cf_df.dropna(inplace=True)

        # Extract required series
        revenue = fin_df['Total Revenue']
        net_income = fin_df['Net Income']
        free_cash_flow = cf_df['Free Cash Flow']

        if revenue.empty or net_income.empty:
            logging.warning(f"Ticker {ticker}: no revenue or net income data. Skipping.")
            continue
        if revenue.iloc[-1] <= 0 or net_income.iloc[-1] <= 0:
            logging.warning(f"Ticker {ticker} has non-positive revenue or net income. Skipping.")
            continue

        # Growth rates
        rev_qoq, rev_yoy = calculate_growth(revenue)
        ni_qoq, ni_yoy = calculate_growth(net_income)
        fcf_qoq, fcf_yoy = calculate_growth(free_cash_flow)

        if growth_type == 'QoQ':
            revenue_growth = rev_qoq
            net_income_growth = ni_qoq
            fcf_growth = fcf_qoq
        else:
            revenue_growth = rev_yoy
            net_income_growth = ni_yoy
            fcf_growth = fcf_yoy

        # Latest growth
        revenue_growth_latest = revenue_growth.iloc[-1] if not revenue_growth.empty else None
        net_income_growth_latest = net_income_growth.iloc[-1] if not net_income_growth.empty else None
        fcf_growth_latest = fcf_growth.iloc[-1] if not fcf_growth.empty else None

        if any(x is None for x in [revenue_growth_latest, net_income_growth_latest, fcf_growth_latest]):
            logging.warning(f"Growth data incomplete for {ticker}. Skipping.")
            continue

        # 4. Historical Price Data for the ticker
        hd = pd.DataFrame(entry['HistoricalData']).set_index("Date")
        hd.index = pd.to_datetime(hd.index, errors='coerce')
        hd = hd[["Close"]].dropna()
        if hd.empty:
            logging.warning(f"No historical data for {ticker}. Skipping.")
            continue

        # 5. Calculate Relative Strength (if we have a benchmark)
        if benchmark_hist is not None and not benchmark_hist.empty:
            relative_strength = calculate_relative_strength(hd, benchmark_hist)
        else:
            relative_strength = None

        # Extract additional metrics
        pe_ratio = entry['Info'].get('trailingPE')
        debt_to_equity = entry['Info'].get('debtToEquity')
        roe = entry['Info'].get('returnOnEquity')
        if roe is not None:
            roe *= 100
        dividend_yield = entry['Info'].get('dividendYield')
        if dividend_yield is not None:
            dividend_yield *= 100

        market_cap = entry['Info'].get('marketCap', 'Unknown')
        sector = entry['Info'].get('sector', 'Unknown')

        # Calculate SMAs from the prefetched data
        hd['SMA_20'] = ta.sma(hd['Close'], length=20)
        hd['SMA_50'] = ta.sma(hd['Close'], length=50)
        hd['SMA_200'] = ta.sma(hd['Close'], length=200)

        latest_price = hd['Close'].iloc[-1]
        sma_20 = hd['SMA_20'].iloc[-1]
        sma_50 = hd['SMA_50'].iloc[-1]
        sma_200 = hd['SMA_200'].iloc[-1]

        price_above_sma20_flag = (latest_price > sma_20) if pd.notna(sma_20) else False
        price_above_sma50_flag = (latest_price > sma_50) if pd.notna(sma_50) else False
        price_above_sma200_flag = (latest_price > sma_200) if pd.notna(sma_200) else False

        results.append({
            'Ticker': ticker,
            'Company Name': company_name,
            'Revenue Growth': revenue_growth_latest,
            'Net Income Growth': net_income_growth_latest,
            'Free Cash Flow Growth': fcf_growth_latest,
            'Relative Strength': relative_strength,
            'P/E Ratio': pe_ratio,
            'Debt-to-Equity': debt_to_equity,
            'ROE': roe,
            'Market Cap': market_cap,
            'Sector': sector,
            'Price Above SMA 20': price_above_sma20_flag,
            'Price Above SMA 50': price_above_sma50_flag,
            'Price Above SMA 200': price_above_sma200_flag
        })

    df = pd.DataFrame(results)
    if df.empty:
        st.error("No data available after processing. Please check the data and try again.")
        return df

    # Fill / handle missing values
    df['Revenue Growth'] = df['Revenue Growth'].fillna(0)
    df['Net Income Growth'] = df['Net Income Growth'].fillna(0)
    df['Free Cash Flow Growth'] = df['Free Cash Flow Growth'].fillna(0)
    df['Relative Strength'] = df['Relative Strength'].fillna(-999)

    # Screening thresholds
    conditions = []
    if revenue_growth_threshold is not None:
        conditions.append(df['Revenue Growth'] >= revenue_growth_threshold)
    if net_income_growth_threshold is not None:
        conditions.append(df['Net Income Growth'] >= net_income_growth_threshold)
    if fcf_growth_threshold is not None:
        conditions.append(df['Free Cash Flow Growth'] >= fcf_growth_threshold)
    conditions.append(df['Relative Strength'] >= rs_threshold)

    # Combine conditions
    if filter_logic == 'ALL':
        combined_condition = pd.Series(True, index=df.index)
        for cond in conditions:
            combined_condition &= cond
    else:
        combined_condition = pd.Series(False, index=df.index)
        for cond in conditions:
            combined_condition |= cond

    screened_df = df[combined_condition]
    return screened_df

#####################################
# Run Screening Button
#####################################
if run_screening:
    with st.spinner('Running screening...'):
        tickers = get_tickers(selected_market)
        screened_data = fetch_and_process_data(
            tickers,
            growth_type,
            revenue_growth_threshold,
            net_income_growth_threshold,
            fcf_growth_threshold,
            rs_threshold,
            filter_logic,
            selected_market
        )
        screened_data.to_json('screened_data.json', orient='records')
    st.success('Screening completed and data saved!')

#####################################
# Load + Display Results
#####################################
def load_screened_data():
    if os.path.exists('screened_data.json'):
        return pd.read_json('screened_data.json')
    else:
        st.error("No screened data found. Please run the screening first.")
        return None

if 'disable_view_filter_controls' not in st.session_state:
    st.session_state.disable_view_filter_controls = False
if 'show_filtering' not in st.session_state:
    st.session_state.show_filtering = False

view_screening = st.sidebar.checkbox("Show Screening Result", value=True)
view_filter_controls = st.sidebar.checkbox("Show Filter Controls", value=False, disabled=st.session_state.disable_view_filter_controls)
show_filtering = st.sidebar.checkbox("Show Filtering Result", value=st.session_state.show_filtering)

screened_data = load_screened_data()

if view_screening:
    with st.expander("View Screening Result", expanded=True):
        if screened_data is not None and not screened_data.empty:
            st.subheader("Screened results")
            st.write(screened_data)
        else:
            logging.warning("Screened data is empty")

# Additional filtering logic...
# If there's screened data, allow further filtering
if screened_data is not None and not screened_data.empty:
    # Collapsible filters
    if view_filter_controls:
        with st.expander("View Screening Result", expanded=True):
            # Technical Indicators
            st.sidebar.subheader("Technical Indicators")
            price_above_sma20 = st.sidebar.checkbox("Price Above SMA 20")
            price_above_sma50 = st.sidebar.checkbox("Price Above SMA 50")
            price_above_sma200 = st.sidebar.checkbox("Price Above SMA 200")
            rsi_overbought = st.sidebar.checkbox("RSI Overbought (>70)")
            rsi_oversold = st.sidebar.checkbox("RSI Oversold (<30)")

            # Sector Filter
            sectors = ['All'] + sorted(screened_data['Sector'].dropna().unique().tolist())
            try:
                selected_sector = st.sidebar.selectbox("Select Sector", sectors)
            except Exception:
                logging.warning("Sector select error ")
                selected_sector = 'All'

            # Logic Selection for Filtering: AND or OR
            filter_logic_filtering = st.sidebar.selectbox("Filtering Logic", ['ALL', 'ANY'])

            # Apply filters
            def apply_filters(df):
                conditions = []
                
                # Technical Filters
                if price_above_sma20:
                    conditions.append(df['Price Above SMA 20'] == True)
                if price_above_sma50:
                    conditions.append(df['Price Above SMA 50'] == True)
                if price_above_sma200:
                    conditions.append(df['Price Above SMA 200'] == True)

                # Sector Filter
                if selected_sector != 'All':
                    conditions.append(df['Sector'] == selected_sector)

                # Combine conditions with logical AND or OR
                if filter_logic_filtering == 'ALL':
                    combined_condition = pd.Series(True, index=df.index)
                    for condition in conditions:
                        combined_condition &= condition
                else:
                    combined_condition = pd.Series(False, index=df.index)
                    for condition in conditions:
                        combined_condition |= condition

                # Apply the combined conditions
                filtered_df = df[combined_condition]
                return filtered_df

            filtered_data = apply_filters(screened_data)
    else:
        filtered_data = screened_data.copy()
else:
    st.write("Please set the screening criteria and click 'RUN SCREENING' to begin.")
    filtered_data = None

# Handling the "Show Filtering Result" checkbox
if show_filtering and view_filter_controls:
    with st.expander("View Filtering Result", expanded=True):
        if filtered_data is None or filtered_data.empty:
            st.write("No tickers match the selected filters.")
        else:
            # Sidebar for selecting the ticker and time period
            tickers_list = filtered_data['Ticker'].tolist()
            company_names = dict(zip(filtered_data['Ticker'], filtered_data['Company Name']))

            selected_ticker = st.sidebar.selectbox("Select a Ticker", tickers_list)
            selected_period = st.sidebar.selectbox("Select Time Period", ['6mo', '1y', '5y', 'max'])

            # Display the filtered results
            st.subheader("Filtered Results")
            st.dataframe(
                filtered_data[
                    ['Ticker', 'Company Name', 'Revenue Growth', 'Net Income Growth',
                     'Free Cash Flow Growth', 'Relative Strength', 'Market Cap', 'Sector']
                ]
            )

            # Display charts for selected ticker
            if selected_ticker:
                st.subheader(f"{company_names[selected_ticker]} ({selected_ticker})")
                fetch_and_plot_data(selected_ticker, selected_period)
else:
    st.warning(
        "Select filtering options from Filter Controls. "
        "Then select 'Show Filtering Result' to view filtered data."
    )
