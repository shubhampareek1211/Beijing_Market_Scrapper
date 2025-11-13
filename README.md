# Unified Market Scraper

A comprehensive scraping solution for Chinese stock markets, consolidating data collection from:
1. **Beijing Stock Exchange (BSE)** - https://www.bseinfo.net
2. **CNINFO (巨潮资讯网)** - https://www.cninfo.com.cn
3. **Shanghai Stock Exchange (SSE)** - https://www.sse.com.cn

## 🚀 Features

- **Three Independent Scrapers**: Each market scraper can run independently
- **Unified Runner**: Run all scrapers together with a single command
- **Flexible Output**: Date-organized CSV and JSON output
- **Configurable Limits**: Control scraping scope for testing or full runs
- **Comprehensive Data**: Company profiles, shareholders, capital structure, and more

## 📋 Requirements

- Python 3.7+
- See `requirements.txt` for dependencies

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/shubhampareek1211/Beijing_Market_Scrapper.git
cd Beijing_Market_Scrapper

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage

### Run All Scrapers Together

```bash
# Run all three scrapers with default settings
python run_all.py

# Run with custom output directory
python run_all.py --output mydata

# Limit Beijing scraper to 10 companies
python run_all.py --beijing-limit 10

# Limit Shanghai scraper to 20 companies
python run_all.py --shanghai-limit 20

# Skip a specific scraper
python run_all.py --skip beijing

# Run only one scraper
python run_all.py --only cninfo
```

### Run Individual Scrapers

#### 1. Beijing Stock Exchange (BSE)

```bash
# Scrape all BSE companies
python run_beijing.py

# Scrape first 10 companies (for testing)
python run_beijing.py --limit 10

# Custom output directory
python run_beijing.py --output mydata
```

**Output**: `beijing_companies_YYYYMMDD_HHMMSS.csv`

#### 2. CNINFO (巨潮资讯网)

```bash
# Run all CNINFO spiders
python run_cninfo.py

# Run specific spider
python run_cninfo.py --spider cninfo_universe

# Custom output directory
python run_cninfo.py --output mydata
```

**Available Spiders**:
- `cninfo_universe` - Basic security listings
- `cninfo_securities` - Security-level information
- `cninfo_enrichment` - Company details and shareholders
- `cninfo_company_details` - Detailed company profiles

**Output**: Multiple CSV files in timestamped directory

#### 3. Shanghai Stock Exchange (SSE)

```bash
# Scrape specific companies
python run_shanghai.py --codes 600000,600004,600007

# Scrape all companies (with limit)
python run_shanghai.py --spider sse_companies_all --limit 50

# Custom output directory
python run_shanghai.py --output mydata
```

**Output**: JSON and CSV files with company profiles, shareholders, and capital structure

## 📁 Output Structure

```
output/
└── YYYYMMDD_HHMMSS/              # Timestamped directory
    ├── beijing_companies_*.csv   # Beijing data
    ├── cn_companies_cn.csv       # CNINFO Chinese listings
    ├── cn_securities.csv         # CNINFO securities
    ├── company_profiles_*.csv    # Shanghai profiles
    ├── shareholders_*.csv        # Shanghai shareholders
    └── capital_structure_*.csv   # Shanghai capital structure
```

## 🎯 Data Fields

### Beijing Stock Exchange
- Issuer Code
- Company Name (Chinese)
- Industry (CSIC)
- Registered Capital
- Established Date
- Listing Date
- ISIN
- Broker

### CNINFO
- Company Name (Chinese & English)
- Security Code
- Exchange & Board
- Organization Type
- Regional Information
- Status

### Shanghai Stock Exchange
- Company Code
- Security Name
- Full Name (Chinese & English)
- Listing Date
- Registered Address
- Legal Representative
- Industry Classification
- Top 10 Shareholders
- Capital Structure

## 🔍 Testing

Each scraper can be tested with limited runs:

```bash
# Test Beijing scraper (5 companies)
python run_beijing.py --limit 5

# Test CNINFO universe spider
python run_cninfo.py --spider cninfo_universe

# Test Shanghai scraper (10 companies)
python run_shanghai.py --spider sse_companies_all --limit 10

# Test all scrapers with limits
python run_all.py --beijing-limit 5 --shanghai-limit 10
```

## 📊 Project Structure

```
Beijing_Market_Scrapper/
├── scrapers/                     # Scraper modules
│   ├── beijing/                  # BSE scraper
│   │   ├── bse_scrapper.py
│   │   └── test_bse_spider.py
│   ├── cninfo/                   # CNINFO scraper
│   │   ├── settings.py
│   │   ├── items.py
│   │   ├── spiders/
│   │   ├── pipelines/
│   │   └── utils/
│   └── shanghai/                 # SSE scraper
│       ├── settings.py
│       ├── items.py
│       ├── pipelines.py
│       └── spiders/
├── run_beijing.py                # Beijing runner
├── run_cninfo.py                 # CNINFO runner
├── run_shanghai.py               # Shanghai runner
├── run_all.py                    # Unified runner
├── requirements.txt              # Dependencies
├── scrapy.cfg                    # Scrapy configuration
└── README.md                     # This file
```

## ⚙️ Configuration

### Beijing Scraper
- Uses standard library (urllib)
- Implements cookie handling and anti-bot measures
- Default delay: 1 second between requests

### CNINFO Scraper
- Built with Scrapy framework
- Download delay: 0.5 seconds
- Supports both Chinese and English endpoints

### Shanghai Scraper
- Built with Scrapy framework
- Concurrent requests: 4
- Download delay: 1.5 seconds
- Handles JSONP responses

## 🛠️ Troubleshooting

**Issue**: Scrapy command not found
```bash
# Install scrapy explicitly
pip install scrapy>=2.11.0
```

**Issue**: Beijing scraper getting blocked
- The site may have anti-bot protection
- Try accessing the site in a browser first
- Increase delay between requests

**Issue**: Empty results from scrapers
- Check your internet connection
- Verify the source websites are accessible
- Check logs in the output directory

## 📝 Notes

- **Rate Limiting**: All scrapers implement delays to be respectful to source servers
- **Data Accuracy**: Data is scraped as-is from source websites
- **Updates**: Website structure may change; scrapers may need updates
- **Compliance**: Ensure you comply with website terms of service

## 🤝 Contributing

Feel free to submit issues or pull requests for improvements.

## 📄 License

MIT License

## 🔗 Source Repositories

This project consolidates code from three original repositories:
1. [Beijing_Market_Scrapper](https://github.com/shubhampareek1211/Beijing_Market_Scrapper)
2. [cininfo_scrapy](https://github.com/shubhampareek1211/cininfo_scrapy)
3. [Shanghai_Market_Scraper](https://github.com/shubhampareek1211/Shanghai_Market_Scraper)

## 🚀 Quick Start Examples

### Example 1: Full Production Run
```bash
# Run all scrapers, collect everything
python run_all.py --output production_data
```

### Example 2: Quick Test
```bash
# Test with small datasets
python run_all.py --beijing-limit 5 --shanghai-limit 10 --cninfo-spider cninfo_universe
```

### Example 3: Shanghai Focus
```bash
# Only scrape Shanghai exchange
python run_all.py --only shanghai --shanghai-limit 100
```

## 📧 Contact

For questions or issues, please open an issue on GitHub.
