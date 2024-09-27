import requests
import logging
import os
import json
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from plot_data import plot_fundamentals, plot_technical_chart

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set page configuration
st.set_page_config(layout="wide")

# Sidebar for Screening Criteria
st.sidebar.header("Screening Criteria")

# Market Index Selection
market_indices = ['S&P500 Index', 'Dow Jones Industrial Index', 'NASDAQ Composite']
selected_market = st.sidebar.selectbox("Select Market Index", market_indices)

# Growth Type
growth_type = st.sidebar.selectbox("Select Growth Type", ['QoQ', 'YoY'])

# Growth Thresholds for Metrics
st.sidebar.subheader("Set Growth Thresholds (%) for Metrics")
revenue_growth_threshold = st.sidebar.number_input("Revenue Growth Threshold (%)", min_value=0, max_value=100, value=10, step=5)
net_income_growth_threshold = st.sidebar.number_input("Net Income Growth Threshold (%)", min_value=0, max_value=100, value=10, step=5)
fcf_growth_threshold = st.sidebar.number_input("Free Cash Flow Growth (%)", min_value=0, max_value=100, value=10, step=5)

# Relative Strength Threshold
rs_threshold = st.sidebar.slider("Relative Strength Threshold (%)", -50, 50, 0)

# Logic Selection: AND or OR
filter_logic = st.sidebar.selectbox("Screening Logic", ['ALL', 'ANY'])

# Button to run the screening
run_screening = st.sidebar.button("RUN SCREENING")


