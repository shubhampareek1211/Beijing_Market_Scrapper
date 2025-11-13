import os, csv
from itemadapter import ItemAdapter


class SnapshotExportPipeline:
    def __init__(self, base_dir, snapshot_date):
        self.base_dir = base_dir
        self.snapshot_date = snapshot_date
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        snap_date = crawler.settings.get("SNAPSHOT_DATE")
        base_dir = crawler.settings.get("SNAPSHOT_DIR")
        return cls(base_dir=base_dir, snapshot_date=snap_date)

    def open_spider(self, spider):
        self.dir = os.path.join(self.base_dir, self.snapshot_date)
        os.makedirs(self.dir, exist_ok=True)

    def _writer(self, item):
        clsname = item.__class__.__name__

        # Special-case: emit EN issuer list to the EN file (spider sets _emit_en flag)
        if hasattr(item, "_emit_en") and getattr(item, "_emit_en"):
            fname = "cn_companies_en.csv"
        else:
            mapping = {
                "IssuerItem": "cn_companies_cn.csv",
                "SecurityItem": "cn_securities.csv",
                "CompanyDetailItem": "cn_company_details.csv",
                "TopShareholderItem": "cn_top5_shareholders.csv",
                "JoinedCompanySecurityItem": "cn_joined_company_security.csv",
            }
            fname = mapping.get(clsname, f"{clsname}.csv")

        path = os.path.join(self.dir, fname)
        if path not in self.files:
            self.files[path] = {
                "fh": open(path, "w", newline="", encoding="utf-8"),
                "writer": None,
                "header": None
            }

        store = self.files[path]
        ad = ItemAdapter(item).asdict()

        # Remove internal flags from CSV output
        ad.pop("_emit_en", None)

        if store["writer"] is None:
            header = list(ad.keys())
            store["header"] = header
            store["writer"] = csv.DictWriter(store["fh"], fieldnames=header)
            store["writer"].writeheader()

        store["writer"].writerow(ad)

    def process_item(self, item, spider):
        self._writer(item)
        return item

    def close_spider(self, spider):
        for store in self.files.values():
            store["fh"].close()