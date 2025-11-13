
from itemadapter import ItemAdapter
from ..utils.name_normalization import normalize_company_name_cn, normalize_company_name_en

class NormalizationPipeline:
    def process_item(self, item, spider):
        ad = ItemAdapter(item)
        if ad.get("company_name_ch"):
            ad["company_name_ch"] = normalize_company_name_cn(ad["company_name_ch"])
        if ad.get("company_name_en"):
            ad["company_name_en"] = normalize_company_name_en(ad["company_name_en"])
        return item
