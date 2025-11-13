#!/usr/bin/env python3
"""
CNINFO Scraper Runner
Collects Chinese company data from CNINFO (巨潮资讯网)
"""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Add scrapers directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))


def run_spider(spider_name, output_dir='output'):
    """Run a specific CNINFO spider"""
    print(f"\n{'=' * 60}")
    print(f"🚀 Running CNINFO spider: {spider_name}")
    print(f"{'=' * 60}\n")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Set environment variable for output directory
    env = os.environ.copy()
    env['SCRAPY_PROJECT'] = 'cninfo'
    env['OUTPUT_DIR'] = str(output_path)

    # Run scrapy spider
    cmd = [
        'scrapy', 'crawl', spider_name,
        '-L', 'INFO',
        '--logfile', str(output_path / f'{spider_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]

    try:
        result = subprocess.run(cmd, env=env, check=True)
        print(f"\n✅ {spider_name} completed successfully")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {spider_name} failed with error code {e.returncode}")
        return e.returncode


def run_all_spiders(output_dir='output'):
    """Run all CNINFO spiders"""
    spiders = [
        'cninfo_universe',
        'cninfo_securities',
        'cninfo_enrichment',
        'cninfo_company_details'
    ]

    results = {}

    for spider in spiders:
        results[spider] = run_spider(spider, output_dir)

    # Print summary
    print(f"\n{'=' * 60}")
    print("📊 CNINFO Scraping Summary")
    print(f"{'=' * 60}")

    for spider, code in results.items():
        status = "✅ Success" if code == 0 else "❌ Failed"
        print(f"  {spider:30s} {status}")

    print(f"{'=' * 60}\n")

    return 0 if all(code == 0 for code in results.values()) else 1


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='CNINFO Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Available spiders:
  cninfo_universe         - Extract basic security listings
  cninfo_securities       - Gather security-level information
  cninfo_enrichment       - Collect company details and shareholders
  cninfo_company_details  - Retrieve detailed company profiles

Examples:
  python run_cninfo.py                           # Run all spiders
  python run_cninfo.py --spider cninfo_universe  # Run specific spider
  python run_cninfo.py --output mydata           # Save to custom directory
        '''
    )

    parser.add_argument('--spider', help='Specific spider to run (default: run all)')
    parser.add_argument('--output', default='output', help='Output directory (default: output)')

    args = parser.parse_args()

    try:
        if args.spider:
            return run_spider(args.spider, args.output)
        else:
            return run_all_spiders(args.output)
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
