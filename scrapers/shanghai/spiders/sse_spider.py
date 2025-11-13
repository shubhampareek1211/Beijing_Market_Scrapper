import scrapy
import json
import re
from datetime import datetime


class SSECompanyAPISpider(scrapy.Spider):
    """
    Spider for scraping SSE company data with fixed shareholder endpoint
    """
    name = 'sse_companies'
    allowed_domains = ['query.sse.com.cn', 'www.sse.com.cn']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1.5,
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE=600000',
            'X-Requested-With': 'XMLHttpRequest',
        },
        'ITEM_PIPELINES': {
            'sse_scraper.pipelines.DataCleaningPipeline': 100,
            'sse_scraper.pipelines.CsvWriterPipeline': 300,
            'sse_scraper.pipelines.JsonWriterPipeline': 400,
        }
    }

    # API endpoints
    BASE_URLS = {
        'commonQuery': 'https://query.sse.com.cn/commonQuery.do',
        'commonSoaQuery': 'https://query.sse.com.cn/commonSoaQuery.do',
    }

    SQL_IDS = {
        'company_info': {
            'base': 'commonQuery',
            'sql_id': 'COMMON_SSE_CP_GPJCTPZ_GPLB_GPGK_GSGK_C',
            'param': 'COMPANY_CODE'
        },
        'shareholders': {
            'base': 'commonSoaQuery',
            'sql_id': 'COMMON_SSE_PL_XBRL_TOP10SHAREHOLDERS',
            'param': 'stockId'
        },
        'capital_structure': {
            'base': 'commonQuery',
            'sql_id': 'COMMON_SSE_CP_GSGK_GBJG_L',
            'param': 'COMPANY_CODE'
        },
    }

    def __init__(self, company_codes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if company_codes:
            self.company_codes = company_codes.split(',')
        else:
            self.company_codes = ['600000', '600004', '600007', '600008']

        self.logger.info(f'Will scrape {len(self.company_codes)} companies')

    def start_requests(self):
        """Start by requesting company info for each code"""
        for code in self.company_codes:
            url = self.build_url('company_info', code)
            yield scrapy.Request(
                url=url,
                callback=self.parse_company_info,
                meta={'company_code': code},
                errback=self.handle_error,
                dont_filter=True
            )

    def build_url(self, endpoint_type, company_code, **kwargs):
        """Build API URL without JSONP callback to get pure JSON"""
        endpoint_config = self.SQL_IDS[endpoint_type]
        base_url = self.BASE_URLS[endpoint_config['base']]

        params = {
            'isPagination': 'false',
            'sqlId': endpoint_config['sql_id'],
            endpoint_config['param']: company_code,
        }
        params.update(kwargs)

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f'{base_url}?{query_string}'

    def parse_response(self, response):
        """Parse response - handle both JSON and JSONP"""
        text = response.text.strip()

        # Check if it's JSONP (starts with callback function)
        if text.startswith('jsonpCallback') or '({' in text:
            # Extract JSON from JSONP: jsonpCallback123({"data": ...})
            match = re.search(r'\((.*)\)$', text)
            if match:
                text = match.group(1)

        try:
            data = json.loads(text)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f'JSON decode error: {e}')
            self.logger.error(f'Response text: {text[:200]}')
            return None

    def parse_company_info(self, response):
        """Parse company information API response"""
        company_code = response.meta['company_code']
        self.logger.info(f'Parsing company info for {company_code}')

        data = self.parse_response(response)

        if data and data.get('result'):
            result = data['result']
            if isinstance(result, list) and result:
                company_profile = self.extract_company_profile(result[0], company_code)
            else:
                company_profile = self.extract_company_profile(result, company_code)
        else:
            self.logger.warning(f'No company info found for {company_code}')
            company_profile = {'company_code': company_code}

        # Request shareholders data
        shareholders_url = self.build_url('shareholders', company_code)
        yield scrapy.Request(
            url=shareholders_url,
            callback=self.parse_shareholders,
            meta={
                'company_code': company_code,
                'company_profile': company_profile
            },
            dont_filter=True
        )

    def parse_shareholders(self, response):
        """Parse shareholders API response"""
        company_code = response.meta['company_code']
        company_profile = response.meta['company_profile']

        self.logger.info(f'Parsing shareholders for {company_code}')

        # DEBUG: Log raw response
        self.logger.info(f'Raw response text (first 500 chars): {response.text[:500]}')

        data = self.parse_response(response)
        shareholders = []

        # DEBUG: Log parsed data structure
        if data:
            self.logger.info(f'Parsed data keys: {list(data.keys())}')
            if 'pageHelp' in data:
                self.logger.info(f'pageHelp keys: {list(data["pageHelp"].keys())}')
                if 'data' in data['pageHelp']:
                    self.logger.info(f'Found {len(data["pageHelp"]["data"])} shareholder records')

        if data and 'pageHelp' in data and 'data' in data['pageHelp']:
            # The actual data is in pageHelp.data
            result = data['pageHelp']['data']
            shareholders = self.extract_shareholders(result)
            self.logger.info(f'Extracted {len(shareholders)} shareholders for {company_code}')
            # DEBUG: Log first shareholder
            if shareholders:
                self.logger.info(f'First shareholder: {shareholders[0]}')
        else:
            self.logger.warning(f'No shareholders found for {company_code}')
            self.logger.warning(f'Data structure: {data}')

        # Request capital structure
        capital_url = self.build_url('capital_structure', company_code)
        yield scrapy.Request(
            url=capital_url,
            callback=self.parse_capital_structure,
            meta={
                'company_code': company_code,
                'company_profile': company_profile,
                'shareholders': shareholders
            },
            dont_filter=True
        )

    def parse_capital_structure(self, response):
        """Parse capital structure API response"""
        company_code = response.meta['company_code']
        company_profile = response.meta['company_profile']
        shareholders = response.meta['shareholders']

        self.logger.info(f'Parsing capital structure for {company_code}')

        data = self.parse_response(response)

        if data and data.get('result'):
            result = data['result']
            capital_structure = self.extract_capital_structure(result)
            self.logger.info(f'Found capital structure for {company_code}')
        else:
            self.logger.warning(f'No capital structure found for {company_code}')
            capital_structure = {}

        # Yield final result
        yield {
            'company_code': company_code,
            'company_profile': company_profile,
            'shareholders': shareholders,
            'capital_structure': capital_structure,
            'scraped_date': datetime.now().isoformat()
        }

    def extract_company_profile(self, data, company_code):
        """Extract company profile from API response"""
        profile = {
            'company_code': data.get('COMPANY_CODE', company_code),
            'security_code': data.get('A_STOCK_CODE', ''),
            'security_name': data.get('COMPANY_ABBR', data.get('NAME', '')),
            'company_full_name': data.get('FULL_NAME', ''),
            'company_full_name_en': data.get('FULL_NAME_EN', data.get('FULL_NAME_IN_ENGLISH', '')),
            'listing_date': data.get('A_LIST_DATE', data.get('LIST_DATE', '')),
            'stock_type': data.get('STOCK_TYPE', ''),
            'list_board': data.get('LIST_BOARD', ''),
            'product_status': data.get('PRODUCT_STATUS', ''),
            'registered_address': data.get('OFFICE_ADDRESS', ''),
            'legal_representative': data.get('LEGAL_REPRESENTATIVE', ''),
            'email': data.get('E_MAIL_ADDRESS', ''),
            'contact_phone': data.get('INVESTOR_TEL', ''),
            'industry_classification': data.get('CSRC_CODE_DESC', ''),
            'province': data.get('REG_PROVINCE', ''),
            'company_website': data.get('FOREIGN_LISTING_ADDRESS', ''),
        }

        # Remove empty values
        return {k: v for k, v in profile.items() if v}

    def extract_shareholders(self, result):
        """Extract shareholders from API response"""
        shareholders = []

        if not result:
            return shareholders

        # Ensure result is a list
        if not isinstance(result, list):
            result = [result]

        for idx, item in enumerate(result[:10], 1):
            shareholder = {
                'rank': str(idx),
                'shareholder_name': str(item.get('NAME', '')),
                'shares': str(item.get('NUMBER_END', '')),
                'percentage': str(item.get('RATIO', '')),
                'report_date': str(item.get('REPORT_DATE', '')),
                'stock_id': str(item.get('STOCK_ID', '')),
            }

            # Remove empty values but keep the structure
            shareholder = {k: v for k, v in shareholder.items() if v}

            if shareholder.get('shareholder_name'):
                shareholders.append(shareholder)

        return shareholders

    def extract_capital_structure(self, result):
        """Extract capital structure from API response"""
        if not result:
            return {}

        # Get first item if list
        data = result[0] if isinstance(result, list) else result

        capital = {
            'total_shares': data.get('TOTAL_SHARE', data.get('TOTAL_SHARES', '')),
            'total_domestic_listed_shares': data.get('A_TOTAL_SHARE', ''),
            'restricted_shares': data.get('LIMITED_SHARE', data.get('RESTRICTED_SHARES', '')),
            'unrestricted_shares': data.get('UNLIMITED_SHARE', data.get('UNRESTRICTED_SHARES', '')),
            'special_voting_shares': data.get('SPECIAL_SHARE', ''),
            'domestic_foreign_shares': data.get('B_TOTAL_SHARE', ''),
            'data_date': data.get('CHANGE_DATE', data.get('DATA_DATE', '')),
        }

        # Remove empty values
        return {k: v for k, v in capital.items() if v}

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f'Request failed: {failure.request.url}')
        self.logger.error(f'Error: {failure.value}')


