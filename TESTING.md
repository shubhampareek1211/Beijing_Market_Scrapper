# Testing Guide for Unified Market Scraper

## Installation

```bash
# Clone the repository
git clone https://github.com/shubhampareek1211/Beijing_Market_Scrapper.git
cd Beijing_Market_Scrapper

# Install dependencies
pip install -r requirements.txt
```

## Testing Individual Scrapers

### 1. Beijing Stock Exchange (BSE)

The Beijing scraper uses Python's standard library (no Scrapy needed) and has been **VERIFIED WORKING**.

```bash
# Test with 5 companies
python run_beijing.py --limit 5

# Full run
python run_beijing.py
```

**Expected Output:**
- CSV file: `output/beijing_companies_YYYYMMDD_HHMMSS.csv`
- Contains: issuer_code, company_name_ch, industry, listing_date, etc.

### 2. CNINFO Scraper

**Status:** Import paths FIXED, missing files ADDED, ready to test

```bash
# Test single spider
python run_cninfo.py --spider cninfo_universe

# Test all spiders
python run_cninfo.py
```

**Available Spiders:**
- `cninfo_universe` - Basic security listings (CN & EN)
- `cninfo_securities` - Security-level information
- `cninfo_enrichment` - Company details + shareholders
- `cninfo_company_details` - Detailed company profiles

**Expected Output:**
- `output/cn_companies_cn.csv` - Chinese company listings
- `output/cn_companies_en.csv` - English company listings
- `output/cn_securities.csv` - Security details
- `output/cn_company_details.csv` - Detailed profiles
- `output/cn_top5_shareholders.csv` - Shareholder data

**Fixes Applied:**
- ✅ Module paths updated: `cninfo_pipeline` → `scrapers.cninfo`
- ✅ Added missing files: `middlewares.py`, `dedupe.py`, `qa.py`, `state.py`
- ✅ All 4 pipelines configured: normalization, dedupe, QA, export
- ✅ Validators module initialized

### 3. Shanghai Stock Exchange (SSE)

**Status:** Import paths FIXED, ready to test

```bash
# Test with specific companies
python run_shanghai.py --codes 600000,600004,600007

# Test with limit (all companies)
python run_shanghai.py --spider sse_companies_all --limit 10
```

**Expected Output:**
- `output/companies_*.json` - Full company data (JSON)
- `output/company_profiles_*.csv` - Company profiles
- `output/shareholders_*.csv` - Top 10 shareholders
- `output/capital_structure_*.csv` - Capital structure

**Fixes Applied:**
- ✅ Module paths in settings.py: `sse_scraper` → `scrapers.shanghai`
- ✅ Pipeline paths in spider: `sse_scraper.pipelines` → `scrapers.shanghai.pipelines`
- ✅ All pipelines properly configured

## Testing All Scrapers Together

```bash
# Run all three with limits (quick test)
python run_all.py --beijing-limit 5 --shanghai-limit 10

# Full production run
python run_all.py

# Run only specific scraper
python run_all.py --only cninfo

# Skip specific scraper
python run_all.py --skip beijing
```

## Verification Checklist

### Beijing Scraper ✅
- [x] Files integrated correctly
- [x] Runs without import errors
- [x] Successfully fetches and saves data
- [x] **STATUS: VERIFIED WORKING**

### CNINFO Scraper ⚠️
- [x] Files integrated correctly
- [x] Import paths fixed
- [x] Missing files added (4 pipelines + middlewares)
- [ ] **Needs testing with Scrapy installed**

### Shanghai Scraper ⚠️
- [x] Files integrated correctly
- [x] Import paths fixed in settings
- [x] Import paths fixed in spider
- [ ] **Needs testing with Scrapy installed**

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'scrapy'"

**Solution:**
```bash
pip install scrapy>=2.11.0 itemadapter>=0.8.0
```

### Issue: "No module named 'scrapers.cninfo'"

**Solution:**
Ensure you're running from the repository root directory:
```bash
cd Beijing_Market_Scrapper
python run_cninfo.py
```

### Issue: Empty output files

**Possible causes:**
1. Website blocking requests (check logs)
2. Network connectivity issues
3. Website structure changed (may need scraper updates)

**Debug:**
```bash
# Check logs in output directory
ls -la output/
cat output/*.log
```

## Next Steps for Full Verification

1. **Install Scrapy** (if not already installed):
   ```bash
   pip install scrapy>=2.11.0 itemadapter>=0.8.0
   ```

2. **Test CNINFO** (should now work):
   ```bash
   python run_cninfo.py --spider cninfo_universe
   ```

3. **Test Shanghai** (should now work):
   ```bash
   python run_shanghai.py --codes 600000
   ```

4. **Test unified runner**:
   ```bash
   python run_all.py --beijing-limit 2 --shanghai-codes 600000
   ```

## Summary of Fixes

| Scraper | Original Issue | Fix Applied | Status |
|---------|----------------|-------------|--------|
| Beijing | None | N/A | ✅ Working |
| CNINFO | Wrong import paths, missing files | Fixed paths, added 5 files | ✅ Ready to test |
| Shanghai | Wrong import paths | Fixed in settings + spider | ✅ Ready to test |

All scrapers are now properly configured and should work once Scrapy is installed!
