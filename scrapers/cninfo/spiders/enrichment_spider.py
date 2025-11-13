import scrapy
from ..items import CompanyDetailItem, TopShareholderItem
from ..utils.jsonp import strip_jsonp
from ..validators.schemas import ensure_percent, ensure_int, ensure_number

class EnrichmentSpider(scrapy.Spider):
    name = "cninfo_enrichment"
    allowed_domains = ["cninfo.com.cn", "www.cninfo.com.cn"]

    async def start(self):
        for r in self.start_requests():
            yield r

    def start_requests(self):
        yp = "https://www.cninfo.com.cn/data/yellowpages/getYellowpageStockList?type=cn&pagenum=-1&keyword=&Sortcolumn=SECCODE"
        yield scrapy.Request(yp, callback=self.parse_yellowpages, meta={"evidence": yp})

    def parse_yellowpages(self, response):
        import json
        snapdate = self.settings.get("SNAPSHOT_DATE")
        txt = response.text

        # 1) Force JSON (this endpoint is returning pure JSON for you)
        try:
            j = json.loads(txt)
        except Exception as e:
            # Fallback to JSONP stripper only if JSON fails
            from ..utils.jsonp import strip_jsonp
            j = strip_jsonp(txt)

        # 2) Choose the container deterministically and log shape
        rows = []
        top_keys = list(j.keys()) if isinstance(j, dict) else None
        if isinstance(j, dict):
            if "records" in j and isinstance(j["records"], list):
                rows = j["records"]
                container = "records"
            elif "data" in j and isinstance(j["data"], list):
                rows = j["data"]
                container = "data"
            else:
                container = "unknown"
        elif isinstance(j, list):
            rows = j
            container = "root_list"
        else:
            container = type(j).__name__

        self.logger.info(
            "Yellowpages shape: type=%s, keys=%s, picked=%s, rows=%s",
            type(j).__name__,
            top_keys[:8] if isinstance(top_keys, list) else top_keys,
            container,
            len(rows) if isinstance(rows, list) else "N/A"
        )

        if not rows:
            self.logger.warning("Yellowpages list empty; first 200 chars: %r", txt[:200])
            return

        # 3) Emit items (Universe: SecurityItem; Enrichment: schedule child requests)
        # ---- Universe spider version ----
        # from ..items import SecurityItem
        # from ..utils.exchange import map_exchange_by_code
        # for row in rows:
        #     code = str(row.get("SECCODE") or row.get("seccode") or "").zfill(6)
        #     if not code:
        #         continue
        #     exch, board = map_exchange_by_code(code)
        #     item = SecurityItem()
        #     item["issuer_code"] = row.get("ORGID") or row.get("ORGCODE") or row.get("SECID")
        #     item["stock_code"] = code
        #     item["exchange"] = exch
        #     item["board"] = board
        #     item["share_class"] = "B" if code.startswith("200") else "A"
        #     item["status"] = "Active"
        #     item["list_date"] = None
        #     item["delist_date"] = None
        #     item["isin"] = None
        #     item["evidence_url"] = response.meta.get("evidence")
        #     item["snapshot_date"] = snapdate
        #     yield item

        # ---- Enrichment spider version ----

        if isinstance(rows[0], dict):
            self.logger.info("YP first-row keys: %s", list(rows[0].keys())[:12])


        # Schedule per-company detail + shareholders
        scheduled = 0
        limit = int(getattr(self, "limit", 0)) or 0   # optional: -a limit=25
        for row in rows:
            scode = str(row.get("SECCODE") or row.get("seccode") or "").zfill(6)
            issuer_code = (
                row.get("ORGID")
                or row.get("ORGCODE")
                or row.get("SECID")
                or scode                         # <- fallback so CSVs don’t have null issuer_code
            )
            company_name_ch = row.get("SECNAME") or row.get("secname")
            if not scode or scode == "000000":
                continue

            url_info = f"https://www.cninfo.com.cn/data/yellowpages/getIndexData?scode={scode}&type=1"
            url_sh   = f"https://www.cninfo.com.cn/data/yellowpages/singleStockData?scode={scode}&sign=1&type=1&mergerMark=shareHoldersData"
            meta = {
                "scode": scode,
                "issuer_code": issuer_code,
                "company_name_ch": company_name_ch
            }
            yield scrapy.Request(url_info, callback=self.parse_company,      meta={**meta, "evidence": url_info}, dont_filter=True)
            yield scrapy.Request(url_sh,   callback=self.parse_shareholders, meta={**meta, "evidence": url_sh},   dont_filter=True)
            scheduled += 2
            if limit and scheduled >= 2 * limit:
                break

        self.logger.info("Scheduled %d child requests for %d stocks", scheduled, scheduled // 2 if scheduled else 0)


    def parse_company(self, response):
        snapdate = self.settings.get("SNAPSHOT_DATE")
        scode = response.meta.get("scode")
        issuer_code = response.meta.get("issuer_code") or scode  # fallback
        fallback_name = response.meta.get("company_name_ch") or scode

        data = strip_jsonp(response.text)
        company = {}
        # Common shapes:
        #   {"baseInfo": {...}, ...}
        #   {"company": {...}, ...}
        #   {"data": {...}, ...}
        # Alternate: {"cninfo5025Data":[...]} (board/management block only)
        if isinstance(data, dict):
            for key in ("baseInfo", "company", "data"):
                if key in data and isinstance(data[key], dict):
                    company = data[key]
                    break

        item = CompanyDetailItem()
        item["issuer_code"] = issuer_code
        item["company_name_ch"] = (
                (company.get("ORGNAME")
                 or company.get("comFullName")
                 or company.get("companyFullName"))
                or fallback_name
        )
        item["company_name_en"] = company.get("ENNAME") or company.get("comFullNameEn") or None
        item["business_profile_cn"] = company.get("COMPROFILE") or company.get("GSJJ") or company.get("COMPANY_INTRO")
        item["business_scope_cn"] = company.get("BUSINESSSCOPE") or company.get("JYFW")
        item["industry_csic"] = company.get("INDUSTRY_CSIC") or company.get("CSRC_IND") or company.get("CSRC_MIDDLE")
        item["registered_capital"] = company.get("REGCAP") or company.get("REGISTEREDCAPITAL")
        item["legal_representative"] = company.get("FRDB") or company.get("LEGALPERSON")
        item["established_date"] = company.get("ESTABLISHDATE") or company.get("FOUNDDATE")
        item["registered_address"] = company.get("REGADDR") or company.get("REGISTERED_ADDRESS")
        item["website"] = company.get("WEBSITE") or company.get("NETADDR")
        item["email"] = company.get("EMAIL")
        item["phone"] = company.get("PHONE")
        item["disclosure_lang"] = "cn"
        item["evidence_url"] = response.meta["evidence"]
        item["snapshot_date"] = snapdate

        if not any([v for k, v in company.items()]) and not fallback_name:
            # truly nothing we can use; log and skip to avoid null-only rows
            self.logger.warning("Empty company object for scode=%s; first 200 chars: %r", scode, response.text[:200])
            return

        yield item

    def parse_shareholders(self, response):
        """
        Parse top shareholders - PDF requires Top 5, but allows up to Top 10 with rank marked.
        We'll collect up to 10 and mark ranks 1-10.
        """
        snapdate = self.settings.get("SNAPSHOT_DATE")
        scode = response.meta.get("scode")
        issuer_code = response.meta.get("issuer_code") or response.meta.get("scode")

        data = strip_jsonp(response.text)
        container = None
        rows = []
        report_date = None

        if isinstance(data, dict) and "shareHoldersData" in data:
            container = data["shareHoldersData"]
            if isinstance(container, dict):
                report_date = container.get("reportDate") or container.get("REPORT_DATE")
                rows = container.get("list") or container.get("data") or []
            elif isinstance(container, list):
                rows = container
        elif isinstance(data, dict):
            rows = data.get("data") or data.get("list") or []
        elif isinstance(data, list):
            rows = data

        if not rows:
            self.logger.warning("No shareholders for scode=%s; first 200 chars: %r", scode, response.text[:200])
            return

        # Detect compact format by presence of F00x keys
        compact = isinstance(rows[0], dict) and any(k.startswith("F00") for k in rows[0].keys())

        # PDF requirement: Keep top 5-10, mark rank
        # Limit to 10 maximum
        MAX_SHAREHOLDERS = 10

        for idx, r in enumerate(rows, start=1):
            # Stop after top 10
            if idx > MAX_SHAREHOLDERS:
                self.logger.debug(f"Stopped at rank {idx - 1} for scode={scode} (max {MAX_SHAREHOLDERS})")
                break

            item = TopShareholderItem()
            item["issuer_code"] = issuer_code

            if compact:
                if report_date is None:
                    report_date = r.get("F001D") or report_date
                item["report_date"] = report_date
                item["rank"] = idx  # Always mark rank 1-10
                item["shareholder_name_ch"] = r.get("F002V")
                item["shareholder_name_en"] = None  # PDF allows this to be blank
                item["holder_type"] = None
                amount = ensure_number(r.get("F003N"))
                item["shares_held"] = int(amount) if amount is not None and float(amount).is_integer() else amount
                item["holding_ratio"] = ensure_percent(r.get("F004N"))
                item["share_class"] = "A"
                item["restricted_flag"] = False
                item["change_direction"] = None
            else:
                # verbose format
                item["report_date"] = report_date or r.get("reportDate") or r.get("REPORT_DATE")
                item["rank"] = r.get("RANK") or r.get("rank") or idx  # Explicit rank or position
                item["shareholder_name_ch"] = r.get("HOLDER_NAME") or r.get("holderName") or r.get("SHAREHOLDER")
                item["shareholder_name_en"] = None  # PDF: "if resolvable; else blank"
                item["holder_type"] = r.get("HOLDER_TYPE") or r.get("holderType")
                item["shares_held"] = ensure_int(r.get("HOLD_NUM") or r.get("holdNum") or r.get("HOLDING"))
                item["holding_ratio"] = ensure_percent(r.get("HOLD_RATIO") or r.get("holdRatio") or r.get("PCT"))
                cls = r.get("SHARE_CLASS") or r.get("shareClass")
                item["share_class"] = "B" if (cls and "B" in str(cls).upper()) else "A"
                restr = r.get("RESTRICTED") or r.get("isRestricted")
                item["restricted_flag"] = True if str(restr).lower() in ("true", "1", "yes", "y") else False
                item["change_direction"] = r.get("CHANGE_DIR") or r.get("changeDir") or None

            item["evidence_url"] = response.meta["evidence"]
            item["snapshot_date"] = snapdate

            # Log if this is rank 5 (common cutoff)
            if idx == 5:
                self.logger.debug(f"Collected top 5 shareholders for scode={scode}")

            yield item

        # Log total collected
        actual_count = min(len(rows), MAX_SHAREHOLDERS)
        self.logger.info(f"Collected {actual_count} shareholders (rank 1-{actual_count}) for scode={scode}")