# Function to fetch JSON data from URL
def fetch_data_from_azure_blob(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()  # Parse the JSON content
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data: {e}")
        return None

# Load and cache the screened data for performance
@st.cache_data
def load_screened_data():
    if os.path.exists('screened_data.json'):
        return pd.read_json('screened_data.json')
    else:
        st.error("No screened data found. Please run the screening first.")
        return None

# Function to get tickers for the selected market index
def get_tickers(market_index):
    if market_index == 'S&P500 Index':
        comp_list = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        print(comp_list)
        return comp_list
    elif market_index == 'Dow Jones Industrial Index':
        comp_list = pd.read_html('https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average')[1]['Symbol'].tolist()
        print("Dow Jones Industrial Companies")
        print(comp_list)
        return comp_list
    elif market_index == 'NASDAQ Composite':
        # For NASDAQ Composite, we'll use a sample due to the large number of tickers
        comp_list = pd.read_csv("nasdaq_components.csv")['Symbol'].to_list()
        print(comp_list)
        return comp_list
    else:
        return []

# Function to calculate QoQ and YoY growth
def calculate_growth(series):
    series = series.sort_index()
    qoQ_growth = series.pct_change(periods=1) * 100  # Quarter over Quarter
    yoY_growth = series.pct_change(periods=4) * 100  # Year over Year
    return qoQ_growth, yoY_growth

# Function to calculate relative strength from data
def calculate_relative_strength_from_data(historical_data, benchmark_data=None):
    # If benchmark data is not provided, fetch S&P 500 data
    if benchmark_data is None:
        benchmark = yf.Ticker('^GSPC')
        benchmark_data = benchmark.history(period='1y')
        benchmark_data = pd.Series(benchmark_data['Close'])
    
    stock_data = pd.Series(historical_data['Close'])
    
    # Align dates
    stock_data, benchmark_data = stock_data.align(benchmark_data, join='inner', axis=0)
    # Calculate cumulative returns
    stock_return = (stock_data.iloc[-1] / stock_data.iloc[0]) - 1
    benchmark_return = (benchmark_data.iloc[-1] / benchmark_data.iloc[0]) - 1
    # Calculate relative strength
    relative_strength = (stock_return - benchmark_return) * 100  # In percentage
    return relative_strength

# Fetch data for the selected ticker and time period
@st.cache_data(show_spinner=True)
def fetch_and_plot_data(ticker, period):
    stock = yf.Ticker(ticker)
    print(stock)
    historical_data = stock.history(period=period)
    if historical_data.empty:
        return None, None
    # Calculate technical indicators
    historical_data['RSI'] = ta.rsi(historical_data['Close'])
    historical_data['SMA_20'] = ta.sma(historical_data['Close'], length=20)
    historical_data['SMA_50'] = ta.sma(historical_data['Close'], length=50)
    historical_data['SMA_200'] = ta.sma(historical_data['Close'], length=200)
    macd = ta.macd(historical_data['Close'])
    historical_data['MACD'] = macd['MACD_12_26_9']
    historical_data['MACD_Hist'] = macd['MACDh_12_26_9']

    # Fetch historical fundamental data (quarterly)
    financials = stock.quarterly_financials
    cashflow = stock.quarterly_cashflow

    # Transpose and format financials data
    financials = financials.T
    financials.index = pd.to_datetime(financials.index, errors='coerce')
    cashflow = cashflow.T
    cashflow.index = pd.to_datetime(cashflow.index, errors='coerce')

    # Merge financial data
    fundamental_timeseries = pd.DataFrame(index=financials.index)
    fundamental_timeseries['Revenue'] = financials.get('Total Revenue')
    fundamental_timeseries['Net Income'] = financials.get('Net Income Common Stockholders')
    fundamental_timeseries['Free Cash Flow'] = cashflow.get('Free Cash Flow')

    # Drop rows with all NaN values
    fundamental_timeseries.dropna(how='all', inplace=True)

    if historical_data is not None and fundamental_timeseries is not None:
        # Create two columns for the charts
        col1, col2 = st.columns(2)

        # Left Column: Fundamental Data Chart
        with col1:
            fig_fundamentals = plot_fundamentals(fundamental_timeseries, historical_data)
            st.plotly_chart(fig_fundamentals, use_container_width=True)

        # Right Column: Technical Analysis Chart
        with col2:
            fig_technical = plot_technical_chart(historical_data)
            st.plotly_chart(fig_technical, use_container_width=True)
    else:
        st.warning("Data not available for this ticker.")

# Function to fetch and process pre-fetched data
@st.cache_data(show_spinner=True)
def fetch_and_process_data(
    tickers,
    growth_type,
    revenue_growth_threshold,
    net_income_growth_threshold,
    fcf_growth_threshold,
    rs_threshold,
    filter_logic,
    index_name="S&P500 Index"  # You can choose between S&P500, NASDAQ, or Dow Jones
):
    # Map index name to corresponding pre-fetched data file (URLs)
    index_file_map = {
        "S&P500 Index": "https://stocktickerdata.blob.core.windows.net/stocktickerdata/s&p500_index_data.json",
        "NASDAQ Composite": "https://stocktickerdata.blob.core.windows.net/stocktickerdata/nasdaq_composite_data.json",
        "Dow Jones Industrial Index": "https://stocktickerdata.blob.core.windows.net/stocktickerdata/dow_jones_industrial_index_data.json"
    }

    # Get the appropriate file for the selected index
    data_file_url = index_file_map.get(index_name)

    if not data_file_url:
        st.error(f"No pre-fetched data file found for {index_name}.")
        return pd.DataFrame()

    # Fetch data from the URL
    data_list = fetch_data_from_azure_blob(data_file_url)

    # Convert JSON to DataFrame
    if data_list:
        df = pd.DataFrame(data_list)
    else:
        st.error("No data available after fetching.")
        return pd.DataFrame()

    # Filter the data for the selected tickers
    results = []
    for data in data_list:
        if data['Ticker'] not in tickers:
            continue
        else:
            ticker = data['Ticker']
            company_name = data['Info'].get('longName', data['Ticker'])
            
            # Convert financial data back to DataFrames
            try:
                financials = pd.DataFrame(data['Financials'])[['Total Revenue', 'Net Income']].dropna()
            except Exception as e:
                logging.warning(f"Ticker {ticker} for {company_name} error")
                logging.warning(f"financial data Total Revenue or Net Income is not available")
                continue
            try:
                cashflow = pd.DataFrame(data['Cashflow'])[['Free Cash Flow']].dropna()
            except Exception as e:
                logging.warning(f"Ticker {ticker} for {company_name} error")
                logging.warning("financial data Cashflow is not available")
                continue
                
            # Convert index to datetime
            financials.index = pd.to_datetime(financials.index, errors='coerce')
            cashflow.index = pd.to_datetime(cashflow.index, errors='coerce')

            # Drop rows with NaT in index
            financials.dropna(inplace=True)
            cashflow.dropna(inplace=True)

            # Extract required metrics
            revenue = financials['Total Revenue']
            net_income = financials['Net Income']
            free_cash_flow = cashflow['Free Cash Flow']

            # Skip companies with negative or zero revenue and net income
            if revenue.iloc[-1] <= 0 or net_income.iloc[-1] <= 0:
                logging.warning(f"Ticker {ticker} for {company_name} has non-positive revenue or net income. Skipping.")
                continue

            # Calculate growth rates (QoQ or YoY)
            revenue_qoq, revenue_yoy = calculate_growth(revenue)
            net_income_qoq, net_income_yoy = calculate_growth(net_income)
            fcf_qoq, fcf_yoy = calculate_growth(free_cash_flow)
           # Select the growth rate based on growth type
            if growth_type == 'QoQ':
                revenue_growth = revenue_qoq
                net_income_growth = net_income_qoq
                fcf_growth = fcf_qoq
            else:
                revenue_growth = revenue_yoy
                net_income_growth = net_income_yoy
                fcf_growth = fcf_yoy

            #print(revenue_growth, net_income_growth, fcf_growth)

            # Get the latest growth values
            revenue_growth_latest = revenue_growth.iloc[-1] if not revenue_growth.empty else None
            net_income_growth_latest = net_income_growth.iloc[-1] if not net_income_growth.empty else None
            fcf_growth_latest = fcf_growth.iloc[-1] if not fcf_growth.empty else None
            # Check if growth values are not None
            if revenue_growth_latest is None or net_income_growth_latest is None or fcf_growth_latest is None:
                logging.warning(f"Growth data for {ticker} is incomplete. Skipping.")
                continue

            # Fetch historical data
            # Fix the order of arguments and handle DataFrame construction properly
            historical_data = pd.DataFrame(data['HistoricalData']).set_index('Date')[['Close', 'Volume']].dropna()
            historical_data.index = pd.to_datetime(historical_data.index, utc=True)  # Ensure it's datetime with UTC
            #print("historical data ", historical_data)
            if historical_data.empty:
                logging.warning(f"No historical data for {ticker}. Skipping.")
                continue

            # Calculate relative strength
            relative_strength = calculate_relative_strength_from_data(historical_data)
            # Extract additional metrics from the pre-fetched data

            pe_ratio = data['Info'].get('trailingPE')
            debt_to_equity = data['Info'].get('debtToEquity')

            roe = data['Info'].get('returnOnEquity') * 100 if data['Info'].get('returnOnEquity') else None
            dividend_yield = data['Info'].get('dividendYield') * 100 if data['Info'].get('dividendYield') else None
            
            market_cap = data['Info'].get('marketCap', 'Unknown')
            total_cash = data['Info'].get('totalCash', 'Unknown')
            sector = data['Info'].get('sector', 'Unknown')  # Default to 'Unknown' if the sector is not available
            
            # Calculate SMAs
            historical_data['SMA_20'] = ta.sma(historical_data['Close'], length=20)
            historical_data['SMA_50'] = ta.sma(historical_data['Close'], length=50)
            historical_data['SMA_200'] = ta.sma(historical_data['Close'], length=200)

            # Get latest price and SMAs
            latest_price = historical_data['Close'].iloc[-1]
            sma_20 = historical_data['SMA_20'].iloc[-1]
            sma_50 = historical_data['SMA_50'].iloc[-1]
            sma_200 = historical_data['SMA_200'].iloc[-1]

            # Check if price is above SMAs
            price_above_sma20_flag = latest_price > sma_20 if not pd.isna(sma_20) else False
            price_above_sma50_flag = latest_price > sma_50 if not pd.isna(sma_50) else False
            price_above_sma200_flag = latest_price > sma_200 if not pd.isna(sma_200) else False

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

        #except Exception as e:
        #    logging.error(f"Error processing data for {ticker}: {e}")

    # Convert to DataFrame for easier filtering
    df = pd.DataFrame(results)

    if df.empty:
        st.error("No data available after processing. Please check the data and try again.")
        return df  # Return the empty DataFrame

    # Fill missing values
    df['Revenue Growth'] = df['Revenue Growth'].dropna()
    df['Net Income Growth'] = df['Net Income Growth'].dropna()
    df['Free Cash Flow Growth'] = df['Free Cash Flow Growth'].dropna()
    df['Relative Strength'] = df['Relative Strength'].dropna()

    # Apply initial screening thresholds
    conditions = []

    if revenue_growth_threshold is not None:
        conditions.append(df['Revenue Growth'] >= revenue_growth_threshold)

    if net_income_growth_threshold is not None:
        conditions.append(df['Net Income Growth'] >= net_income_growth_threshold)

    if fcf_growth_threshold is not None:
        conditions.append(df['Free Cash Flow Growth'] >= fcf_growth_threshold)

    # Apply relative strength threshold
    conditions.append(df['Relative Strength'] >= rs_threshold)

    # Combine conditions based on selected logic
    if filter_logic == 'ALL':
        combined_condition = pd.Series(True, index=df.index)
        for condition in conditions:
            combined_condition &= condition
    else:
        combined_condition = pd.Series(False, index=df.index)
        for condition in conditions:
            combined_condition |= condition

    # Apply combined condition
    screened_df = df[combined_condition]

    return screened_df

# Main part of the app
# Initialize session state variables
if 'disable_view_filter_controls' not in st.session_state:
    st.session_state.disable_view_filter_controls = False

if 'show_filtering' not in st.session_state:
    st.session_state.show_filtering = False

# Checkboxes to enable/disable components
view_screening = st.sidebar.checkbox("Show Screening Result", value=True)
view_filter_controls = st.sidebar.checkbox(
    "Show Filter Controls", 
    value=False, 
    disabled=st.session_state.disable_view_filter_controls
)
show_filtering = st.sidebar.checkbox(
    "Show Filtering Result", 
    value=st.session_state.show_filtering
)

# Run screening when button is pressed
if run_screening:
    with st.spinner('Running screening...'):
        print("Selected market ", selected_market)
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
        # Save screened data to JSON
        screened_data.to_json('screened_data.json', orient='records')
        # Clear cache to ensure new data is loaded
        st.cache_data.clear()

    st.success('Screening completed and data saved!')
    screened_data = load_screened_data()

screened_data = load_screened_data()

# Collapsible table section
if view_screening:
    screened_data = load_screened_data()
    with st.expander("View Screening Result", expanded=True):
        if not screened_data.empty:
            st.subheader("Screened results")
            st.write(screened_data)  # Display all the screened data without any filtering
            first_ticker = screened_data['Ticker'].to_list()[0]
            company_name = dict(zip(screened_data['Ticker'], screened_data['Company Name']))[first_ticker]
            # Clear the cache to load new data
            st.cache_data.clear()
        else:
            logging.warning("Screened data is empty")

# Load the screened data after screening
screened_data = load_screened_data()

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
            except Exception as e:
                logging.warning("Sector select error ")
                
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

                # Apply the combined conditions to filter the DataFrame
                filtered_df = df[combined_condition]
                return filtered_df

            print("screened_data ", screened_data)
            filtered_data = apply_filters(screened_data)
        
else:
    st.write("Please set the screening criteria and click 'RUN SCREENING' to begin.")
    screened_data = load_screened_data()


# Handling the "Show Filtering Result" checkbox and disabling filter controls
if show_filtering and view_filter_controls:
    with st.expander("View Filtering Result", expanded=True):
        #st.session_state.show_filtering = True  # Update the state

        if filtered_data.empty:
            st.write("No tickers match the selected filters.")
        else:
            # Sidebar for selecting the ticker and time period
            tickers = filtered_data['Ticker'].tolist()
            company_names = dict(zip(filtered_data['Ticker'], filtered_data['Company Name']))

            selected_ticker = st.sidebar.selectbox("Select a Ticker", tickers)
            selected_period = st.sidebar.selectbox("Select Time Period", ['6mo', '1y', '5y', 'max'])

            # Display the filtered results
            st.subheader("Filtered Results")
            st.dataframe(filtered_data[['Ticker', 'Company Name', 'Revenue Growth', 'Net Income Growth', 'Free Cash Flow Growth', 'Relative Strength', 'Market Cap', 'Sector']])

            # Display charts for selected ticker
            if selected_ticker:
                st.subheader(f"{company_names[selected_ticker]} ({selected_ticker})")
                fetch_and_plot_data(selected_ticker, selected_period)
            
        st.cache_data.clear()  # Clear cache

else:
    st.warning("Select filtering options from Filter Controls. Then select \'Show Filtering Result'\ to view filtered data.")
