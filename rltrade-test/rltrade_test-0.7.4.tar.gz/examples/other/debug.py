from rltrade.data import load_csv

df = load_csv('data/ibkrcontfutgc5mins.csv')
df['day'] = df['only date'].dt.day

df = df.query('day == 1').reset_index(drop=True)
df.to_csv('data/ibkrgoldcontfutmonth.csv',index=False)