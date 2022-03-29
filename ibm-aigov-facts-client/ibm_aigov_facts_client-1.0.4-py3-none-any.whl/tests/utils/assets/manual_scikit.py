from . import WMLDeployment
import os


class MulticlassIrisManual(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisManual,self).__init__(name="Scikit Iris manual",
            asset_name="Scikit Iris manual ",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):

        self.facts_client.manual_log.start_trace()
        
        import pandas as pd
        from sklearn import model_selection
        from sklearn import metrics
        from sklearn.linear_model import LinearRegression
        from sklearn import svm, datasets
        import sys
        import numpy as np
        from math import sqrt
        from sklearn.model_selection import train_test_split


        iris = datasets.load_iris()
        data1 = pd.DataFrame(data= np.c_[iris['data'], iris['target']],
                            columns= ['sepal_length','sepal_width','petal_length','petal_width','target'])
        
        train, test = train_test_split(data1, test_size = 0.4, random_state = 42)

        X_train = train[['sepal_length','sepal_width','petal_length','petal_width']]
        y_train = train.target
        X_test = test[['sepal_length','sepal_width','petal_length','petal_width']]
        y_test = test.target

        svc = svm.SVC(kernel="rbf", C=2,probability=True)
        model=svc.fit(X_train,y_train)

        score=model.score(X_test, y_test)
        y_pred = model.predict(X_test)
        mse=metrics.mean_squared_error(y_test, y_pred)

        self.facts_client.manual_log.log_metric("score", score)
        self.facts_client.manual_log.log_metrics({"mse": 200.00, "rmse": 50.00})

        self.facts_client.manual_log.log_param("learning_rate", 0.01)
        p={"learning_rate1": 0.001, "n_estimators": 10}
        self.facts_client.manual_log.log_params(p)

        self.facts_client.manual_log.set_tags({"engineering": "ML Platform",
        "release.candidate": "RC1",
        "release.version": "2.2.0"})

        self.facts_client.export_facts.export_payload_manual(self.facts_client.runs.get_current_run_id())

        self.facts_client.manual_log.end_trace()