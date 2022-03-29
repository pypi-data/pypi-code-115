"""
This is code to translate original ACS tables
with the B variables into the SVI table estimate

Andy Wheeler
"""

from census import Census
import numpy as np
import pandas as pd
import re

############################################################################
# dictionary describing the variables directly from SVI docs
# https://www.atsdr.cdc.gov/placeandhealth/svi/documentation/pdf/SVI2018Documentation-H.pdf

di = {
    "E_TOTPOP": ["S0601_C01_001", "Population"],
    "E_HU": ["DP04_0001", "Housing Units"],
    "E_HH": ["DP02_0001", "Households"],
    "E_FAM": [
        "B11003_001",
        "Families",
    ],  # adding in families, single parents should be divided by this
    "E_POV": ["B17001_002", "Persons below poverty"],  # should probably be B17001_002
    "E_UNEMP": ["DP03_0005", "Civilian (age 16+) unemployed"],
    "E_PCI": ["B19301_001", "Per capita income estimate"],
    "E_NOHSDP": ["B06009_002", "Persons (age 25+) with no high school diploma"],
    "E_AGE65": ["S0101_C01_030", "Persons aged 65 and older"],
    "E_AGE17": ["B09001_001", "Persons aged 17 and younger"],
    "E_DISABL": [
        "DP02_0071",
        "Civilian noninstitutionalized population with a disability",
    ],
    "E_SNGPNT": [
        "(DP02_0007 + DP02_0009)",
        "Single parent household with children under 18",
    ],
    "E_MINRTY": [
        "E_TOTPOP - B01001H_001",
        "Minority (all persons except white, non-Hispanic)",
    ],
    "E_LIMENG": [
        """B16005_007 +
 B16005_008 +
 B16005_012 +
 B16005_013 +
 B16005_017 +
 B16005_018 +
 B16005_022 +
 B16005_023 +
 B16005_029 +
 B16005_030 +
 B16005_034 +
 B16005_035 +
 B16005_039 +
 B16005_040 +
 B16005_044 +
 B16005_045""".replace(
            "\n", ""
        ),
        "Persons (age 5+) who speak English less than well",
    ],
    "E_MUNIT": [
        "(DP04_0012 + DP04_0013)",
        "Housing in structures with 10 or more units",
    ],
    "E_MOBILE": ["DP04_0014", "Mobile homes"],
    "E_CROWD": [
        "(DP04_0078 + DP04_0079)",
        "At household level (occupied housing units), more people than rooms",
    ],
    "E_NOVEH": ["DP04_0058", "Households with no vehicle"],
    "E_GROUPQ": ["B26001_001", "Persons in group quarters"],
    "EP_POV": ["S0601_C01_049", "Percentage of persons below poverty"],
    "EP_UNEMP": ["DP03_0009", "Unemployment rate"],  # should technically be DP03_0009PE
    "EP_PCI": ["B19301_001", "Per capita income estimate"],
    "EP_NOHSDP": ["S0601_C01_033", "Percentage of persons with no high school diploma"],
    "EP_AGE65": ["S0101_C02_030", "Percentage of persons aged 65 and older"],
    "EP_AGE17": ["(E_AGE17/E_TOTPOP)*100", "Percentage of persons aged 17 and younger"],
    "EP_DISABL": [
        "DP02_0071P",
        "Percentage of civilian noninstitutionalized population with a disability",
    ],
    "EP_SNGPNT": [
        "(E_SNGPNT/E_FAM)*100",
        "Percentage of single parent households with children under 18",
    ],
    "EP_MINRTY": [
        "(E_MINRTY/E_TOTPOP)*100",
        "Percentage minority (all persons except white, non-Hispanic",
    ],
    "EP_LIMENG": [
        "E_LIMENG/B16005_001",
        "Percentage of persons (age 5+) who speak English less than well",
    ],
    "EP_MUNIT": [
        "(E_MUNIT/E_HU)*100",
        "Percentage of housing in structures with 10 or more units",
    ],
    "EP_MOBILE": ["DP04_0014P", "Percentage of mobile homes"],
    "EP_CROWD": [
        "(E_CROWD/B25014_001)*100",
        "Percentage of occupied housing units with more people than rooms",
    ],
    "EP_NOVEH": ["DP04_0058P", "Percentage of households with no vehicle available"],
    "EP_GROUPQ": ["(E_GROUPQ/E_TOTPOP)*100", "Percentage of persons in group quarters"],
    "EPL_POV": ["PercentRank EP_POV", "Percentile Percentage of persons below poverty"],
    "EPL_UNEMP": [
        "PercentRank EP_UNEMP",
        "Percentile Percentage of civilian (age 16+) unemployed",
    ],
    "EPL_PCI": [
        "PercentRank EP_PCI",
        "Percentile per capita income estimate (reversed)",
    ],
    "EPL_NOHSDP": [
        "PercentRank EP_NOHSDP",
        "Percentile percenage of persons with no high school diploma",
    ],
    "SPL_THEME1": [
        "EPL_POV + EPL_UNEMP + EPL_PCI + EPL_NOHSDP",
        "Sum for series for Socioeconomic theme",
    ],
    "RPL_THEME1": [
        "PercentRank SPL_THEME1",
        "Percentile ranking for socioeconomic theme",
    ],
    "EPL_AGE65": [
        "PercentRank EP_AGE65",
        "Percentile percentage of persons aged 65 and older",
    ],
    "EPL_AGE17": ["PercentRank EP_AGE17", "Percentile of persons aged 17 and younger"],
    "EPL_DISABL": [
        "PercentRank EP_DISABL",
        "Percentile percentage of civilian noninstitutionalized"
        " population with a disability",
    ],
    "EPL_SNGPNT": [
        "PercentRank EP_SNGPNT",
        "Percentile percentage of single parent households with children under 18",
    ],
    "SPL_THEME2": [
        "EPL_AGE65 + EPL_AGE17 + EPL_DISABL + EPL_SNGPNT",
        "Sum of series for Household composition theme",
    ],
    "RPL_THEME2": [
        "PercentRank SPL_THEME2",
        "Percentile ranking for Household composition theme",
    ],
    "EPL_MINRTY": [
        "PercentRank EP_MINRTY",
        "Percentile percentage minority (all persons excet white, non-Hispanic",
    ],
    "EPL_LIMENG": [
        "PercentRank EP_LIMENG",
        "Percentile percentage of persons (age 5+) who speak English less than well",
    ],
    "SPL_THEME3": [
        "EPL_MINRTY + EPL_LIMENG",
        "Sum of series for minority status/language theme",
    ],
    "RPL_THEME3": [
        "PercentRank SPL_THEME3",
        "Percentile ranking for minority status/language",
    ],
    "EPL_MUNIT": [
        "PercentRank EP_MUNIT",
        "Percentile percentage housing in structures with 10 or more units",
    ],
    "EPL_MOBILE": ["PercentRank EP_MOBILE", "Percentile percentage mobile homes"],
    "EPL_CROWD": [
        "PercentRank EP_CROWD",
        "Percentile percentage households with more people than rooms",
    ],
    "EPL_NOVEH": [
        "PercentRank EP_NOVEH",
        "Percentile percentage households with no vehicle available",
    ],
    "EPL_GROUPQ": [
        "PercentRank EP_GROUPQ",
        "Percentile percentage of persons in group quarters",
    ],
    "SPL_THEME4": [
        "EPL_MUNIT + EPL_MOBILE + EPL_CROWD + EPL_NOVEH + EPL_GROUPQ",
        "Sum of series for housing type/transportation theme",
    ],
    "RPL_THEME4": [
        "PercentRank SPL_THEME4",
        "Percentile ranking for housing type/transportation theme",
    ],
    "SPL_THEMES": [
        "SPL_THEME1 + SPL_THEME2 + SPL_THEME3 + SPL_THEME4",
        "Sum of series themes",
    ],
    "RPL_THEMES": ["PercentRank SPL_THEMES", "Overall percentile ranking"],
    "E_UNINSUR": [
        "S2701_C04_001",
        "Adjunct variable - uninsured in the total civilian"
        " noninstitutionalized population",
    ],
    "EP_UNINSUR": [
        "S2701_C05_001",
        "Adjunct variable - percentage uninsured in the total civilian"
        "noninstitutionalized population",
    ],
}
############################################################################

