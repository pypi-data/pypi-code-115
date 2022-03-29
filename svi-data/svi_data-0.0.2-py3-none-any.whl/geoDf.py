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

from sympy import N

state_list = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "DistrictOfColumbia",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "NewHampshire",
    "NewJersey",
    "NewMexico",
    "NewYork",
    "NorthCarolina",
    "NorthDakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "PuertoRico",
    "RhodeIsland",
    "SouthCarolina",
    "SouthDakota",
    "Tennessee",
    "Texas",
    "UnitedStates",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "WestVirginia",
    "Wisconsin",
    "Wyoming",
]
states_dict = {state.lower(): state for state in state_list}

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

loc = "."


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
    # print(df.head())
    print(df.info())
    return df


get_geofiles(2020, "alaBAmA")
