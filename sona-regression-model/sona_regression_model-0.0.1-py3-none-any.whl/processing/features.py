import pandas as pd
import numpy as np
from scipy import stats
from scipy.special import boxcox1p
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import  MinMaxScaler
from sklearn import base
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.base import BaseEstimator, TransformerMixin
from regression_model.config.core import config


class bed_bath_transformer(BaseEstimator, TransformerMixin):
    def __init__(self,features,ref_var):
        if not isinstance(features, list):
            raise ValueError('variables should be a list')

        if not isinstance(ref_var, list):
            raise ValueError('variables should be a list')
        self.features = features
        self.ref_var = ref_var


    def fit(self, X, y=None):
            return self


    def transform(self,X,y=None):
        X_ = X.copy()
        for feat in self.features:
            print(self.ref_var)
            new_val = 'new_'+feat
            print(new_val)
            dfgrouped = X_[X_[feat].notnull()]
            dfgrouped = dfgrouped.groupby(self.ref_var)[feat].agg(lambda x: pd.Series.mode(x)[0]).reset_index(name=new_val)
            X_ = pd.merge(X_,dfgrouped,how='left',on=self.ref_var)
            X_[feat] = np.where(X_[feat].isnull(),X_[new_val], X_[feat])
            if feat == 'bathroom':
                X_[feat] = np.where(X_[feat]=='6,540 sqft',np.nan,X_[feat])
                X_[feat] = np.where(X_[feat]=='9,466 sqft (on 0.29 acres)',np.nan,X_[feat])
                X_[feat] = X_[feat].astype(str).map(lambda x: x.rstrip(' Baths'))
                X_[feat] = X_[feat].astype(str).map(lambda x: x.rstrip(' bath'))


            if feat == 'bed':
                X_[feat] = X_[feat].astype(str).map(lambda x: x.rstrip(' Beds'))
                X_[feat] = X_[feat].astype(str).map(lambda x: x.rstrip(' b'))

            X_[feat]= X_[feat].replace('—', np.NaN)
            X_[feat] = X_[feat].astype(str).map(lambda x: x.rstrip('\n'))
            X_[feat] = X_[feat].astype(float)
            X_[feat]= X_[feat].fillna(X_.groupby(self.ref_var)[feat].transform('mean'))

            X_[feat] = X_[feat].astype(int)
            X_.drop(new_val, axis=1, inplace=True)

        print(pd.DataFrame(X_).head())
        print(X_.shape)
        return X_


class heatEncTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, feat):

        self.feat = feat


    def fit(self,X,y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()


        X_[self.feat] = np.where(X_[self.feat].isnull(),'No',X_[self.feat] )

        X_[self.feat]  = X_[self.feat].astype(str).map(lambda x: x.lstrip('Heating: '))
        X_[self.feat]  = X_[self.feat].astype(str).map(lambda x: x.lstrip('Details: '))



        X_[self.feat]  = np.where(X_[self.feat].isin(['an','Unknown','No',' ','','None','nan']),'No','Yes')

        print(pd.DataFrame(X_).head())
        print(X_.shape)
        return X_


class propertyEncTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, feat):

        self.feat = feat


    def fit(self,X,y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        self.searchfor = ['Residential', 'Apartment', 'Triplex','Quadruplex','Duplex','Rise','Patio','Mobile','House']
        X_[self.feat] = np.where(X_[self.feat].str.contains('|'.join(self.searchfor)),'Residential',
                               np.where(X_[self.feat].str.contains('Townhouse'),'Townhouse',
         np.where(X_[self.feat].str.contains('Condo'),'Condo','unknown')))



        print(pd.DataFrame(X_).head())
        print(X_.shape)
        return X_

class yearbuiltEncTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, feat):
        self.feat = feat

    def fit(self,X,y=None):
        return self
    def transform(self,X,y=None):
        X_ = X.copy()
        self.var = 'year_built_year'
        X_[self.feat] = X_[self.feat].fillna(2021)
        X_[self.var] = X_[self.feat].str.extract('built in (\d+).')
        X_[self.feat] = np.where(X_[self.var].notnull(),X_[self.var],X_[self.feat])
        X_[self.feat] = np.where(X_[self.feat].str.len()<20,X_[self.feat],'No')
        X_[self.feat] = X_[self.feat].astype(str).map(lambda x: x.lstrip('Year Built: '))
        X_[self.feat] = X_[self.feat].astype(str).map(lambda x: x.lstrip('New Const., '))
        X_[self.feat] = np.where(X_[self.feat]=='',2021,X_[self.feat])
        X_[self.feat] = np.where(X_[self.feat]=='No',2021,X_[self.feat])
        X_[self.feat] = np.where(X_[self.feat]==202,2021,X_[self.feat])
        X_.drop({self.var},axis=1, inplace=True)

        X_[self.feat] = X_[self.feat].astype(float)
        X_[self.feat] = X_[self.feat].astype(int)
        self.current_year = 2022