############################################################################
# This is a dictionary that translates between
# the DP/S tables and the original micro level estimates

trans_dict = {}
trans_dict["S0601_C01_001"] = "B01001_001"
trans_dict["DP04_0001"] = "B25001_001"
trans_dict["DP02_0001"] = "B28004_001"
trans_dict["DP03_0005"] = "B23025_005"
trans_dict["S0101_C01_030"] = "B27010_051"
trans_dict[
    "DP02_0071"
] = "(B18101_004 + B18101_007 + B18101_010 + B18101_013 + B18101_016 + B18101_019 "
trans_dict[
    "DP02_0071"
] += "+ B18101_023 + B18101_026 + B18101_029 + B18101_032 + B18101_035 + B18101_038)"
trans_dict["(DP02_0007 + DP02_0009)"] = "(B11003_010 + B11003_016)"
trans_dict["(DP04_0012 + DP04_0013)"] = "(B25024_007 + B25024_008 + B25024_009)"
trans_dict["DP04_0014"] = "B25024_010"
trans_dict["(DP04_0078 + DP04_0079)"] = "(B25014_005 + B25014_006 + B25014_007 "
trans_dict["(DP04_0078 + DP04_0079)"] += "+ B25014_011 + B25014_012 + B25014_013)"
trans_dict["DP04_0058"] = "(B25044_003 + B25044_010)"
trans_dict["S0601_C01_049"] = "(B17001_002/B17001_001)*100"
trans_dict[
    "DP03_0009"
] = "(B23025_005/B23025_002)*100"  # these are very close, but not 100% match
trans_dict["S0601_C01_033"] = "(B06009_002/B06009_001)*100"
trans_dict["S0101_C02_030"] = "(B27010_051/B27010_001)*100"
trans_dict["DP02_0071P"] = "(E_DISABL/B18101_001)*100"
trans_dict["DP04_0014P"] = "(B25024_010/B25024_001)*100"
trans_dict["DP04_0058P"] = "(E_NOVEH/B25044_001)*100"
trans_dict["S2701_C04_001"] = "(B27001_005 + B27001_008 + B27001_011 + B27001_014 "
trans_dict[
    "S2701_C04_001"
] += "+ B27001_017 + B27001_020 + B27001_023 + B27001_026 + B27001_029 "
trans_dict[
    "S2701_C04_001"
] += "+ B27001_033 + B27001_036 + B27001_039 + B27001_042 + B27001_045 "
trans_dict["S2701_C04_001"] += "+ B27001_048 + B27001_051 + B27001_054 + B27001_057)"
trans_dict["S2701_C05_001"] = "(E_UNINSUR/B27001_001)*100"

