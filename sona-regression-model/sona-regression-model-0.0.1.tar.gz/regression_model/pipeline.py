
from sklearn.pipeline import Pipeline
from regression_model.processing import features as pp
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from regression_model.config.core import config
from sklearn.model_selection import GridSearchCV

pipeline = Pipeline([
#     ("filter_data",filterDataTransformer()),
    # ("heat_Enc", pp.heatEncTransformer(config.model_config.categorical_heating)),
    #  ("property_Enc",pp.propertyEncTransformer(config.model_config.categorical_property_type)),
    ("bed_bath_Enc",pp.bed_bath_transformer(config.model_config.cat_vars_to_num,config.model_config.variables_to_drop)),
    ("year_Enc", pp.yearbuiltEncTransformer(config.model_config.temporal_year_built)),
    ("outliers_feat", pp.OutliersTransformer(config.model_config.num_var)),
    ('Box_Cox_trans',pp.BoxCoxTransformer(config.model_config.num_var)),
    ("columnDropper", pp.columnDropperTransformer(config.model_config.variables_to_drop)),
     ('converted_dummies',pp.factorizeTransformer(config.model_config.cat_to_dummies)),
     ('scaler',MinMaxScaler()),
     ("rfr", RandomForestRegressor(bootstrap=True, ccp_alpha=0.0, criterion='mse',
                      max_depth=None, max_features='auto', max_leaf_nodes=None,
                      max_samples=None, min_impurity_decrease=0.0,
                      min_samples_leaf=1,
                      min_samples_split=2, min_weight_fraction_leaf=0.0,
                      n_estimators=100, n_jobs=None, oob_score=False,
                      random_state=None, verbose=0, warm_start=False)),

])

grid_param = [{
               'rfr__n_estimators' : [10,50,100],
               "rfr__max_features" : ['auto', 'log2', 'sqrt'],
               "rfr__min_samples_leaf":[1,2,5,10,15,100],
                "rfr__max_leaf_nodes": [2, 5,10],
               'rfr__bootstrap' : [True, False],
                }]


gridsearch = GridSearchCV(pipeline,grid_param, cv=5, verbose=0,n_jobs =-1,refit=True)
