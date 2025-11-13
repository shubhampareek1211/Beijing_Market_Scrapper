import json
import csv
from datetime import datetime
from pathlib import Path


class JsonWriterPipeline:
    """Pipeline to write scraped data to JSON file"""

    def open_spider(self, spider):
        from datetime import datetime
        from pathlib import Path

        # Create output directory with today's date
        today = datetime.now().strftime('%Y-%m-%d')
        self.output_dir = Path('output') / today
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%H%M%S')
        json_file = self.output_dir / f'companies_{today}_{timestamp}.json'

        self.file = open(json_file, 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True
        self.items = []

        spider.logger.info(f'JSON output: {json_file}')

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()
        spider.logger.info(f'Saved {len(self.items)} companies to JSON')

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False, indent=2)
        if not self.first_item:
            self.file.write(',\n')
        self.file.write(line)
        self.first_item = False
        self.items.append(item)
        return item


class CsvWriterPipeline:
    """Pipeline to write company profiles to CSV"""

    def open_spider(self, spider):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create output directory
        Path('output').mkdir(exist_ok=True)

        # Company profile CSV
        self.profile_file = open(f'output/company_profiles_{timestamp}.csv', 'w',
                                 newline='', encoding='utf-8-sig')
        self.profile_fieldnames = None
        self.profile_writer = None

        # Shareholders CSV
        self.shareholders_file = open(f'output/shareholders_{timestamp}.csv', 'w',
                                      newline='', encoding='utf-8-sig')
        # Find this section in pipelines.py around line 54-60
        self.shareholders_writer = csv.DictWriter(
            self.shareholders_file,
            fieldnames=['company_code', 'rank', 'shareholder_name', 'shares',
                        'percentage', 'report_date', 'stock_id',
                        'shares_numeric', 'percentage_numeric']  # ADD THESE TWO FIELDS
        )
        self.shareholders_writer.writeheader()

        # Capital structure CSV
        self.capital_file = open(f'output/capital_structure_{timestamp}.csv', 'w',
                                 newline='', encoding='utf-8-sig')
        self.capital_fieldnames = None
        self.capital_writer = None

        spider.logger.info(f'CSV files created in output/ directory')

    def close_spider(self, spider):
        self.profile_file.close()
        self.shareholders_file.close()
        self.capital_file.close()
        spider.logger.info('CSV files closed')

    def process_item(self, item, spider):
        company_code = item.get('company_code', '')

        # Write company profile
        profile = item.get('company_profile', {})
        if profile:
            # Initialize writer with actual fields from first item
            if not self.profile_writer:
                self.profile_fieldnames = list(profile.keys())
                self.profile_writer = csv.DictWriter(
                    self.profile_file,
                    fieldnames=self.profile_fieldnames
                )
                self.profile_writer.writeheader()

            # Only write fields that exist in the header
            row = {k: v for k, v in profile.items() if k in self.profile_fieldnames}
            self.profile_writer.writerow(row)
            spider.logger.debug(f'Wrote company profile for {company_code}')

        # Write shareholders
        shareholders = item.get('shareholders', [])
        if shareholders:
            for shareholder in shareholders:
                row = {'company_code': company_code}
                row.update(shareholder)
                self.shareholders_writer.writerow(row)
            spider.logger.debug(f'Wrote {len(shareholders)} shareholders for {company_code}')

        # Write capital structure
        capital = item.get('capital_structure', {})
        if capital:
            capital_with_code = {'company_code': company_code}
            capital_with_code.update(capital)

            # Initialize writer with actual fields
            if not self.capital_writer:
                self.capital_fieldnames = list(capital_with_code.keys())
                self.capital_writer = csv.DictWriter(
                    self.capital_file,
                    fieldnames=self.capital_fieldnames
                )
                self.capital_writer.writeheader()

            # Only write fields that exist
            row = {k: v for k, v in capital_with_code.items() if k in self.capital_fieldnames}
            self.capital_writer.writerow(row)
            spider.logger.debug(f'Wrote capital structure for {company_code}')

        return item


class DataCleaningPipeline:
    """Pipeline to clean and normalize data"""

    def process_item(self, item, spider):
        # Clean company profile
        if 'company_profile' in item:
            profile = item['company_profile']
            for key, value in profile.items():
                if isinstance(value, str):
                    # Remove extra whitespace
                    profile[key] = ' '.join(value.split())
                    # Remove common suffixes
                    profile[key] = profile[key].replace('/-', '').strip()

        # Clean shareholders data
        if 'shareholders' in item:
            for shareholder in item['shareholders']:
                if 'shares' in shareholder:
                    # Convert shares to numeric if possible
                    shares_str = shareholder['shares'].replace(',', '')
                    try:
                        shareholder['shares_numeric'] = float(shares_str)
                    except ValueError:
                        pass

                if 'percentage' in shareholder:
                    # Extract numeric percentage
                    pct = shareholder['percentage'].replace('%', '').strip()
                    try:
                        shareholder['percentage_numeric'] = float(pct)
                    except ValueError:
                        pass

        # Add scraping timestamp
        item['scraped_date'] = datetime.now().isoformat()

        return item


class DuplicateFilterPipeline:
    """Pipeline to filter duplicate items"""

    def __init__(self):
        self.seen_codes = set()

    def process_item(self, item, spider):
        company_code = item.get('company_code')
        if company_code in self.seen_codes:
            raise Exception(f"Duplicate item found: {company_code}")
        else:
            self.seen_codes.add(company_code)
            return item
