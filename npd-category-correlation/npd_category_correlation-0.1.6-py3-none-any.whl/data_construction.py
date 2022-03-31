import datetime
import calendar
import logging
from npd_cat_corr.client import BloombergClient
import pandas as pd
from npd_cat_corr.reports import NON_SALES_COLS

def get_quarter_end(date, calendar_type, npd_date):

    fiscal_months = [calendar_type + x for x in [0, 3, 6, 9]]
    if date.month - 1 in fiscal_months and date.day < 15 and not npd_date:
        last_day = calendar.monthrange(date.year, date.month-1)[1]
        date = datetime.datetime(date.year, date.month-1, last_day)
    elif date.month == 1 and 12 in fiscal_months and date.day < 15 and not npd_date:
        last_day = calendar.monthrange(date.year-1, 12)[1]
        date = datetime.datetime(date.year-1, 12, last_day)

    for month in fiscal_months:
        if date.month <= month:
            last_day = calendar.monthrange(date.year, month)[1]
            return datetime.datetime(date.year, month, last_day)
    last_day = calendar.monthrange(date.year+1, fiscal_months[0])[1]
    return datetime.datetime(date.year+1, fiscal_months[0], last_day)

def choose_calendar_type(dates):

    ctypes = {1:0, 2:0, 3:0}
    for d in dates:
        last_day = calendar.monthrange(d.year, d.month)[1]
        if d.day / last_day >= 0.5:
            this_month = d.month
        elif d.month > 1:
            this_month = d.month - 1
        else:
            this_month = 12
        if this_month in [1,4,7,10]:
            ctypes[1] += 1
        elif this_month in [2,5,8,11]:
            ctypes[2] += 1
        elif this_month in [3,6,9,12]:
            ctypes[3] += 1
    return max(ctypes, key = lambda k: ctypes[k])

def create_dataset(ew_data, log=False):

    ew_data = ew_data[(~ew_data["Ticker"].str.contains(" ", regex=False)) & (~ew_data["Ticker"].str.contains(".", regex=False))]
    tickers = list(ew_data["Ticker"].unique())
    bclient = BloombergClient()
    bdata = bclient.get_quarterly_financials(tickers, log=log)
    bdata["q_datetime"] = pd.to_datetime(bdata["date"])
    
    if log:
        logging.info("Inferring Company Financial Calendars")
    #construct financial calendar map
    ticker_quarters = {}
    for ticker in bdata["symbol"].unique():
        ticker_quarters[ticker] = choose_calendar_type(list(bdata[bdata["symbol"] == ticker]["q_datetime"]))

    ew_data["Month"] = ew_data["Time Periods"].apply(lambda x: datetime.datetime.strptime(x, "%b %Y"))
    ew_data["calendar_type"] = ew_data["Ticker"].apply(lambda x: ticker_quarters[x])
    ew_data["quarter_end"] = ew_data.apply(lambda x: get_quarter_end(x["Month"], x["calendar_type"], True), axis=1)

    bdata["calendar_type"] = bdata["symbol"].apply(lambda x: ticker_quarters[x])
    bdata["quarter_end"] = bdata.apply(lambda x: get_quarter_end(x["q_datetime"], x["calendar_type"], False), axis=1)

    if log:
        logging.info("Transforming Equity Watch data")
    num_months = ew_data.groupby(["Ticker","quarter_end"])["Month"].nunique()
    valid_quarter = num_months == 3
    ew_data = ew_data.groupby(["Ticker","quarter_end","Category"])["Dollars Adjusted"].sum().reset_index()
    ew_data = ew_data.pivot(index=["Ticker","quarter_end"], columns="Category", values="Dollars Adjusted")
    ew_data["valid_quarter"] = valid_quarter
    ew_data = ew_data.reset_index().rename(columns={"Ticker":"symbol"})
    
    if log:
        logging.info("Mergin Equity Watch and Bloomberg data")
    all_data = ew_data.merge(bdata, on=["symbol","quarter_end"])
    all_data["total_dollars"] = all_data[[x for x in all_data.columns if x not in NON_SALES_COLS]].sum(axis=1)
    return all_data