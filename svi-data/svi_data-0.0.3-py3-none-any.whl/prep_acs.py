"""
Functions to prep the SVI
database
Authors: Ram Kolli
"""

from datetime import datetime
import urllib.request
import re
import os
import shutil
import numpy as np
import requests, zipfile
import glob
import pandas as pd
from io import BytesIO
from tokenize import String
import sqlite3

# state_list = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
#        'DistrictOfColumbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
#        'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
#        'Missouri', 'Montana', 'Nebraska', 'Nevada', 'NewHampshire', 'NewJersey', 'NewMexico', 'NewYork',
#        'NorthCarolina', 'NorthDakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'PuertoRico', 'RhodeIsland',
#        'SouthCarolina', 'SouthDakota', 'Tennessee', 'Texas', 'UnitedStates', 'Utah', 'Vermont', 'Virginia',
#        'Washington', 'WestVirginia', 'Wisconsin', 'Wyoming']

state_list = ["Alabama", "Delaware", "Vermont", "WestVirginia"]

geo_cols_list = [
    "FILEID",
    "STUSAB",
    "SUMLEVEL",
    "COMPONENT",
    "LOGRECNO",
    "US",
    "REGION",
    "DIVISION",
    "STATECE",
    "STATE",
    "COUNTY",
    "COUSUB",
    "PLACE",
    "TRACT",
    "BLKGRP",
    "CONCIT",
    "AIANHH",
    "AIANHHFP",
    "AIHHTLI",
    "AITSCE",
    "AITS",
    "ANRC",
    "CBSA",
    "CSA",
    "METDIV",
    "MACC",
    "MEMI",
    "NECTA",
    "CNECTA",
    "NECTADIV",
    "UA",
    "BLANK",
    "CDCURR",
    "SLDU",
    "SLDL",
    "BLANK",
    "BLANK",
    "ZCTA5",
    "SUBMCD",
    "SDELM",
    "SDSEC",
    "SDUNI",
    "UR",
    "PCI",
    "BLANK",
    "BLANK",
    "PUMA5",
    "BLANK",
    "GEOID",
    "NAME",
    "BTTR",
    "BTBG",
    "BLANK",
]

states_dict = {state.lower(): state for state in state_list}
loc = (
    "."  # os.getcwd() #this should still be a passed parameter, just use '.' as default
)
con = sqlite3.connect("./data/acs.sqlite")

# Getting the list of zip files from a URL given the year and the State
def getZipFilesList(year, state: String):
    """
    This function reads all the zip file names from the Census.gov URL and outputs a list of Zip file names given Year and State.
    Arguments:
    - year : Integer, Year
    - state : String, state name (Ex: Texas, NewJersey, SouthDakota, DistrictofColumbia, Utah).
    """
    state = states_dict.get(state.lower(), "NA")

    if state == "NA":
        return list()

    url = "https://www2.census.gov/programs-surveys/acs/summary_file/{}/data/5_year_seq_by_state/{}/Tracts_Block_Groups_Only/".format(
        year, state
    )
    try:
        with urllib.request.urlopen(url) as u:
            txt = u.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(e.reason)

    lst = re.findall(r"href=\".*.zip\"", txt)
    new_list = []
    for i in lst:
        new_list.append(i.split("=")[1].strip('"'))
    return new_list


# Downloading the zip files from a URL and extracting the contents given the Year and the State
def ImportnExtractZipFiles(year, state: String):
    """
    This function downloads the zip files from the census.gov URL and extracts it given year, state and location
    Arguments:
    - year : Integer, Year
    - state : String, state name (Ex: Texas, NewJersey, SouthDakota, DistrictofColumbia, Utah)
    """
    state = states_dict.get(state.lower(), "NA")

    if state == "NA":
        return list()

    zipFileList = getZipFilesList(year, state)
    for z in zipFileList:
        # print('Downloading started - {} {} {}'.format(year,state,z))
        # Defining the zip file URL
        url = "https://www2.census.gov/programs-surveys/acs/summary_file/{}/data/5_year_seq_by_state/{}/Tracts_Block_Groups_Only/{}".format(
            year, state, z
        )
        local_loc = os.path.join(loc, "data", str(year), state)

        # Downloading the file by sending the request to the URL
        req = requests.get(url)
        # print('Downloading completed - {} {} {}'.format(year,state,z))

        # extracting the zip file contents
        zf = zipfile.ZipFile(BytesIO(req.content))
        zf.extractall(local_loc)
        zf.close()
        # print('Extraction completed - {} {} {}'.format(year,state,z))


# Downloading the Summary file templates
def ImportnExtractSeqFiles(year):
    """
    This function extracts the '5yr_Summary_FileTemplates' (sequence files) given year and the location
    Arguments:
    - year : Integer, Year
    - state : String, state name (Ex: Texas, NewJersey, SouthDakota, DistrictofColumbia, Utah).
    """
    # Defining the zip file URL
    url = "https://www2.census.gov/programs-surveys/acs/summary_file/{}/data/{}_5yr_Summary_FileTemplates.zip".format(
        year, year
    )
    local_loc = os.path.join(loc, "data", str(year), "seq_files")

    # Downloading the file by sending the request to the URL
    req = requests.get(url)

    # extracting the zip file contents
    zf = zipfile.ZipFile(BytesIO(req.content))
    zf.extractall(local_loc)
    zf.close()


