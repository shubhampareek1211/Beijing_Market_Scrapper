
from itemadapter import ItemAdapter
from .state import StateStore
from scrapy.exceptions import DropItem

class DedupePipeline:
    def __init__(self, state_dir):
        self.state = StateStore(state_dir)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(state_dir=crawler.settings.get("STATE_DIR"))

    def process_item(self, item, spider):
        ad = ItemAdapter(item).asdict()
        key_parts = [item.__class__.__name__]
        for k in ("issuer_code","stock_code","report_date","rank"):
            if k in ad and ad.get(k) is not None:
                key_parts.append(str(ad[k]))
        key = "::".join(key_parts)
        changed = self.state.put_if_changed(key, ad)
        if not changed:
            raise DropItem(f"Duplicate/unchanged item skipped: {key}")
        return item
