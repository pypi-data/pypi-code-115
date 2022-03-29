from . import WMLDeployment

class MulticlassIrisXGB(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisXGB,self).__init__(name="Spark Iris XGB",
            asset_name="Spark Iris XGB",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        
        
        from sklearn import datasets
        import xgboost as xgb
        from sklearn.model_selection import train_test_split

        iris = datasets.load_iris()
        X = iris.data
        y = iris.target


        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)

        params = {
        #'eta': 0.3,  
        #'silent': True,  # option for logging
        #'objective': 'multi:softprob',  # error evaluation for multiclass tasks
        'num_class': 3,  # number of classes to predic
        'max_depth': 3  # depth of the trees in the boosting process
        } 
        bst = xgb.train(params, dtrain=dtrain, evals=[(dtrain, 'train'), (dtest, 'valid')])


class MulticlassIrisLGBM(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisLGBM,self).__init__(name="Spark Iris LGBM",
            asset_name="Spark Iris LGBM",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        
        from sklearn import datasets
        import lightgbm as lgb
        from sklearn.model_selection import train_test_split

        iris = datasets.load_iris()
        X = iris.data
        y = iris.target


        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        
        train_set = lgb.Dataset(X_train, label=y_train)

        params = {
        "objective": "multiclass",
        "num_class": 3,
        "metric": "multi_logloss",
        "seed": 42,
        }

        bst = lgb.train(
            params, train_set, num_boost_round=10, valid_sets=[train_set], valid_names=["train"]
        )