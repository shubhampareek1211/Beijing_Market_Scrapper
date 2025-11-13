#!/usr/bin/env python3
"""
Shanghai Stock Exchange (SSE) Scraper Runner
Collects company data from Shanghai Stock Exchange API
"""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Add scrapers directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))


def run_spider(spider_name, company_codes=None, max_companies=None, output_dir='output'):
    """Run a specific SSE spider"""
    print(f"\n{'=' * 60}")
    print(f"🚀 Running Shanghai SSE spider: {spider_name}")
    print(f"{'=' * 60}\n")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Set environment variable for output directory
    env = os.environ.copy()
    env['SCRAPY_PROJECT'] = 'shanghai'
    env['OUTPUT_DIR'] = str(output_path)

    # Build command
    cmd = [
        'scrapy', 'crawl', spider_name,
        '-L', 'INFO',
        '--logfile', str(output_path / f'{spider_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]

    # Add spider-specific arguments
    if spider_name == 'sse_companies' and company_codes:
        cmd.extend(['-a', f'company_codes={company_codes}'])
    elif spider_name == 'sse_companies_all' and max_companies:
        cmd.extend(['-a', f'max_companies={max_companies}'])

    try:
        result = subprocess.run(cmd, env=env, check=True)
        print(f"\n✅ {spider_name} completed successfully")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {spider_name} failed with error code {e.returncode}")
        return e.returncode


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Shanghai Stock Exchange (SSE) Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Available spiders:
  sse_companies      - Scrape specific companies by codes
  sse_companies_all  - Scrape all companies (with optional limit)

Examples:
  python run_shanghai.py                                          # Scrape default companies
  python run_shanghai.py --codes 600000,600004,600007             # Scrape specific companies
  python run_shanghai.py --spider sse_companies_all --limit 50    # Scrape first 50 companies
  python run_shanghai.py --output mydata                          # Save to custom directory
        '''
    )

    parser.add_argument('--spider', default='sse_companies',
                       choices=['sse_companies', 'sse_companies_all'],
                       help='Spider to run (default: sse_companies)')
    parser.add_argument('--codes', help='Comma-separated company codes (for sse_companies)')
    parser.add_argument('--limit', type=int, help='Maximum companies to scrape (for sse_companies_all)')
    parser.add_argument('--output', default='output', help='Output directory (default: output)')

    args = parser.parse_args()

    try:
        return run_spider(
            args.spider,
            company_codes=args.codes,
            max_companies=args.limit,
            output_dir=args.output
        )
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
