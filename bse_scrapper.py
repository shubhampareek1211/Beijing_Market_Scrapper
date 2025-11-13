#!/usr/bin/env python3
"""Collect BSE data using the working test approach"""
import sys
import csv
import time
from test_bse_spider import fetch_bse_company, format_date


def collect_all_companies(limit=None):
    """Collect all BSE companies and save to CSV"""
    results = []

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
        filename = f"bse_companies_{time.strftime('%Y%m%d')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        print(f"💾 Saved to: {filename}")
        return filename

    return None


if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    collect_all_companies(limit)