def get_geofiles(year, state):
    state = states_dict.get(state.lower(), "NA")
    if state == "NA":
        return list()
    url = "https://www2.census.gov/programs-surveys/acs/summary_file/{}/data/5_year_seq_by_state/{}/Tracts_Block_Groups_Only/".format(
        year, state
    )
    str_vars = [
        "US",
        "REGION",
        "DIVISION",
    ]  # This list need to be modified per Andy's suggestions
    try:
        with urllib.request.urlopen(url) as u:
            txt = u.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(e.reason)
    lst = re.findall(r"href=\".*.csv\"", txt)
    new_list = []
    for i in lst:
        new_list.append(i.split("=")[1].strip('"'))
    file = new_list[0]

    url = "{}{}".format(url, file)
    df = pd.read_csv(url)
    df.columns = geo_cols_list
    df = df.drop(["BLANK"], axis=1)
    for v in str_vars:
        try:
            df[v] = df[v].astype("str")
        except:
            continue
    # Save table to sqllite db, append rows for particular geo_file
    tab_name = tab_name = "geofile_{}_{}".format(state, year)
    df.to_sql(tab_name, con, index=False, if_exists="append")
    return -2


def fileConcat(year, state):
    """
    This function
    - reads the Data files and the Sequence files from a saved location given the state and the year
    - matches the data files with the respective Seq files and creates a dataframe with the column names from the Seq files and the rows from the Data files.
    - loops through all the files in the given location and frames a dataframe
    - Concatinates all the temp dataframes and saves in a given location
    Attributes:
    - year : Integer, Year
    - state : String, state name (Ex: Texas, NewJersey, SouthDakota, DistrictofColumbia, Utah).
    """
    dummy_list = []
    state = states_dict.get(state.lower(), "NA")
    if state == "NA":
        return list()
    pre_tag = os.path.join(loc, "data", str(year), state)
    str_vars = ["FILEID", "FILETYPE", "STUSAB", "CHARITER", "SEQUENCE", "LOGRECNO"]
    nav = [".", ""]
    for file in glob.iglob(pre_tag + "\*.*"):
        splt = file.split("\\")[-1].split(".")[0]
        if splt[0] != "e":
            continue
        else:
            seq_file_num = int(splt[8:12])
            seq_file_path = os.path.join(
                loc,
                "data",
                "{}".format(year),
                "seq_files",
                "Seq{}.xlsx".format(seq_file_num),
            )
            df_seq = pd.read_excel(seq_file_path)
            seq_cols = df_seq.columns.tolist()
            dtype_dict = {v: "float" for v in seq_cols}
            for sv in str_vars:
                dtype_dict[sv] = "str"
            df_data = pd.read_csv(
                file,
                names=seq_cols,
                dtype=dtype_dict,
                keep_default_na=False,
                na_values=nav,
            )
            # df_data.set_index('LOGRECNO') #This does nothing without inplace=True
            # convert to ints if possible
            int_cols = list(set(seq_cols) - set(str_vars))
            for v in int_cols:
                # Sometimes they have decimals, but most are int
                try:
                    x = df_data[v].astype("Int64")
                    df_data[v] = x
                except:
                    continue
            # Save table to sqllite db, append rows for particular seq_file
            tab_name = f"seq{seq_file_num}_{year}"
            df_data.to_sql(tab_name, con, index=False, if_exists="append")
            # dummy_list.append(df_data)
    # dummy_df = pd.concat(dummy_list,axis=1)
    # removing duplicate column names
    # df = dummy_df.loc[:,~dummy_df.columns.duplicated()]
    # return df
    return -1


# Takes around an hour on my machine
def get_acs(year):
    """
    This funtion Unions all the data from all the states given 'year'.
    Arguments:
    - year : Integer, Year
    """
    # con = sqlite3.connect("./data/acs.sqlite")
    csv_file = os.path.join(loc, "data", f"acs{year}.csv")
    ImportnExtractSeqFiles(year)  # you only need to do this once
    head = True
    md = "w"
    for state in state_list:
        print(f'Currently extracting {state} @ {datetime.now().strftime("%H:%M")}')
        ImportnExtractZipFiles(year, state)
        get_geofiles(year, state)
        dummy_df = fileConcat(year, state)
        # dummy_df.to_csv(csv_file,header=head,mode=md)
        head = False
        md = "a"
        # dummy_df.to_sql(f'acs{year}',index=False,if_exists='append',con=con)
        # st_path = os.path.join(loc, 'data', str(year), state)
        # shutil.rmtree(st_path) # getting permission error, maybe close prior zip
    dir_path = os.path.join(loc, "data", "{}".format(year))
    # removing the sequence templates
    # st_path = os.path.join(loc, 'data', str(year), 'seq_files')
    # shutil.rmtree(dir_path) # still getting errors in access permissions
