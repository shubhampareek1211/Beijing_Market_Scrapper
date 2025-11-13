#!/usr/bin/env python3
"""
Unified Market Scraper Runner
Runs all market scrapers: Beijing, CNINFO, and Shanghai
"""
import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
import argparse


class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")


def print_status(market, status, message=""):
    """Print status message"""
    if status == "running":
        print(f"{Colors.YELLOW}🔄 {market:20s} - Running...{Colors.END}")
    elif status == "success":
        print(f"{Colors.GREEN}✅ {market:20s} - Completed{Colors.END} {message}")
    elif status == "failed":
        print(f"{Colors.RED}❌ {market:20s} - Failed{Colors.END} {message}")
    elif status == "skipped":
        print(f"{Colors.YELLOW}⏭️  {market:20s} - Skipped{Colors.END}")


def run_beijing_scraper(output_dir, limit=None):
    """Run Beijing Stock Exchange scraper"""
    market_name = "Beijing (BSE)"
    print_status(market_name, "running")

    cmd = [sys.executable, 'run_beijing.py', '--output', output_dir]
    if limit:
        cmd.extend(['--limit', str(limit)])

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start_time

    if result.returncode == 0:
        print_status(market_name, "success", f"({elapsed:.1f}s)")
        return True
    else:
        print_status(market_name, "failed", f"(exit code: {result.returncode})")
        return False


def run_cninfo_scraper(output_dir, spider=None):
    """Run CNINFO scraper"""
    market_name = "CNINFO"
    print_status(market_name, "running")

    cmd = [sys.executable, 'run_cninfo.py', '--output', output_dir]
    if spider:
        cmd.extend(['--spider', spider])

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start_time

    if result.returncode == 0:
        print_status(market_name, "success", f"({elapsed:.1f}s)")
        return True
    else:
        print_status(market_name, "failed", f"(exit code: {result.returncode})")
        return False


def run_shanghai_scraper(output_dir, codes=None, limit=None):
    """Run Shanghai Stock Exchange scraper"""
    market_name = "Shanghai (SSE)"
    print_status(market_name, "running")

    cmd = [sys.executable, 'run_shanghai.py', '--output', output_dir]

    if codes:
        cmd.extend(['--codes', codes])
    elif limit:
        cmd.extend(['--spider', 'sse_companies_all', '--limit', str(limit)])

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start_time

    if result.returncode == 0:
        print_status(market_name, "success", f"({elapsed:.1f}s)")
        return True
    else:
        print_status(market_name, "failed", f"(exit code: {result.returncode})")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Unified Market Scraper - Run all market scrapers together',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script runs all three market scrapers in sequence:
  1. Beijing Stock Exchange (BSE)
  2. CNINFO (巨潮资讯网)
  3. Shanghai Stock Exchange (SSE)

Examples:
  python run_all.py                          # Run all scrapers with default settings
  python run_all.py --output mydata          # Save to custom directory
  python run_all.py --beijing-limit 10       # Limit Beijing scraper to 10 companies
  python run_all.py --shanghai-limit 20      # Limit Shanghai scraper to 20 companies
  python run_all.py --skip beijing           # Skip Beijing scraper
  python run_all.py --only cninfo            # Run only CNINFO scraper

Output:
  All data will be saved to the output directory with timestamps
        '''
    )

    parser.add_argument('--output', default='output',
                       help='Output directory for all scrapers (default: output)')
    parser.add_argument('--beijing-limit', type=int,
                       help='Limit number of companies for Beijing scraper')
    parser.add_argument('--shanghai-codes',
                       help='Comma-separated company codes for Shanghai scraper')
    parser.add_argument('--shanghai-limit', type=int,
                       help='Maximum companies for Shanghai scraper')
    parser.add_argument('--cninfo-spider',
                       help='Specific CNINFO spider to run (default: all)')
    parser.add_argument('--skip', choices=['beijing', 'cninfo', 'shanghai'],
                       action='append', help='Skip specific scraper(s)')
    parser.add_argument('--only', choices=['beijing', 'cninfo', 'shanghai'],
                       help='Run only specific scraper')

    args = parser.parse_args()

    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(args.output) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print_header("🌏 UNIFIED MARKET SCRAPER")
    print(f"Output directory: {output_dir}\n")

    # Determine which scrapers to run
    skip_scrapers = args.skip or []

    if args.only:
        run_scrapers = {args.only}
    else:
        run_scrapers = {'beijing', 'cninfo', 'shanghai'} - set(skip_scrapers)

    # Track results
    results = {}
    start_time = time.time()

    # Run Beijing scraper
    if 'beijing' in run_scrapers:
        results['beijing'] = run_beijing_scraper(str(output_dir), args.beijing_limit)
    else:
        print_status("Beijing (BSE)", "skipped")
        results['beijing'] = None

    # Run CNINFO scraper
    if 'cninfo' in run_scrapers:
        results['cninfo'] = run_cninfo_scraper(str(output_dir), args.cninfo_spider)
    else:
        print_status("CNINFO", "skipped")
        results['cninfo'] = None

    # Run Shanghai scraper
    if 'shanghai' in run_scrapers:
        results['shanghai'] = run_shanghai_scraper(
            str(output_dir),
            args.shanghai_codes,
            args.shanghai_limit
        )
    else:
        print_status("Shanghai (SSE)", "skipped")
        results['shanghai'] = None

    # Print summary
    total_time = time.time() - start_time

    print_header("📊 SCRAPING SUMMARY")

    successful = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    print(f"  ✅ Successful:  {successful}")
    print(f"  ❌ Failed:      {failed}")
    print(f"  ⏭️  Skipped:     {skipped}")
    print(f"  ⏱️  Total time:  {total_time:.1f}s")
    print(f"\n  📁 Output: {output_dir}")

    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.END}\n")

    # Return appropriate exit code
    if failed > 0:
        return 1
    elif successful > 0:
        return 0
    else:
        return 2  # All skipped


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
