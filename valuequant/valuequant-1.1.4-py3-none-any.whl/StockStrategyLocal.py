# 著作者：叶凯文
# Author: YE KAIWEN
# 版权归著作者叶凯文所有
# Copyright (c) 2022 YE KAIWEN. All Rights Reserved.

import pandas as pd

class NormalTrade:
    def __init__(self,buyfee,sellfee,stopprofit=None,stoploss=None):
        self.buyfee=buyfee
        self.sellfee=sellfee
        self.extralogics=[]
        if stopprofit:
            extralogic=stopprofit_logic(stopprofit=stopprofit)
            self.extralogics.append(extralogic)
        if stoploss:
            extralogic=stoploss_logic(stoploss=stoploss)
            self.extralogics.append(extralogic)

    def statistics(self,data):
        if (set(['orderbuy','ordersell','refer','high','low','openlogic','holdlogic'])<=set(data.columns))==False:
            print('缺少必要数据列',set(['orderbuy','ordersell','refer','high','low','openlogic','holdlogic']).difference(set(data.columns)))
            return None
        status='close'
        trades=[]
        for inx,row in data.iterrows():
            if status=='close':
                if (row['openlogic']&row['holdlogic']):
                    status='buying'
                    orderday=0
            elif status=='buying':
                orderday+=1
                if (row['orderbuy']>=row['low']):
                    status='open'
                    orderinfo={'buyinx':inx,'buyday':orderday,'buybid':min(row['orderbuy'],row['high'])}
                if status=='open':
                    revbase=row['refer']
                    revenue=(revbase/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold==False:
                        status = 'selling'
                        orderday = 0
                else:
                    if (row['openlogic']&row['holdlogic'])==False:
                        status='close'
            elif status=='open':
                revbase = row['refer']
                revenue = (revbase / orderinfo['buybid']) * (1 - self.sellfee)/(1 + self.buyfee) - 1
                hold = row['holdlogic']
                for logic in self.extralogics:
                    hold = hold & logic.calc(revenue)
                if hold == False:
                    status = 'selling'
                    orderday = 0
            elif status=='selling':
                orderday+=1
                if row['ordersell']<=row['high']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=max(row['ordersell'],row['low'])
                    orderinfo['revenue']=(orderinfo['sellbid']/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    orderinfo['cost']=(1-1/(1+self.buyfee))+(orderinfo['sellbid']/orderinfo['buybid'])*self.sellfee/(1+self.buyfee)
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['ordersell'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spmax=sppiece.max()
                    spmin=sppiece.min()
                    orderinfo['revmax']=(spmax/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    orderinfo['revmin']=(spmin/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    trades.append(orderinfo)
                    status='close'
                if status=='close':
                    if (row['openlogic'] & row['holdlogic']):
                        status = 'buying'
                        orderday = 0
                else:
                    revbase = row['refer']
                    revenue = (revbase / orderinfo['buybid']) * (1 - self.sellfee)/(1+self.buyfee) - 1
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold:
                        status = 'open'
            else:
                raise Exception("Illegal status!")
        if status!='close':
            orderinfo['status']=status
            trades.append(orderinfo)
        return trades

    def statistics_with_callauction(self,data):
        if (set(['conbuy','consell','callbuy','callsell','refer','open','high','low','openlogic','holdlogic'])<=set(data.columns))==False:
            print('缺少必要数据列',set(['conbuy','consell','callbuy','callsell','refer','open','high','low','openlogic','holdlogic']).difference(set(data.columns)))
            return None
        status='close'
        trades=[]
        for inx,row in data.iterrows():
            if status=='close':
                if (row['openlogic']&row['holdlogic']):
                    status='buying'
                    orderday=0
            elif status=='buying':
                orderday+=1
                if (row['callbuy']>=row['open']):
                    status='open'
                    orderinfo={'buyinx':inx,'buyday':orderday,'buybid':row['open']}
                elif (row['conbuy']>=row['low']):
                    status='open'
                    orderinfo={'buyinx':inx,'buyday':orderday,'buybid':min(row['conbuy'],row['high'])}
                if status=='open':
                    revbase=row['refer']
                    revenue=(revbase/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold==False:
                        status = 'selling'
                        orderday = 0
                else:
                    if (row['openlogic']&row['holdlogic'])==False:
                        status='close'
            elif status=='open':
                revbase = row['refer']
                revenue = (revbase / orderinfo['buybid']) * (1 - self.sellfee)/(1+self.buyfee) - 1
                hold = row['holdlogic']
                for logic in self.extralogics:
                    hold = hold & logic.calc(revenue)
                if hold == False:
                    status = 'selling'
                    orderday = 0
            elif status=='selling':
                orderday+=1
                if row['callsell']<=row['open']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=row['open']
                    orderinfo['revenue']=(orderinfo['sellbid']/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    orderinfo['cost']=(1-1/(1+self.buyfee))+(orderinfo['sellbid']/orderinfo['buybid'])*self.sellfee/(1+self.buyfee)
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['refer'].shift()[orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spmax=sppiece.max()
                    spmin=sppiece.min()
                    orderinfo['revmax']=(spmax/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    orderinfo['revmin']=(spmin/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    trades.append(orderinfo)
                    status='close'
                elif row['consell']<=row['high']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=max(row['consell'],row['low'])
                    orderinfo['revenue']=(orderinfo['sellbid']/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    orderinfo['cost']=(1-1/(1+self.buyfee))+(orderinfo['sellbid']/orderinfo['buybid'])*self.sellfee/(1+self.buyfee)
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['refer'].shift()[orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spmax=sppiece.max()
                    spmin=sppiece.min()
                    orderinfo['revmax']=(spmax/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    orderinfo['revmin']=(spmin/orderinfo['buybid'])*(1-self.sellfee)/(1+self.buyfee)-1
                    trades.append(orderinfo)
                    status='close'
                if status=='close':
                    if (row['openlogic'] & row['holdlogic']):
                        status = 'buying'
                        orderday = 0
                else:
                    revbase = row['refer']
                    revenue =  (revbase / orderinfo['buybid']) * (1 - self.sellfee)/(1+self.buyfee) - 1
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold:
                        status = 'open'
            else:
                raise Exception("Illegal status!")
        if status!='close':
            orderinfo['status']=status
            trades.append(orderinfo)
        return trades

class MarginTrade:
    def __init__(self,buyfee,sellfee,interest,margin,guarantee,stopprofit=None,stoploss=None):
        self.buyfee=buyfee
        self.sellfee=sellfee
        self.interest=interest/360
        self.margin=margin
        self.guarantee=guarantee
        self.extralogics = []
        if stopprofit:
            extralogic=stopprofit_logic(stopprofit=stopprofit)
            self.extralogics.append(extralogic)
        if stoploss:
            extralogic=stoploss_logic(stoploss=stoploss)
            self.extralogics.append(extralogic)

    def statistics(self,data):
        if (set(['orderbuy','ordersell','closeout','refer','high','low','openlogic','holdlogic'])<=set(data.columns))==False:
            print('缺少必要数据列',set(['orderbuy','ordersell','closeout','refer','high','low','openlogic','holdlogic']).difference(set(data.columns)))
            return None
        status='close'
        trades=[]
        for inx,row in data.iterrows():
            if status=='close':
                if (row['openlogic']&row['holdlogic']):
                    status='buying'
                    orderday=0
            elif status=='buying':
                orderday+=1
                if (row['orderbuy']>=row['low']):
                    status='open'
                    holdday=0
                    orderinfo={'buyinx':inx,'buyday':orderday,'buybid':min(row['orderbuy'],row['high'])}
                if status=='open':
                    revbase=row['refer']
                    revenue=((revbase/orderinfo['buybid'])*(1-self.sellfee)-(1+self.interest*holdday))/(self.margin+self.buyfee)
                    guarantee=(revbase/orderinfo['buybid'])*(1-self.sellfee)-self.interest*holdday+self.margin
                    if guarantee<self.guarantee:
                        status='mco'
                        orderday=0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold==False:
                            status = 'selling'
                            orderday = 0
                else:
                    if (row['openlogic']&row['holdlogic'])==False:
                        status='close'
            elif status=='open':
                holdday+=1
                revbase = row['refer']
                revenue = ((revbase / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                guarantee = (revbase / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                if guarantee < self.guarantee:
                    status = 'mco'
                    orderday = 0
                else:
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold == False:
                        status = 'selling'
                        orderday = 0
            elif status=='mco':
                holdday += 1
                orderday +=1
                if row['closeout']<=row['high']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=max(row['closeout'],row['low'])
                    orderinfo['revenue']=((orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    orderinfo['guarantee']=(orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    orderinfo['cost']=(self.buyfee+(orderinfo['sellbid'] / orderinfo['buybid'])*self.sellfee+self.interest * holdday)/(self.margin + self.buyfee)
                    orderinfo['closetype']='margin-closeout'
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['ordersell'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spdays=pd.Series(range(len(sppiece)),index=sppiece.index)
                    revenueseries=((sppiece / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * spdays)) / (self.margin + self.buyfee)
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
            elif status=='selling':
                holdday += 1
                orderday+=1
                if row['ordersell']<=row['high']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=max(row['ordersell'],row['low'])
                    orderinfo['revenue']=((orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    orderinfo['guarantee']=(orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    orderinfo['cost']=(self.buyfee+(orderinfo['sellbid'] / orderinfo['buybid'])*self.sellfee+self.interest * holdday)/(self.margin + self.buyfee)
                    orderinfo['closetype']='sell-close'
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['ordersell'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spdays = pd.Series(range(len(sppiece)), index=sppiece.index)
                    revenueseries = ((sppiece / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * spdays)) / (self.margin + self.buyfee)
                    orderinfo['revmax'] = revenueseries.max()
                    orderinfo['revmin'] = revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                if status=='close':
                    if (row['openlogic'] & row['holdlogic']):
                        status = 'buying'
                        orderday = 0
                else:
                    revbase = row['refer']
                    revenue = ((revbase / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    guarantee = (revbase / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    if guarantee < self.guarantee:
                        status = 'mco'
                        orderday = 0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold:
                            status = 'open'
            else:
                raise Exception("Illegal status!")
        if status!='close':
            orderinfo['status']=status
            trades.append(orderinfo)
        return trades

    def statistics_with_callauction(self,data):
        if (set(['conbuy','consell','closeout','callbuy','callsell','refer','high','low','openlogic','holdlogic'])<=set(data.columns))==False:
            print('缺少必要数据列',set(['conbuy','consell','closeout','callbuy','callsell','refer','high','low','openlogic','holdlogic']).difference(set(data.columns)))
            return None
        status='close'
        trades=[]
        for inx,row in data.iterrows():
            if status=='close':
                if (row['openlogic']&row['holdlogic']):
                    status='buying'
                    orderday=0
            elif status=='buying':
                orderday+=1
                if (row['callbuy']>=row['open']):
                    status='open'
                    holdday=0
                    orderinfo={'buyinx':inx,'buyday':orderday,'buybid':row['open']}
                elif (row['conbuy']>=row['low']):
                    status='open'
                    holdday=0
                    orderinfo={'buyinx':inx,'buyday':orderday,'buybid':min(row['conbuy'],row['high'])}
                if status=='open':
                    revbase=row['refer']
                    revenue=((revbase/orderinfo['buybid'])*(1-self.sellfee)-(1+self.interest*holdday))/(self.margin+self.buyfee)
                    guarantee=(revbase/orderinfo['buybid'])*(1-self.sellfee)-self.interest*holdday+self.margin
                    if guarantee<self.guarantee:
                        status='mco'
                        orderday=0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold==False:
                            status = 'selling'
                            orderday = 0
                else:
                    if (row['openlogic']&row['holdlogic'])==False:
                        status='close'
            elif status=='open':
                holdday+=1
                revbase = row['refer']
                revenue = ((revbase / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                guarantee = (revbase / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                if guarantee < self.guarantee:
                    status = 'mco'
                    orderday = 0
                else:
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold == False:
                        status = 'selling'
                        orderday = 0
            elif status=='mco':
                holdday += 1
                orderday +=1
                if row['closeout']<=row['open']:
                    orderinfo['sellinx'] = inx
                    orderinfo['sellday'] = orderday
                    orderinfo['sellbid'] = row['open']
                    orderinfo['revenue'] = ((orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    orderinfo['guarantee'] = (orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    orderinfo['cost'] = (self.buyfee + (orderinfo['sellbid'] / orderinfo['buybid']) * self.sellfee + self.interest * holdday) / (self.margin + self.buyfee)
                    orderinfo['closetype'] = 'margin-closeout'
                    highpiece = data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece = data['refer'].shift()[orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece = (highpiece >= sppiece) * sppiece + (highpiece < sppiece) * highpiece
                    sppiece = (lowpiece <= sppiece) * sppiece + (lowpiece > sppiece) * lowpiece
                    spdays = pd.Series(range(len(sppiece)), index=sppiece.index)
                    revenueseries = ((sppiece / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * spdays)) / (self.margin + self.buyfee)
                    orderinfo['revmax'] = revenueseries.max()
                    orderinfo['revmin'] = revenueseries.min()
                    trades.append(orderinfo)
                    status = 'close'
                elif row['closeout']<=row['high']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=max(row['closeout'],row['low'])
                    orderinfo['revenue']=((orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    orderinfo['guarantee']=(orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    orderinfo['cost']=(self.buyfee+(orderinfo['sellbid'] / orderinfo['buybid'])*self.sellfee+self.interest * holdday)/(self.margin + self.buyfee)
                    orderinfo['closetype']='margin-closeout'
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['refer'].shift()[orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spdays = pd.Series(range(len(sppiece)), index=sppiece.index)
                    revenueseries = ((sppiece / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * spdays)) / (self.margin + self.buyfee)
                    orderinfo['revmax'] = revenueseries.max()
                    orderinfo['revmin'] = revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
            elif status=='selling':
                holdday += 1
                orderday+=1
                if row['callsell']<=row['open']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=row['open']
                    orderinfo['revenue']=((orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    orderinfo['guarantee']=(orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    orderinfo['cost']=(self.buyfee+(orderinfo['sellbid'] / orderinfo['buybid'])*self.sellfee+self.interest * holdday)/(self.margin + self.buyfee)
                    orderinfo['closetype']='sell-close'
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['refer'].shift()[orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spdays = pd.Series(range(len(sppiece)), index=sppiece.index)
                    revenueseries = ((sppiece / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * spdays)) / (self.margin + self.buyfee)
                    orderinfo['revmax'] = revenueseries.max()
                    orderinfo['revmin'] = revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                elif row['consell']<=row['high']:
                    orderinfo['sellinx']=inx
                    orderinfo['sellday']=orderday
                    orderinfo['sellbid']=max(row['consell'],row['low'])
                    orderinfo['revenue']=((orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    orderinfo['guarantee']=(orderinfo['sellbid'] / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    orderinfo['cost']=(self.buyfee+(orderinfo['sellbid'] / orderinfo['buybid'])*self.sellfee+self.interest * holdday)/(self.margin + self.buyfee)
                    orderinfo['closetype']='sell-close'
                    highpiece=data['high'][orderinfo['buyinx']:orderinfo['sellinx']]
                    lowpiece = data['low'][orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=data['refer'].shift()[orderinfo['buyinx']:orderinfo['sellinx']]
                    sppiece=(highpiece>=sppiece)*sppiece+(highpiece<sppiece)*highpiece
                    sppiece=(lowpiece<=sppiece)*sppiece+(lowpiece>sppiece)*lowpiece
                    spdays = pd.Series(range(len(sppiece)), index=sppiece.index)
                    revenueseries = ((sppiece / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * spdays)) / (self.margin + self.buyfee)
                    orderinfo['revmax'] = revenueseries.max()
                    orderinfo['revmin'] = revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                if status=='close':
                    if (row['openlogic'] & row['holdlogic']):
                        status = 'buying'
                        orderday = 0
                else:
                    revbase = row['refer']
                    revenue = ((revbase / orderinfo['buybid']) * (1 - self.sellfee) - (1 + self.interest * holdday)) / (self.margin + self.buyfee)
                    guarantee = (revbase / orderinfo['buybid']) * (1 - self.sellfee) - self.interest * holdday + self.margin
                    if guarantee < self.guarantee:
                        status = 'mco'
                        orderday = 0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold:
                            status = 'open'
            else:
                raise Exception("Illegal status!")
        if status!='close':
            orderinfo['status']=status
            trades.append(orderinfo)
        return trades

class ShortSell:
    def __init__(self,buyfee,sellfee,interest,margin,guarantee,stopprofit=None,stoploss=None):
        self.buyfee=buyfee
        self.sellfee=sellfee
        self.interest=interest/360
        self.margin=margin
        self.guarantee=guarantee
        self.extralogics = []
        if stopprofit:
            extralogic=stopprofit_logic(stopprofit=stopprofit)
            self.extralogics.append(extralogic)
        if stoploss:
            extralogic=stoploss_logic(stoploss=stoploss)
            self.extralogics.append(extralogic)

    def statistics(self,data):
        if (set(['orderbuy','ordersell','closeout','refer','high','low','openlogic','holdlogic'])<=set(data.columns))==False:
            print('缺少必要数据列',set(['orderbuy','ordersell','closeout','refer','high','low','openlogic','holdlogic']).difference(set(data.columns)))
            return None
        status='close'
        trades=[]
        for inx,row in data.iterrows():
            if status=='close':
                if (row['openlogic']&row['holdlogic']):
                    status='selling'
                    orderday=0
            elif status=='selling':
                orderday+=1
                if (row['ordersell']<=row['high']):
                    status='open'
                    holdday=0
                    orderinfo={'sellinx':inx,'sellday':orderday,'sellbid':max(row['ordersell'],row['low'])}
                if status=='open':
                    revbase=row['refer']
                    revenue=(1-self.sellfee-(revbase/orderinfo['sellbid'])*(1+self.buyfee)-self.interest*holdday)/self.margin
                    guarantee=(1-self.sellfee+self.margin)/((revbase/orderinfo['sellbid'])*(1+self.buyfee)+self.interest*holdday)
                    if guarantee<self.guarantee:
                        status='mco'
                        orderday=0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold==False:
                            status = 'buying'
                            orderday = 0
                else:
                    if (row['openlogic']&row['holdlogic'])==False:
                        status='close'
            elif status=='open':
                holdday+=1
                revbase = row['refer']
                revenue = (1 - self.sellfee - (revbase / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                guarantee = (1 - self.sellfee + self.margin) / ((revbase / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                if guarantee < self.guarantee:
                    status = 'mco'
                    orderday = 0
                else:
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold == False:
                        status = 'buying'
                        orderday = 0
            elif status=='mco':
                holdday += 1
                orderday+=1
                if row['closeout']>=row['low']:
                    orderinfo['buyinx']=inx
                    orderinfo['buyday']=orderday
                    orderinfo['buybid']=min(row['closeout'],row['high'])
                    orderinfo['revenue']=(1 - self.sellfee - (orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    orderinfo['guarantee']=(1 - self.sellfee + self.margin) / ((orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    orderinfo['cost']=(self.sellfee+(orderinfo['buybid'] / orderinfo['sellbid'])*self.buyfee+self.interest * holdday)/self.margin
                    orderinfo['closetype']='margin-closeout'
                    highpiece=data['high'][orderinfo['sellinx']:orderinfo['buyinx']]
                    lowpiece = data['low'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=data['orderbuy'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=(highpiece>=bppiece)*bppiece+(highpiece<bppiece)*highpiece
                    bppiece=(lowpiece<=bppiece)*bppiece+(lowpiece>bppiece)*lowpiece
                    bpdays=pd.Series(range(len(bppiece)),index=bppiece.index)
                    revenueseries=(1 - self.sellfee - (bppiece / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * bpdays) / self.margin
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
            elif status=='buying':
                holdday += 1
                orderday+=1
                if row['orderbuy']>=row['low']:
                    orderinfo['buyinx']=inx
                    orderinfo['buyday']=orderday
                    orderinfo['buybid']=min(row['orderbuy'],row['high'])
                    orderinfo['revenue']=(1 - self.sellfee - (orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    orderinfo['guarantee']=(1 - self.sellfee + self.margin) / ((orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    orderinfo['cost']=(self.sellfee+(orderinfo['buybid'] / orderinfo['sellbid'])*self.buyfee+self.interest * holdday)/self.margin
                    orderinfo['closetype']='buy-close'
                    highpiece=data['high'][orderinfo['sellinx']:orderinfo['buyinx']]
                    lowpiece = data['low'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=data['orderbuy'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=(highpiece>=bppiece)*bppiece+(highpiece<bppiece)*highpiece
                    bppiece=(lowpiece<=bppiece)*bppiece+(lowpiece>bppiece)*lowpiece
                    bpdays=pd.Series(range(len(bppiece)),index=bppiece.index)
                    revenueseries=(1 - self.sellfee - (bppiece / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * bpdays) / self.margin
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                if status=='close':
                    if (row['openlogic'] & row['holdlogic']):
                        status = 'selling'
                        orderday = 0
                else:
                    revbase = row['refer']
                    revenue = (1 - self.sellfee - (revbase / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    guarantee = (1 - self.sellfee + self.margin) / ((revbase / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    if guarantee < self.guarantee:
                        status = 'mco'
                        orderday = 0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold:
                            status='open'
            else:
                raise Exception("Illegal status!")
        if status!='close':
            orderinfo['status']=status
            trades.append(orderinfo)
        return trades

    def statistics_with_callauction(self,data):
        if (set(['conbuy','consell','closeout','callbuy','callsell','refer','high','low','openlogic','holdlogic'])<=set(data.columns))==False:
            print('缺少必要数据列',set(['conbuy','consell','closeout','callbuy','callsell','refer','high','low','openlogic','holdlogic']).difference(set(data.columns)))
            return None
        status='close'
        trades=[]
        for inx,row in data.iterrows():
            if status=='close':
                if (row['openlogic']&row['holdlogic']):
                    status='selling'
                    orderday=0
            elif status=='selling':
                orderday+=1
                if (row['callsell']<=row['open']):
                    status='open'
                    holdday=0
                    orderinfo={'sellinx':inx,'sellday':orderday,'sellbid':row['open']}
                elif (row['consell']<=row['high']):
                    status='open'
                    holdday=0
                    orderinfo={'sellinx':inx,'sellday':orderday,'sellbid':max(row['consell'],row['low'])}
                if status=='open':
                    revbase=row['refer']
                    revenue=(1-self.sellfee-(revbase/orderinfo['sellbid'])*(1+self.buyfee)-self.interest*holdday)/self.margin
                    guarantee=(1-self.sellfee+self.margin)/((revbase/orderinfo['sellbid'])*(1+self.buyfee)+self.interest*holdday)
                    if guarantee<self.guarantee:
                        status='mco'
                        orderday=0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold==False:
                            status = 'buying'
                            orderday = 0
                else:
                    if (row['openlogic']&row['holdlogic'])==False:
                        status='close'
            elif status=='open':
                holdday+=1
                revbase = row['refer']
                revenue = (1 - self.sellfee - (revbase / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                guarantee = (1 - self.sellfee + self.margin) / ((revbase / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                if guarantee < self.guarantee:
                    status = 'mco'
                    orderday = 0
                else:
                    hold = row['holdlogic']
                    for logic in self.extralogics:
                        hold = hold & logic.calc(revenue)
                    if hold == False:
                        status = 'buying'
                        orderday = 0
            elif status=='mco':
                holdday += 1
                orderday+=1
                if row['closeout']>=row['open']:
                    orderinfo['buyinx']=inx
                    orderinfo['buyday']=orderday
                    orderinfo['buybid']=row['open']
                    orderinfo['revenue']=(1 - self.sellfee - (orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    orderinfo['guarantee']=(1 - self.sellfee + self.margin) / ((orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    orderinfo['cost']=(self.sellfee+(orderinfo['buybid'] / orderinfo['sellbid'])*self.buyfee+self.interest * holdday)/self.margin
                    orderinfo['closetype']='margin-closeout'
                    highpiece=data['high'][orderinfo['sellinx']:orderinfo['buyinx']]
                    lowpiece = data['low'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=data['refer'].shift()[orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=(highpiece>=bppiece)*bppiece+(highpiece<bppiece)*highpiece
                    bppiece=(lowpiece<=bppiece)*bppiece+(lowpiece>bppiece)*lowpiece
                    bpdays=pd.Series(range(len(bppiece)),index=bppiece.index)
                    revenueseries=(1 - self.sellfee - (bppiece / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * bpdays) / self.margin
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                elif row['closeout']>=row['low']:
                    orderinfo['buyinx']=inx
                    orderinfo['buyday']=orderday
                    orderinfo['buybid']=min(row['closeout'],row['high'])
                    orderinfo['revenue']=(1 - self.sellfee - (orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    orderinfo['guarantee']=(1 - self.sellfee + self.margin) / ((orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    orderinfo['cost']=(self.sellfee+(orderinfo['buybid'] / orderinfo['sellbid'])*self.buyfee+self.interest * holdday)/self.margin
                    orderinfo['closetype']='margin-closeout'
                    highpiece=data['high'][orderinfo['sellinx']:orderinfo['buyinx']]
                    lowpiece = data['low'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=data['refer'].shift()[orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=(highpiece>=bppiece)*bppiece+(highpiece<bppiece)*highpiece
                    bppiece=(lowpiece<=bppiece)*bppiece+(lowpiece>bppiece)*lowpiece
                    bpdays=pd.Series(range(len(bppiece)),index=bppiece.index)
                    revenueseries=(1 - self.sellfee - (bppiece / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * bpdays) / self.margin
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
            elif status=='buying':
                holdday += 1
                orderday+=1
                if row['callbuy']>=row['open']:
                    orderinfo['buyinx']=inx
                    orderinfo['buyday']=orderday
                    orderinfo['buybid']=row['open']
                    orderinfo['revenue']=(1 - self.sellfee - (orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    orderinfo['guarantee']=(1 - self.sellfee + self.margin) / ((orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    orderinfo['cost']=(self.sellfee+(orderinfo['buybid'] / orderinfo['sellbid'])*self.buyfee+self.interest * holdday)/self.margin
                    orderinfo['closetype']='buy-close'
                    highpiece=data['high'][orderinfo['sellinx']:orderinfo['buyinx']]
                    lowpiece = data['low'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=data['refer'].shift()[orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=(highpiece>=bppiece)*bppiece+(highpiece<bppiece)*highpiece
                    bppiece=(lowpiece<=bppiece)*bppiece+(lowpiece>bppiece)*lowpiece
                    bpdays=pd.Series(range(len(bppiece)),index=bppiece.index)
                    revenueseries=(1 - self.sellfee - (bppiece / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * bpdays) / self.margin
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                elif row['conbuy']>=row['low']:
                    orderinfo['buyinx']=inx
                    orderinfo['buyday']=orderday
                    orderinfo['buybid']=min(row['conbuy'],row['high'])
                    orderinfo['revenue']=(1 - self.sellfee - (orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    orderinfo['guarantee']=(1 - self.sellfee + self.margin) / ((orderinfo['buybid'] / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    orderinfo['cost']=(self.sellfee+(orderinfo['buybid'] / orderinfo['sellbid'])*self.buyfee+self.interest * holdday)/self.margin
                    orderinfo['closetype']='buy-close'
                    highpiece=data['high'][orderinfo['sellinx']:orderinfo['buyinx']]
                    lowpiece = data['low'][orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=data['refer'].shift()[orderinfo['sellinx']:orderinfo['buyinx']]
                    bppiece=(highpiece>=bppiece)*bppiece+(highpiece<bppiece)*highpiece
                    bppiece=(lowpiece<=bppiece)*bppiece+(lowpiece>bppiece)*lowpiece
                    bpdays=pd.Series(range(len(bppiece)),index=bppiece.index)
                    revenueseries=(1 - self.sellfee - (bppiece / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * bpdays) / self.margin
                    orderinfo['revmax']=revenueseries.max()
                    orderinfo['revmin']=revenueseries.min()
                    trades.append(orderinfo)
                    status='close'
                if status=='close':
                    if (row['openlogic'] & row['holdlogic']):
                        status = 'selling'
                        orderday = 0
                else:
                    revbase = row['refer']
                    revenue = (1 - self.sellfee - (revbase / orderinfo['sellbid']) * (1 + self.buyfee) - self.interest * holdday) / self.margin
                    guarantee = (1 - self.sellfee + self.margin) / ((revbase / orderinfo['sellbid']) * (1 + self.buyfee) + self.interest * holdday)
                    if guarantee < self.guarantee:
                        status = 'mco'
                        orderday = 0
                    else:
                        hold = row['holdlogic']
                        for logic in self.extralogics:
                            hold = hold & logic.calc(revenue)
                        if hold:
                            status='open'
            else:
                raise Exception("Illegal status!")
        if status!='close':
            orderinfo['status']=status
            trades.append(orderinfo)
        return trades

class stopprofit_logic:
    def __init__(self,stopprofit):
        self.stopprofit=stopprofit

    def calc(self,revenue):
        return revenue<self.stopprofit

class stoploss_logic:
    def __init__(self,stoploss):
        self.stoploss=stoploss

    def calc(self,revenue):
        return revenue>self.stoploss




