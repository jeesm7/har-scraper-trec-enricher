# 🏠 HAR Scraper + TREC Enricher

A unified tool to scrape real estate agents from HAR.com and automatically enrich them with TREC license data. This application combines web scraping and data matching into a single, easy-to-use interface.

## Features

- 🔍 **Web Scraping**: Automatically scrape agent data from HAR.com for any Texas city
- 📊 **Data Enrichment**: Match scraped agents with TREC license database
- 🎯 **Smart Matching**: Advanced name matching algorithm with confidence scores
- 🖥️ **User-Friendly UI**: Simple web interface built with Streamlit
- 📁 **Automatic Export**: Saves enriched data to CSV files in organized folders
- ⚡ **Real-time Progress**: Live progress tracking and statistics

## Quick Start

### 🌐 **Online Demo**
**Deployed App:** [HAR Scraper + TREC Enricher](https://har-scraper-trec-enricher.streamlit.app/) *(Live on Streamlit Cloud)*

### 💻 **Local Installation**

#### Option 1: One-Click Launch (Easiest)
```bash
python run_app.py
```
This will automatically install dependencies and start the application.

#### Option 2: Manual Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run har_trec_enricher.py
```

### 📁 **TREC Database Setup**
- The app includes a **sample TREC database** for demonstration
- For production use, upload your full TREC database via the web interface
- Supported format: CSV with columns `license_number`, `name`, `license_type`

## Usage

1. **Launch the Application**: Use either method above to start the web interface
2. **Configure Settings** (in the sidebar):
   - Enter the Texas city name (e.g., "austin", "dallas", "houston")
   - Set the number of pages to scrape (20 agents per page)
   - Adjust the match threshold (higher = more strict matching)
   - **Select license types** to include in matching (Sales Agents, Brokers, LLCs, etc.)
3. **Start Processing**: Click the "🚀 Start Scraping & Enrichment" button
4. **Monitor Progress**: Watch real-time progress bars and status updates
5. **Review Results**: View statistics, data preview, and download the CSV

## Output

The application generates enriched CSV files containing:

### Original HAR Data
- `name`: Agent name
- `phone`: Contact phone number
- `organization`: Brokerage/company name
- `for_sale`, `for_rent`, `sold`, `leased`, `showings`: Property statistics

### TREC Enrichment Data
- `license_type`: License type from TREC database (e.g., SALE, AGENT)
- `license_number`: TREC license number
- `match_confidence`: Matching confidence score (0.0-1.0)
- `matched_trec_name`: Full name from TREC database

## Configuration Options

- **City Name**: Any Texas city available on HAR.com
- **Pages to Scrape**: 1-500 pages (recommended: start with 5-10 for testing)
- **Match Threshold**: 0.1-1.0 (default: 0.6)
  - Lower values = more matches but potentially less accurate
  - Higher values = fewer matches but higher accuracy
- **License Type Filter**: Choose which license types to include
  - **SALE**: Sales Agents (248,115 records)
  - **BRK**: Brokers (41,119 records)
  - **BLLC**: Broker LLCs (13,270 records)
  - **BCRP**: Broker Corporations (4,411 records)
  - **REB**: Real Estate Brokers (1,261 records)
  - **Type 6**: Other license types (160 records)
  - Quick select: "Select All" or "Sales Only"

## File Structure

```
HAR Scraper + TREC Enricher/
├── har_trec_enricher.py       # Main application
├── run_app.py                 # Launcher script
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── trec-sales-or-agent copy 2.csv  # TREC database
└── Enriched CSVs/            # Output folder (auto-created)
    └── har_[city]_enriched_[timestamp].csv
```

## Requirements

- Python 3.7+
- Internet connection for scraping
- TREC database file (`trec-sales-or-agent copy 2.csv`)

## Dependencies

- `streamlit`: Web interface framework
- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `lxml`: XML/HTML parser

## Troubleshooting

### Common Issues

1. **"TREC database not found"**
   - Ensure `trec-sales-or-agent copy 2.csv` is in the main directory

2. **No agents found**
   - Check the city name spelling
   - Some cities might not be available on HAR.com
   - Try different city variations (e.g., "dallas" vs "dallas-fort-worth")

3. **Slow performance**
   - Reduce the number of pages to scrape
   - The application includes delays to be respectful to the server

4. **Low match rates**
   - Lower the match threshold
   - Check data quality in the TREC database

### Performance Tips

- Start with 5-10 pages for testing
- Use higher thresholds (0.7-0.8) for higher quality matches
- Monitor the progress and cancel if needed (Ctrl+C in terminal)

## License

This tool is for educational and research purposes. Please respect HAR.com's terms of service and use responsibly.

## Support

For issues or questions, please check:
1. This README file
2. The application's built-in help text
3. Console output for error messages 