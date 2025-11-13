
from itemadapter import ItemAdapter
import logging

class QAPipeline:
    def __init__(self):
        self.counts = {}

    def process_item(self, item, spider):
        cls = item.__class__.__name__
        self.counts[cls] = self.counts.get(cls, 0) + 1
        ad = ItemAdapter(item)
        if not ad.get("snapshot_date"):
            spider.logger.warning(f"Item missing snapshot_date: {cls}")
        return item

    def close_spider(self, spider):
        logging.getLogger(__name__).info(f"QA COUNTS: {self.counts}")
