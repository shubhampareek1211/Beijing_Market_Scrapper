import json
import scrapy
from ..items import IssuerItem
from ..utils.exchange import map_exchange_by_code, map_board_by_code


class UniverseSpider(scrapy.Spider):
    name = "cninfo_universe"
    custom_settings = {"DOWNLOAD_DELAY": 0.5}

    async def start(self):
        for r in self.start_requests():
            yield r

    def start_requests(self):
        # CN snapshot - generates cn_companies_cn.csv
        yield scrapy.Request(
            "https://www.cninfo.com.cn/data/yellowpages/getYellowpageStockList?type=cn&pagenum=-1&keyword=&Sortcolumn=SECCODE",
            callback=self.parse_cn_snapshot,
            meta={"evidence": "https://www.cninfo.com.cn/data/yellowpages/getYellowpageStockList?type=cn"}
        )
        # EN snapshot - generates cn_companies_en.csv
        yield scrapy.Request(
            "https://www.cninfo.com.cn/data/yellowpages/getYellowpageStockList?type=en&pagenum=-1&keyword=&Sortcolumn=SECCODE",
            callback=self.parse_en_snapshot,
            meta={"evidence": "https://www.cninfo.com.cn/data/yellowpages/getYellowpageStockList?type=en"}
        )

    def parse_cn_snapshot(self, response):
        """Parse CN company list - outputs to cn_companies_cn.csv"""
        snapdate = self.settings.get("SNAPSHOT_DATE")
        txt = response.text

        # Parse JSON
        try:
            j = json.loads(txt)
        except Exception:
            from ..utils.jsonp import strip_jsonp
            j = strip_jsonp(txt)

        # Extract rows
        rows = []
        if isinstance(j, dict):
            if isinstance(j.get("records"), list):
                rows = j["records"]
            elif isinstance(j.get("data"), list):
                rows = j["data"]
        elif isinstance(j, list):
            rows = j

        self.logger.info(f"CN Snapshot: Found {len(rows)} companies")

        if not rows:
            self.logger.warning("CN snapshot empty; first 200 chars: %r", txt[:200])
            return

        # Emit IssuerItem for each company
        for row in rows:
            code = str(row.get("SECCODE") or row.get("seccode") or "").zfill(6)
            if not code:
                continue

            exch, board = map_exchange_by_code(code)

            item = IssuerItem()
            item["issuer_code"] = row.get("ORGID") or row.get("ORGCODE") or row.get("SECID") or code
            item["company_name_ch"] = row.get("ORGNAME") or row.get("SECNAME") or row.get("orgname") or row.get(
                "secname")
            item["company_name_en"] = None  # Not in CN endpoint
            item["short_name_ch"] = row.get("SECNAME") or row.get("secname")
            item["short_name_en"] = None
            item["exchange"] = exch
            item["board"] = board or map_board_by_code(code, exch)
            item["region"] = "CN"
            item["status"] = "Active"  # Default; refine if status field exists
            item["org_type"] = row.get("ORGTYPE") or row.get("orgtype") or "上市公司"
            item["evidence_url"] = response.meta.get("evidence")
            item["snapshot_date"] = snapdate

            yield item

    def parse_en_snapshot(self, response):
        """Parse EN company list - outputs to cn_companies_en.csv"""
        snapdate = self.settings.get("SNAPSHOT_DATE")
        txt = response.text

        # Parse JSON
        try:
            j = json.loads(txt)
        except Exception:
            from ..utils.jsonp import strip_jsonp
            j = strip_jsonp(txt)

        # Extract rows
        rows = []
        if isinstance(j, dict):
            if isinstance(j.get("records"), list):
                rows = j["records"]
            elif isinstance(j.get("data"), list):
                rows = j["data"]
        elif isinstance(j, list):
            rows = j

        self.logger.info(f"EN Snapshot: Found {len(rows)} companies")

        if not rows:
            self.logger.warning("EN snapshot empty; first 200 chars: %r", txt[:200])
            return

        # Emit IssuerItem for each company (with _emit_en flag)
        for row in rows:
            code = str(row.get("SECCODE") or row.get("seccode") or "").zfill(6)
            if not code:
                continue

            exch, board = map_exchange_by_code(code)

            item = IssuerItem()
            item["issuer_code"] = row.get("ORGID") or row.get("ORGCODE") or row.get("SECID") or code
            item["company_name_ch"] = None  # Not in EN endpoint typically
            item["company_name_en"] = row.get("ORGNAME") or row.get("SECNAME") or row.get("orgname") or row.get(
                "secname")
            item["short_name_ch"] = None
            item["short_name_en"] = row.get("SECNAME") or row.get("secname")
            item["exchange"] = exch
            item["board"] = board or map_board_by_code(code, exch)
            item["region"] = "CN"
            item["status"] = "Active"
            item["org_type"] = row.get("ORGTYPE") or row.get("orgtype") or "Listed Company"
            item["evidence_url"] = response.meta.get("evidence")
            item["snapshot_date"] = snapdate

            # Special flag to route to EN file
            item._emit_en = True

            yield item