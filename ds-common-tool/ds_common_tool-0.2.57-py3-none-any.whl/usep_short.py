from enum import Enum
from ds_common_tool.suite_base import PriceForecastBase
from ds_common_tool import suite_feature_engineer_sg, suite_model, suite_data
import numpy as np

class Message(Enum):
  USE_DF_FETCH_MESSAGE = 'use df_fetch(df_name: string, data_path: string) to add dataframe into the df_list.'
  USE_DF_REMOVE_MESSAGE = 'use df_remove(df_name: string) to remove the dataframe from the df_list.'
  USE_DF_CHECK_MESSAGE = 'use df_display_all() to list all dataframe in the df_list.'
  USE_CHECK_DF_VALID_MESSAGE = 'use check_df_valid(df_name_list: string[]) to check if the dataframe loaded is valid for the training.'

class USEP_SHORT(PriceForecastBase):
  def __init__(self, case_name = 'short', node_id = '', env = 'localtest', log_level = 0):
    super().__init__(case_name, env)
    self.df_dic = {}
    self.target_column = 'USEP'
    self.feature_columns = []
    self.model_type = 'xgb'
    self.log_level = log_level
    self.display_hint(log_level, msg = [Message.USE_DF_FETCH_MESSAGE, Message.USE_DF_CHECK_MESSAGE])
  
  # ------------------------------- loading in data [add, check, remove]----------------------------
  def df_fetch(self, path_pre = '', log_level = 0):
    usep_df = super().df_fetch(df_name = 'usep-48', data_path = path_pre)
    advisory_df = super().df_fetch(df_name = 'usep-advisory', data_path = path_pre)
    self.df_dic = { 'usep_data' : usep_df, 'advisory_data': advisory_df }

  def df_display_all(self, log_level = 0):
    print(self.usep_df)
    print(self.advisory_df)

  # ----- feature engineer ------
  def feature_engineer(self, log_level = 0):
    self.train_df = suite_feature_engineer_sg.sg_short_term_feature_engineer(self.df_dic,
                                                                             targetvariable = self.target_column, 
                                                                             no_of_period = 12, 
                                                                             divideby = 10)
  
  # ------  train model ---------------
  def train_model(self, start_index = '2020-02-01', end_index = '2022-02-03', model_path = '', n_trials = 10, enable_optuna = True):
    super().generate_model_path(model_path)
    print('out', self.model_path)
    self.model = suite_model.xgb_with_optuna(df = self.train_df, 
                                             label_column = self.target_column, 
                                             column_set_index = 'DATE', start_index = start_index, end_index = end_index, 
                                             save_model = True, model_path = self.model_path, 
                                             enable_optuna = enable_optuna, n_trials = n_trials)
    print('----- Completed traning -----')
  
  def get_model(self):
    return self.model
  
  # ----- predict ----- -------------------------------
  def predict(self, model, data = None, path_pre = '', start_index = '2020-02-01', end_index = '2022-02-03'):
    self.df_fetch(path_pre)
    self.feature_engineer()
    self.predict_df = self.train_df
    self.predict_df = suite_data.predict_data(df = self.train_df, 
                                              target_column = self.target_column,
                                              look_back = 48, 
                                              start_index = start_index, end_index = end_index,
                                              date_column = 'DATE')
    self.model = model #
    prediction =  self.model.predict(self.predict_df)
    self.predict_result =  np.array(prediction) * 10
  
  def display_predict(self):
    print(self.predict_result)
  
  def get_predict(self):
    print(self.predict_result)

  # -------- support function -------------------
  def display_hint(self, log_level = 0, msg = []):
    self.log_level = log_level
    if self.log_level == 1:
      for item in Message:
        if item in msg:
          print(item.value)