class SSECompanyListSpider(scrapy.Spider):
    """
    Spider that gets all companies from the list endpoint then scrapes each
    """
    name = 'sse_companies_all'
    allowed_domains = ['query.sse.com.cn', 'www.sse.com.cn']

    custom_settings = SSECompanyAPISpider.custom_settings.copy()

    # SQL ID for getting all companies
    COMPANY_LIST_SQL_ID = 'COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L'

    def __init__(self, max_companies=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_companies = int(max_companies) if max_companies else 50  # Default limit
        self.logger.info(f'Will scrape up to {self.max_companies} companies')

    def start_requests(self):
        """Get full company list"""
        url = f'https://query.sse.com.cn/commonQuery.do?isPagination=false&sqlId={self.COMPANY_LIST_SQL_ID}'
        yield scrapy.Request(
            url=url,
            callback=self.parse_company_list,
            dont_filter=True
        )

    def parse_company_list(self, response):
        """Parse company list and extract company codes"""
        main_spider = SSECompanyAPISpider()

        data = main_spider.parse_response(response)

        if not data or not data.get('result'):
            self.logger.error('Failed to get company list')
            return

        result = data['result']
        self.logger.info(f'Found {len(result)} total companies')

        # Extract unique company codes
        company_codes = []
        seen = set()

        for company in result:
            code = company.get('COMPANY_CODE', '')
            if code and code not in seen:
                seen.add(code)
                company_codes.append(code)

        self.logger.info(f'Extracted {len(company_codes)} unique company codes')

        # Limit companies
        company_codes = company_codes[:self.max_companies]
        self.logger.info(f'Processing {len(company_codes)} companies')

        # Now scrape each company
        for code in company_codes:
            url = main_spider.build_url('company_info', code)
            yield scrapy.Request(
                url=url,
                callback=main_spider.parse_company_info,
                meta={'company_code': code},
                dont_filter=True
            )