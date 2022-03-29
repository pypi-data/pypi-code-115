import pandas as pd
from rltrade.data import IBKRDownloader

demo = True
time_frame = '1 month' # options 1 min, 5 mins, 15 mins. 1 hour , 4 hours, 1 day 
start_date = '2020-01-29'
end_date = '2022-03-29'

csv_path = 'data/ibkrcontfutgc1month.csv' # .csv path where data is stored
date_range = pd.date_range(start=start_date,end=end_date,freq='100 D')
date_range = [x.strftime('%Y-%m-%d') for x in date_range]

if start_date not in date_range:
    date_range = [start_date] + date_range
if end_date not in date_range:
    date_range = date_range + [end_date]


df_final = pd.DataFrame()
for i in range(len(date_range)-1):

    ticker_list = ['GC']
    sec_types = ['CONTFUT']
    exchanges = ['NYMEX']

    change_name = True # for changing name of ticker else keep False
    ticker_list2 = ['GOLD']
    sec_types2 = ['-']
    exchanges2 = ['-']

    start_date_ = date_range[i]
    end_date_ = date_range[i+1]

    print(start_date_,end_date_)

    ib = IBKRDownloader(start_date = start_date, # first date
                        end_date = end_date, #last date
                        ticker_list = ticker_list,
                        time_frame=time_frame,
                        sec_types=sec_types,
                        exchanges=exchanges,
                        demo=demo)
                  
    if time_frame in ['1 day','1 week','1 month']:
        df = ib.fetch_daily_data()
    else:
        df = ib.fetch_data()

    df = df.sort_values(by=['date','tic'])

    if change_name:
        for i in range(len(ticker_list)):
            df.loc[df['tic']==ticker_list[i],'tic'] = ticker_list2[i]
            df.loc[df['tic']==ticker_list[i],'sec'] = sec_types2[i]
            df.loc[df['tic']==ticker_list[i],'exchange'] = exchanges2[i]
    
    df_final = df_final.append(df)

df_final.to_csv(csv_path)    