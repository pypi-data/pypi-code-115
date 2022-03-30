import pandas as pd
import numpy as np
from dateutil.parser import parse # 문자열을 시간 데이터로 찾아주는 메서드
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib 
mpl.rcParams['axes.unicode_minus'] = False
import plotly.express as px
import plotly.graph_objects as go    
from datetime import datetime

matplotlib.font_manager._rebuild()

import warnings
warnings.filterwarnings('ignore')
from scipy.signal import savgol_filter
import os
import random
import tensorflow as tf
import pymysql
pymysql.install_as_MySQLdb()
import sqlalchemy as db
import pymysql.cursors
from sqlalchemy import create_engine
from datetime import datetime 
# from datetimerange import DateTimeRange
# from tensorflow.python.ops.gen_array_ops import unique
from PIL import Image

import matplotlib
matplotlib.matplotlib_fname()

pd.options.display.float_format = '{:.5f}'.format

import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "NanumGothic"
PATH = 'C:\\Users\\Administrator\\Desktop\\EXE_suppro_0118\\2_suppro' 
os.chdir(PATH)
os.getcwd()

from model_function import *

# engine = db.create_engine("mysql+mysqldb://suppro:"+"dnfla#3300"+"@127.0.0.1:3306/suppro", encoding='utf-8')
# conn = engine.connect()

# save_path = 'plot'
image_path = 'D:\\images\\suppro'
YTrend_path = 'D:\\images\\suppro\\\YTrend'
model_path = 'saved'

# data = pd.read_excel('D:\\2. 데이터\\수프로-출하현황자료(기밀).xlsx',header=13, engine='openpyxl')
# data = data[:-3]

data = pd.read_excel('C:\\Users\\Administrator\\Desktop\\EXE_suppro_0330\\2_suppro\\수프로 데이터 취합_1202_ver2.xlsx', engine='openpyxl')
raw_data = data.copy()
data = raw_data.copy()

tree_list = pd.DataFrame(data['수종'].value_counts())
tree_list = tree_list.reset_index()
tree_list = tree_list.drop(['수종'], axis=1)
tree_list = tree_list[:1]

tree_list = np.array(tree_list['index'].tolist())

