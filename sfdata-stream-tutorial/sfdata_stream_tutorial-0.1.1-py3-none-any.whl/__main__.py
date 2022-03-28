import click

from ._generate import StreamDataGenerator


@click.command()
@click.option('--dir', default='data', help='Where to write the data')
@click.option('--seed', default=0, help='Random seed')
@click.option('--start-year', default=2010, help='Start year')
@click.option('--end-year', default=2022, help='End year')
@click.option('--companies', default=10, help='Company count')
def generate(dir:str, seed:int, start_year:int, end_year:int, companies:int):
    generator = StreamDataGenerator(seed=seed, data_dir=dir, start_year=start_year, end_year=end_year,
                                    company_count=companies)
    generator.generate_data()


if __name__ == '__main__':
    generate()