############################################################################

############################################################################
# Further global variables defining the variables to query
# as well as the eval plan to create the SVI variables

# transforming di with updated trans_dict
for k, v in di.items():
    if v[0] in trans_dict:
        v[0] = trans_dict[v[0]]

# creating a nice data frame for the labels
lab_df = pd.DataFrame(di.values(), columns=["Def", "Desc"])
lab_df["Var"] = list(di.keys())
lab_df = lab_df[["Var", "Def", "Desc"]].copy()

# getting list of all the B variables I need
tot_vars = lab_df["Def"].tolist()
combo_str = " ".join(tot_vars)
reg_ex = r"B\d{5}(?:H_|_)\d{3}"  # single annoying H variable!
bvars = list(set(re.findall(reg_ex, combo_str)))
evars = [b + "E" for b in bvars]
erep = {e: b for e, b in zip(evars, bvars)}

# list of fips codes for states
fips = [
    "01",
    "02",
    "04",
    "05",
    "06",
    "08",
    "09",
    "10",
    "12",
    "13",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "53",
    "54",
    "55",
    "56",
]

############################################################################

# function to take an original dataframe with the ACS variables
# loop over di items, and generate the new variables


def create_svi(df, zscore=True):
    """
    df - pandas dataframe with the E variables
    zscore - boolean, use zscores to create the themes (default True)
             if false uses percentiles

    returns pandas dataframe with the SVI variables
    """
    dc = df.copy()
    # get rid of areas with 0 population
    dc = dc[dc["B01001_001"] > 0].copy()
    # per capita income has a missing value for -666,666,666.0
    neginc = dc["B19301_001"] < -10000
    dc.loc[neginc, "B19301_001"] = np.NaN
    # sometimes these are objects, converting all to numeric
    for v in bvars:
        dc[v] = pd.to_numeric(dc[v], errors="coerce")
    # now looping through each variable
    vrs = list(di.keys())  # final list of SVI variables
    ld = {s: dc[s] for s in list(dc)}  # dict mapping str to vars in df (for eval)
    for v in vrs:
        qs = di[v][0]  # query string for eval
        # If percent rank, it pulls out and *Zscores* or does percentile ranking
        if qs[0:11] == "PercentRank":
            perc, lvar = qs.split()
            # if income reverses it
            if lvar == "EP_PCI":
                x = -dc[lvar]
            else:
                x = dc[lvar]
            if zscore:
                meanx, stdx = x.mean(), x.std()
                dc[v] = (x - meanx) / stdx
            else:
                dc[v] = x.rank(method="average", pct=True)
        else:
            # Otherwise does eval
            dc[v] = pd.eval(qs, local_dict=ld, target=dc)
            # For some small values can have 0/0, eg EP_POV
            # for per capita income mean imputation
            if v == "B19301_001":
                mv = dc[v].mean()
                dc[v].fillna(mv, inplace=True)
            else:
                dc[v].fillna(0, inplace=True)
        ld[v] = dc[v]  # adding in new variable into data copy (dc)
    # should add in the geo variable
    vgeo = ["GEO_ID"] + vrs
    return dc[vgeo]


