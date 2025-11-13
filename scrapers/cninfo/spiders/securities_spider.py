import json
import scrapy
from ..items import SecurityItem
from ..utils.jsonp import strip_jsonp
from ..utils.exchange import map_exchange_by_code, map_board_by_code

class SecuritiesSpider(scrapy.Spider):
    """
    Harvests security-level facts from Yellowpages per-security XHR.
    Produces: 10_snapshots/<date>/cn_securities.csv
    """
    name = "cninfo_securities"
    allowed_domains = ["cninfo.com.cn", "www.cninfo.com.cn"]
    custom_settings = {"DOWNLOAD_DELAY": 0.5}

    async def start(self):
        for r in self.start_requests():
            yield r

    def start_requests(self):
        # Universe list (records[]: includes SECCODE etc.)
        yp = ("https://www.cninfo.com.cn/data/yellowpages/"
              "getYellowpageStockList?type=cn&pagenum=-1&keyword=&Sortcolumn=SECCODE")
        yield scrapy.Request(yp, callback=self.parse_yellowpages, meta={"evidence": yp})

    def parse_yellowpages(self, response):
        """Enumerate all scodes, schedule per-security detail calls (type=2)."""
        txt = response.text
        try:
            data = json.loads(txt)
        except Exception:
            data = strip_jsonp(txt)

        rows = data.get("records") if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not rows:
            self.logger.warning("Yellowpages list empty; first 200: %r", txt[:200])
            return

        limit = int(getattr(self, "limit", 0)) or 0  # for quick tests: -a limit=50
        count = 0

        for r in rows:
            scode = str(r.get("SECCODE") or r.get("seccode") or "").zfill(6)
            if not scode:
                continue

            # type=2 has the 'transaction / board' block you observed
            url = f"https://www.cninfo.com.cn/data/yellowpages/getIndexData?scode={scode}&type=2"
            meta = {
                "scode": scode,
                "evidence": url,
            }
            yield scrapy.Request(url, callback=self.parse_security_detail, meta=meta, dont_filter=True)

            count += 1
            if limit and count >= limit:
                break

        self.logger.info("Scheduled %d security detail requests", count)

    def parse_security_detail(self, response):
        """
        Map per-security detail payload to SecurityItem using the 'snapshot5015Data' block:
          - list_date: snapshot5015Data[0]['F003V']  (YYYY-MM-DD)
          - isin: parse from snapshot5015Data[0]['F001V'] when it starts with 'ISIN:'
          - exchange: snapshot5015Data[0]['F012V'] (normalize to SSE/SZSE/BSE)
          - stock_code: SECCODE (fallback to scode)
          - board/share_class: derived from code if not present
        """
        snapdate = self.settings.get("SNAPSHOT_DATE")
        scode = response.meta["scode"]
        txt = response.text

        # Load JSON or JSONP
        try:
            j = json.loads(txt)
        except Exception:
            j = strip_jsonp(txt)

        # Normalize to a dict 'payload'. We may have nested dicts.
        if isinstance(j, dict):
            # Most consistent place for what we need:
            payload = j
        else:
            payload = {}

        # --- Find the 'snapshot5015Data' record (list with a single dict is common) ---
        snap5015 = None
        if isinstance(payload.get("snapshot5015Data"), list) and payload["snapshot5015Data"]:
            snap5015 = payload["snapshot5015Data"][0]
        elif isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("snapshot5015Data"), list):
            arr = payload["data"]["snapshot5015Data"]
            if arr:
                snap5015 = arr[0]

        # There can also be a flat 'data' dict with basics like SECCODE:
        flatdata = payload.get("data") if isinstance(payload.get("data"), dict) else payload

        # --- Field extraction (defensive) ---
        stock_code = str(
            (flatdata.get("SECCODE") if isinstance(flatdata, dict) else None)
            or scode
        ).zfill(6)

        # Exchange: prefer explicit F012V in snapshot5015Data
        exchange = None
        if isinstance(snap5015, dict):
            xchg_raw = snap5015.get("F012V")
            if xchg_raw:
                s = str(xchg_raw)
                if "上交" in s or "上海" in s or "SSE" in s.upper() or "Shanghai" in s:
                    exchange = "SSE"
                elif "深交" in s or "深圳" in s or "SZSE" in s.upper() or "Shenzhen" in s:
                    exchange = "SZSE"
                elif "北交" in s or "北京" in s or "BSE" in s.upper() or "Beijing" in s:
                    exchange = "BSE"
        if not exchange:
            exchange, _ = map_exchange_by_code(stock_code)

        # Board: keep derivation unless you later find an explicit key on this endpoint
        board = map_board_by_code(stock_code, exchange)

        # Share class: B-share ranges; else A
        share_class = "A"
        if stock_code.startswith(("200", "900")):
            share_class = "B"

        # List/delist dates & ISIN from snapshot5015Data
        # List/delist dates & ISIN from snapshot5015Data (robust scan)
        list_date = None
        delist_date = None
        isin = None

        def _maybe_isin(s: str) -> str:
            """Return ISIN if string looks like one; else None."""
            if not s:
                return None
            s2 = s.strip().replace("：", ":")
            # case 1: explicit 'ISIN: XYZ'
            if s2.lower().startswith("isin:"):
                cand = s2.split(":", 1)[1].strip()
                if len(cand) == 12 and cand.isalnum():
                    return cand.upper()
            # case 2: bare 12-char code (common for CN: starts with CNE)
            s3 = s2.replace(" ", "")
            if len(s3) == 12 and s3.isalnum():
                return s3.upper()
            # case 3: embedded 'ISIN' text somewhere; pull last 12-alnum token
            if "isin" in s2.lower():
                parts = [p for p in s2.replace("ISIN", "isin").split() if p.isalnum()]
                for p in reversed(parts):
                    if len(p) == 12 and p.isalnum():
                        return p.upper()
            return None

        if isinstance(snap5015, dict):
            # Listed date is usually here
            list_date = snap5015.get("F003V") or snap5015.get("LIST_DATE")

            # Primary ISIN candidate
            cand = snap5015.get("F001V")
            if isinstance(cand, str):
                isin = _maybe_isin(cand)

            # If still missing, scan all values of this object
            if not isin:
                for v in snap5015.values():
                    if isinstance(v, str):
                        hit = _maybe_isin(v)
                        if hit:
                            isin = hit
                            break

        # Some payloads carry an array of records; scan all for ISIN if still None
        if not isin:
            snap_arr = []
            if isinstance(payload.get("snapshot5015Data"), list):
                snap_arr = payload["snapshot5015Data"]
            elif isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("snapshot5015Data"), list):
                snap_arr = payload["data"]["snapshot5015Data"]

            for rec in snap_arr or []:
                if not isinstance(rec, dict):
                    continue
                for v in rec.values():
                    if isinstance(v, str):
                        hit = _maybe_isin(v)
                        if hit:
                            isin = hit
                            break
                if isin:
                    break

        # Also try any top-level fallbacks if still missing
        if not list_date:
            list_date = flatdata.get("F003V") or flatdata.get("LIST_DATE")
        if not isin:
            isin = flatdata.get("ISIN") or flatdata.get("isin")

        # Also try any top-level fallbacks if still missing
        if not list_date:
            list_date = flatdata.get("F003V") or flatdata.get("LIST_DATE")
        if not isin:
            isin = flatdata.get("ISIN") or flatdata.get("isin")

        # Status: best-effort
        status = "Active"
        if delist_date:
            status = "Delisted"

        item = SecurityItem()
        item["issuer_code"] = (
                (flatdata.get("ORGID") if isinstance(flatdata, dict) else None)
                or (flatdata.get("ORGCODE") if isinstance(flatdata, dict) else None)
                or (flatdata.get("SECID") if isinstance(flatdata, dict) else None)
                or stock_code
        )
        item["stock_code"] = stock_code
        item["exchange"] = exchange
        item["board"] = board
        item["share_class"] = share_class
        item["status"] = status
        item["list_date"] = list_date
        item["delist_date"] = delist_date
        item["isin"] = isin
        item["evidence_url"] = response.meta["evidence"]
        item["snapshot_date"] = snapdate
        yield item

