import json
import scrapy
from ..items import JoinedCompanySecurityItem
from ..utils.exchange import map_exchange_by_code, map_board_by_code


class JoinedViewSpider(scrapy.Spider):
    """
    Combines company (issuer) and security data into a single joined view.
    Merges CN and EN data into single rows per company.
    Produces: 10_snapshots/<date>/cn_joined_company_security.csv
    """
    name = "cninfo_joined_view"
    allowed_domains = ["cninfo.com.cn", "www.cninfo.com.cn"]
    custom_settings = {"DOWNLOAD_DELAY": 0.5}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store CN and EN data for merging
        self.cn_data = {}  # key: issuer_code, value: row dict
        self.en_data = {}  # key: issuer_code, value: row dict

    async def start(self):
        for r in self.start_requests():
            yield r

    def start_requests(self):
        # Get universe from yellowpages (has both company and security info)
        yp_cn = ("https://www.cninfo.com.cn/data/yellowpages/"
                 "getYellowpageStockList?type=cn&pagenum=-1&keyword=&Sortcolumn=SECCODE")
        yp_en = ("https://www.cninfo.com.cn/data/yellowpages/"
                 "getYellowpageStockList?type=en&pagenum=-1&keyword=&Sortcolumn=SECCODE")

        # Use meta to track request order
        yield scrapy.Request(yp_cn, callback=self.parse_cn,
                             meta={"evidence_issuer": yp_cn, "lang": "cn"},
                             dont_filter=True)
        yield scrapy.Request(yp_en, callback=self.parse_en,
                             meta={"evidence_issuer": yp_en, "lang": "en"},
                             dont_filter=True)

    def parse_cn(self, response):
        """Parse CN list and store in memory"""
        txt = response.text

        try:
            j = json.loads(txt)
        except Exception:
            from ..utils.jsonp import strip_jsonp
            j = strip_jsonp(txt)

        rows = []
        if isinstance(j, dict):
            rows = j.get("records") or j.get("data") or []
        elif isinstance(j, list):
            rows = j

        self.logger.info(f"CN data: Found {len(rows)} companies")

        if not rows:
            self.logger.warning("CN list empty; first 200: %r", txt[:200])
            return

        for row in rows:
            stock_code = str(row.get("SECCODE") or row.get("seccode") or "").zfill(6)
            if not stock_code:
                continue

            issuer_code = (row.get("ORGID") or row.get("ORGCODE") or
                           row.get("SECID") or stock_code)

            # Store CN data by issuer_code
            self.cn_data[issuer_code] = {
                "stock_code": stock_code,
                "company_name_ch": (row.get("ORGNAME") or row.get("SECNAME") or
                                    row.get("orgname") or row.get("secname")),
                "evidence_cn": response.meta.get("evidence_issuer"),
            }

        self.logger.info(f"Stored {len(self.cn_data)} CN records")

    def parse_en(self, response):
        """Parse EN list, merge with CN data, and emit joined items"""
        txt = response.text

        try:
            j = json.loads(txt)
        except Exception:
            from ..utils.jsonp import strip_jsonp
            j = strip_jsonp(txt)

        rows = []
        if isinstance(j, dict):
            rows = j.get("records") or j.get("data") or []
        elif isinstance(j, list):
            rows = j

        self.logger.info(f"EN data: Found {len(rows)} companies")

        if not rows:
            self.logger.warning("EN list empty; first 200: %r", txt[:200])
            return

        # Store EN data
        for row in rows:
            stock_code = str(row.get("SECCODE") or row.get("seccode") or "").zfill(6)
            if not stock_code:
                continue

            issuer_code = (row.get("ORGID") or row.get("ORGCODE") or
                           row.get("SECID") or stock_code)

            self.en_data[issuer_code] = {
                "company_name_en": (row.get("ORGNAME") or row.get("SECNAME") or
                                    row.get("orgname") or row.get("secname")),
                "evidence_en": response.meta.get("evidence_issuer"),
            }

        self.logger.info(f"Stored {len(self.en_data)} EN records")

        # Now merge and emit all records
        yield from self._merge_and_emit()

    def _merge_and_emit(self):
        """Merge CN and EN data, emit joined items"""
        snapdate = self.settings.get("SNAPSHOT_DATE")

        # Get union of all issuer codes
        all_issuers = set(self.cn_data.keys()) | set(self.en_data.keys())

        self.logger.info(f"Merging {len(all_issuers)} companies (CN: {len(self.cn_data)}, EN: {len(self.en_data)})")

        emitted = 0
        for issuer_code in all_issuers:
            cn_record = self.cn_data.get(issuer_code, {})
            en_record = self.en_data.get(issuer_code, {})

            # Get stock code from either source
            stock_code = cn_record.get("stock_code") or issuer_code
            if not stock_code or len(stock_code) != 6:
                continue

            exch, board = map_exchange_by_code(stock_code)

            # Build security detail URLs
            security_evidence_cn = f"https://www.cninfo.com.cn/new/snapshot/companyDetailCn?code={stock_code}"
            security_evidence_en = f"https://www.cninfo.com.cn/new/snapshot/companyDetailEn?code={stock_code}"

            item = JoinedCompanySecurityItem()
            item["issuer_code"] = issuer_code

            # Merge names from both sources
            item["company_name_ch"] = cn_record.get("company_name_ch")
            item["company_name_en"] = en_record.get("company_name_en")

            item["stock_code"] = stock_code
            item["exchange"] = exch
            item["board"] = board or map_board_by_code(stock_code, exch)
            item["share_class"] = "B" if stock_code.startswith("200") else "A"
            item["status"] = "Active"
            item["list_date"] = None  # Would need detail page
            item["delist_date"] = None
            item["isin"] = None  # Would need detail page

            # Use CN evidence as primary, fallback to EN
            item["issuer_evidence_url"] = (cn_record.get("evidence_cn") or
                                           en_record.get("evidence_en"))
            item["security_evidence_url"] = security_evidence_cn
            item["snapshot_date"] = snapdate

            emitted += 1
            yield item

        self.logger.info(f"Emitted {emitted} joined records")

        # Check for mismatches
        cn_only = len(self.cn_data) - len(self.en_data & self.cn_data.keys())
        en_only = len(self.en_data) - len(self.en_data & self.cn_data.keys())

        if cn_only > 0:
            self.logger.warning(f"{cn_only} companies only in CN list")
        if en_only > 0:
            self.logger.warning(f"{en_only} companies only in EN list")