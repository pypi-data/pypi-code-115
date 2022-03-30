import pandas as pd
from dateutil.parser import parse # 문자열을 시간 데이터로 찾아주는 메서드
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'NanumSquare_ac'
import warnings
warnings.filterwarnings('ignore')
from scipy.signal import savgol_filter
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def yearquarter2(data):
    Date = pd.to_datetime(data['DATE'])
    data = pd.DataFrame(data)
    data.index = Date
    
    Date = pd.to_datetime(data['DATE'])
    data = data.resample('W').mean().interpolate()
    return data

def yearquarter(data):
    data['출하일'] = pd.to_datetime(data['출하일'])
    year = data['출하일'].dt.year
    month = data['출하일'].dt.month
    quarter = data['출하일'].dt.quarter
    week = data['출하일'].dt.week
    data['년도'] = year
    data['월'] = month
    data['quarter'] = quarter
    data['week'] = week
    data['quarter'] = data['quarter'].astype(str)
    data['월'] = data['월'].astype(str)
    data['년도'] = data['년도'].astype(str)
    data['week'] = data['week'].astype(str)
    data['주'] = data['년도'] +'년 '+ data['week'] + '째주'
    data['출하일'] = pd.to_datetime(data['출하일'])
    data = data.drop(['월',  '년도', 'quarter'], axis=1)
    return data


def identify_outliers(row, n_sigmas=2):
    x = row['Mean']
    mu = row['mean']
    sigma = row['std']
    if (x > mu + n_sigmas * sigma) | (x < mu - n_sigmas*sigma):
        return 1
    else:
        return 0

def plot_graph(data,tree,window,sav_window,D_t='D', n_sigma=2):

    max_price_lim = int(max(data['Mean']))
    if D_t=='W':
        d_range='주별'
        t_range='Week'

    if D_t=='D':
        d_range='일별'
        t_range='Day'

    if D_t == 'M':
        d_range = '월별'
        t_range = 'Month'

    if D_t=='Y':
        d_range= '년도별'
        t_range='Year'
  ############ plot(1)

    data.dtypes

    D_mean_price = data.resample(D_t).mean()
    D_mean_price.dropna(inplace=True)
    plt.figure(figsize=(15, 10))
    plt.plot(data['Mean'], label=f'{tree}')
    plt.ylabel(f'Average Price / 주별')
    plt.title(f'[느티나무] 주별 가격 추이',fontsize=15)
    plt.xlabel('WEEK',fontsize=13)
    plt.legend()
    plt.show()
    plt.savefig(f'[{tree}] {d_range} 가격 추이.jpg', dpi=300)
    

    ############ plot(1)


    df_rolling = D_mean_price['Mean'].rolling(window=window).agg(['mean', 'std'])
    df_outliers = D_mean_price.join(df_rolling)

    #df_outliers['outlier'] = df_outliers.apply(identify_outliers, axis=1)
    df_outliers['outlier'] = df_outliers.apply(lambda x: identify_outliers(x, n_sigma), axis=1)
    outliers = df_outliers.loc[df_outliers['outlier'] == 1, ['Mean']]

    ############ plot(2)
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.plot(df_outliers.index, df_outliers['Mean'], color='blue', label=f'{tree}')
    ax.scatter(outliers.index, outliers['Mean'], color='red', label='Clensing Target')
    ax.set_title(f'[{tree}] {d_range} 가격추이 Prepare Clensing({n_sigma}σ)',fontsize=15)
    ax.legend(loc='lower right')
    plt.ylabel(f'Average Price / {t_range}',fontsize=13)
    plt.xlabel('year',fontsize=13)
    plt.ylim(0,max_price_lim)
    plt.savefig(f'[{tree}] {d_range} 가격추이 Prepare Clensing({n_sigma}σ).jpg', dpi=300)
    ############ plot(2)


    drop_df_outliers = df_outliers.drop(index=outliers.index)

    ############ plot(3)
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.plot(drop_df_outliers.index, drop_df_outliers['Mean'], color='blue', label=f'{tree}')
    plt.ylim(0, max_price_lim)
    ax.set_title(f'[{tree}] {d_range} 가격추이 After Clensing({n_sigma}σ,window={window})',fontsize=15)
    plt.ylabel(f'Average Price / {t_range}',fontsize=13)
    plt.xlabel('year',fontsize=13)
    ax.legend(loc='lower right')
    plt.savefig(f'[{tree}] {d_range} 가격추이 After Clensing({n_sigma}σ, window={window}).jpg', dpi=300)
    ############ plot(3)

    ############ plot(4)
    ## Savgol

    savgol_f = savgol_filter(drop_df_outliers['mean'][window-1:], sav_window, 1,deriv=0)
    savgol_f = pd.DataFrame(savgol_f)
    savgol_f.columns = ['savgol_mean']
    savgol_f['Date'] = drop_df_outliers.index[window-1:]

    fig, ax = plt.subplots(figsize=(15, 10))
    ax.plot(savgol_f['Date'], savgol_f['savgol_mean'], color='blue', label=f'{tree}')
    ax.set_title(f'[{tree}] {d_range} 가격추이 Smoothing 적용(after S-G({sav_window},{sav_window},1))',fontsize=15)
    ax.legend(loc='lower right')
    plt.ylabel(f'Average Price / {t_range}',fontsize=13)
    #plt.text(len(savgol_f)//4, int(max_price_lim // 1.25), "after S-G( 15 , 15, 0 )",fontsize=15)
    #ax.text(0.5, -0.5, '한글',transform=ax.transAxes)
    #plt.ylim(0, max_price_lim)
    plt.xlabel('year',fontsize=13)
    plt.savefig(f'[{tree}] {d_range} 가격 추이 Smoothing 적용.jpg', dpi=300)
    ###################################
    return savgol_f


def get_outlier(df=None, column=None, weight=1.5):
    quantile_25 = np.percentile(df[column].values, 25)
    quantile_75 = np.percentile(df[column].values, 75)
    
    IQR = quantile_75 - quantile_25
    IQR_weight = IQR*weight
    
    lowest = quantile_25 - IQR_weight
    highest = quantile_75 + IQR_weight
    
    outlier_idx = df[column][ (df[column] < lowest) | (df[column] > highest) ].index
    return outlier_idx

def suppro_prepro(data, name):
    tree_data = data[data['품목명'] == name]
    tree_data = tree_data[tree_data['단가(원가)'] > 0]
    tree_data = tree_data[tree_data['단가'] > 0]
    
    if name == '복자기':
        tree_data = tree_data.loc[tree_data['규격'] == 'H3.5*R12']
    elif name == '칠엽수':
        tree_data = tree_data.loc[tree_data['규격'] == 'H3.5*R12']
    elif name == '계수나무':
        tree_data = tree_data.loc[tree_data['규격'] == 'H3.5*R8']
    elif name == '스트로브잣나무':
        tree_data = tree_data.loc[tree_data['규격'] == 'H2.0*W1.0']    
    else:
        size = tree_data['규격'].value_counts().index[0]
        tree_data = tree_data.loc[tree_data['규격'] == size]
    tree_data = tree_data.drop(['Unnamed: 0', '사업장', '프로젝트', '프로젝트명', '품목코드', '매입처코드', '매입처', '납품유형', '출하유형', '출하처코드', '출하처', '양품/불량', '자재창고', '출하번호', '출하순번', '수주번호', '수주순번', '출하방법', '출하부서', '담당자', '수주처코드', '수주처', '수주일', '납기일',  '매출처', '출하창고', '비고'], axis=1)
    tree_data.columns = ['DATE', 'SPECIES_NM', 'SIZE', 'SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']
    #tree_data = tree_data.groupby(['DATE']).mean()
    #tree_data = tree_data[['SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']]
    tree_data = tree_data[['SPECIES_NM', 'DATE', 'SIZE', 'SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']]
    return tree_data

def createDirectory(directory): 
    import os
    try: 
        if not os.path.exists(directory): 
            os.makedirs(directory) 
    except OSError: print("Error: Failed to create the directory.")


def suppro_prepro2(data, name):
    tree_data = data[data['품목명'] == name]
    tree_data = tree_data[tree_data['단가(원가)'] > 0]
    tree_data = tree_data[tree_data['단가'] > 0]
    # tree_data = tree_data.loc[tree_data['규격'] == size]
    # if name == '복자기':
    #     tree_data = tree_data.loc[tree_data['규격'] == 'H3.5*R12']
    # elif name == '칠엽수':
    #     tree_data = tree_data.loc[tree_data['규격'] == 'H3.5*R12']
    # elif name == '계수나무':
    #     tree_data = tree_data.loc[tree_data['규격'] == 'H3.5*R8']
    # elif name == '스트로브잣나무':
    #     tree_data = tree_data.loc[tree_data['규격'] == 'H2.0*W1.0']    
    # else:
    #     size = tree_data['규격'].value_counts().index[0]
    #     tree_data = tree_data.loc[tree_data['규격'] == size]
    tree_data = tree_data.drop(['Unnamed: 0', '사업장', '프로젝트', '프로젝트명', '품목코드', '매입처코드', '매입처', '납품유형', '출하유형', '출하처코드', '출하처', '양품/불량', '자재창고', '출하번호', '출하순번', '수주번호', '수주순번', '출하방법', '출하부서', '담당자', '수주처코드', '수주처', '수주일', '납기일',  '매출처', '출하창고', '비고'], axis=1)
    tree_data.columns = ['DATE', 'SPECIES_NM', 'SIZE', 'SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']
    #tree_data = tree_data.groupby(['DATE']).mean()
    #tree_data = tree_data[['SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']]
    tree_data = tree_data[['SPECIES_NM', 'DATE', 'SIZE', 'SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']]
    return tree_data

def suppro_prepro22(data, name):
    tree_data = data[data['수종'] == name]
    tree_data = tree_data[tree_data['매입단가'] > 0]
    tree_data = tree_data[tree_data['매출단가'] > 0]
    tree_data = tree_data[['납품일', '수종', '규격', '총반입', '매출단가', '매출액', '매입단가', '매입액']]
    tree_data.columns = ['DATE', 'SPECIES_NM', 'SIZE', 'SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)']
    #tree_data = tree_data.groupby(['DATE']).mean()
    #tree_data = tree_data[['SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)', 'SALES']]
    tree_data = tree_data[['SPECIES_NM', 'DATE', 'SIZE', 'SHIPMNET', 'UNIT_PREICE', 'SHIPMENT_PRICE','UNIT_PREICE(COST)', 'PRICE(COST)']]
    return tree_data

def suppro_prepro3(data, name, size):
    data = data.loc[data['SIZE'] == size]
    return data

def stl_data_make(data):
    ma_n = 2
    stl_len = 35
    #stl_d = stl_data(data, 7)
    for i in range(0, stl_len, 7):
        if i != 0 :
            stl_d = stl_data(data, i)
        else :
            pass
    stl_MA12_data = MA_data(stl_d,n=ma_n,rm=True)
    data = sav_gol(stl_MA12_data)
    return data

def stl_data(data, perio=None): # stl preprocessing trend, seasonal, residual parameter
    from statsmodels.tsa.seasonal import STL,seasonal_decompose
    price = data['UNIT_PREICE(COST)']
    price.index = pd.to_datetime(data['DATE'])
    price.sort_index(inplace=True)
    if perio == None:
        stl = STL(price,period=len(data['DATE'][pd.DatetimeIndex(data['DATE']).year==2017]))
        res = stl.fit()
        data.sort_values(by='DATE',inplace=True)
        trend = pd.DataFrame(res.trend) # trend
        seasonal = pd.DataFrame(res.seasonal) # seasonal
        residual = pd.DataFrame(res.resid) # residual
        data['trend'] = trend['trend'].values
        data['seasonal'] = seasonal['season'].values
        data['residual'] = residual['resid'].values
    elif perio != None:
        stl = STL(price,period=perio)
        res = stl.fit()
        data.sort_values(by='DATE',inplace=True)
        trend = pd.DataFrame(res.trend) # trend
        seasonal = pd.DataFrame(res.seasonal) # seasonal
        residual = pd.DataFrame(res.resid) # residual

        data[f'trend{perio}'] = trend['trend'].values
        data[f'seasonal{perio}'] = seasonal['season'].values
        data[f'residual{perio}'] = residual['resid'].values
    
    return data

def MA_data(data,n=3,rm=True):  # MA n, rm: MA NAN value Remove
    data[f'sma{n}'] = data['UNIT_PREICE(COST)'].rolling(n).mean() 
    
    if rm==True:
        return data[n-1:]
    return data

def sav_gol(data,window_length=11,polyorder=3):  # window_length(odd number): , polyorder :  diff 
    from scipy.signal import savgol_filter
    data['savgol'] = savgol_filter(data['UNIT_PREICE(COST)'],window_length,polyorder)
    return data

def rm_zero(data): # remove zero value
    return data[data['UNIT_PREICE(COST)']>0]


