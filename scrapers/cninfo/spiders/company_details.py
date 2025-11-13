# cninfo_pipeline/spiders/company_details_spider.py

import json
import re
import scrapy

from ..items import CompanyDetailItem

# Local JSONP stripper so this file is self-contained
_JSONP_RE = re.compile(r"^[\s\r\n\t]*([$\w]+)\s*\((.*)\)\s*;?\s*$", re.S)
def _strip_jsonp(txt: str):
    m = _JSONP_RE.match(txt or "")
    if m:
        inner = m.group(2)
        try:
            return json.loads(inner)
        except Exception:
            pass
    # if it's already JSON, try to load; otherwise return {}
    try:
        return json.loads(txt)
    except Exception:
        return {}

class CompanyDetailsSpider(scrapy.Spider):
    """
    Collects company profile details from Yellowpages XHR (type=2)
    and writes them (via your existing exporter) to:
      10_snapshots/<SNAPSHOT_DATE>/cn_company_details.csv
    """
    name = "cninfo_company_details"
    allowed_domains = ["cninfo.com.cn", "www.cninfo.com.cn"]
    custom_settings = {
        "DOWNLOAD_DELAY": 0.5,  # be polite to the site
    }

    # use start_requests for Scrapy <2.13 compatibility, still works on 2.13+
    def start_requests(self):
        yp = ("https://www.cninfo.com.cn/data/yellowpages/"
              "getYellowpageStockList?type=cn&pagenum=-1&keyword=&Sortcolumn=SECCODE")
        yield scrapy.Request(yp, callback=self.parse_yellowpages, meta={"evidence": yp})

    def parse_yellowpages(self, response):
        data = _strip_jsonp(response.text)
        rows = data.get("records") if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not rows:
            self.logger.warning("Yellowpages list empty; first 200: %r", (response.text or "")[:200])
            return

        limit = int(getattr(self, "limit", 0) or 0)                 # e.g. -a limit=50
        only  = (getattr(self, "only", "") or "").strip()           # e.g. -a only=000008

        scheduled = 0
        for r in rows:
            scode = str(r.get("SECCODE") or r.get("seccode") or "").zfill(6)
            if not scode:
                continue
            if only and scode != only:
                continue

            url = f"https://www.cninfo.com.cn/data/yellowpages/getIndexData?scode={scode}&type=2"
            yield scrapy.Request(
                url,
                callback=self.parse_company_detail_type2,
                meta={"scode": scode, "evidence": url},
                dont_filter=True,
            )
            scheduled += 1
            if limit and scheduled >= limit:
                break

        self.logger.info("Scheduled %d company detail (type=2) requests", scheduled)

    # Replace the parse_company_detail_type2 method in company_details.py with this:

    def parse_company_detail_type2(self, response):
        snapdate = self.settings.get("SNAPSHOT_DATE")
        scode = response.meta["scode"]

        j = _strip_jsonp(response.text)

        # The response structure is: data -> { snapshot5015Data: [...], cninfo5015Data: [...], cninfo5023Data: [...] }
        data_block = j.get("data") if isinstance(j, dict) and isinstance(j.get("data"), dict) else j
        if not isinstance(data_block, dict):
            data_block = {}

        # Extract the three key arrays
        snapshot5015 = None
        if isinstance(data_block.get("snapshot5015Data"), list) and data_block["snapshot5015Data"]:
            snapshot5015 = data_block["snapshot5015Data"][0]

        cninfo5015 = None
        if isinstance(data_block.get("cninfo5015Data"), list) and data_block["cninfo5015Data"]:
            cninfo5015 = data_block["cninfo5015Data"][0]

        cninfo5023 = None
        if isinstance(data_block.get("cninfo5023Data"), list) and data_block["cninfo5023Data"]:
            cninfo5023 = data_block["cninfo5023Data"][0]

        # ---- Extract fields based on your mapping ----

        # Issuer code: SECCODE from cninfo5015Data
        issuer_code = None
        if isinstance(cninfo5015, dict):
            issuer_code = cninfo5015.get("SECCODE")
        if not issuer_code and isinstance(snapshot5015, dict):
            issuer_code = snapshot5015.get("SECCODE")
        if not issuer_code:
            issuer_code = scode
        issuer_code = str(issuer_code or "").zfill(6)

        # Company names
        company_name_en = None
        company_name_ch = None
        if isinstance(snapshot5015, dict):
            company_name_en = snapshot5015.get("ORGNAME")  # English name
        if isinstance(cninfo5015, dict):
            company_name_ch = cninfo5015.get("ORGNAME")  # Chinese name

        # Dates and contact info from snapshot5015Data (all F00xV fields)
        established_date = None  # F002V - Founded date
        list_date = None  # F003V - Listing date
        website = None  # F004V - Website
        registered_addr = None  # F005V - Domicile/legal registered office
        office_addr = None  # F006V - Office address
        email = None  # F007V - Email
        phone = None  # F008V - Telephone

        if isinstance(snapshot5015, dict):
            established_date = snapshot5015.get("F002V")
            list_date = snapshot5015.get("F003V")
            website = snapshot5015.get("F004V")
            registered_addr = snapshot5015.get("F005V")
            office_addr = snapshot5015.get("F006V")
            email = snapshot5015.get("F007V")
            phone = snapshot5015.get("F008V")

        # Industry classifications from snapshot5015Data
        industry_csic = None  # F010V - Business scope/industry (CSRC Sector)
        industry_csic_sub = None  # F011V - Business CSRC sub-sector

        if isinstance(snapshot5015, dict):
            industry_csic = snapshot5015.get("F010V")
            industry_csic_sub = snapshot5015.get("F011V")

        # Business description from cninfo5023Data
        business_profile_cn = None  # F001V - First paragraph business description
        if isinstance(cninfo5023, dict):
            business_profile_cn = cninfo5023.get("F001V")

        # ---- Build item ----
        item = CompanyDetailItem()
        item["issuer_code"] = issuer_code
        item["company_name_ch"] = company_name_ch
        item["company_name_en"] = company_name_en
        item["business_profile_cn"] = business_profile_cn
        item["business_scope_cn"] = None  # Not in this endpoint
        item["industry_csic"] = industry_csic
        item["registered_capital"] = None  # Not extracted yet
        item["legal_representative"] = None  # Not extracted yet
        item["established_date"] = established_date
        item["registered_address"] = registered_addr
        item["website"] = website
        item["email"] = email
        item["phone"] = phone
        item["disclosure_lang"] = "cn"
        item["evidence_url"] = response.meta["evidence"]
        item["snapshot_date"] = snapdate

        yield item
