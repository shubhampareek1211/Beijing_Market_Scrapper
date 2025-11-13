#!/usr/bin/env python3
"""
BSE Spider Test Script - Enhanced Version
Handles redirects and anti-bot measures
"""

import sys
import json
import argparse
import time

try:
    from urllib.request import urlopen, Request, HTTPCookieProcessor, build_opener
    from urllib.error import HTTPError, URLError
    from http.cookiejar import CookieJar
except ImportError:
    print("❌ Error: This script requires Python 3")
    sys.exit(1)


def strip_jsonp(text):
    """Strip JSONP wrapper from response text."""
    if not text:
        return {}

    left = text.find('(')
    right = text.rfind(')')

    if left != -1 and right != -1 and right > left:
        text = text[left + 1:right]

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        try:
            import re
            text = re.sub(r'^\ufeff', '', text)
            return json.loads(text)
        except Exception:
            return {}


def format_date(date_str):
    """Convert YYYYMMDD to YYYY-MM-DD."""
    if not date_str:
        return None

    s = str(date_str).strip()

    if "-" in s:
        return s

    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

    return s


def fetch_bse_company(stock_code, verbose=False):
    """
    Fetch BSE company data with enhanced headers and cookie handling.
    """
    # Create cookie jar for session management
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))

    # Step 1: Visit main page first to get cookies
    main_url = "https://www.bseinfo.net/nq/listedcompany.html"

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"Step 1: Getting session cookies from main page")
        print(f"{'=' * 60}")
        print(f"Visiting: {main_url}")

    headers_main = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        req_main = Request(main_url, headers=headers_main)
        response_main = opener.open(req_main, timeout=10)
        _ = response_main.read()  # Read to ensure cookies are set

        if verbose:
            print(f"✅ Got cookies from main page")
            print(f"Cookies: {len(cookie_jar)} cookie(s) stored")

        # Small delay to appear more human
        time.sleep(0.5)

    except Exception as e:
        if verbose:
            print(f"⚠️  Could not get main page cookies: {e}")
            print(f"Continuing anyway...")

    # Step 2: Now fetch company detail
    url = (f"https://www.bseinfo.net/nqhqController/detailCompany.do"
           f"?callback=jQuery371008590243684555687_1762466533461"
           f"&zqdm={stock_code}&xxfcbj=2&_={int(time.time() * 1000)}")

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"Step 2: Fetching company data")
        print(f"{'=' * 60}")
        print(f"URL: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.bseinfo.net/nq/listedcompany.html',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    try:
        req = Request(url, headers=headers)
        response = opener.open(req, timeout=10)

        # Handle gzip encoding
        import gzip
        from io import BytesIO

        content = response.read()

        # Check if gzipped
        if response.headers.get('Content-Encoding') == 'gzip':
            content = gzip.decompress(content)

        text = content.decode('utf-8')

        if verbose:
            print(f"\n✅ Got response (status 200)")
            print(f"Response length: {len(text)} chars")
            print(f"\nRaw response (first 500 chars):")
            print(text[:500])
            print("...")

        # Parse JSONP
        data = strip_jsonp(text)

        if verbose:
            print(f"\n📊 Parsed JSON structure:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
            print("...")

        # Extract baseinfo
        baseinfo = data.get('baseinfo')
        if not isinstance(baseinfo, dict):
            if verbose:
                print(f"\n❌ No baseinfo found. Response keys: {list(data.keys())}")
            return None

        if not baseinfo.get('stockCode') and not baseinfo.get('name'):
            if verbose:
                print(f"\n❌ Empty baseinfo - company likely does not exist at code {stock_code}")
            return None

        return baseinfo

    except HTTPError as e:
        if verbose:
            print(f"\n❌ HTTP Error {e.code}: {e.reason}")
            if e.code == 302:
                print(f"  Site is redirecting - possible anti-bot protection")
                print(f"Try accessing the site in a browser first, then retry")
        return None
    except URLError as e:
        if verbose:
            print(f"\n❌ URL Error: {e.reason}")
        return None
    except Exception as e:
        if verbose:
            print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        return None


def print_company_info(baseinfo, verbose=False):
    """Pretty print company information."""
    if not baseinfo:
        print("\n❌ No company data available")
        return

    print(f"\n{'=' * 60}")
    print("✅ BSE COMPANY INFORMATION")
    print(f"{'=' * 60}")

    print(f"\n📊 Basic Information:")
    print(f"  Stock Code:     {baseinfo.get('stockCode', 'N/A')}")
    print(f"  Short Name:     {baseinfo.get('shortname', 'N/A')}")
    print(f"  Full Name:      {baseinfo.get('name', 'N/A')}")
    print(f"  Name History:   {baseinfo.get('namehis', 'N/A')}")

    print(f"\n🏷️  Identifiers:")
    print(f"  ISIN:           {baseinfo.get('ISIN', 'N/A')}")

    print(f"\n🏢 Business:")
    print(f"  Industry:       {baseinfo.get('industry', 'N/A')}")
    print(f"  Area:           {baseinfo.get('area', 'N/A')}")
    print(f"  Broker:         {baseinfo.get('broker', 'N/A')}")

    print(f"\n💰 Financial:")
    total_equity = baseinfo.get('totalStockEquity')
    if total_equity:
        print(f"  Total Equity:   {int(total_equity):,} shares")
    else:
        print(f"  Total Equity:   N/A")

    print(f"\n📈 Trading:")
    print(f"  Transfer Mode:  {baseinfo.get('transferMode', 'N/A')}")

    print(f"\n📅 Important Dates:")
    listing_date = format_date(baseinfo.get('listingDate'))
    publishing_date = format_date(baseinfo.get('publishingDate'))
    print(f"  Listing Date:   {listing_date or 'N/A'}")
    print(f"  Publish Date:   {publishing_date or 'N/A'}")

    if verbose:
        print(f"\n📋 All Fields:")
        for key, value in sorted(baseinfo.items()):
            print(f"  {key:20s}: {value}")

    print(f"\n{'=' * 60}")


def test_multiple_codes(codes, verbose=False):
    """Test multiple stock codes."""
    results = {
        'success': [],
        'not_found': [],
        'error': []
    }

    print(f"\n🧪 Testing {len(codes)} BSE stock codes...")
    print(f"{'=' * 60}")

    for i, code in enumerate(codes, 1):
        sys.stdout.write(f"\rTesting {i}/{len(codes)}: {code}...")
        sys.stdout.flush()

        try:
            baseinfo = fetch_bse_company(code, verbose=False)
            if baseinfo:
                results['success'].append(code)
                if verbose:
                    print(f"\n✅ {code}: {baseinfo.get('name', 'N/A')}")
            else:
                results['not_found'].append(code)
                if verbose:
                    print(f"\n⚠️  {code}: Not found")

            # Be nice to the server
            time.sleep(1)

        except Exception as e:
            results['error'].append(code)
            if verbose:
                print(f"\n❌ {code}: Error - {e}")

    print(f"\r{'':60}\r")

    print(f"\n📊 Test Summary:")
    print(f"{'=' * 60}")
    print(f"  ✅ Success:   {len(results['success']):3d} companies found")
    print(f"  ⚠️  Not Found: {len(results['not_found']):3d} codes")
    print(f"  ❌ Errors:    {len(results['error']):3d} failed requests")
    print(f"{'=' * 60}")

    if results['success']:
        print(f"\n✅ Found Companies:")
        for code in results['success'][:10]:
            baseinfo = fetch_bse_company(code, verbose=False)
            if baseinfo:
                name = baseinfo.get('name', 'Unknown')
                print(f"  {code}: {name}")
            time.sleep(0.5)
        if len(results['success']) > 10:
            print(f"  ... and {len(results['success']) - 10} more")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Test BSE spider data extraction (Enhanced)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python test_bse_spider.py                    # Test default company (920001)
  python test_bse_spider.py --code 920001      # Test specific company
  python test_bse_spider.py --range 920001:920010  # Test range of codes
  python test_bse_spider.py --sample 20        # Test random 20 companies
  python test_bse_spider.py --verbose          # Show detailed debug info
        '''
    )

    parser.add_argument('--code', type=str, help='Single stock code to test (e.g., 920001)')
    parser.add_argument('--range', type=str, help='Range of codes to test (e.g., 920001:920010)')
    parser.add_argument('--sample', type=int, help='Test N random codes from BSE range')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.range:
        try:
            start, end = args.range.split(':')
            start = int(start)
            end = int(end)
            codes = [str(c) for c in range(start, end + 1)]
            test_multiple_codes(codes, args.verbose)
        except ValueError:
            print("❌ Invalid range format. Use: START:END (e.g., 920001:920010)")
            return 1

    elif args.sample:
        import random
        all_codes = [str(c) for c in range(920001, 920993)]
        codes = random.sample(all_codes, min(args.sample, len(all_codes)))
        test_multiple_codes(codes, args.verbose)

    elif args.code:
        baseinfo = fetch_bse_company(args.code, args.verbose)
        print_company_info(baseinfo, args.verbose)
        return 0 if baseinfo else 1

    else:
        print("ℹ️  Testing default company (920001)")
        print("   Use --code, --range, or --sample for other tests")
        print("\n  Note: BSE website may block direct requests.")
        print("   The script will try to get session cookies first.\n")

        baseinfo = fetch_bse_company('920001', args.verbose)
        print_company_info(baseinfo, args.verbose)

        if baseinfo:
            print("\n✅ BSE spider test PASSED!")
            print("   Integration should work correctly.")
            return 0
        else:
            print("\n❌ BSE spider test FAILED!")
            print("   Possible reasons:")
            print("   1. BSE website is blocking automated requests")
            print("   2. Network connectivity issues")
            print("   3. Website structure may have changed")
            print("\n Try:")
            print("   - Access https://www.bseinfo.net in your browser first")
            print("   - Check your internet connection")
            print("   - Try again in a few minutes")
            return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)