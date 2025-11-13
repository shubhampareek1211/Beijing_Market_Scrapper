# Save this as test_spider.py in sse_scraper/spiders/
import scrapy
import json


class TestSpider(scrapy.Spider):
    name = 'test'

    def start_requests(self):
        url = "https://query.sse.com.cn/commonSoaQuery.do?isPagination=false&sqlId=COMMON_SSE_PL_XBRL_TOP10SHAREHOLDERS&stockId=600000"
        headers = {
            'Referer': 'https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE=600000',
            'X-Requested-With': 'XMLHttpRequest',
        }
        yield scrapy.Request(url, headers=headers, callback=self.parse)

    def parse(self, response):
        self.logger.info(f"Got response: {response.status}")
        data = json.loads(response.text)
        if 'pageHelp' in data and 'data' in data['pageHelp']:
            shareholders = data['pageHelp']['data']
            self.logger.info(f"Found {len(shareholders)} shareholders")
            for s in shareholders:
                self.logger.info(f"Shareholder: {s['NAME']} - {s['NUMBER_END']}")
                yield {
                    'name': s['NAME'],
                    'shares': s['NUMBER_END'],
                    'percentage': s['RATIO']
                }