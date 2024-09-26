import json
import pandas as pd

# Load the data from the JSON file
with open('nasdaq_composite_data.json', 'r') as f:
    data_list = json.load(f)

# Convert the list of dictionaries to a DataFrame for easier inspection
data_df = pd.DataFrame(data_list)

# Display the available columns in the data
print("Available columns in the data:")
print(data_df.columns.tolist())

# Inspect the first few entries for a general overview
print("\nFirst few entries in the data:")
print(data_df.head())

# Function to gather and display keys from nested dictionaries
def get_nested_keys(data_list, column_name):
    keys = set()
    for data in data_list:
        column_data = data.get(column_name, {})
        for key in column_data:
            keys.add(key)
    return sorted(keys)

# Gather available metrics in 'Financials', 'Cashflow', 'BalanceSheet', and 'HistoricalData'
financials_keys = get_nested_keys(data_list, 'Financials')
cashflow_keys = get_nested_keys(data_list, 'Cashflow')
balance_sheet_keys = get_nested_keys(data_list, 'BalanceSheet')

# HistoricalData usually has predefined columns (like Date, Close, etc.)
historical_data_keys = set()
for data in data_list:
    historical_data = data.get('HistoricalData', {})
    if historical_data:  # Once we find a non-empty entry, extract the keys
        historical_data_keys.update(historical_data.keys())
        print(historical_data)
        break

# Extract available keys in 'Info'
info_keys = get_nested_keys(data_list, 'Info')

# Display all the collected metrics
print("\nAvailable metrics in 'Financials':")
print(financials_keys)

print("\nAvailable metrics in 'Cashflow':")
print(cashflow_keys)

print("\nAvailable metrics in 'BalanceSheet':")
print(balance_sheet_keys)

print("\nAvailable columns in 'HistoricalData':")
print(sorted(historical_data_keys))

print("\nAvailable keys in 'Info':")
print(info_keys)