def stl_data2(data, perio=None): # stl preprocessing trend, seasonal, residual parameter
    from statsmodels.tsa.seasonal import STL,seasonal_decompose
    price = data['UNIT_PREICE']
    price.index = pd.to_datetime(data['DATE'])
    price.sort_index(inplace=True)
    if perio == None:
        stl = STL(price,period=len(data['DATE'][pd.DatetimeIndex(data['DATE']).year==2017]))
        res = stl.fit()
        data.sort_values(by='DATE',inplace=True)
        trend = pd.DataFrame(res.trend) # trend
        seasonal = pd.DataFrame(res.seasonal) # seasonal
        residual = pd.DataFrame(res.resid) # residual
        data['trend'] = trend['trend'].values
        data['seasonal'] = seasonal['season'].values
        data['residual'] = residual['resid'].values
    elif perio != None:
        stl = STL(price,period=perio)
        res = stl.fit()
        data.sort_values(by='DATE',inplace=True)
        trend = pd.DataFrame(res.trend) # trend
        seasonal = pd.DataFrame(res.seasonal) # seasonal
        residual = pd.DataFrame(res.resid) # residual

        data[f'trend{perio}'] = trend['trend'].values
        data[f'seasonal{perio}'] = seasonal['season'].values
        data[f'residual{perio}'] = residual['resid'].values
    
    return data


def stl_data_make2(data):
    ma_n = 2
    stl_len = 35
    #stl_d = stl_data(data, 7)
    for i in range(0, stl_len, 7):
        if i != 0 :
            stl_d = stl_data2(data, i)
        else :
            pass
    stl_MA12_data = MA_data2(stl_d,n=ma_n,rm=True)
    data = sav_gol2(stl_MA12_data)
    return data

def stl_data2(data, perio=None): # stl preprocessing trend, seasonal, residual parameter
    from statsmodels.tsa.seasonal import STL,seasonal_decompose
    price = data['UNIT_PREICE']
    price.index = pd.to_datetime(data['DATE'])
    price.sort_index(inplace=True)
    if perio == None:
        stl = STL(price,period=len(data['DATE'][pd.DatetimeIndex(data['DATE']).year==2017]))
        res = stl.fit()
        data.sort_values(by='DATE',inplace=True)
        trend = pd.DataFrame(res.trend) # trend
        seasonal = pd.DataFrame(res.seasonal) # seasonal
        residual = pd.DataFrame(res.resid) # residual
        data['trend'] = trend['trend'].values
        data['seasonal'] = seasonal['season'].values
        data['residual'] = residual['resid'].values
    elif perio != None:
        stl = STL(price,period=perio)
        res = stl.fit()
        data.sort_values(by='DATE',inplace=True)
        trend = pd.DataFrame(res.trend) # trend
        seasonal = pd.DataFrame(res.seasonal) # seasonal
        residual = pd.DataFrame(res.resid) # residual

        data[f'trend{perio}'] = trend['trend'].values
        data[f'seasonal{perio}'] = seasonal['season'].values
        data[f'residual{perio}'] = residual['resid'].values
    
    return data

def MA_data2(data,n=3,rm=True):  # MA n, rm: MA NAN value Remove
    data[f'sma{n}'] = data['UNIT_PREICE'].rolling(n).mean() 
    
    if rm==True:
        return data[n-1:]
    return data

def sav_gol2(data,window_length=11,polyorder=3):  # window_length(odd number): , polyorder :  diff 
    from scipy.signal import savgol_filter
    data['savgol'] = savgol_filter(data['UNIT_PREICE'],window_length,polyorder)
    return data

def rm_zero2(data): # remove zero value
    return data[data['UNIT_PREICE']>0]



###########################################
def lstm_set_seq(series, n_lags):
    X, y = [], []
    for step in range(len(series)-n_lags):
        end_step = step + n_lags
        X.append(series[step:end_step])
        y.append(series[end_step])
    return np.array(X), np.array(y)

def lstm_set_sequence(seq, seq_len):
    X = []
    y = []
    for t in range(len(seq) - seq_len):  ## 268 - 12 = 256
        end = t + seq_len  # End index is equal to the current index plus the specified number of sequence length
        # t + 12
        if end > len(
                seq) - 1:  # t + 12 > 268 - 1 -> 0~255  # if the length of the formed train sequence is greater than the length of the input feature,stop
            break
        # for seq_length=12 : X_input seq. ->12 (indices 0-11) past observations, y_target -> 1 observation at one time step ahead
        # (index 12)
        Xseq = seq[t:end]  # shape(256, 3) 0~12,x1,x2,x3
        y_target = seq[end]  # shape(256,1) 12~268,y
        X.append(Xseq)
        y.append(y_target)
    return np.array(X), np.array(y)  # initializing the arrays

def lstm_input(input_data):
    import datetime
    import time
    import os
    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    return input_data