# tree_list = ['느티나무', '왕벚나무', '이팝나무', '소나무', '청단풍', '회양목', '스트로브잣나무', '자산홍', '영산홍', '산수유', '산철쭉', '전나무']
tree_list = ['느티나무']#, '소나무', '청단풍', '스트로브잣나무', '전나무', '산수유']
# tree_list = ['팥배나무', '칠엽수', '산사나무', '계수나무', '꽃사과', '복자기']
def supprotest(tree_list, input_data):
    for name in tree_list:
        #데이터 불러오기
        input_data = suppro_prepro22(data, name)
        # # 매입가
        # save_path = (f'treePredictPrice\\{name}')
        # 매출가
        save_path = (f'treePredictPrice_sales\\{name}')
        os.chdir(image_path)
        # createDirectory(save_path)
        size = pd.DataFrame(input_data['SIZE'].value_counts())
        size = size.reset_index()
        size = size.drop(['SIZE'], axis=1)
        size = np.array(size['index'].tolist())
        # size = ['H4.0*R12']
        # input_data.to_csv('input_data.csv',encoding='cp949',index=False)
        # p_data = pd.read_csv('input_data.csv',encoding='cp949')
        # input_data = input_data.append(p_data)
        # input_data.to_csv('input_data.csv',encoding='cp949',index=False)

        #db에 넣기
        # input_data.to_sql(name='PRICE2', con=conn, if_exists='append')

        # input_data = pd.read_sql_query(f'''select * from price2''', conn)
        input_data = input_data.loc[input_data['SPECIES_NM'] == name]

        for i in size:
            input_data2 = suppro_prepro3(input_data, name, i)
            os.chdir(YTrend_path)
            monthplot_data = input_data2.copy()
            monthplot_data['DATE'] = monthplot_data['DATE'].astype(str)

            split = monthplot_data['DATE'].str.split('-')
            monthplot_data['year'] = split.str.get(0)
            monthplot_data['year'] = monthplot_data['year'].astype(int)

            today = datetime.today().year
            today = today - 3

            monthplot_data = monthplot_data[monthplot_data['year'] >= today]

            if len(monthplot_data) > 1:
                month_plot(monthplot_data, name, i)
                month_plot2(monthplot_data, name, i)
            else:
                pass
            # month_plot2(input_data2, name, i)
            # suppro_prepro4(input_data, name, size)

            #DB만들기
            # input_data = input_data.drop(['SIZE'], axis = 1)

            # data_g = input_data.groupby(['DATE']).sum()
            # data_min = input_data.groupby(['DATE']).min()
            # data_max = input_data.groupby(['DATE']).max()
            # data_mean = input_data.groupby(['DATE']).mean()
            # data_g = data_g.reset_index()
            # data_min = data_min.reset_index()
            # data_max = data_max.reset_index()
            # data_mean = data_mean.reset_index()

            # # data_g = data_g.drop(['index'], axis =1)
            # # data_min = data_min.drop(['index'], axis =1)
            # # data_max = data_max.drop(['index'], axis =1)
            # # data_mean = data_mean.drop(['index'], axis =1)

            # data_mean['SPECIES_NM'] = name

            # data_min.columns = ['DATE', 'SPECIES_NM', 'SHIPMNET_MIN','UNIT_PREICE_MIN', 'SHIPMENT_PRICE_MIN', 'UNIT_PREICE(COST)_MIN', 'PRICE(COST)_MIN', 'SALES_MIN']
            # data_max.columns = ['DATE', 'SPECIES_NM', 'SHIPMNET_MAX','UNIT_PREICE_MAX', 'SHIPMENT_PRICE_MAX', 'UNIT_PREICE(COST)_MAX', 'PRICE(COST)_MAX', 'SALES_MAX']
            # data_mean.columns = ['DATE', 'SHIPMNET_MEAM','UNIT_PREICE_MEAN', 'SHIPMENT_PRICE_MEAN', 'UNIT_PREICE(COST)_MEAN', 'PRICE(COST)_MEAN', 'SALES_MEAN', 'SPECIES_NM']

            # data_mean = data_mean[['SPECIES_NM', 'DATE', 'SHIPMNET_MEAM','UNIT_PREICE_MEAN', 'SHIPMENT_PRICE_MEAN', 'UNIT_PREICE(COST)_MEAN', 'PRICE(COST)_MEAN', 'SALES_MEAN']]

            # data_min.to_sql(name='PRICE_MIN', con=conn, if_exists='append')
            # data_max.to_sql(name='PRICE_MAX', con=conn, if_exists='append')
            # data_mean.to_sql(name='PRICE_MEAN', con=conn, if_exists='append')

            # # 단가(원가)
            # outlier_idx = get_outlier(input_data2, 'UNIT_PREICE(COST)')

            #단가
            outlier_idx = get_outlier(input_data2, 'UNIT_PREICE')

            input_data2.drop(outlier_idx, axis=0, inplace=True)

            p_data2 = pd.read_csv('supprodata_0217.csv',encoding='cp949')
            new_data = input_data2.append(p_data2)
            new_data.to_csv('supprodata_0217.csv',encoding='cp949',index=False)
            

            if len(input_data2) < 13:
                # image = plt.imread('./supuro_needmoredata.png')
                # plt.imshow(image)
                size = str(i)
                size = size.replace('*', 'X')
                size = size.replace('/', '')
                title = f"LSTM_W(5)_epochs(10000)_LSTM_{name}_{size}_result.jpg"  
                import matplotlib.ticker as mticker
                fig1 = go.Figure()
                fig1.add_trace(
                    go.Scatter(
                        x=['2000', '2004', '2008', '2012', '2016', '2020', '2024', '2028'],
                        y=[' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
                        textposition=["top center"],
                        ))
                
                fig1.update_layout(
                autosize=False,width=1300,
                height=600,
                scene_xaxis = dict(exponentformat= "none",separatethousands= True,tickprefix='$'),
                title={
                    'text': "AI 솔루션 가격 예측을 위하여 조경수 거래 데이터가 더 필요합니다.",
                    'y':0.9,
                    'x':0.5},
                font=dict(size=18))
                fig1.update_yaxes(tickformat=',')
                # fig1.update_yaxes(exponentformat='none')
                os.chdir(image_path)
                title=os.path.join(save_path,title)
                fig1.write_html(f'{title[:-3]}html')
                fig1.write_image(f'{title}')

            else:
                # #단가(원가)
                # input_data2 = stl_data_make(input_data2)
                #단가
                input_data2 = stl_data_make2(input_data2)
                
                input_data3 = datamake(input_data2)
                pred_horizon=input_data3.shape[0]//10 * 3
                
                input_data3 = lstm_input(input_data3)

                if len(input_data3) < 20:
                    size = str(i)
                    size = size.replace('*', 'X')
                    size = size.replace('/', '')
                    title = f"LSTM_W(5)_epochs(10000)_LSTM_{name}_{size}_result.jpg"  
                    import matplotlib.ticker as mticker
                    fig1 = go.Figure()
                    fig1.add_trace(
                        go.Scatter(
                            x=['2000', '2004', '2008', '2012', '2016', '2020', '2024', '2028'],
                            y=[' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
                            textposition=["top center"],
                            ))
                    
                    fig1.update_layout(
                    autosize=False,width=1300,
                    height=600,
                    scene_xaxis = dict(exponentformat= "none",separatethousands= True,tickprefix='$'),
                    title={
                        'text': "AI 솔루션 가격 예측을 위하여 조경수 거래 데이터가 더 필요합니다.",
                        'y':0.9,
                        'x':0.5},
                    font=dict(size=18))
                    fig1.update_yaxes(tickformat=',')
                    # fig1.update_yaxes(exponentformat='none')
                    os.chdir(image_path)
                    title=os.path.join(save_path,title)
                    fig1.write_html(f'{title[:-3]}html')
                    fig1.write_image(f'{title}')
                else:
                    os.chdir(image_path)
                    class config:
                        seed = 42
                        device = "cuda:0"            
                
                    def seed_everything(seed: int = 42):
                        random.seed(seed)
                        np.random.seed(seed)
                        os.environ["PYTHONHASHSEED"] = str(seed)
                        tf.random.set_seed(seed)

                    seed_everything(config.seed)

                    seq_len=5
                    num_epochs=10
                    # num_epochs=5
                    batch=20
                    save=2
                    verbose=1 
                    model_name = 'LSTM'
                    tree_name = name
                    size = i

                    #3년 가격 추이 차트
                    # os.chdir(YTrend_path)
                    # os.getcwd()
                    # month_plot(input_data3, tree_name, size)
                    # month_plot2(input_data3, tree_name, size)

                    # #단가(원가)
                    # os.chdir(save_path)
                    # os.getcwd()
                    # real_price, pred_value, RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8 = LSTM(input_data3, seq_len, batch, num_epochs, tree_name, size, verbose, model_name, save, save_path, model_path)
                    # os.chdir(PATH)
                    # # temp = {
                    # #     'tree':tree_name,
                    # #     'size':size,
                    # #     'y1':int(pred_value[0:1]),
                    # #     'y2':int(pred_value[1:2]),
                    # #     'y3':int(pred_value[2:3]),
                    # #     'y4':int(pred_value[3:4]),
                    # #     'y5':int(pred_value[4:5]),
                    # #     'y6':int(pred_value[5:6]),
                    # #     'y7':int(pred_value[6:7]),
                    # #     'y8':int(pred_value[7:8])}
                    # # result = []
                    # # result.append(temp)
                    # # result = pd.DataFrame(result)
                    # # result.to_sql(name='Purchase_result', con=conn, if_exists='append')

                    #매출가
                    os.chdir(save_path)
                    os.getcwd()
                    real_price, pred_value, RMSE, RMSE_1y, RMSE_2y, RMSE_3y, RMSE_4y, RMSE_5y, RMSE_6y, RMSE_7y, RMSE_8y, mape1, mape2, mape3, mape4, mape5, mape6, mape7, mape8 = LSTM_UNIT_PREICE(input_data3, seq_len, batch, num_epochs, tree_name, size, verbose, model_name, save, save_path, model_path)
                    #성능지표용
                    os.chdir(PATH)
                    temp = {
                        'tree':tree_name,
                        'size':size,
                        'y1':int(pred_value[0:1]),
                        'y2':int(pred_value[1:2]),
                        'y3':int(pred_value[2:3]),
                        'y4':int(pred_value[3:4]),
                        'y5':int(pred_value[4:5]),
                        'y6':int(pred_value[5:6]),
                        'y7':int(pred_value[6:7]),
                        'y8':int(pred_value[7:8])}
                    result = []
                    result.append(temp)
                    result = pd.DataFrame(result)
                    return result
                    # result.to_sql(name='Sales_result_0330test', con=conn, if_exists='append')
                    # # # p_result = pd.read_csv('size_test.csv',encoding='cp949')
                    # # # result = result.append(p_result)
                    # # # result.to_csv('model_result_unitprice.csv',encoding='cp949',index=False)

result = supprotest(tree_list, data)
