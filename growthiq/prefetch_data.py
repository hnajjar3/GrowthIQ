# prefetch_data.py
import yfinance as yf
import pandas as pd
import json
import time
import logging
from tqdm import tqdm


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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_ticker_data(tickers, index_name):
    data_list = []
    success_count = 0
    error_count = 0

    pbar = tqdm(tickers, desc=f"Fetching {index_name} data", unit="ticker")
    for ticker in pbar:
        try:
            stock = yf.Ticker(ticker)

            # Fetch historical data
            historical_data = stock.history(period='1y')  # Adjust period as needed
            if len(historical_data) < 150:
                continue

            # Fetch financial data
            financials = stock.quarterly_financials.T
            cashflow = stock.quarterly_cashflow.T
            balance_sheet = stock.quarterly_balance_sheet.T

            # Convert index to string
            financials.index = financials.index.astype(str)
            cashflow.index = cashflow.index.astype(str)
            balance_sheet.index = balance_sheet.index.astype(str)

            # Convert historical data index to string
            historical_data.reset_index(inplace=True)
            historical_data['Date'] = historical_data['Date'].astype(str)

            # Fetch other info
            info = stock.info

            # Store data in a dictionary
            data = {
                'Ticker': ticker,
                'Financials': financials.to_dict(),
                'Cashflow': cashflow.to_dict(),
                'BalanceSheet': balance_sheet.to_dict(),
                'HistoricalData': historical_data.to_dict(orient='list'),
                'Info': info
            }

            data_list.append(data)

            success_count += 1
            pbar.set_description(f"Fetching {index_name} data (Success: {success_count}, Errors: {error_count})")
            logging.info(f"Successfully fetched data for {ticker}")

            # Sleep to avoid rate limits
            time.sleep(0.1)

        except Exception as e:
            error_count += 1
            pbar.set_description(f"Fetching {index_name} data (Success: {success_count}, Errors: {error_count})")
            logging.error(f"Error fetching data for {ticker}: {e}")

    # Save data to a JSON file
    file_name = f'{index_name.lower().replace(" ", "_")}_data.json'
    with open(file_name, 'w') as f:
        json.dump(data_list, f)

    logging.info(f"{index_name} data fetching completed. Data saved to '{file_name}'.")


def prefetch_data():
    # Fetch tickers for each market index
    sp500_tickers = get_tickers("S&P500 Index")
    nasdaq_comp_tickers = get_tickers("NASDAQ Composite")
    dow_tickers = get_tickers("Dow Jones Industrial Index")

    # Fetch and store data for each index in separate files
    fetch_ticker_data(sp500_tickers, "S&P500 Index")
    fetch_ticker_data(nasdaq_comp_tickers, "NASDAQ Composite")
    fetch_ticker_data(dow_tickers, "Dow Jones Industrial Index")


if __name__ == "__main__":
    prefetch_data()
