import pandas as pd
from regbot import signal
df = pd.read_csv('../../../regbot_v4.csv')



y_pred = []
for index,row in df.iterrows():
    pred = signal(row.open,row.close, row['b-v-r'])
    y_pred.append(pred)
    if pred == 1:
        print(row)


#df['y_pred'] = y_pred

#print(len(df[df['buy'] == 1]))