#         print(self.current_year.dtypes)
        print(X_[self.feat].dtypes)
#         X_[feat] = pd.to_datetime(X_[feat], format='%Y')
#         X_[feat] = pd.to_datetime(self.current_year - X_[feat])
#         X_[self.feat] = (X_[self.feat]).astype(int)
        X_[self.feat] = self.current_year - X_[self.feat]
        print(pd.DataFrame(X_).head())
        print(X_.shape)
        return X_


# class areaTransformer(BaseEstimator, TransformerMixin):
#     def __init__(self, feat):
#         self.feat = feat
#
#     def fit(self,X,y=None):
#         return self
#     def transform(self,X,y=None):
#         X_ = X.copy()
#         X_[self.feat] = np.where(X_[self.feat].str.contains('N/A /'), np.nan,df['area'])
#         X_[self.feat] = df['area'].str.replace(',', '')
#         X_[self.feat] = np.where(df['area'].str.contains('N/A /'), np.nan,df['area'])
#         X_[self.feat] = np.where(df['area']=='nan', np.nan,df['area'])
#         X_[self.feat] = df['area'].str.rstrip(' SqFt.')
#         self.clean_area = X_[X_[self.feat].str.contains('sq f', na=False)]
#         self.clean_area[self.feat] = clean_area[self.feat].astype(str).map(lambda x: x.lstrip('$'))
#         self.clean_area[self.feat] = clean_area[self.feat].astype(str).map(lambda x: x.rstrip(' / sq f'))
#         self.clean_area[self.feat] = clean_area[self.feat].astype(int)
#         self.clean_area[self.feat] = (clean_area['price']/clean_area['area']).round(2)
#         self.clean_area.drop(['area'], axis=1,inplace=True)
#         self.clean_area['new_area'] = clean_area['new_area'].astype(str)
#         df = pd.merge(df, clean_area, how='left', on=['price', 'bed', 'bathroom', 'year_built',
#        'heating', 'air_conditioner', 'basement', 'security', 'construction',
#        'Floor', 'fireplace', 'Roof', 'Parking', 'Property_type', 'zipcode',
#        'county'])
#         df['area'] = np.where(df['new_area'].isnull(), df['area'], df['new_area'])
#         df['area'] = np.where(df['area']=='—',np.nan,df['area'])
#         df['area'] = df['area'].astype(float)
#         df['area'] = df['area'].fillna(df.groupby(['county','zipcode'])['area'].transform('mean'))
#         df['area'] = df['area'].fillna(df.groupby(['county'])['area'].transform('mean'))
#         df['area'] = df['area'].fillna(df['area'].mean())
#         df.drop('new_area', axis=1, inplace=True)
#
#         self.var = 'year_built_year'
#         X_[self.feat] = X_[self.feat].fillna(2021)
#
#
#         return X_

def find_skewed_boundaries(df, variable, distance):
    IQR = df[variable].quantile(0.75) - df[variable].quantile(0.25)

    lower_boundary = df[variable].quantile(0.25) - (IQR * distance)
    upper_boundary = df[variable].quantile(0.75) + (IQR * distance)

    return upper_boundary, lower_boundary

class OutliersTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, feat):

        self.feat = feat


    def fit(self,X,y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        upper_limit, lower_limit = find_skewed_boundaries(X_, self.feat, 1.5)
        X_[self.feat]= np.where(X_[self.feat] > upper_limit, upper_limit,
                   np.where(X_[self.feat] < lower_limit, lower_limit, X_[self.feat]))

        return X_

class BoxCoxTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, feat, lam=0.15):

        self.feat = feat
        self.lam = lam


    def fit(self,X,y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        X_[self.feat] = boxcox1p(X_[self.feat], self.lam)


        return X_

class columnDropperTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X,y=None):
        return self

    def transform(self, X,y=None):
        X_ = X.copy()
        print(pd.DataFrame(X_).head())
        print(X_.shape)
        return X_.drop(self.columns, axis=1)


class factorizeTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, feat_list):
        self.feat_list = feat_list

    def fit(self, X,y=None):
        return self

    def transform(self, X,y=None):
        X_ = X.copy()
        X_[self.feat_list] = X_[self.feat_list].apply(lambda x:pd.factorize(x)[0])
        # X_ = pd.get_dummies(X_, columns=self.feat_list, drop_first=True)
        print(pd.DataFrame(X_).head())
        print(X_.shape)
        return X_


def get_data(df):
    new_df = df[~df[config.model_config.target].str.contains("mo",na=False)].copy()
    new_df[config.model_config.target] = new_df[config.model_config.target].str.replace(',', '',regex=False)
    new_df[config.model_config.target] = new_df[config.model_config.target].str.replace('$', '',regex=False)
    new_df[config.model_config.target] = new_df[config.model_config.target].str.replace('+', '',regex=False)
    new_df[config.model_config.target] = new_df[config.model_config.target].str.replace('Est. ', '',regex=False)
    new_df[config.model_config.target] =  pd.to_numeric(new_df[config.model_config.target], errors='coerce')
    new_df[config.model_config.target] = new_df.groupby(config.model_config.variables_to_drop)[config.model_config.target].transform(lambda x:x.fillna(x.mean()))

    new_df[config.model_config.num_var] = np.where(new_df[config.model_config.num_var].str.contains('N/A /'), np.nan,new_df[config.model_config.num_var])
    new_df[config.model_config.num_var] = new_df[config.model_config.num_var].str.replace(',', '',regex=False)
    new_df[config.model_config.num_var] = np.where(new_df[config.model_config.num_var].str.contains('N/A /'), np.nan,new_df[config.model_config.num_var])
    new_df[config.model_config.num_var] = np.where(new_df[config.model_config.num_var]=='nan', np.nan,new_df[config.model_config.num_var])
    new_df[config.model_config.num_var] = new_df[config.model_config.num_var].str.rstrip(' SqFt.')
    clean_area = new_df[new_df[config.model_config.num_var].str.contains('sq f', na=False)].copy()
    clean_area[config.model_config.num_var] = clean_area[config.model_config.num_var].astype(str).map(lambda x: x.lstrip('$'))
    clean_area[config.model_config.num_var] = clean_area[config.model_config.num_var].astype(str).map(lambda x: x.rstrip(' / sq f'))
    clean_area[config.model_config.num_var] = clean_area[config.model_config.num_var].astype(int)
    clean_area['new_area'] = (clean_area[config.model_config.target]/clean_area[config.model_config.num_var]).round(2)
    clean_area.drop([config.model_config.num_var], axis=1,inplace=True)
    clean_area['new_area'] = clean_area['new_area'].astype(str)
    new_df = pd.merge(new_df, clean_area, how='left', on=config.model_config.merge_features)
    new_df[config.model_config.num_var] = np.where(new_df['new_area'].isnull(), new_df[config.model_config.num_var], new_df['new_area'])
    new_df[config.model_config.num_var] = np.where(new_df[config.model_config.num_var]=='—',np.nan,new_df[config.model_config.num_var])
    new_df[config.model_config.num_var] = new_df[config.model_config.num_var].astype(float)
    new_df[config.model_config.num_var] = new_df[config.model_config.num_var].fillna(new_df.groupby(config.model_config.variables_to_drop)[config.model_config.num_var].transform('mean'))
    new_df[config.model_config.num_var] = new_df[config.model_config.num_var].fillna(new_df.groupby(['county'])[config.model_config.num_var].transform('mean'))
    new_df[config.model_config.num_var] = new_df[config.model_config.num_var].fillna(new_df[config.model_config.num_var].mean())
    new_df.drop('new_area', axis=1, inplace=True)

    return new_df
