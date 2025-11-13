import scrapy


class CompanyItem(scrapy.Item):
    """Item for storing company information"""
    company_code = scrapy.Field()
    company_profile = scrapy.Field()
    shareholders = scrapy.Field()
    capital_structure = scrapy.Field()
    url = scrapy.Field()
    scraped_date = scrapy.Field()


class CompanyProfileItem(scrapy.Item):
    """Detailed company profile fields"""
    security_code = scrapy.Field()
    security_name = scrapy.Field()
    extended_security_name = scrapy.Field()
    listing_date = scrapy.Field()
    convertible_bond_name_code = scrapy.Field()
    converted_stock_name_code = scrapy.Field()
    company_full_name = scrapy.Field()
    registered_address = scrapy.Field()
    mailing_address = scrapy.Field()
    legal_representative = scrapy.Field()
    board_secretary = scrapy.Field()
    email = scrapy.Field()
    contact_phone = scrapy.Field()
    industry_classification = scrapy.Field()
    province = scrapy.Field()
    city_district = scrapy.Field()
    company_website = scrapy.Field()
    business_scope = scrapy.Field()


class ShareholderItem(scrapy.Item):
    """Individual shareholder information"""
    rank = scrapy.Field()
    shareholder_name = scrapy.Field()
    shares = scrapy.Field()
    percentage = scrapy.Field()
    shareholder_type = scrapy.Field()


class CapitalStructureItem(scrapy.Item):
    """Capital structure information"""
    total_domestic_listed_shares = scrapy.Field()
    restricted_shares = scrapy.Field()
    unrestricted_shares = scrapy.Field()
    special_voting_shares = scrapy.Field()
    domestic_foreign_shares = scrapy.Field()
    data_date = scrapy.Field()