# Note blockgroup has some missing data
# so not all of the themes can be computed


def get_svi(api_key, geo, zscore=True):
    """
    Function to get SVI data for a given geography

    api_key -- string with census geo api key
    geo -- string, can either be 'zip','tract','blockgroup', or 'county'
    states -- string for specific states fips code, default to all states
    zscore -- boolean, whether to calculate themes via summing z-scores
              or via summing percentile rankings

    returns a pandas dataframe with the SVI variables for given geo
    """
    # Set up the census api
    # ?Future work pass in year?
    c = Census(api_key, year=2018)
    # download the data, all subgroups within a given state
    if geo == "zip":
        # Census.ALL is just '*'
        res = pd.DataFrame(c.acs5.state_zipcode(evars, "*", "*"))
    elif geo == "tract":
        # Need to loop over every state and concat
        rl = []
        for s in fips:
            temp = pd.DataFrame(c.acs5.state_county_tract(evars, s, "*", "*"))
            rl.append(temp.copy())
        res = pd.concat(rl, axis=0, ignore_index=True)
    elif geo == "blockgroup":
        # Need to loop over every state and concat
        rl = []
        for s in fips:
            temp = pd.DataFrame(c.acs5.state_county_blockgroup(evars, s, "*", "*"))
            rl.append(temp.copy())
        res = pd.concat(rl, axis=0, ignore_index=True)
    elif geo == "county":
        res = pd.DataFrame(c.acs5.state_county(evars, "*", "*"))
    else:
        print(f"geo parameter, {geo}, is not a valid geography")
        print("Potential geographies are zip,tract,blockgroup, or county")
        return -1
    # Need to replace E variable endings
    res.rename(columns=erep, inplace=True)
    # Now generate the SVI variables
    svi = create_svi(res, zscore)
    return svi


# Simple helper to read in census api key
# saved in a text file
def get_key(file):
    with open(file, "r") as f:
        key = f.read()
    return key


############################################################################


###########################################################
# Note, attempts to auto-parse the PDF have gotten
# somewhere, but not far enough for me to not
# just do it by hand, leaving detritus in file
# in case others want to give it a shot
#
#
# For 2018
# import camelot
# import pandas as pd
# doc = r'https://www.atsdr.cdc.gov/placeandhealth/svi/documentation/pdf/'
# doc += r'SVI2018Documentation-H.pdf'
# tables = camelot.read_pdf(doc,pages='6-end')
#
# Table 0 is no good
#
# fn = tables[1].df.loc[0,].tolist()
# fn = [f.replace('\n','').replace(' ','_') for f in fn]
#
# res = []
# for i in range(1,tables.n):
#    res.append(tables[i].df.loc[1:,])
#
# res_df = pd.concat(res,axis=0)
# res_df.columns = fn
#
#
# Only get columns with E variables
#
###########################################################
