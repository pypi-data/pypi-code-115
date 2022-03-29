import click
import os
from tabulate import tabulate
import pandas as pd
import geopandas as gpd
from PL94andTigertoSQLite3 import *
from datetime import datetime

@click.command()
@click.option('--program', '-t', prompt='Choice Process', type=click.Choice(['Tiger_Files','Tiger','PL94_171','PL94']))
@click.option('--path',prompt='Path to working Directory', default=os.getcwd(), type=click.Path(exists=True))
def main(program, path):
    os.chdir(path)
    if program == 'PL94_171' or  program == 'PL94':
        database = click.prompt('Please enter SQLite3 Database', type=str)
        Vintage = click.prompt('Please Enter Vitage',type=click.Choice(['2010', '2020']),show_choices=True)
        Table = click.prompt('Please enter Table Name', type=str)
        getPL94(database=database, Exists='fail', Table=Table, Vintage=Vintage)
    if program == 'Tiger_Files' or program == 'Tiger':
        database = click.prompt('Please enter SQLite3 Database', type=str)
        Vintage = click.prompt(f'Please Enter Vitage between 2010 and {datetime.now().year-1}', default=datetime.now().year-1, show_default=True)
        State = click.prompt('Choice state leave blank for entire Nation', default=None, show_default=False)
        Layer = click.prompt('Choice GIS layer or ENTER TO SEE LIST', default='List')
        if Layer == 'List':
            list_url = f'https://www2.census.gov/geo/tiger/TIGER{Vintage}'
            base = requests.get(list_url)
            base_res = base.content
            file_list = []
            for link in BeautifulSoup(base_res, parse_only=SoupStrainer('a')):
                if link.has_attr('href'):
                    if '.' not in link['href']:
                        if '-' not in link['href']:
                            if '=' not in link['href']:
                                file_list.append(link['href'].replace('/',''))
            print(file_list)
            Layer = click.prompt('Choice GIS layer or ENTER TO SEE LIST', default='List')
        Table_Name = click.prompt('Name of Table for Tiger Files if blank each files get it own table', default='file_to_table')
        if Table_Name == 'file_to_table':
            getTiger(database=database, Layer=Layer, Table_Name=None, Vintage=Vintage, State=State, file_to_table=True)
        else:
            getTiger(database=database, Layer=Layer, Table_Name=Table_Name, Vintage=Vintage, State=State)
if __name__ == '__main__':
    main()  