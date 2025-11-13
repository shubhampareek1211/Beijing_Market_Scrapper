
BOT_NAME = "cninfo_pipeline"
SPIDER_MODULES = ["cninfo_pipeline.spiders"]
NEWSPIDER_MODULE = "cninfo_pipeline.spiders"

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 0.5
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5.0
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8

DEFAULT_REQUEST_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Origin": "https://www.cninfo.com.cn",
    "Referer": "https://www.cninfo.com.cn/",
    "X-Requested-With": "XMLHttpRequest",
}


DOWNLOADER_MIDDLEWARES = {
    "cninfo_pipeline.middlewares.UserAgentMiddleware": 400,
}

ITEM_PIPELINES = {
    "cninfo_pipeline.pipelines.normalization.NormalizationPipeline": 100,
    "cninfo_pipeline.pipelines.dedupe.DedupePipeline": 200,
    "cninfo_pipeline.pipelines.qa.QAPipeline": 300,
    "cninfo_pipeline.pipelines.export.SnapshotExportPipeline": 800,
}

import os, datetime
SNAPSHOT_DIR = os.environ.get("SNAPSHOT_DIR", "10_snapshots")
SNAPSHOT_DATE = os.environ.get("SNAPSHOT_DATE", datetime.date.today().strftime("%Y-%m-%d"))
STATE_DIR = os.environ.get("STATE_DIR", ".state")
