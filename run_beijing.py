#!/usr/bin/env python3
"""
Beijing Stock Exchange (BSE) Scraper Runner
Collects BSE data from https://www.bseinfo.net/nq/listedcompany.html
"""
import sys
import os
import csv
import time
from pathlib import Path

# Add scrapers directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))

from beijing.test_bse_spider import fetch_bse_company, format_date


def collect_all_companies(limit=None, output_dir='output'):
    """Collect all BSE companies and save to CSV"""
    results = []

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"🚀 Starting BSE data collection...")
    print(f"{'=' * 60}")

    for code in range(920001, 920993):
        stock_code = str(code)

        print(f"\rProcessing {stock_code}...", end="", flush=True)

        try:
            baseinfo = fetch_bse_company(stock_code, verbose=False)

            if baseinfo and baseinfo.get('stockCode'):
                results.append({
                    'issuer_code': baseinfo.get('stockCode'),
                    'company_name_ch': baseinfo.get('name'),
                    'company_name_en': None,
                    'industry_csic': baseinfo.get('industry'),
                    'registered_capital': baseinfo.get('totalStockEquity'),
                    'established_date': format_date(baseinfo.get('publishingDate')),
                    'registered_address': baseinfo.get('area'),
                    'disclosure_lang': 'cn',
                    'isin': baseinfo.get('ISIN'),
                    'listing_date': format_date(baseinfo.get('listingDate')),
                    'broker': baseinfo.get('broker'),
                    'snapshot_date': time.strftime('%Y-%m-%d')
                })
                print(f"\r✅ {stock_code}: {baseinfo.get('name', 'Unknown')[:40]}")

            time.sleep(1)  # Be polite

            if limit and len(results) >= limit:
                break

        except Exception as e:
            print(f"\r❌ {stock_code}: Error - {e}")
            continue

    print(f"\n{'=' * 60}")
    print(f"✅ Collected {len(results)} companies")

    # Save to CSV
    if results:
        filename = output_path / f"beijing_companies_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        print(f"💾 Saved to: {filename}")
        return str(filename)

    return None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Beijing Stock Exchange (BSE) Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_beijing.py                    # Scrape all BSE companies
  python run_beijing.py --limit 10         # Scrape first 10 companies
  python run_beijing.py --output mydata    # Save to custom directory
        '''
    )

    parser.add_argument('--limit', type=int, help='Limit number of companies to scrape')
    parser.add_argument('--output', default='output', help='Output directory (default: output)')

    args = parser.parse_args()

    try:
        collect_all_companies(limit=args.limit, output_dir=args.output)
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
