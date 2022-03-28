from pathlib import Path

import tablib
from faker import Faker


class StreamDataGenerator:

    def __init__(self, seed=0, data_dir='data', start_year=2000, end_year=2022, company_count=10):
        print(f'Generating data for {company_count} companies in {start_year}-{end_year}')
        Faker.seed(seed)
        self.faker = Faker(['en_GB'])
        self.organisations = [self.faker.company() for _ in range(company_count)]
        self.years = list(range(start_year, end_year))
        self.DATA_DIR = Path(data_dir)

    def generate_data(self):
        """
        Generate a list of random data.

        :param num_rows: number of rows to generate
        :return: list of random data
        """

        for org in self.organisations:
            for year in self.years:
                print(f'Generating data for {org} in {year}')
                self.generate_files(org, year)

    def generate_files(self, org, year):
        _modes = ['csv', 'xslx-single', 'xslx-multi']
        _mode = self.faker.random.choice(_modes)
        datasets = self.generate_dataset(org, year)
        if _mode == 'csv':
            return self.save_csv(org, year, datasets)
        elif _mode == 'xslx-single':
            return self.save_xlsx_single(org, year, datasets)
        elif _mode == 'xslx-multi':
            return self.save_xlsx_multi(org, year, datasets)

    def generate_dataset(self, org, year):
        col_count = 10
        sheet_data = []
        for sheets in range(1, 11):
            headers = [
                self.get_column_name(col+1)
                for col in range(col_count)
            ]
            data = tablib.Dataset(headers=headers)
            for row in range(1, self.faker.random.randint(20, 100)):
                data.append([
                    self.faker.first_name(),
                    self.faker.last_name(),
                    self.faker.job(),
                    self.faker.address(),
                    self.faker.random.randint(13, 99),
                    self.faker.address(),
                    self.faker.credit_card_number(),
                    year,
                    org,
                    self.faker.bs(),
                ])
            sheet_data.append(data)
        return sheet_data

    def get_column_name(self, col):
        prefix = self.faker.random.choice(['col', 'c', 'column'])
        style = self.faker.random.choice(['lower', 'camel', 'upper'])
        if style == 'camel':
            prefix = prefix[0].upper() + prefix[1:]
        elif style == 'upper':
            prefix = prefix.upper()

        separator = self.faker.random.choice(['_', '-', '', ''])
        return f'{prefix}{separator}{col}'

    def save_csv(self, org, year, datasets):
        sheet_prefix = self.faker.random.choice(['table', 'sheet', 'data'])
        separator = self.faker.random.choice(['_', '-', '', ''])
        pattern = self.faker.random.choice([
            '{org}-{year}-{sheet}.csv',
            '{org}/{year}/{sheet_prefix}{separator}{sheet}.csv',
            '{year}/{org}/{sheet_prefix}{separator}{sheet}.csv',
            '{year}-{org}/{sheet_prefix}{separator}{sheet}.csv',
            '{org}-{year}/{sheet_prefix}{separator}{sheet}.csv',
        ])
        for sheet, data in enumerate(datasets):
            filename = pattern.format(
                org=org,
                year=year,
                sheet_prefix=sheet_prefix,
                separator=separator,
                sheet=sheet+1,
            )
            filename = self.DATA_DIR / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, 'wt') as f:
                f.write(data.export('csv'))

    def save_xlsx_single(self, org, year, datasets):
        sheet_prefix = self.faker.random.choice(['table', 'sheet', 'data'])
        separator = self.faker.random.choice(['_', '-', '', ''])
        pattern = self.faker.random.choice([
            '{org}-{year}-{sheet}.csv',
            '{org}/{year}/{sheet_prefix}{separator}{sheet}.xlsx',
            '{year}/{org}/{sheet_prefix}{separator}{sheet}.xlsx',
            '{year}-{org}/{sheet_prefix}{separator}{sheet}.xlsx',
            '{org}-{year}/{sheet_prefix}{separator}{sheet}.xlsx',
        ])
        for sheet, data in enumerate(datasets):
            filename = pattern.format(
                org=org,
                year=year,
                sheet_prefix=sheet_prefix,
                separator=separator,
                sheet=sheet+1,
            )
            filename = self.DATA_DIR / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(data.export('xlsx'))

    def save_xlsx_multi(self, org, year, datasets):
        sheet_prefix = self.faker.random.choice(['table', 'sheet', 'data'])
        separator = self.faker.random.choice(['_', '-', '', ''])
        pattern = self.faker.random.choice([
            '{org}-{year}.xlsx',
            '{org}/{year}.xlsx',
            '{year}/{org}.xlsx',
            '{year}-{org}.xlsx',
            '{org}-{year}.xlsx',
        ])
        for sheet, data in enumerate(datasets):
            data.title = f'{sheet_prefix}{separator}{sheet+1}'
        databook = tablib.Databook(datasets)

        filename = pattern.format(
            org=org,
            year=year,
            sheet_prefix=sheet_prefix,
            separator=separator,
        )
        filename = self.DATA_DIR / filename
        filename.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(databook.export('xlsx'))


if __name__ == '__main__':
    generator = StreamDataGenerator()
    generator.generate_data()
