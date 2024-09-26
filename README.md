# Growth Stock Screener Dashboard

Are you tired of stock screeners that do not give _real insight_ into the stock market? I built this stock screener and dashboard in Python and Streamlit, designed to help investors screen stocks based on growth fundamentals, and filter based on technicals. 

According to renouned researcher and professor of finance at NYU, Aswath Damodaran, there are 3 key metrics for stocks that outperform:
- Revenue Growth
- Earnings Growth
- Free Cash Flow Growth

This screener is the only such tool that screens the stock market for growth fundamentals. 

## Table of Contents

- [Growth Stock Screener Dashboard](#growth-stock-screener-dashboard)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
  - [Usage](#usage)
    - [Navigating the App](#navigating-the-app)
  - [Application Structure](#application-structure)
  - [Screenshots](#screenshots)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)
    - [**Q\&A**](#qa)

## Introduction

This application allows users to:

- **Screen stocks** based on various financial ratios and technical indicators.
- **Visualize** fundamental and technical data through interactive charts.
- **Filter** stocks dynamically and view detailed analysis for selected tickers.

## Features

- **Stock Screening**: Deep market screening based on company fundamental growth factors.
- **Fundamental Analysis**: Visualize revenue, net income, and free cash flow with price overlay.
- **Technical Analysis**: Chart stocks, including price trends, moving averages, RSI, MACD, and volume side-by-side fundamentals.
- **Interactive Dashboard**: Modular design with collapsible sections for a clean and user-friendly interface.
- **Data Caching**: Improved performance with data caching mechanisms.
- **Customizable Filters**: Adjust filters and view results in real-time.

## Installation

### Prerequisites

- Python 3.7 or higher
- Poetry package manager

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/hnajjar3/GrowthStockScreenerApp.git
   cd GrowthStockScreenerApp
   ```

2. **Install required packages and activate a virtual environment** (optional but recommended)

   ```bash
   pip install poetry
   poetry install
   poetry shell
   ```
3. **Pre-fetch data for faster screening** (DO NOT SKIP)
   
   ```bash
    poetry run python prefetch_data.py  
   ```
4. **Verify pre-fetched data** (OPTIONAL)
   ```bash
   poetru run python analyze_sp500_json.py
   ```
    If screening NASDAQ Composite, you'll need to create a new script based on this one.

## Usage

Start up the app using:

```bash
poetry run streamlit run growth_dashboard.py
```

Now the web app will open up in your browser (if not copy Local URL and paste in browser).

### Navigating the App

- **Show Screening Result**: View the initial list of screened stocks based on fundamental growth analysis.
- **Show Filter Controls**: Apply additional filters to narrow down the stocks based on technical analysis.
- **Show Filtering Result**: View the stocks that meet your filter criteria.
- **Select a Ticker**: Choose a stock to view detailed charts and analysis.
- **Select Time Period**: Adjust the time frame for historical data.

## Application Structure

- **`growth_dashboard.py`**: Main application file containing the Streamlit app code.
- **`screened_data.json`**: JSON file where screened stock data is stored.
- **`README.md`**: Documentation file.

## Screenshots

![Dashboard screening view](screenshots/screening_view.png)
*Fig. 1: Analyze results of screening*

![Dashboard filtering view ](screenshots/filtering_view.png)
*Fig. 2: Apply filters to hone in further*

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a new branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Make your changes**
4. **Commit your changes**

   ```bash
   git commit -m "Add some feature"
   ```

5. **Push to the branch**

   ```bash
   git push origin feature/YourFeature
   ```

6. **Open a pull request**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Hassan Khaled Najjar**
- **Email**: [hnajjar.ab@gmail.com](mailto:hnajjar.ab@gmail.com)
- **GitHub**: [hnajjar3](https://github.com/hnajjar3)

---

Feel free to modify and expand upon this template to better suit your project's needs. Add any additional sections that you think would be helpful, such as:

- **Known Issues**
  The app isn't perfect and needs improvement in many areas. It's an MVP. 
- **Future Improvements**
    -Add more fundamentals.
    -Screen New markets. 
    -More technical charts and filtering options.
- **MISC**
  I'm happy to receive your feedback to improve it. What more can I add to make it a better experience?
### **Q&A**

> <span style="color:red;">**Q**</span>: The app is not responsive, what should I do?  
> <span style="color:green;">**A**</span>: Please restart the application from the command line by following these steps:
> 1. Open your terminal.
> 2. Navigate to the app's directory.
> 3. Run `poetry run streamlit run growth_dashboard.py`.   
>
> If the issue persists, feel free to reach out to support for further assistance.

> <span style="color:red;">**Q**</span>: The dashboard is buggy. I prefer command-line version.  Is it available?   
> <span style="color:green;">**A**</span>: YES! You can run `poetry run python analyze_screened_json.py`. It will generate a PrettyTable with detailed screened stocks info.
