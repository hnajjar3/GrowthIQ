import json
from pprint import pprint
from prettytable import PrettyTable


# Function to load and analyze JSON data and generate a PrettyTable
def analyze_json_file_and_generate_table(filename):
    try:
        # Load the JSON data
        with open(filename, 'r') as file:
            data = json.load(file)

        # Check if the data is a list of records
        if isinstance(data, list):
            print(f"Total records: {len(data)}")

            # Initialize PrettyTable
            table = PrettyTable()
            table.field_names = ["Ticker", "Company Name", "Market Cap", "Revenue Growth", "Net Income Growth", "Free Cash Flow Growth", "Relative Strength", "Sector"]

            # Loop through each record and add to PrettyTable
            for record in data:
                ticker = record.get('Ticker', 'N/A')
                name = record.get('Company Name', 'N/A')

                # Format Market Cap to billions or millions (if not None)
                market_cap = record.get('Market Cap')
                if market_cap is not None:
                    if market_cap >= 1e9:
                        market_cap = f"{market_cap / 1e9:.2f}B"
                    elif market_cap >= 1e6:
                        market_cap = f"{market_cap / 1e6:.2f}M"
                else:
                    market_cap = 'N/A'

                # Format numerical values to 2 decimal places
                revenue_growth = f"{record.get('Revenue Growth', 'N/A'):.1f}" if record.get('Revenue Growth') is not None else 'N/A'
                net_income_growth = f"{record.get('Net Income Growth', 'N/A'):.1f}" if record.get('Net Income Growth') is not None else 'N/A'
                free_cash_flow_growth = f"{record.get('Free Cash Flow Growth', 'N/A'):.1f}" if record.get('Free Cash Flow Growth') is not None else 'N/A'
                relative_strength = f"{record.get('Relative Strength', 'N/A'):.1f}" if record.get('Relative Strength') is not None else 'N/A'
                sector = record.get('Sector', 'N/A')

                # Add row to PrettyTable
                table.add_row([ticker, name, market_cap, revenue_growth, net_income_growth, free_cash_flow_growth, relative_strength, sector])

            # Print the PrettyTable
            print(table)

        else:
            print("The JSON file does not contain a list of records.")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Function to load and analyze JSON data
def analyze_json_file(filename):
    try:
        # Load the JSON data
        with open(filename, 'r') as file:
            data = json.load(file)

        # Check if the data is a list of records
        if isinstance(data, list):
            print(f"Total records: {len(data)}")

            # Loop through each record and analyze it
            for idx, record in enumerate(data, 1):
                print(f"\n--- Analyzing Record {idx} ---")
                
                # Check for required fields
                required_fields = [
                    'Ticker', 'Company Name', 'Revenue Growth', 'Net Income Growth', 
                    'Free Cash Flow Growth', 'Relative Strength', 'P/E Ratio', 
                    'Debt-to-Equity', 'ROE', 'Market Cap', 'Sector', 
                    'Price Above SMA 50', 'Price Above SMA 200'
                ]
                
                missing_fields = [field for field in required_fields if field not in record]
                if missing_fields:
                    print(f"Missing fields: {missing_fields}")
                
                # Print the record fields
                pprint(record)

                # Check for None or missing values
                for field in record:
                    if record[field] is None or record[field] == "":
                        print(f"Warning: Field '{field}' is missing or None")

                # Check for specific types of data
                if not isinstance(record.get('Revenue Growth'), (int, float)):
                    print(f"Warning: 'Revenue Growth' should be a number, found: {record.get('Revenue Growth')}")

                if not isinstance(record.get('Sector'), str):
                    print(f"Warning: 'Sector' should be a string, found: {record.get('Sector')}")
                
        else:
            print("The JSON file does not contain a list of records.")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Main function to run the analysis
if __name__ == "__main__":
    filename = "screened_data.json"
    analyze_json_file(filename)
    analyze_json_file_and_generate_table(filename)
