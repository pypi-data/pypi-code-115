import sqlite3
import requests
import pandas as pd
import geopandas as gpd
from bs4 import BeautifulSoup, SoupStrainer
import zipfile
import wget
import os

def tiger_process(file, name, con, Exists):
    df = gpd.read_file(file)
    df['geometry'] = df['geometry'].to_wkb()
    df.to_sql(name, con=con, if_exists=Exists)

def getPL94(database, Exists='drop', Table='PL94', Vintage=2020, State=None, Directory=None):
    if Directory:
        os.chwd(Directory)
    headers='https://www2.census.gov/programs-surveys/decennial/rdo/about/2020-census-program/Phase3/SupportMaterials/2020_PLSummaryFile_FieldNames.xlsx'
    wget.download(headers)
    if State:
        if len(State) == 2:
            stateList = pd.read_csv('https://gist.githubusercontent.com/dantonnoriega/bf1acd2290e15b91e6710b6fd3be0a53/raw/11d15233327c8080c9646c7e1f23052659db251d/us-state-ansi-fips.csv',skipinitialspace=True, dtype=str)
            State = stateList[stateList['stname'] == State.upper()]
        State = State.replace(' ', '_')
        url = f'https://www2.census.gov/programs-surveys/decennial/{Vintage}/data/01-Redistricting_File--PL_94-171/{State}/'
    else:
        url = f'https://www2.census.gov/programs-surveys/decennial/{Vintage}/data/01-Redistricting_File--PL_94-171/National/'
    r = requests.get(url)
    res = r.content
    for link in BeautifulSoup(res, parse_only=SoupStrainer('a')):
        if 'zip' in link.contents[0]:
            f = link.contents[0]
    file = f'{url}{f}'
    wget.download(file)
    df_header1 = pd.read_excel('2020_PLSummaryFile_FieldNames.xlsx', sheet_name='2020 P.L. Segment 1 Definitions').dropna(axis=0, how='all').reset_index(drop=True)
    df_header2 = pd.read_excel('2020_PLSummaryFile_FieldNames.xlsx', sheet_name='2020 P.L. Segment 2 Definitions').dropna(axis=0, how='all').reset_index(drop=True)
    df_header3 = pd.read_excel('2020_PLSummaryFile_FieldNames.xlsx', sheet_name='2020 P.L. Segment 3 Definitions').dropna(axis=0, how='all').reset_index(drop=True)
    df_headergeo = pd.read_excel('2020_PLSummaryFile_FieldNames.xlsx', sheet_name='2020 P.L. Geoheader Definitions').dropna(axis=0, how='all').reset_index(drop=True)
    header_replace_1 = {i :None for i in range(0,len(df_header1.index)) }
    header_replace_2 = {i :None for i in range(0,len(df_header2.index)) }
    header_replace_3 = {i :None for i in range(0,len(df_header3.index)) }
    header_replace_geo = {i :None for i in range(0,len(df_headergeo.index)) }
    array = [[df_header1,header_replace_1, '1'],[df_header2,header_replace_2,'2'],[df_header3,header_replace_3,'3'],[df_headergeo,header_replace_geo,'o']]
    for i in array:
        json = i[1]
        header = i[0]
        for key in json.keys():
            json[key] = header.iloc[key][1]
    archive = zipfile.ZipFile(f, 'r')
    csv = []
    for i in archive.infolist():
        temp = archive.open(i)
        fileName = temp.name.split('.')[0]
        fileNum = fileName[-5:][0]
        df = pd.read_csv(temp, sep="|", header=None, low_memory=False ,encoding = "ISO-8859-1")
        for j in array:
            if fileNum == j[2] :
                df = df.rename(columns=j[1])
        df.to_csv(f'{fileName}.csv', index=False)
        csv.append(fileName)
    join_on = ['STUSAB','LOGRECNO']
    df_out = None
    for i in csv:
        if df_out is None:
            df_out = pd.read_csv(f'{i}.csv', low_memory=False, dtype={'FILEID':'str','STUSAB':'str','CHARITER':'str','CIFSN':'str','LOGRECNO':'str'})
            continue
        else:
            df = pd.read_csv(f'{i}.csv', low_memory=False, dtype={'FILEID':'str','STUSAB':'str','CHARITER':'str','CIFSN':'str','LOGRECNO':'str'})
            df_out = df_out.merge(df, on=join_on, suffixes=('', '_y'))
            delt = []
            for k in df_out.columns:
                if '_y' in k:
                    delt.append(k)
            df_out = df_out.drop(columns=delt)
    con = sqlite3.connect(f'{database}.db')
    df_out.to_sql(f'{Table}',con, if_exists=Exists , index=False)
    for i in csv:
        os.remove(f'{i}.csv')

def getTiger(database, Layer, Table_Name=None, Exists='append', Vintage=2020, State=None, Directory=None, file_to_table=False):
    base_url = f'https://www2.census.gov/geo/tiger/TIGER{Vintage}/{Layer}/'
    con = sqlite3.connect(f'{database}.db')
    if Directory:
        os.chwd(Directory)
    base = requests.get(base_url)
    base_res = base.content
    file_list = []
    for link in BeautifulSoup(base_res, parse_only=SoupStrainer('a')):
        if 'zip' in link.contents[0]:
             file_list.append(link.contents[0])
    if len(file_list) == 1:
        file = f'{base_url}{file_list[0]}'
        tiger_process(file, Table_Name, con, Exists)
    elif State:
        if isinstance(State, int):
            sta_fips = State
        elif len(State) == 2:
            stateList = pd.read_csv('https://gist.githubusercontent.com/dantonnoriega/bf1acd2290e15b91e6710b6fd3be0a53/raw/11d15233327c8080c9646c7e1f23052659db251d/us-state-ansi-fips.csv',skipinitialspace=True, dtype=str)
            sta_fips = stateList[stateList['stusps']==State.upper()]
            sta_fips =sta_fips['st'].values
        else:
            stateList = pd.read_csv('https://gist.githubusercontent.com/dantonnoriega/bf1acd2290e15b91e6710b6fd3be0a53/raw/11d15233327c8080c9646c7e1f23052659db251d/us-state-ansi-fips.csv',skipinitialspace=True, dtype=str)
            sta_fips = stateList[stateList['stname']==State.capitalize()]
            sta_fips =sta_fips['st'].values
        if len(sta_fips) == 0:
            raise Exception(f'{State} is not in 2 Letter Code, Spelt Right, or Not a FIPS')
        for k in file_list:
            if k.split('_')[2] == sta_fips:
                file = f'{base_url}{k}'
                tiger_process(file, Table_Name, con, Exists)
                break
    else:
        if Exists == 'append':
            for j in file_list:
                file = f'{base_url}{j}'
                tiger_process(file, Table_Name, con, Exists)
        elif file_to_table and not Table_Name:
            for j in file_list:
                Table_Name = j.split('.')[0]
                tiger_process(file, Table_Name, con, Exists)
        else: 
            raise Exception('Please set Pramater correctly either (file_to_table = True) or (Exists = "append")')