def LSTM(input_data, seq_len,batch,num_epochs,tree_name, size, verbose,model_name, save,save_path, model_path=None, type=None):
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM
    from tensorflow.keras import initializers
    from sklearn.metrics import mean_squared_error
    import tensorflow as tf
    from tensorflow.keras.callbacks import ModelCheckpoint
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    import datetime
    import time
    import os
    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    input_1 = input_data['UNIT_PREICE(COST)'].values
    input_2 = input_data['trend7'].values
    input_3 = input_data['seasonal7'].values
    input_4 = input_data['residual7'].values
    input_5 = input_data['sma2'].values
    input_6 = input_data['savgol'].values
    input_7 = input_data['seasonal14'].values
    input_8 = input_data['residual14'].values
    input_9 = input_data['trend14'].values
    input_10 = input_data['seasonal21'].values
    input_11 = input_data['residual21'].values
    input_12 = input_data['trend21'].values
    input_13 = input_data['seasonal28'].values
    input_14 = input_data['residual28'].values
    input_15 = input_data['trend28'].values
    # input_16 = input_data['seasonal35'].values
    # input_17 = input_data['residual35'].values
    # input_18 = input_data['trend35'].values

    output_feat = input_data['UNIT_PREICE(COST)'].values

    # Reshaping for converting the inputs/output to 2d shape
    input_1 = input_1.reshape((len(input_1), 1))
    input_2 = input_2.reshape((len(input_2), 1))
    input_3 = input_3.reshape((len(input_3), 1))
    input_4 = input_4.reshape((len(input_4), 1))
    input_5 = input_5.reshape((len(input_5), 1))
    input_6 = input_6.reshape((len(input_6), 1))
    input_7 = input_7.reshape((len(input_7), 1))
    input_8 = input_8.reshape((len(input_8), 1))
    input_9 = input_9.reshape((len(input_9), 1))
    input_10 = input_10.reshape((len(input_10), 1))
    input_11 = input_11.reshape((len(input_11), 1))
    input_12 = input_12.reshape((len(input_12), 1))
    input_13 = input_13.reshape((len(input_13), 1))
    input_14 = input_14.reshape((len(input_14), 1))
    input_15 = input_15.reshape((len(input_15), 1))
    # input_16 = input_16.reshape((len(input_16), 1))
    # input_17 = input_17.reshape((len(input_17), 1))
    # input_18 = input_18.reshape((len(input_18), 1))

    output_feat = output_feat.reshape((len(output_feat), 1))
    from numpy import hstack
    df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

    mean_df = df.reshape((-1, 1))

    pred_horizon = input_data.shape[0]//10 * 3

    X_train = df[:-pred_horizon] 
    Y_train = output_feat[:-pred_horizon]  

    X_test = df[-pred_horizon:]  
    Y_test = output_feat[-pred_horizon:] 

    real_price = output_feat[-8:]

    print(f' X_test.shape : {X_test.shape}, Y_test.shape : {Y_test.shape}')
    print(f' X_train.shape : {X_train.shape}, Y_train.shape : {Y_train.shape}')

    #from sklearn.preprocessing import RobustScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    x_train = scaler.fit_transform(X_train)
    x_test = scaler.transform(X_test)
    y_train = scaler.fit_transform(Y_train)
    y_test = scaler.transform(Y_test)

    
    ### nan value solution 
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)

    df_x_train = pd.DataFrame(x_train)
    delete_idx = df_x_train[df_x_train[1].isnull()].index.values
    x_train = np.delete(x_train,delete_idx,axis=0)
    y_train = np.delete(y_train,delete_idx,axis=0)

    # Creating the training sequences
    train_generator = TimeseriesGenerator(x_train,y_train,length=seq_len,batch_size=batch)
    test_generator = TimeseriesGenerator(x_test, y_test, length=seq_len, batch_size=batch)

    features_num = X_train.shape[1]  # 3
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout   
    from tensorflow.keras.callbacks import EarlyStopping  
    #initializer = tf.keras.initializers.he_uniform(seed=0)
    
    model = Sequential()
    model.add(
        LSTM(200,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(
            100,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(60,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )   
    model.add(Dropout(0.5))
    model.add(
        LSTM(30,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(10,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=False)
    )
    model.add(Dense(1))
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss='mse')
    cb_early_stopping = EarlyStopping(monitor='loss', mode='min', patience=200)
    best_model = f'LSTMlen({seq_len})_epochs({num_epochs})_{model_name}.h5'

    start = time.time()

    history = model.fit_generator(train_generator, epochs=num_epochs, verbose=1,callbacks=[cb_early_stopping])

    model.summary()

    prediction = model.predict_generator(test_generator)

    end_time = time.time() - start
    end_time = time.strftime("%H:%M:%S", time.gmtime(end_time))


    learning_time = '{:0.3f}s'.format(time.time()-start)
    #be_rmse = np.sqrt(mean_squared_error(prediction,y_test[seq_len:]))
    # inverse scale
    predicted = scaler.inverse_transform(prediction)
    MSE = mean_squared_error(predicted, Y_test[seq_len:])
    RMSE = np.sqrt(MSE) 

    pred = model.predict(x_test[-seq_len:].reshape(1,seq_len,features_num))
    pred_value = scaler.inverse_transform(pred)
    pred_value = pd.DataFrame(pred_value,columns=['predict'])    

    from tensorflow.keras.models import load_model
    model.save('C:\\Users\\aiicon\\Desktop\\project_0831_server\\2_suppro\\Base_Model\\model.h5')

    # input_data = input_data[:-8]
    from datetime import timedelta
    for i in range(8):
        date = input_data['DATE']
        one_year = timedelta(days=365)
        next_year = date[-1:] + one_year
        next = pd.DataFrame()
        next['DATE'] = next_year.values
        date
        next
        
        date = pd.concat([date,next['DATE']])
        date = pd.DataFrame(date)
        date.reset_index(inplace=True, drop=True)
        date
        
        
        price = list(input_data['UNIT_PREICE(COST)'].values)
        price.append(pred_value['predict'][0])
        
        pred_price = pd.DataFrame()
        pred_price['UNIT_PREICE(COST)'] = price
        pred_price['DATE'] = date
        pred_price
        ma_n = 2
        # stl_d = stl_data(pred_price, 7)
        for i in range(0, 29, 7):
            if i != 0 :
                stl_d = stl_data(pred_price, i)
            else :
                pass
        stl_MA12_data = MA_data(stl_d,n=ma_n)
        
        stl_MA12_data.dropna(inplace=True)
        
        c_stl_MA12_data = stl_MA12_data.copy()
        data = sav_gol(c_stl_MA12_data)
        #data = smooth(data, 10)
        
        input_1 = input_data['UNIT_PREICE(COST)'].values
        input_2 = input_data['trend7'].values
        input_3 = input_data['seasonal7'].values
        input_4 = input_data['residual7'].values
        input_5 = input_data['sma2'].values
        input_6 = input_data['savgol'].values
        input_7 = input_data['seasonal14'].values
        input_8 = input_data['residual14'].values
        input_9 = input_data['trend14'].values
        input_10 = input_data['seasonal21'].values
        input_11 = input_data['residual21'].values
        input_12 = input_data['trend21'].values
        input_13 = input_data['seasonal28'].values
        input_14 = input_data['residual28'].values
        input_15 = input_data['trend28'].values
        # input_16 = input_data['seasonal35'].values
        # input_17 = input_data['residual35'].values
        # input_18 = input_data['trend35'].values


        # Reshaping for converting the inputs/output to 2d shape
        input_1 = input_1.reshape((len(input_1), 1))
        input_2 = input_2.reshape((len(input_2), 1))
        input_3 = input_3.reshape((len(input_3), 1))
        input_4 = input_4.reshape((len(input_4), 1))
        input_5 = input_5.reshape((len(input_5), 1))
        input_6 = input_6.reshape((len(input_6), 1))
        input_7 = input_7.reshape((len(input_7), 1))
        input_8 = input_8.reshape((len(input_8), 1))
        input_9 = input_9.reshape((len(input_9), 1))
        input_10 = input_10.reshape((len(input_10), 1))
        input_11 = input_11.reshape((len(input_11), 1))
        input_12 = input_12.reshape((len(input_12), 1))
        input_13 = input_13.reshape((len(input_13), 1))
        input_14 = input_14.reshape((len(input_14), 1))
        input_15 = input_15.reshape((len(input_15), 1))
        # input_16 = input_16.reshape((len(input_16), 1))
        # input_17 = input_17.reshape((len(input_17), 1))
        # input_18 = input_18.reshape((len(input_18), 1))

        from numpy import hstack
        df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

        from sklearn.preprocessing import MinMaxScaler
        scaler1 = MinMaxScaler()
        scaler2 = MinMaxScaler()
        
        df_scaler = scaler1.fit_transform(df)
        df_price = scaler2.fit_transform(input_1)

        pred = model.predict(df_scaler[-seq_len:].reshape(1,seq_len,features_num))
        
        predicted = scaler2.inverse_transform(pred)
        pred_value = pd.DataFrame(predicted,columns=['predict'])

        input_data = input_data.append(data[-1:])
        # input_data = data

        size = str(size)
        size = size.replace('*', 'X')
        # title = f"LSTM_({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_loss.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title, tree_name, option='loss',history=history,save=save)
    # print('========================= Training Complete====================')

    title = f"LSTM_W({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_result.jpg"    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title, tree_name, size, option='result',pred_horizon=pred_horizon,seq_len=seq_len,input_data=input_data,predicted=predicted,pred_value=pred_value,save=save)
    

    predict_8years = input_data['UNIT_PREICE(COST)'][-8:]

    MSE_1y = mean_squared_error(real_price[0], predict_8years[0:1])
    MSE_2y = mean_squared_error(real_price[1], predict_8years[1:2])
    MSE_3y = mean_squared_error(real_price[2], predict_8years[2:3])
    MSE_4y = mean_squared_error(real_price[3], predict_8years[3:4])
    MSE_5y = mean_squared_error(real_price[4], predict_8years[4:5])
    MSE_6y = mean_squared_error(real_price[5], predict_8years[5:6])
    MSE_7y = mean_squared_error(real_price[6], predict_8years[6:7])
    MSE_8y = mean_squared_error(real_price[7], predict_8years[7:8])
    
    RMSE_1y = np.sqrt(MSE_1y)
    RMSE_2y = np.sqrt(MSE_2y)
    RMSE_3y = np.sqrt(MSE_3y)
    RMSE_4y = np.sqrt(MSE_4y)
    RMSE_5y = np.sqrt(MSE_5y)
    RMSE_6y = np.sqrt(MSE_6y)
    RMSE_7y = np.sqrt(MSE_7y)
    RMSE_8y = np.sqrt(MSE_8y)

    mape1 = 1 - np.abs((real_price[0] - predict_8years[0:1]) / real_price[0])
    mape2 = 1 - np.abs((real_price[1] - predict_8years[1:2]) / real_price[1])
    mape3 = 1 - np.abs((real_price[2] - predict_8years[2:3]) / real_price[2])
    mape4 = 1 - np.abs((real_price[3] - predict_8years[3:4]) / real_price[3])
    mape5 = 1 - np.abs((real_price[4] - predict_8years[4:5]) / real_price[4])
    mape6 = 1 - np.abs((real_price[5] - predict_8years[5:6]) / real_price[5])
    mape7 = 1 - np.abs((real_price[6] - predict_8years[6:7]) / real_price[6])
    mape8 = 1 - np.abs((real_price[7] - predict_8years[7:8]) / real_price[7])
    return real_price, input_data['UNIT_PREICE(COST)'][-8:], RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8

def LSTM_UNIT_PREICE(input_data, seq_len,batch,num_epochs,tree_name, size, verbose,model_name, save,save_path, model_path=None, type=None):
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM
    from tensorflow.keras import initializers
    from sklearn.metrics import mean_squared_error
    import tensorflow as tf
    from tensorflow.keras.callbacks import ModelCheckpoint
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    import datetime
    import time
    import os
    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    input_1 = input_data['UNIT_PREICE'].values
    input_2 = input_data['trend7'].values
    input_3 = input_data['seasonal7'].values
    input_4 = input_data['residual7'].values
    input_5 = input_data['sma2'].values
    input_6 = input_data['savgol'].values
    input_7 = input_data['seasonal14'].values
    input_8 = input_data['residual14'].values
    input_9 = input_data['trend14'].values
    input_10 = input_data['seasonal21'].values
    input_11 = input_data['residual21'].values
    input_12 = input_data['trend21'].values
    input_13 = input_data['seasonal28'].values
    input_14 = input_data['residual28'].values
    input_15 = input_data['trend28'].values
    # input_16 = input_data['seasonal35'].values
    # input_17 = input_data['residual35'].values
    # input_18 = input_data['trend35'].values

    output_feat = input_data['UNIT_PREICE'].values

    # Reshaping for converting the inputs/output to 2d shape
    input_1 = input_1.reshape((len(input_1), 1))
    input_2 = input_2.reshape((len(input_2), 1))
    input_3 = input_3.reshape((len(input_3), 1))
    input_4 = input_4.reshape((len(input_4), 1))
    input_5 = input_5.reshape((len(input_5), 1))
    input_6 = input_6.reshape((len(input_6), 1))
    input_7 = input_7.reshape((len(input_7), 1))
    input_8 = input_8.reshape((len(input_8), 1))
    input_9 = input_9.reshape((len(input_9), 1))
    input_10 = input_10.reshape((len(input_10), 1))
    input_11 = input_11.reshape((len(input_11), 1))
    input_12 = input_12.reshape((len(input_12), 1))
    input_13 = input_13.reshape((len(input_13), 1))
    input_14 = input_14.reshape((len(input_14), 1))
    input_15 = input_15.reshape((len(input_15), 1))
    # input_16 = input_16.reshape((len(input_16), 1))
    # input_17 = input_17.reshape((len(input_17), 1))
    # input_18 = input_18.reshape((len(input_18), 1))

    output_feat = output_feat.reshape((len(output_feat), 1))
    from numpy import hstack
    df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

    mean_df = df.reshape((-1, 1))

    pred_horizon = input_data.shape[0]//10 * 3

    X_train = df[:-pred_horizon] 
    Y_train = output_feat[:-pred_horizon]  

    X_test = df[-pred_horizon:]  
    Y_test = output_feat[-pred_horizon:] 

    real_price = output_feat[-8:]

    print(f' X_test.shape : {X_test.shape}, Y_test.shape : {Y_test.shape}')
    print(f' X_train.shape : {X_train.shape}, Y_train.shape : {Y_train.shape}')

    #from sklearn.preprocessing import RobustScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    x_train = scaler.fit_transform(X_train)
    x_test = scaler.transform(X_test)
    y_train = scaler.fit_transform(Y_train)
    y_test = scaler.transform(Y_test)

    
    ### nan value solution 
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)

    df_x_train = pd.DataFrame(x_train)
    delete_idx = df_x_train[df_x_train[1].isnull()].index.values
    x_train = np.delete(x_train,delete_idx,axis=0)
    y_train = np.delete(y_train,delete_idx,axis=0)

    # Creating the training sequences
    train_generator = TimeseriesGenerator(x_train,y_train,length=seq_len,batch_size=batch)
    test_generator = TimeseriesGenerator(x_test, y_test, length=seq_len, batch_size=batch)

    features_num = X_train.shape[1]  # 3
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout   
    from tensorflow.keras.callbacks import EarlyStopping  
    #initializer = tf.keras.initializers.he_uniform(seed=0)
    
    model = Sequential()
    model.add(
        LSTM(200,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(
            100,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(60,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )   
    model.add(Dropout(0.5))
    model.add(
        LSTM(30,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(10,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=False)
    )
    model.add(Dense(1))
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss='mse')
    cb_early_stopping = EarlyStopping(monitor='loss', mode='min', patience=200)
    best_model = f'LSTMlen({seq_len})_epochs({num_epochs})_{model_name}.h5'

    start = time.time()

    history = model.fit_generator(train_generator, epochs=num_epochs, verbose=1,callbacks=[cb_early_stopping])

    model.summary()

    prediction = model.predict_generator(test_generator)

    end_time = time.time() - start
    end_time = time.strftime("%H:%M:%S", time.gmtime(end_time))


    learning_time = '{:0.3f}s'.format(time.time()-start)
    #be_rmse = np.sqrt(mean_squared_error(prediction,y_test[seq_len:]))
    # inverse scale
    predicted = scaler.inverse_transform(prediction)
    MSE = mean_squared_error(predicted, Y_test[seq_len:])
    RMSE = np.sqrt(MSE) 

    pred = model.predict(x_test[-seq_len:].reshape(1,seq_len,features_num))
    pred_value = scaler.inverse_transform(pred)
    pred_value = pd.DataFrame(pred_value,columns=['predict'])    

    from tensorflow.keras.models import load_model
    model.save('C:\\Users\\aiicon\\Desktop\\project_0831_server\\2_suppro\\Base_Model\\model.h5')

    # input_data = input_data[:-8]
    from datetime import timedelta
    for i in range(8):
        date = input_data['DATE']
        one_year = timedelta(days=365)
        next_year = date[-1:] + one_year
        next = pd.DataFrame()
        next['DATE'] = next_year.values
        date
        next
        
        date = pd.concat([date,next['DATE']])
        date = pd.DataFrame(date)
        date.reset_index(inplace=True, drop=True)
        date
        
        
        price = list(input_data['UNIT_PREICE'].values)
        price.append(pred_value['predict'][0])
        
        pred_price = pd.DataFrame()
        pred_price['UNIT_PREICE'] = price
        pred_price['DATE'] = date
        pred_price
        ma_n = 2
        # stl_d = stl_data(pred_price, 7)
        for i in range(0, 29, 7):
            if i != 0 :
                stl_d = stl_data2(pred_price, i)
            else :
                pass
        stl_MA12_data = MA_data2(stl_d,n=ma_n)
        
        stl_MA12_data.dropna(inplace=True)
        
        c_stl_MA12_data = stl_MA12_data.copy()
        data = sav_gol2(c_stl_MA12_data)
        #data = smooth(data, 10)
        
        input_1 = input_data['UNIT_PREICE'].values
        input_2 = input_data['trend7'].values
        input_3 = input_data['seasonal7'].values
        input_4 = input_data['residual7'].values
        input_5 = input_data['sma2'].values
        input_6 = input_data['savgol'].values
        input_7 = input_data['seasonal14'].values
        input_8 = input_data['residual14'].values
        input_9 = input_data['trend14'].values
        input_10 = input_data['seasonal21'].values
        input_11 = input_data['residual21'].values
        input_12 = input_data['trend21'].values
        input_13 = input_data['seasonal28'].values
        input_14 = input_data['residual28'].values
        input_15 = input_data['trend28'].values
        # input_16 = input_data['seasonal35'].values
        # input_17 = input_data['residual35'].values
        # input_18 = input_data['trend35'].values


        # Reshaping for converting the inputs/output to 2d shape
        input_1 = input_1.reshape((len(input_1), 1))
        input_2 = input_2.reshape((len(input_2), 1))
        input_3 = input_3.reshape((len(input_3), 1))
        input_4 = input_4.reshape((len(input_4), 1))
        input_5 = input_5.reshape((len(input_5), 1))
        input_6 = input_6.reshape((len(input_6), 1))
        input_7 = input_7.reshape((len(input_7), 1))
        input_8 = input_8.reshape((len(input_8), 1))
        input_9 = input_9.reshape((len(input_9), 1))
        input_10 = input_10.reshape((len(input_10), 1))
        input_11 = input_11.reshape((len(input_11), 1))
        input_12 = input_12.reshape((len(input_12), 1))
        input_13 = input_13.reshape((len(input_13), 1))
        input_14 = input_14.reshape((len(input_14), 1))
        input_15 = input_15.reshape((len(input_15), 1))
        # input_16 = input_16.reshape((len(input_16), 1))
        # input_17 = input_17.reshape((len(input_17), 1))
        # input_18 = input_18.reshape((len(input_18), 1))

        from numpy import hstack
        df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

        from sklearn.preprocessing import MinMaxScaler
        scaler1 = MinMaxScaler()
        scaler2 = MinMaxScaler()
        
        df_scaler = scaler1.fit_transform(df)
        df_price = scaler2.fit_transform(input_1)

        pred = model.predict(df_scaler[-seq_len:].reshape(1,seq_len,features_num))
        
        predicted = scaler2.inverse_transform(pred)
        pred_value = pd.DataFrame(predicted,columns=['predict'])

        input_data = input_data.append(data[-1:])
        # input_data = data

        size = str(size)
        size = size.replace('*', 'X')
        # title = f"LSTM_({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_loss.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title, tree_name, option='loss',history=history,save=save)
    # print('========================= Training Complete====================')

    title = f"LSTM_W({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_result.jpg"    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss2(title, tree_name, size, option='result',pred_horizon=pred_horizon,seq_len=seq_len,input_data=input_data,predicted=predicted,pred_value=pred_value,save=save)
    

    predict_8years = input_data['UNIT_PREICE'][-8:]

    MSE_1y = mean_squared_error(real_price[0], predict_8years[0:1])
    MSE_2y = mean_squared_error(real_price[1], predict_8years[1:2])
    MSE_3y = mean_squared_error(real_price[2], predict_8years[2:3])
    MSE_4y = mean_squared_error(real_price[3], predict_8years[3:4])
    MSE_5y = mean_squared_error(real_price[4], predict_8years[4:5])
    MSE_6y = mean_squared_error(real_price[5], predict_8years[5:6])
    MSE_7y = mean_squared_error(real_price[6], predict_8years[6:7])
    MSE_8y = mean_squared_error(real_price[7], predict_8years[7:8])
    
    RMSE_1y = np.sqrt(MSE_1y)
    RMSE_2y = np.sqrt(MSE_2y)
    RMSE_3y = np.sqrt(MSE_3y)
    RMSE_4y = np.sqrt(MSE_4y)
    RMSE_5y = np.sqrt(MSE_5y)
    RMSE_6y = np.sqrt(MSE_6y)
    RMSE_7y = np.sqrt(MSE_7y)
    RMSE_8y = np.sqrt(MSE_8y)

    mape1 = 1 - np.abs((real_price[0] - predict_8years[0:1]) / real_price[0])
    mape2 = 1 - np.abs((real_price[1] - predict_8years[1:2]) / real_price[1])
    mape3 = 1 - np.abs((real_price[2] - predict_8years[2:3]) / real_price[2])
    mape4 = 1 - np.abs((real_price[3] - predict_8years[3:4]) / real_price[3])
    mape5 = 1 - np.abs((real_price[4] - predict_8years[4:5]) / real_price[4])
    mape6 = 1 - np.abs((real_price[5] - predict_8years[5:6]) / real_price[5])
    mape7 = 1 - np.abs((real_price[6] - predict_8years[6:7]) / real_price[6])
    mape8 = 1 - np.abs((real_price[7] - predict_8years[7:8]) / real_price[7])
    return real_price, input_data['UNIT_PREICE'][-8:], RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8


def LSTM_load(input_data, seq_len,batch,num_epochs,tree_name, size, verbose,model_name, save,save_path, model_path=None, type=None):
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM
    from tensorflow.keras import initializers
    from sklearn.metrics import mean_squared_error
    import tensorflow as tf
    from tensorflow.keras.callbacks import ModelCheckpoint
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    import datetime
    import time
    import os
    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    input_1 = input_data['UNIT_PREICE(COST)'].values
    input_2 = input_data['trend7'].values
    input_3 = input_data['seasonal7'].values
    input_4 = input_data['residual7'].values
    input_5 = input_data['sma2'].values
    input_6 = input_data['savgol'].values
    input_7 = input_data['seasonal14'].values
    input_8 = input_data['residual14'].values
    input_9 = input_data['trend14'].values
    input_10 = input_data['seasonal21'].values
    input_11 = input_data['residual21'].values
    input_12 = input_data['trend21'].values
    input_13 = input_data['seasonal28'].values
    input_14 = input_data['residual28'].values
    input_15 = input_data['trend28'].values
    # input_16 = input_data['seasonal35'].values
    # input_17 = input_data['residual35'].values
    # input_18 = input_data['trend35'].values

    output_feat = input_data['UNIT_PREICE(COST)'].values

    # Reshaping for converting the inputs/output to 2d shape
    input_1 = input_1.reshape((len(input_1), 1))
    input_2 = input_2.reshape((len(input_2), 1))
    input_3 = input_3.reshape((len(input_3), 1))
    input_4 = input_4.reshape((len(input_4), 1))
    input_5 = input_5.reshape((len(input_5), 1))
    input_6 = input_6.reshape((len(input_6), 1))
    input_7 = input_7.reshape((len(input_7), 1))
    input_8 = input_8.reshape((len(input_8), 1))
    input_9 = input_9.reshape((len(input_9), 1))
    input_10 = input_10.reshape((len(input_10), 1))
    input_11 = input_11.reshape((len(input_11), 1))
    input_12 = input_12.reshape((len(input_12), 1))
    input_13 = input_13.reshape((len(input_13), 1))
    input_14 = input_14.reshape((len(input_14), 1))
    input_15 = input_15.reshape((len(input_15), 1))
    # input_16 = input_16.reshape((len(input_16), 1))
    # input_17 = input_17.reshape((len(input_17), 1))
    # input_18 = input_18.reshape((len(input_18), 1))

    output_feat = output_feat.reshape((len(output_feat), 1))
    from numpy import hstack
    df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

    mean_df = df.reshape((-1, 1))

    pred_horizon = input_data.shape[0]//10 * 3

    X_train = df[:-pred_horizon] 
    Y_train = output_feat[:-pred_horizon]  

    X_test = df[-pred_horizon:]  
    Y_test = output_feat[-pred_horizon:] 

    real_price = output_feat[-8:]

    print(f' X_test.shape : {X_test.shape}, Y_test.shape : {Y_test.shape}')
    print(f' X_train.shape : {X_train.shape}, Y_train.shape : {Y_train.shape}')

    #from sklearn.preprocessing import RobustScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    x_train = scaler.fit_transform(X_train)
    x_test = scaler.transform(X_test)
    y_train = scaler.fit_transform(Y_train)
    y_test = scaler.transform(Y_test)

    
    ### nan value solution 
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)

    df_x_train = pd.DataFrame(x_train)
    delete_idx = df_x_train[df_x_train[1].isnull()].index.values
    x_train = np.delete(x_train,delete_idx,axis=0)
    y_train = np.delete(y_train,delete_idx,axis=0)

    # Creating the training sequences
    train_generator = TimeseriesGenerator(x_train,y_train,length=seq_len,batch_size=batch)
    test_generator = TimeseriesGenerator(x_test, y_test, length=seq_len, batch_size=batch)

    features_num = X_train.shape[1]  # 3
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout   
    from tensorflow.keras.callbacks import EarlyStopping  
    #initializer = tf.keras.initializers.he_uniform(seed=0)
    from tensorflow.keras.models import load_model

    model = tensorflow.keras.models.load_model('C:\\Users\\aiicon\\Desktop\\project_0831_server\\2_suppro\\Base_Model\\model.h5')
    # cb_early_stopping = EarlyStopping(monitor='loss', mode='min', patience=200)

    # history = model.fit_generator(train_generator, epochs=num_epochs, verbose=1,callbacks=[cb_early_stopping])

    # model.summary()

    prediction = model.predict_generator(test_generator)
    #be_rmse = np.sqrt(mean_squared_error(prediction,y_test[seq_len:]))
    # inverse scale
    predicted = scaler.inverse_transform(prediction)
    MSE = mean_squared_error(predicted, Y_test[seq_len:])
    RMSE = np.sqrt(MSE) 

    pred = model.predict(x_test[-seq_len:].reshape(1,seq_len,features_num))
    pred_value = scaler.inverse_transform(pred)
    pred_value = pd.DataFrame(pred_value,columns=['predict'])    


    # input_data = input_data[:-8]
    from datetime import timedelta
    for i in range(8):
        date = input_data['DATE']
        one_year = timedelta(days=365)
        next_year = date[-1:] + one_year
        next = pd.DataFrame()
        next['DATE'] = next_year.values
        date
        next
        
        date = pd.concat([date,next['DATE']])
        date = pd.DataFrame(date)
        date.reset_index(inplace=True, drop=True)
        date
        
        
        price = list(input_data['UNIT_PREICE(COST)'].values)
        price.append(pred_value['predict'][0])
        
        pred_price = pd.DataFrame()
        pred_price['UNIT_PREICE(COST)'] = price
        pred_price['DATE'] = date
        pred_price
        ma_n = 2
        # stl_d = stl_data(pred_price, 7)
        for i in range(0, 29, 7):
            if i != 0 :
                stl_d = stl_data(pred_price, i)
            else :
                pass
        stl_MA12_data = MA_data(stl_d,n=ma_n)
        
        stl_MA12_data.dropna(inplace=True)
        
        c_stl_MA12_data = stl_MA12_data.copy()
        data = sav_gol(c_stl_MA12_data)
        #data = smooth(data, 10)
        
        input_1 = input_data['UNIT_PREICE(COST)'].values
        input_2 = input_data['trend7'].values
        input_3 = input_data['seasonal7'].values
        input_4 = input_data['residual7'].values
        input_5 = input_data['sma2'].values
        input_6 = input_data['savgol'].values
        input_7 = input_data['seasonal14'].values
        input_8 = input_data['residual14'].values
        input_9 = input_data['trend14'].values
        input_10 = input_data['seasonal21'].values
        input_11 = input_data['residual21'].values
        input_12 = input_data['trend21'].values
        input_13 = input_data['seasonal28'].values
        input_14 = input_data['residual28'].values
        input_15 = input_data['trend28'].values
        # input_16 = input_data['seasonal35'].values
        # input_17 = input_data['residual35'].values
        # input_18 = input_data['trend35'].values


        # Reshaping for converting the inputs/output to 2d shape
        input_1 = input_1.reshape((len(input_1), 1))
        input_2 = input_2.reshape((len(input_2), 1))
        input_3 = input_3.reshape((len(input_3), 1))
        input_4 = input_4.reshape((len(input_4), 1))
        input_5 = input_5.reshape((len(input_5), 1))
        input_6 = input_6.reshape((len(input_6), 1))
        input_7 = input_7.reshape((len(input_7), 1))
        input_8 = input_8.reshape((len(input_8), 1))
        input_9 = input_9.reshape((len(input_9), 1))
        input_10 = input_10.reshape((len(input_10), 1))
        input_11 = input_11.reshape((len(input_11), 1))
        input_12 = input_12.reshape((len(input_12), 1))
        input_13 = input_13.reshape((len(input_13), 1))
        input_14 = input_14.reshape((len(input_14), 1))
        input_15 = input_15.reshape((len(input_15), 1))
        # input_16 = input_16.reshape((len(input_16), 1))
        # input_17 = input_17.reshape((len(input_17), 1))
        # input_18 = input_18.reshape((len(input_18), 1))

        from numpy import hstack
        df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

        from sklearn.preprocessing import MinMaxScaler
        scaler1 = MinMaxScaler()
        scaler2 = MinMaxScaler()
        
        df_scaler = scaler1.fit_transform(df)
        df_price = scaler2.fit_transform(input_1)

        pred = model.predict(df_scaler[-seq_len:].reshape(1,seq_len,features_num))
        
        predicted = scaler2.inverse_transform(pred)
        pred_value = pd.DataFrame(predicted,columns=['predict'])

        input_data = input_data.append(data[-1:])
        # input_data = data

        size = str(size)
        size = size.replace('*', 'X')
        # title = f"LSTM_({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_loss.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title, tree_name, option='loss',history=history,save=save)
    # print('========================= Training Complete====================')

    title = f"LSTM_W({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_result.jpg"    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title, tree_name, size, option='result',pred_horizon=pred_horizon,seq_len=seq_len,input_data=input_data,predicted=predicted,pred_value=pred_value,save=save)
    

    predict_8years = input_data['UNIT_PREICE(COST)'][-8:]

    MSE_1y = mean_squared_error(real_price[0], predict_8years[0:1])
    MSE_2y = mean_squared_error(real_price[1], predict_8years[1:2])
    MSE_3y = mean_squared_error(real_price[2], predict_8years[2:3])
    MSE_4y = mean_squared_error(real_price[3], predict_8years[3:4])
    MSE_5y = mean_squared_error(real_price[4], predict_8years[4:5])
    MSE_6y = mean_squared_error(real_price[5], predict_8years[5:6])
    MSE_7y = mean_squared_error(real_price[6], predict_8years[6:7])
    MSE_8y = mean_squared_error(real_price[7], predict_8years[7:8])
    
    RMSE_1y = np.sqrt(MSE_1y)
    RMSE_2y = np.sqrt(MSE_2y)
    RMSE_3y = np.sqrt(MSE_3y)
    RMSE_4y = np.sqrt(MSE_4y)
    RMSE_5y = np.sqrt(MSE_5y)
    RMSE_6y = np.sqrt(MSE_6y)
    RMSE_7y = np.sqrt(MSE_7y)
    RMSE_8y = np.sqrt(MSE_8y)

    mape1 = 1 - np.abs((real_price[0] - predict_8years[0:1]) / real_price[0])
    mape2 = 1 - np.abs((real_price[1] - predict_8years[1:2]) / real_price[1])
    mape3 = 1 - np.abs((real_price[2] - predict_8years[2:3]) / real_price[2])
    mape4 = 1 - np.abs((real_price[3] - predict_8years[3:4]) / real_price[3])
    mape5 = 1 - np.abs((real_price[4] - predict_8years[4:5]) / real_price[4])
    mape6 = 1 - np.abs((real_price[5] - predict_8years[5:6]) / real_price[5])
    mape7 = 1 - np.abs((real_price[6] - predict_8years[6:7]) / real_price[6])
    mape8 = 1 - np.abs((real_price[7] - predict_8years[7:8]) / real_price[7])
    return real_price, input_data['UNIT_PREICE(COST)'][-8:], RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8



def LSTM2(input_data, seq_len,batch,num_epochs,tree_name, size, verbose,model_name, save,save_path, model_path, type=None):
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM
    from tensorflow.keras import initializers
    from sklearn.metrics import mean_squared_error
    import tensorflow as tf
    from tensorflow.keras.callbacks import ModelCheckpoint
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    import datetime
    import time
    import os
    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    
    input_1 = input_data['UNIT_PREICE(COST)'].values
    input_2 = input_data['trend7'].values
    input_3 = input_data['seasonal7'].values
    input_4 = input_data['residual7'].values
    input_5 = input_data['sma2'].values
    input_6 = input_data['savgol'].values

    output_feat = input_data['UNIT_PREICE(COST)'].values

    # Reshaping for converting the inputs/output to 2d shape
    input_1 = input_1.reshape((len(input_1), 1))
    input_2 = input_2.reshape((len(input_2), 1))
    input_3 = input_3.reshape((len(input_3), 1))
    input_4 = input_4.reshape((len(input_4), 1))
    input_5 = input_5.reshape((len(input_5), 1))
    input_6 = input_6.reshape((len(input_6), 1))

    output_feat = output_feat.reshape((len(output_feat), 1))
    from numpy import hstack
    df = hstack((input_1, input_2, input_3, input_4, input_5, input_6))

    mean_df = df.reshape((-1, 1))

    pred_horizon = input_data.shape[0]//10 * 3

    X_train = df[:-pred_horizon]  # (827, 3) / (646, 10)
    X_train.shape
    Y_train = output_feat[:-pred_horizon]  # (827, 1)
    #Y_train.shape
    X_test = df[-pred_horizon:]  # (300, 3)
    Y_test = output_feat[-pred_horizon:]  # (300, 1)

    real_price = output_feat[-8:]

    print(f' X_test.shape : {X_test.shape}, Y_test.shape : {Y_test.shape}')
    print(f' X_train.shape : {X_train.shape}, Y_train.shape : {Y_train.shape}')

    #from sklearn.preprocessing import RobustScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    x_train = scaler.fit_transform(X_train)
    x_test = scaler.transform(X_test)
    y_train = scaler.fit_transform(Y_train)
    y_test = scaler.transform(Y_test)

    
    ### nan value solution 
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)

    df_x_train = pd.DataFrame(x_train)
    delete_idx = df_x_train[df_x_train[1].isnull()].index.values
    x_train = np.delete(x_train,delete_idx,axis=0)
    y_train = np.delete(y_train,delete_idx,axis=0)

    # Creating the training sequences
    train_generator = TimeseriesGenerator(x_train,y_train,length=seq_len,batch_size=batch)
    test_generator = TimeseriesGenerator(x_test, y_test, length=seq_len, batch_size=batch)

    features_num = X_train.shape[1]  # 3
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout   
    from tensorflow.keras.callbacks import EarlyStopping  
    #initializer = tf.keras.initializers.he_uniform(seed=0)
    
    model = Sequential()
    model.add(
        LSTM(200,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(
            100,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(60,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )   
    model.add(Dropout(0.5))
    model.add(
        LSTM(30,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        LSTM(10,
            activation='relu',
            input_shape=(seq_len, features_num),
            return_sequences=False)
    )
    model.add(Dense(1))
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss='mse')
    cb_early_stopping = EarlyStopping(monitor='loss', mode='min', patience=200)
    best_model = f'LSTMlen({seq_len})_epochs({num_epochs})_{model_name}.h5'

    start = time.time()

    history = model.fit_generator(train_generator, epochs=num_epochs, verbose=1,callbacks=[cb_early_stopping])

    title = f"LSTMlen({seq_len})_epochs({num_epochs})_{model_name}.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title,option='loss',history=history,save=save)
    # print('========================= Training Complete====================')
    model.summary()

    prediction = model.predict_generator(test_generator)

    end_time = time.time() - start
    end_time = time.strftime("%H:%M:%S", time.gmtime(end_time))


    learning_time = '{:0.3f}s'.format(time.time()-start)
    #be_rmse = np.sqrt(mean_squared_error(prediction,y_test[seq_len:]))
    # inverse scale
    predicted = scaler.inverse_transform(prediction)
    MSE = mean_squared_error(predicted, Y_test[seq_len:])
    RMSE = np.sqrt(MSE) 

    pred = model.predict(x_test[-seq_len:].reshape(1,seq_len,features_num))
    pred_value = scaler.inverse_transform(pred)
    pred_value = pd.DataFrame(pred_value,columns=['predict'])    

    # raw_input_data = input_data.copy()

    # input_data = raw_input_data.copy()
    
    # input_data = input_data[:-8]
    input_data_raw = input_data.copy()
    input_data = input_data_raw.copy()
    from datetime import timedelta
    for i in range(8):
        date = input_data['DATE']
        one_year = timedelta(days=365)
        next_year = date[-1:] + one_year
        next = pd.DataFrame()
        next['DATE'] = next_year.values
        
        date = pd.concat([date,next['DATE']])
        date = pd.DataFrame(date)
        date.reset_index(inplace=True, drop=True)
        
        price = list(input_data['UNIT_PREICE(COST)'].values)
        price.append(pred_value['predict'][0])
        
        pred_price = pd.DataFrame()
        pred_price['UNIT_PREICE(COST)'] = price
        pred_price['DATE'] = date

        ma_n = 2
        # stl_d = stl_data(pred_price, 7)
        for i in range(0, 29, 7):
            if i != 0 :
                stl_d = stl_data(pred_price, i)
            else :
                pass
        stl_MA12_data = MA_data(stl_d,n=ma_n)
        
        stl_MA12_data.dropna(inplace=True)
        
        c_stl_MA12_data = stl_MA12_data.copy()
        data = sav_gol(c_stl_MA12_data)
        #data = smooth(data, 10)
        
        input_1 = input_data['UNIT_PREICE(COST)'].values
        input_2 = input_data['trend7'].values
        input_3 = input_data['seasonal7'].values
        input_4 = input_data['residual7'].values
        input_5 = input_data['sma2'].values
        input_6 = input_data['savgol'].values

        # Reshaping for converting the inputs/output to 2d shape
        input_1 = input_1.reshape((len(input_1), 1))
        input_2 = input_2.reshape((len(input_2), 1))
        input_3 = input_3.reshape((len(input_3), 1))
        input_4 = input_4.reshape((len(input_4), 1))
        input_5 = input_5.reshape((len(input_5), 1))
        input_6 = input_6.reshape((len(input_6), 1))

        from numpy import hstack
        df = hstack((input_1, input_2, input_3, input_4, input_5, input_6))

        from sklearn.preprocessing import MinMaxScaler
        scaler1 = MinMaxScaler()
        scaler2 = MinMaxScaler()
        
        df_scaler = scaler1.fit_transform(df)
        df_price = scaler2.fit_transform(input_1)

        pred = model.predict(df_scaler[-seq_len:].reshape(1,seq_len,features_num))
        
        predicted = scaler2.inverse_transform(pred)
        pred_value = pd.DataFrame(predicted,columns=['predict'])
        
        # data[-1:]
        input_data = input_data.append(data[-1:])
        # input_data = data

        size = str(size)
        size = size.replace('*', 'X')

        title = f"LSTM_({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_loss.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title, tree_name, option='loss',history=history,save=save)
    # print('========================= Training Complete====================')


    title = f"LSTM_W({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_{size}_result.jpg"    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title, tree_name, size, option='result',pred_horizon=pred_horizon,seq_len=seq_len,input_data=input_data,predicted=predicted,pred_value=pred_value,save=save)
    

    predict_8years = input_data['UNIT_PREICE(COST)'][-8:]

    MSE_1y = mean_squared_error(real_price[0], predict_8years[0:1])
    MSE_2y = mean_squared_error(real_price[1], predict_8years[1:2])
    MSE_3y = mean_squared_error(real_price[2], predict_8years[2:3])
    MSE_4y = mean_squared_error(real_price[3], predict_8years[3:4])
    MSE_5y = mean_squared_error(real_price[4], predict_8years[4:5])
    MSE_6y = mean_squared_error(real_price[5], predict_8years[5:6])
    MSE_7y = mean_squared_error(real_price[6], predict_8years[6:7])
    MSE_8y = mean_squared_error(real_price[7], predict_8years[7:8])
    
    RMSE_1y = np.sqrt(MSE_1y)
    RMSE_2y = np.sqrt(MSE_2y)
    RMSE_3y = np.sqrt(MSE_3y)
    RMSE_4y = np.sqrt(MSE_4y)
    RMSE_5y = np.sqrt(MSE_5y)
    RMSE_6y = np.sqrt(MSE_6y)
    RMSE_7y = np.sqrt(MSE_7y)
    RMSE_8y = np.sqrt(MSE_8y)

    mape1 = 1 - np.abs((real_price[0] - predict_8years[0:1]) / real_price[0])
    mape2 = 1 - np.abs((real_price[1] - predict_8years[1:2]) / real_price[1])
    mape3 = 1 - np.abs((real_price[2] - predict_8years[2:3]) / real_price[2])
    mape4 = 1 - np.abs((real_price[3] - predict_8years[3:4]) / real_price[3])
    mape5 = 1 - np.abs((real_price[4] - predict_8years[4:5]) / real_price[4])
    mape6 = 1 - np.abs((real_price[5] - predict_8years[5:6]) / real_price[5])
    mape7 = 1 - np.abs((real_price[6] - predict_8years[6:7]) / real_price[6])
    mape8 = 1 - np.abs((real_price[7] - predict_8years[7:8]) / real_price[7])

    return real_price, input_data['UNIT_PREICE(COST)'][-8:], RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8

def RNN(input_data, seq_len,batch,num_epochs,tree_name,verbose,model_name, save,save_path, model_path, type=None):
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, SimpleRNN
    from tensorflow.keras import initializers
    from sklearn.metrics import mean_squared_error
    import tensorflow as tf
    from tensorflow.keras.callbacks import ModelCheckpoint
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    import datetime
    import time
    import os

    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    
    input_1 = input_data['UNIT_PREICE(COST)'].values
    input_2 = input_data['trend7'].values
    input_3 = input_data['seasonal7'].values
    input_4 = input_data['residual7'].values
    input_5 = input_data['sma2'].values
    input_6 = input_data['savgol'].values
    input_7 = input_data['seasonal14'].values
    input_8 = input_data['residual14'].values
    input_9 = input_data['trend14'].values
    input_10 = input_data['seasonal21'].values
    input_11 = input_data['residual21'].values
    input_12 = input_data['trend21'].values
    input_13 = input_data['seasonal28'].values
    input_14 = input_data['residual28'].values
    input_15 = input_data['trend28'].values
    # input_16 = input_data['seasonal35'].values
    # input_17 = input_data['residual35'].values
    # input_18 = input_data['trend35'].values

    output_feat = input_data['UNIT_PREICE(COST)'].values

    # Reshaping for converting the inputs/output to 2d shape
    input_1 = input_1.reshape((len(input_1), 1))
    input_2 = input_2.reshape((len(input_2), 1))
    input_3 = input_3.reshape((len(input_3), 1))
    input_4 = input_4.reshape((len(input_4), 1))
    input_5 = input_5.reshape((len(input_5), 1))
    input_6 = input_6.reshape((len(input_6), 1))
    input_7 = input_7.reshape((len(input_7), 1))
    input_8 = input_8.reshape((len(input_8), 1))
    input_9 = input_9.reshape((len(input_9), 1))
    input_10 = input_10.reshape((len(input_10), 1))
    input_11 = input_11.reshape((len(input_11), 1))
    input_12 = input_12.reshape((len(input_12), 1))
    input_13 = input_13.reshape((len(input_13), 1))
    input_14 = input_14.reshape((len(input_14), 1))
    input_15 = input_15.reshape((len(input_15), 1))
    # input_16 = input_16.reshape((len(input_16), 1))
    # input_17 = input_17.reshape((len(input_17), 1))
    # input_18 = input_18.reshape((len(input_18), 1))

    output_feat = output_feat.reshape((len(output_feat), 1))
    from numpy import hstack
    df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

    mean_df = df.reshape((-1, 1))

    pred_horizon = input_data.shape[0]//10 * 3

    X_train = df[:-pred_horizon]  # (827, 3) / (646, 10)
    X_train.shape
    Y_train = output_feat[:-pred_horizon]  # (827, 1)
    #Y_train.shape
    X_test = df[-pred_horizon:]  # (300, 3)
    Y_test = output_feat[-pred_horizon:]  # (300, 1)

    real_price = output_feat[-8:]

    print(f' X_test.shape : {X_test.shape}, Y_test.shape : {Y_test.shape}')
    print(f' X_train.shape : {X_train.shape}, Y_train.shape : {Y_train.shape}')

    #from sklearn.preprocessing import RobustScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    x_train = scaler.fit_transform(X_train)
    x_test = scaler.transform(X_test)
    y_train = scaler.fit_transform(Y_train)
    y_test = scaler.transform(Y_test)

    
    ### nan value solution 
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)

    df_x_train = pd.DataFrame(x_train)
    delete_idx = df_x_train[df_x_train[1].isnull()].index.values
    x_train = np.delete(x_train,delete_idx,axis=0)
    y_train = np.delete(y_train,delete_idx,axis=0)

    # Creating the training sequences
    train_generator = TimeseriesGenerator(x_train,y_train,length=seq_len,batch_size=batch)
    test_generator = TimeseriesGenerator(x_test, y_test, length=seq_len, batch_size=batch)

    features_num = X_train.shape[1]  # 3
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import SimpleRNN, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping  
    #initializer = tf.keras.initializers.he_uniform(seed=0)
    
    model = Sequential()
    model.add(
        SimpleRNN(200,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        SimpleRNN(
            150,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        SimpleRNN(
            100,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        SimpleRNN(60,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=True)
    )   
    model.add(Dropout(0.5))
    model.add(
        SimpleRNN(30,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        SimpleRNN(10,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=False)
    )
    model.add(Dense(1))
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss='mse')
    cb_early_stopping = EarlyStopping(monitor='loss', mode='min', patience=200)
    best_model = f'RNNlen({seq_len})_epochs({num_epochs})_{model_name}.h5'

    start = time.time()

    history = model.fit_generator(train_generator, epochs=num_epochs, verbose=1,callbacks=[cb_early_stopping])

    title = f"RNNlen({seq_len})_epochs({num_epochs})_{model_name}.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title,option='loss',history=history,save=save)
    # print('========================= Training Complete====================')
    model.summary()

    prediction = model.predict_generator(test_generator)

    end_time = time.time() - start
    end_time = time.strftime("%H:%M:%S", time.gmtime(end_time))


    learning_time = '{:0.3f}s'.format(time.time()-start)
    #be_rmse = np.sqrt(mean_squared_error(prediction,y_test[seq_len:]))
    # inverse scale
    predicted = scaler.inverse_transform(prediction)
    MSE = mean_squared_error(predicted, Y_test[seq_len:])
    RMSE = np.sqrt(MSE) 

    pred = model.predict(x_test[-seq_len:].reshape(1,seq_len,features_num))
    pred_value = scaler.inverse_transform(pred)
    pred_value = pd.DataFrame(pred_value,columns=['predict'])    

    input_data = input_data[:-8]
    from datetime import timedelta
    for i in range(16):
        date = input_data['DATE']
        one_year = timedelta(days=365)
        next_year = date[-1:] + one_year
        next = pd.DataFrame()
        next['DATE'] = next_year.values
        date
        next
        
        date = pd.concat([date,next['DATE']])
        date = pd.DataFrame(date)
        date.reset_index(inplace=True, drop=True)
        date
        
        
        price = list(input_data['UNIT_PREICE(COST)'].values)
        price.append(pred_value['predict'][0])
        
        pred_price = pd.DataFrame()
        pred_price['UNIT_PREICE(COST)'] = price
        pred_price['DATE'] = date
        pred_price
        ma_n = 2
        # stl_d = stl_data(pred_price, 7)
        for i in range(0, 29, 7):
            if i != 0 :
                stl_d = stl_data(pred_price, i)
            else :
                pass
        stl_MA12_data = MA_data(stl_d,n=ma_n)
        
        stl_MA12_data.dropna(inplace=True)
        
        c_stl_MA12_data = stl_MA12_data.copy()
        data = sav_gol(c_stl_MA12_data)
        #data = smooth(data, 10)
        
        input_1 = input_data['UNIT_PREICE(COST)'].values
        input_2 = input_data['trend7'].values
        input_3 = input_data['seasonal7'].values
        input_4 = input_data['residual7'].values
        input_5 = input_data['sma2'].values
        input_6 = input_data['savgol'].values
        input_7 = input_data['seasonal14'].values
        input_8 = input_data['residual14'].values
        input_9 = input_data['trend14'].values
        input_10 = input_data['seasonal21'].values
        input_11 = input_data['residual21'].values
        input_12 = input_data['trend21'].values
        input_13 = input_data['seasonal28'].values
        input_14 = input_data['residual28'].values
        input_15 = input_data['trend28'].values
        # input_16 = input_data['seasonal35'].values
        # input_17 = input_data['residual35'].values
        # input_18 = input_data['trend35'].values


        # Reshaping for converting the inputs/output to 2d shape
        input_1 = input_1.reshape((len(input_1), 1))
        input_2 = input_2.reshape((len(input_2), 1))
        input_3 = input_3.reshape((len(input_3), 1))
        input_4 = input_4.reshape((len(input_4), 1))
        input_5 = input_5.reshape((len(input_5), 1))
        input_6 = input_6.reshape((len(input_6), 1))
        input_7 = input_7.reshape((len(input_7), 1))
        input_8 = input_8.reshape((len(input_8), 1))
        input_9 = input_9.reshape((len(input_9), 1))
        input_10 = input_10.reshape((len(input_10), 1))
        input_11 = input_11.reshape((len(input_11), 1))
        input_12 = input_12.reshape((len(input_12), 1))
        input_13 = input_13.reshape((len(input_13), 1))
        input_14 = input_14.reshape((len(input_14), 1))
        input_15 = input_15.reshape((len(input_15), 1))
        # input_16 = input_16.reshape((len(input_16), 1))
        # input_17 = input_17.reshape((len(input_17), 1))
        # input_18 = input_18.reshape((len(input_18), 1))

        from numpy import hstack
        df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

        from sklearn.preprocessing import MinMaxScaler
        scaler1 = MinMaxScaler()
        scaler2 = MinMaxScaler()
        
        df_scaler = scaler1.fit_transform(df)
        df_price = scaler2.fit_transform(input_1)

        pred = model.predict(df_scaler[-seq_len:].reshape(1,seq_len,features_num))
        
        predicted = scaler2.inverse_transform(pred)
        pred_value = pd.DataFrame(predicted,columns=['predict'])
        pred_value

        input_data = input_data.append(data[-1:])

        # input_data = data

        title = f"RNN_({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_loss.jpg"
    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title,option='loss',history=history,save=save)
    print('========================= Training Complete====================')


    title = f"RNN_W({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_result.jpg"    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title,option='result',pred_horizon=pred_horizon,seq_len=seq_len,input_data=input_data,predicted=predicted,pred_value=pred_value,save=save)
    

    predict_8years = input_data['UNIT_PREICE(COST)'][-8:]

    MSE_1y = mean_squared_error(real_price[0], predict_8years[0:1])
    MSE_2y = mean_squared_error(real_price[1], predict_8years[1:2])
    MSE_3y = mean_squared_error(real_price[2], predict_8years[2:3])
    MSE_4y = mean_squared_error(real_price[3], predict_8years[3:4])
    MSE_5y = mean_squared_error(real_price[4], predict_8years[4:5])
    MSE_6y = mean_squared_error(real_price[5], predict_8years[5:6])
    MSE_7y = mean_squared_error(real_price[6], predict_8years[6:7])
    MSE_8y = mean_squared_error(real_price[7], predict_8years[7:8])
    
    
    RMSE_1y = np.sqrt(MSE_1y)
    RMSE_2y = np.sqrt(MSE_2y)
    RMSE_3y = np.sqrt(MSE_3y)
    RMSE_4y = np.sqrt(MSE_4y)
    RMSE_5y = np.sqrt(MSE_5y)
    RMSE_6y = np.sqrt(MSE_6y)
    RMSE_7y = np.sqrt(MSE_7y)
    RMSE_8y = np.sqrt(MSE_8y)

    mape1 = 1 - np.abs((real_price[0] - predict_8years[0:1]) / real_price[0])
    mape2 = 1 - np.abs((real_price[1] - predict_8years[1:2]) / real_price[1])
    mape3 = 1 - np.abs((real_price[2] - predict_8years[2:3]) / real_price[2])
    mape4 = 1 - np.abs((real_price[3] - predict_8years[3:4]) / real_price[3])
    mape5 = 1 - np.abs((real_price[4] - predict_8years[4:5]) / real_price[4])
    mape6 = 1 - np.abs((real_price[5] - predict_8years[5:6]) / real_price[5])
    mape7 = 1 - np.abs((real_price[6] - predict_8years[6:7]) / real_price[6])
    mape8 = 1 - np.abs((real_price[7] - predict_8years[7:8]) / real_price[7])
    
    return real_price, input_data['UNIT_PREICE(COST)'][-8:], RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8

def GRU(input_data, seq_len,batch,num_epochs,tree_name,verbose,model_name, save,save_path, model_path, type=None):
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, GRU
    from tensorflow.keras import initializers
    from sklearn.metrics import mean_squared_error
    import tensorflow as tf
    from tensorflow.keras.callbacks import ModelCheckpoint
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    import datetime
    import time
    import os

    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    
    Date = pd.to_datetime(input_data['DATE'])

    input_data = input_data.resample('y').mean().interpolate()
    input_data = input_data.reset_index()
    
    input_1 = input_data['UNIT_PREICE(COST)'].values
    input_2 = input_data['trend7'].values
    input_3 = input_data['seasonal7'].values
    input_4 = input_data['residual7'].values
    input_5 = input_data['sma2'].values
    input_6 = input_data['savgol'].values
    input_7 = input_data['seasonal14'].values
    input_8 = input_data['residual14'].values
    input_9 = input_data['trend14'].values
    input_10 = input_data['seasonal21'].values
    input_11 = input_data['residual21'].values
    input_12 = input_data['trend21'].values
    input_13 = input_data['seasonal28'].values
    input_14 = input_data['residual28'].values
    input_15 = input_data['trend28'].values
    # input_16 = input_data['seasonal35'].values
    # input_17 = input_data['residual35'].values
    # input_18 = input_data['trend35'].values

    output_feat = input_data['UNIT_PREICE(COST)'].values

    # Reshaping for converting the inputs/output to 2d shape
    input_1 = input_1.reshape((len(input_1), 1))
    input_2 = input_2.reshape((len(input_2), 1))
    input_3 = input_3.reshape((len(input_3), 1))
    input_4 = input_4.reshape((len(input_4), 1))
    input_5 = input_5.reshape((len(input_5), 1))
    input_6 = input_6.reshape((len(input_6), 1))
    input_7 = input_7.reshape((len(input_7), 1))
    input_8 = input_8.reshape((len(input_8), 1))
    input_9 = input_9.reshape((len(input_9), 1))
    input_10 = input_10.reshape((len(input_10), 1))
    input_11 = input_11.reshape((len(input_11), 1))
    input_12 = input_12.reshape((len(input_12), 1))
    input_13 = input_13.reshape((len(input_13), 1))
    input_14 = input_14.reshape((len(input_14), 1))
    input_15 = input_15.reshape((len(input_15), 1))
    # input_16 = input_16.reshape((len(input_16), 1))
    # input_17 = input_17.reshape((len(input_17), 1))
    # input_18 = input_18.reshape((len(input_18), 1))

    output_feat = output_feat.reshape((len(output_feat), 1))
    from numpy import hstack
    df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

    mean_df = df.reshape((-1, 1))

    pred_horizon = input_data.shape[0]//10 * 3

    X_train = df[:-pred_horizon]  # (827, 3) / (646, 10)
    X_train.shape
    Y_train = output_feat[:-pred_horizon]  # (827, 1)
    #Y_train.shape
    X_test = df[-pred_horizon:]  # (300, 3)
    Y_test = output_feat[-pred_horizon:]  # (300, 1)

    real_price = output_feat[-8:]

    print(f' X_test.shape : {X_test.shape}, Y_test.shape : {Y_test.shape}')
    print(f' X_train.shape : {X_train.shape}, Y_train.shape : {Y_train.shape}')

    #from sklearn.preprocessing import RobustScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    x_train = scaler.fit_transform(X_train)
    x_test = scaler.transform(X_test)
    y_train = scaler.fit_transform(Y_train)
    y_test = scaler.transform(Y_test)

    
    ### nan value solution 
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)

    df_x_train = pd.DataFrame(x_train)
    delete_idx = df_x_train[df_x_train[1].isnull()].index.values
    x_train = np.delete(x_train,delete_idx,axis=0)
    y_train = np.delete(y_train,delete_idx,axis=0)

    # Creating the training sequences
    train_generator = TimeseriesGenerator(x_train,y_train,length=seq_len,batch_size=batch)
    test_generator = TimeseriesGenerator(x_test, y_test, length=seq_len, batch_size=batch)

    features_num = X_train.shape[1]  # 3
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, GRU, Dropout
    from tensorflow.keras.callbacks import EarlyStopping  
    #initializer = tf.keras.initializers.he_uniform(seed=0)
    
    model = Sequential()
    model.add(
        GRU(200,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        GRU(
            150,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        GRU(
            100,
            activation='relu',
            input_shape=(seq_len,features_num),
            return_sequences=True
        )
    )
    model.add(Dropout(0.5))
    model.add(
        GRU(60,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=True)
    )   
    model.add(Dropout(0.5))
    model.add(
        GRU(30,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=True)
    )
    model.add(Dropout(0.5))
    model.add(
        GRU(10,
             activation='relu',
             input_shape=(seq_len, features_num),
             return_sequences=False)
    )
    model.add(Dense(1))
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss='mse')
    cb_early_stopping = EarlyStopping(monitor='loss', mode='min', patience=200)
    best_model = f'GRUlen({seq_len})_epochs({num_epochs})_{model_name}.h5'

    start = time.time()

    history = model.fit_generator(train_generator, epochs=num_epochs, verbose=1,callbacks=[cb_early_stopping])

    title = f"GRUlen({seq_len})_epochs({num_epochs})_{model_name}.jpg"
    
    # if save_path!=None:
    #     title=os.path.join(save_path,title)
    # if verbose==1:
    #     plot_graph_model_loss(title,option='loss',history=history,save=save)
    # print('========================= Training Complete====================')
    model.summary()

    prediction = model.predict_generator(test_generator)

    end_time = time.time() - start
    end_time = time.strftime("%H:%M:%S", time.gmtime(end_time))


    learning_time = '{:0.3f}s'.format(time.time()-start)
    #be_rmse = np.sqrt(mean_squared_error(prediction,y_test[seq_len:]))
    # inverse scale
    predicted = scaler.inverse_transform(prediction)
    MSE = mean_squared_error(predicted, Y_test[seq_len:])
    RMSE = np.sqrt(MSE) 

    pred = model.predict(x_test[-seq_len:].reshape(1,seq_len,features_num))
    pred_value = scaler.inverse_transform(pred)
    pred_value = pd.DataFrame(pred_value,columns=['predict'])    

    input_data = input_data[:-8]
    from datetime import timedelta
    for i in range(16):
        date = input_data['DATE']
        one_year = timedelta(days=365)
        next_year = date[-1:] + one_year
        next = pd.DataFrame()
        next['DATE'] = next_year.values
        date
        next
        
        date = pd.concat([date,next['DATE']])
        date = pd.DataFrame(date)
        date.reset_index(inplace=True, drop=True)
        date
        
        
        price = list(input_data['UNIT_PREICE(COST)'].values)
        price.append(pred_value['predict'][0])
        
        pred_price = pd.DataFrame()
        pred_price['UNIT_PREICE(COST)'] = price
        pred_price['DATE'] = date
        pred_price
        ma_n = 2
        # stl_d = stl_data(pred_price, 7)
        for i in range(0, 29, 7):
            if i != 0 :
                stl_d = stl_data(pred_price, i)
            else :
                pass
        stl_MA12_data = MA_data(stl_d,n=ma_n)
        
        stl_MA12_data.dropna(inplace=True)
        
        c_stl_MA12_data = stl_MA12_data.copy()
        data = sav_gol(c_stl_MA12_data)
        #data = smooth(data, 10)
        
        input_1 = input_data['UNIT_PREICE(COST)'].values
        input_2 = input_data['trend7'].values
        input_3 = input_data['seasonal7'].values
        input_4 = input_data['residual7'].values
        input_5 = input_data['sma2'].values
        input_6 = input_data['savgol'].values
        input_7 = input_data['seasonal14'].values
        input_8 = input_data['residual14'].values
        input_9 = input_data['trend14'].values
        input_10 = input_data['seasonal21'].values
        input_11 = input_data['residual21'].values
        input_12 = input_data['trend21'].values
        input_13 = input_data['seasonal28'].values
        input_14 = input_data['residual28'].values
        input_15 = input_data['trend28'].values
        # input_16 = input_data['seasonal35'].values
        # input_17 = input_data['residual35'].values
        # input_18 = input_data['trend35'].values


        # Reshaping for converting the inputs/output to 2d shape
        input_1 = input_1.reshape((len(input_1), 1))
        input_2 = input_2.reshape((len(input_2), 1))
        input_3 = input_3.reshape((len(input_3), 1))
        input_4 = input_4.reshape((len(input_4), 1))
        input_5 = input_5.reshape((len(input_5), 1))
        input_6 = input_6.reshape((len(input_6), 1))
        input_7 = input_7.reshape((len(input_7), 1))
        input_8 = input_8.reshape((len(input_8), 1))
        input_9 = input_9.reshape((len(input_9), 1))
        input_10 = input_10.reshape((len(input_10), 1))
        input_11 = input_11.reshape((len(input_11), 1))
        input_12 = input_12.reshape((len(input_12), 1))
        input_13 = input_13.reshape((len(input_13), 1))
        input_14 = input_14.reshape((len(input_14), 1))
        input_15 = input_15.reshape((len(input_15), 1))
        # input_16 = input_16.reshape((len(input_16), 1))
        # input_17 = input_17.reshape((len(input_17), 1))
        # input_18 = input_18.reshape((len(input_18), 1))

        from numpy import hstack
        df = hstack((input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15))#, input_16, input_17, input_18))

        from sklearn.preprocessing import MinMaxScaler
        scaler1 = MinMaxScaler()
        scaler2 = MinMaxScaler()
        
        df_scaler = scaler1.fit_transform(df)
        df_price = scaler2.fit_transform(input_1)

        pred = model.predict(df_scaler[-seq_len:].reshape(1,seq_len,features_num))
        
        predicted = scaler2.inverse_transform(pred)
        pred_value = pd.DataFrame(predicted,columns=['predict'])
        pred_value

        input_data = input_data.append(data[-1:])

        # input_data = data

        title = f"GRU_({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_loss.jpg"
    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title,option='loss',history=history,save=save)
    print('========================= Training Complete====================')


    title = f"GRU_W({seq_len})_epochs({num_epochs})_{model_name}_{tree_name}_result.jpg"    
    if save_path!=None:
        title=os.path.join(save_path,title)
    if verbose==1:
        plot_graph_model_loss(title,option='result',pred_horizon=pred_horizon,seq_len=seq_len,input_data=input_data,predicted=predicted,pred_value=pred_value,save=save)
    

    predict_8years = input_data['UNIT_PREICE(COST)'][-8:]

    MSE_1y = mean_squared_error(real_price[0], predict_8years[0:1])
    MSE_2y = mean_squared_error(real_price[1], predict_8years[1:2])
    MSE_3y = mean_squared_error(real_price[2], predict_8years[2:3])
    MSE_4y = mean_squared_error(real_price[3], predict_8years[3:4])
    MSE_5y = mean_squared_error(real_price[4], predict_8years[4:5])
    MSE_6y = mean_squared_error(real_price[5], predict_8years[5:6])
    MSE_7y = mean_squared_error(real_price[6], predict_8years[6:7])
    MSE_8y = mean_squared_error(real_price[7], predict_8years[7:8])
    
    
    RMSE_1y = np.sqrt(MSE_1y)
    RMSE_2y = np.sqrt(MSE_2y)
    RMSE_3y = np.sqrt(MSE_3y)
    RMSE_4y = np.sqrt(MSE_4y)
    RMSE_5y = np.sqrt(MSE_5y)
    RMSE_6y = np.sqrt(MSE_6y)
    RMSE_7y = np.sqrt(MSE_7y)
    RMSE_8y = np.sqrt(MSE_8y)

    mape1 = 1 - np.abs((real_price[0] - predict_8years[0:1]) / real_price[0])
    mape2 = 1 - np.abs((real_price[1] - predict_8years[1:2]) / real_price[1])
    mape3 = 1 - np.abs((real_price[2] - predict_8years[2:3]) / real_price[2])
    mape4 = 1 - np.abs((real_price[3] - predict_8years[3:4]) / real_price[3])
    mape5 = 1 - np.abs((real_price[4] - predict_8years[4:5]) / real_price[4])
    mape6 = 1 - np.abs((real_price[5] - predict_8years[5:6]) / real_price[5])
    mape7 = 1 - np.abs((real_price[6] - predict_8years[6:7]) / real_price[6])
    mape8 = 1 - np.abs((real_price[7] - predict_8years[7:8]) / real_price[7])
    
    return real_price, input_data['UNIT_PREICE(COST)'][-8:], RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8


def model_select(model_name, input_data, seq_len,batch,num_epochs, verbose, save, save_path, model_path, tree_name, size):
    result = []
    if model_name == 'LSTM':
        real_price, pred_value, RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8 = LSTM(input_data, seq_len, batch, num_epochs, tree_name, size, verbose, model_name, save, save_path, model_path)
    elif model_name == 'GRU':
        real_price, pred_value, RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8 = GRU(input_data, seq_len, batch, num_epochs, tree_name, verbose, model_name, save, save_path, model_path)
    elif model_name == 'RNN':
        real_price, pred_value, RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8 = RNN(input_data, seq_len, batch, num_epochs, tree_name, verbose, model_name, save, save_path, model_path)
    temp = {
        'tree':tree_name,
        'batch':batch,
        'num_epochs':num_epochs,
        'lstm_seq_len':seq_len,
        'real_price1' : int(real_price[0].item()),
        'real_price2' : int(real_price[1].item()),
        'real_price3' : int(real_price[2].item()),
        'real_price4' : int(real_price[3].item()),
        'real_price5' : int(real_price[4].item()),
        'real_price6' : int(real_price[5].item()),
        'real_price7' : int(real_price[6].item()),
        'real_price8' : int(real_price[7].item()),
        'y1':int(pred_value[0:1]),
        'y2':int(pred_value[1:2]),
        'y3':int(pred_value[2:3]),
        'y4':int(pred_value[3:4]),
        'y5':int(pred_value[4:5]),
        'y6':int(pred_value[5:6]),
        'y7':int(pred_value[6:7]),
        'y8':int(pred_value[7:8]),
        'RMSE':RMSE, 
        'RMSE1':RMSE_1y,
        'RMSE2':RMSE_2y,
        'RMSE3':RMSE_3y,
        'RMSE4':RMSE_4y,
        'RMSE5':RMSE_5y,
        'RMSE6':RMSE_6y,
        'RMSE7':RMSE_7y,
        'RMSE8':RMSE_8y,
        'MAPE1':float(mape1),
        'MAPE2':float(mape2),
        'MAPE3':float(mape3),
        'MAPE4':float(mape4),
        'MAPE5':float(mape5),
        'MAPE6':float(mape6),
        'MAPE7':float(mape7),
        'MAPE8':float(mape8),
        'model_name':model_name}

    result.append(temp)
    result = pd.DataFrame(result)
    return result

def s_lstm(input_data, lstm_seq_len, lstm_pred_horizon, tree, predict_len,D_t):
    # Defining the inputs and output of the LSTM model so as to create the sequences

    if D_t=='W':
        d_range='주별'
        t_range='Week'

    if D_t=='D':
        d_range='일별'
        t_range='Day'

    if D_t == 'M':
        d_range = '월별'
        t_range = 'Month'

    if D_t=='Y':
        d_range= '년도별'
        t_range='Year'


    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM

    input = input_data['savgol_mean'].values
    input = input.reshape((len(input), 1))

    # Scale the data
    from sklearn.preprocessing import MinMaxScaler

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(np.array(input_data).reshape(-1,1))

    train_data = scaled_data[0:-predict_len]
    x_train = []
    y_train = []

    for i in range(60, len(train_data)):
        x_train.append(train_data[i - 60:i])
        y_train.append(train_data[i])

    x_train, y_train = np.array(x_train), np.array(y_train)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    model = Sequential()
    model.add(LSTM(128, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))

    # Compile the model
    model.compile(optimizer='adam', loss='mean_squared_error')

    model.fit(x_train, y_train, batch_size=60, epochs=60)

    # Create the testing data set
    # Create a new array containing scaled values from index 1543 to 2002
    test_data = scaled_data[-predict_len:]
    # Create the data sets x_test and y_test
    x_test = []
    y_test = input_data[-predict_len:]
    for i in range(0, len(test_data)):
        x_test.append(scaled_data[-predict_len+i-60-1:-predict_len+i-1])

    # Convert the data to a numpy array
    x_test = np.array(x_test)

    # Reshape the data
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    predictions = model.predict(x_test)
    predictions = scaler.inverse_transform(predictions)


    rmse = np.sqrt(np.mean(((predictions[:,0] - y_test) ** 2)))

    batch_first = scaled_data[-60:]
    batch_first = np.reshape(batch_first, (1, 60, 1))

    lstm_pred_out = model.predict(batch_first)

    lstm_output = []
    for i in range(predict_len):

        output = model.predict(batch_first)
        batch_first[:,0:59,:] = batch_first[:,1:,:]
        batch_first[:,59, :] = output[0]
        lstm_output.append(output[0][0])

    lstm_predictions = scaler.inverse_transform(np.array(lstm_output).reshape(-1,1))
    train = pd.DataFrame()
    valid = pd.DataFrame()


    train['Mean'] = input_data[:-predict_len]
    valid['Mean'] = input_data[-predict_len:]
    valid['Predictions'] = predictions

    # Visualize the data
    plt.figure(figsize=(16, 6))

    plt.title(f'[{tree}] {d_range} 가격 LSTM 적용 예측 결과{rmse}',fontsize=15)
    plt.xlabel('Date', fontsize=13)
    plt.ylabel('Mean Price', fontsize=13)
    plt.plot(train['Mean'],label='Train')
    plt.plot(range(len(train_data),len(train_data)+len(valid)),valid['Mean'],label='Validation')
    plt.plot(range(len(train_data),len(train_data)+len(valid)),valid['Predictions'], label='Predictions')
    #plt.plot(range(len(train_data)+predict_len,len(train_data)+2*predict_len),lstm_predictions,label='Forecast')
    plt.xlabel('After Preprocessing Data Index')
    plt.ylim(0,4*max(train['Mean']))
    plt.legend(loc='lower right')
    plt.ylabel(f'Average Price / {t_range}')
    plt.savefig(f'[{tree}] {d_range} 가격 LSTM 적용 예측 결과.jpg', dpi=300)
    plt.show()

    print(f'RMSE : {rmse}')


def learning_data(input_data, lstm_seq_len, lstm_pred_horizon, tree, predict_len,D_t):
    # Defining the inputs and output of the LSTM model so as to create the sequences

    if D_t=='W':
        d_range='주별'
        t_range='Week'

    if D_t=='D':
        d_range='일별'
        t_range='Day'

    if D_t == 'M':
        d_range = '월별'
        t_range = 'Month'

    if D_t=='Y':
        d_range= '년도별'
        t_range='Year'


    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, GRU

    input = input_data['savgol_mean'].values
    input = input.reshape((len(input), 1))

    # Scale the data
    from sklearn.preprocessing import MinMaxScaler

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(np.array(input).reshape(-1,1))

    train_data = scaled_data[0:-predict_len]
    x_train = []
    y_train = []
    #for i in range(60, len(train_data)):
    #   x_train.append(train_data[i - 60:i])
    #   y_train.append(train_data[i])

    #x_train, y_train = np.array(x_train), np.array(y_train)
    x_train, y_train = lstm_set_sequence(train_data, lstm_seq_len)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    test_data = scaled_data[-lstm_pred_horizon:]
    # Create the data sets x_test and y_test
    x_test = []

    for i in range(0, len(test_data)):
        x_test.append(scaled_data[-lstm_seq_len-lstm_pred_horizon+i:-lstm_pred_horizon+i])
    # Convert the data to a numpy array
    x_test = np.array(x_test)

    y_test = input[-lstm_pred_horizon:]
    # Reshape the data
    x_test = np.reshape(x_test[:], (lstm_pred_horizon, x_test[0].shape[0], 1))
    return x_train, y_train, x_test, x_test, scaler, scaled_data

def gen_totalDay(first, last):
    import datetime
    from datetimerange import DateTimeRange
    time_range = DateTimeRange(first,last)
    total_day = []
    for value in time_range.range(datetime.timedelta(days=1)):
        total_day.append(value)
    return total_day

def model_predict(num_prediction,look_back, mean_data, model):
    prediction_list = mean_data[-look_back:]
    sc = MinMaxScaler(feature_range=(0, 1))
    pred_set_scaled = sc.fit_transform(prediction_list.reshape(-1, 1))
    for _ in range(num_prediction):
        x = pred_set_scaled[-look_back:]
        x = x.reshape((1, look_back, 1))
        out = model.predict(x)[0][0]
        pred_set_scaled = np.append(pred_set_scaled, out)
    pred_set_scaled = pred_set_scaled[look_back-1:]

    # inverse scale
    predicted = sc.inverse_transform(pred_set_scaled.reshape(-1, 1))

    return predicted[1:].reshape(-1)

def predict_dates(totalDay, num_prediction=5):
    last_date = totalDay[-1]
    prediction_dates = pd.date_range(pd.to_datetime(last_date), periods=num_prediction).tolist()
    return prediction_dates

def predict_month_dates(totalDay, num_prediction=1):
    last_date = totalDay[-1]
    prediction_dates = pd.date_range(pd.to_datetime(last_date), periods=num_prediction+1, freq='M').tolist()
    return prediction_dates[-1]

def predict_week_dates(totalDay, num_prediction=3):
    last_date = totalDay[-1]
    prediction_dates = pd.date_range(pd.to_datetime(last_date), periods=num_prediction, freq='W').tolist()
    return prediction_dates


def month_plot(input_data, name, size):
    import plotly.express as px
    import plotly.graph_objects as go  
    import matplotlib.ticker as mticker
    from datetime import datetime

    # Date = pd.to_datetime(input_data['DATE'])
    # input_data = pd.DataFrame(input_data)
    # input_data.index = Date
    # # input_data = input_data.resample('m').mean().interpolate()
    # # input_data = input_data.reset_index()
    # # input_data = input_data[-36:]    
    # monthly_mean = input_data['UNIT_PREICE(COST)'].resample('M').mean()
    # monthly_mean = monthly_mean.reset_index()

    # monthly_mean['DATE'] = monthly_mean['DATE'].astype(str)

    # split = monthly_mean['DATE'].str.split('-')
    # monthly_mean['year'] = split.str.get(0)
    # monthly_mean['year'] = monthly_mean['year'].astype(int)

    # today = datetime.today().year
    # today = today - 3

    # monthly_mean = monthly_mean[monthly_mean['year'] >= today]

    x = input_data['DATE']
    y = input_data['UNIT_PREICE(COST)']

    size = str(size)
    size = size.replace('*', 'X')

    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=x,
            y=y, mode='lines+markers'))
    fig1.update_layout(
        autosize=False,width=1300,
        height=600,
        yaxis = dict(tickformat =":04,2f"),
        scene_xaxis = dict(exponentformat= "none",separatethousands= True,tickprefix='$'),
        title={
            'text': f"매입가 기준 {name} {size} 가격 추이(원).jpg" ,
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
            font=dict(size=18))
    # fig1.update_yaxes(exponentformat='none')
    fig1.update_yaxes(tickformat=',')

    title = f'매입가_{name}_{size}_가격추이(원).jpg'
    fig1.write_image(f'{title}')
    fig1.write_html(f'{title[:-3]}html')

def month_plot2(input_data, name, size):
    import plotly.express as px
    import plotly.graph_objects as go  
    import matplotlib.ticker as mticker
    # Date = pd.to_datetime(input_data['DATE'])
    # input_data = pd.DataFrame(input_data)
    # input_data.index = Date
    # # input_data = input_data.resample('m').mean().interpolate()
    # # input_data = input_data.reset_index()
    # # input_data = input_data[-36:]    

    # monthly_mean = input_data['UNIT_PREICE(COST)'].resample('M').mean()
    # monthly_mean = monthly_mean.reset_index()

    # x = monthly_mean['DATE']

    x = input_data['DATE']
    y = input_data['UNIT_PREICE']

    size = str(size)
    size = size.replace('*', 'X')

    input_data.dtypes
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=x,
            y=y, mode='lines+markers'))
    fig1.update_layout(
        autosize=False,width=1300,
        height=600,
        yaxis = dict(tickformat =":04,2f"),
        scene_xaxis = dict(exponentformat= "none",separatethousands= True,tickprefix='$'),
        title={
            'text': f"매출가 기준 {name} {size} 가격 추이(원).jpg" ,
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
            font=dict(size=18))        
    # fig1.update_yaxes(exponentformat='none')
    fig1.update_yaxes(tickformat=',')
    title = f'매출가_{name}_{size}_가격추이(원).jpg'
    fig1.write_image(f'{title}')
    fig1.write_html(f'{title[:-3]}html')



def month_plot_before(input_data, name, size):
    import matplotlib.ticker as mticker
    Date = pd.to_datetime(input_data['DATE'])
    input_data = pd.DataFrame(input_data)
    input_data.index = Date
    input_data = input_data.resample('m').mean().interpolate()
    input_data = input_data.reset_index()
    input_data = input_data[-36:]    

    fig, ax = plt.subplots(figsize=(10,6))
    ax.ticklabel_format(style='plain')
    ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.title(f'3년간 {name}_{size} 거래 가격 추이(원)')
    ax.plot(input_data['DATE'],input_data['UNIT_PREICE(COST)'], linestyle='solid',label='Test', color = 'green')

    # plt.figure(figsize=(10,6))
    # plt.title(f'3년간 {name}_{size} 거래 가격 추이')
    # plt.plot(input_data['DATE'],input_data['UNIT_PREICE(COST)'], linestyle='solid',label='Test', color = 'green')
    input_data['DATE'] = input_data['DATE'].astype(str)
    input_data['DATE2'] = input_data['DATE'].str[:7]
    ticklabel=input_data['DATE2']
    plt.xticks(input_data['DATE2'], ticklabel, rotation=90, fontsize=8)
    # plt.xticks(rotation = 45, fontsize = 8)
    # plt.show()
    plt.savefig(f'3년간 [{name}] 거래 가격 추이.jpg', dpi=300)

def plot_graph_model_loss(title, tree_name, size, option,history=None,pred_horizon=None,seq_len=None,input_data=None,predicted=None,pred_value=None,save=None):
    '''
    save 1 show and save  
    save 2 non-show and save
    save 3 show and non-save
    '''
    import plotly.express as px
    import plotly.graph_objects as go    
    
    if option=='loss':
        history = history.history
        fig0 = go.Figure()
        fig0.add_trace(
            go.Scatter(
                x=range(len(history['loss'])),
                y=history['loss'], 
                mode='lines+markers',name=f'{title}'))
        fig0.update_layout(autosize=False,width=1000,height=600)
        if save==2 or save==1:
            fig0.write_image(f'{title}')
            fig0.write_html(f'{title[:-3]}html')
        # if save==2:
        #     fig0.close()

    if option=='result':
        input_data['UNIT_PREICE(COST)'] = input_data['UNIT_PREICE(COST)'].astype(int)
        x = input_data['DATE']
        y = input_data['UNIT_PREICE(COST)']
        # input_data = input_data[9:]
        import matplotlib.ticker as mticker
        input_data.dtypes
        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
                x=x[:-15],
                y=y[:-15], mode='lines+markers', name=f'과거데이터'))
        fig1.add_trace(
            go.Scatter(
                x=x[-16:21],
                y=y[-16:21], mode='lines+markers',name=f'Back-Testing 구간'))
        fig1.add_trace(
            go.Scatter(
                x=x[20:],
                y=y[20:], mode='lines+markers',name=f'AI 미래 예측 데이터'))
                
        fig1.update_layout(
            autosize=False,width=1300,
            height=600,
            yaxis = dict(tickformat =":04,2f"),
            scene_xaxis = dict(exponentformat= "none",separatethousands= True,tickprefix='$'),
            title={
                'text': f"매입가 기준 {tree_name} {size} 가격 추이 예측(원)" ,
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
                font=dict(size=18))        
        # fig1.update_yaxes(exponentformat='none')
        fig1.update_yaxes(tickformat=',')
        title = f"LSTM_W(5)_epochs(10000)_LSTM_{tree_name}_{size}_result.jpg"
        # fig1.show()
        if save==2 or save==1:
            fig1.write_image(f'{title}')
            fig1.write_html(f'{title[:-3]}html')
        # if save==2:
        #     fig1.close()


def plot_graph_model_loss2(title, tree_name, size, option,history=None,pred_horizon=None,seq_len=None,input_data=None,predicted=None,pred_value=None,save=None):
    '''
    save 1 show and save  
    save 2 non-show and save
    save 3 show and non-save
    '''
    import plotly.express as px
    import plotly.graph_objects as go    
    
    if option=='loss':
        history = history.history
        fig0 = go.Figure()
        fig0.add_trace(
            go.Scatter(
                x=range(len(history['loss'])),
                y=history['loss'], 
                mode='lines+markers',name=f'{title}'))
        fig0.update_layout(autosize=False,width=1000,height=600)
        if save==2 or save==1:
            fig0.write_image(f'{title}')
            fig0.write_html(f'{title[:-3]}html')
        # if save==2:
        #     fig0.close()

    if option=='result':
        input_data['UNIT_PREICE'] = input_data['UNIT_PREICE'].astype(int)
        x = input_data['DATE']
        y = input_data['UNIT_PREICE']
        # input_data = input_data[9:]
        import matplotlib.ticker as mticker
        input_data.dtypes
        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
                x=x[:-15],
                y=y[:-15], mode='lines+markers', name=f'과거데이터'))
        fig1.add_trace(
            go.Scatter(
                x=x[-16:21],
                y=y[-16:21], mode='lines+markers',name=f'Back-Testing 구간'))
        fig1.add_trace(
            go.Scatter(
                x=x[20:],
                y=y[20:], mode='lines+markers',name=f'AI 미래 예측 데이터'))
                
        fig1.update_layout(
            autosize=False,width=1300,
            height=600,
            yaxis = dict(tickformat =":04,2f"),
            scene_xaxis = dict(exponentformat= "none",separatethousands= True,tickprefix='$'),
            title={
                'text': f"매출가 기준 {tree_name} {size} 가격 추이 예측(원)" ,
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
                font=dict(size=18))        
        # fig1.update_yaxes(exponentformat='none')       
        fig1.update_yaxes(tickformat=',')
        title = f"LSTM_W(5)_epochs(10000)_LSTM_{tree_name}_{size}_result.jpg"
        # fig1.show()
        if save==2 or save==1:
            fig1.write_image(f'{title}')
            fig1.write_html(f'{title[:-3]}html')
        # if save==2:
        #     fig1.close()

def yearchart(data, name, save_path, save=None):
    import os
    data = data[-365:]
    data = data[['DATE', 'UNIT_PREICE(COST)']]
    data.plot('DATE', 'UNIT_PREICE(COST)', c='g')
    title = f'{name} 30일 거래 가격 추이.jpg'
    plt.rcParams["figure.figsize"] = (10,5)
    plt.xlabel('Date')
    plt.ylabel(f'{name} UNIT_PREICE(COST)')
    plt.title(title)
    plt.xticks(rotation = 360, fontsize = 8)
    plot_path = os.path.join(save_path, '가격추이')
    if save==2 or save==1:
        title=os.path.join(plot_path, title)
        plt.savefig(f'{title}',dpi=300)
    if save==2:
        plt.close()

def datamake(input_data):
    input_data2 = input_data.copy()
    date_split = input_data2['DATE'].str.split('-')
    input_data2['년'] = date_split.str.get(0)
    input_data2['월'] = date_split.str.get(1)
    input_data2['일'] = date_split.str.get(2)
    input_data2['년'] = input_data2['년'].astype(int)
    input_data2['년'] = input_data2['년'] - 10
    input_data2['년'] = input_data2['년'].astype(str)
    input_data2['DATE2'] = input_data2['년']+'-'+input_data2['월']+'-'+input_data2['일']
    input_data2 = input_data2.drop(['DATE', '년', '월', '일'], axis=1)
    input_data2.rename(columns={"DATE2":"DATE"}, inplace = True)

    input_data3 = pd.concat([input_data, input_data2], axis = 0)
    
    duplicate = input_data3[input_data3.duplicated(['DATE'])]
    input_data3 = input_data3.drop_duplicates(['DATE'], keep='first')

    input_data3 = input_data3.sort_values(by = ['DATE'], axis=0)
    dele = input_data3.loc[input_data3['DATE']=='2006-02-29'].index
    dele2 = input_data3.loc[input_data3['DATE']=='2010-02-29'].index
    dele3 = input_data3.loc[input_data3['DATE'] == '2002-02-29'].index

    input_data3 = input_data3.drop(dele)
    input_data3 = input_data3.drop(dele2)
    input_data3 = input_data3.drop(dele3)

    input_data3 = input_data3.groupby(['DATE']).mean()

    input_data3 = input_data3.reset_index()
    return input_data3
