from . import WMLDeployment
import os


class MulticlassIris(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIris,self).__init__(name="Scikit Iris",
            asset_name="Scikit Iris",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        import pandas as pd
        from sklearn import model_selection
        from sklearn import metrics
        from sklearn.linear_model import LinearRegression
        from sklearn import svm, datasets
        import numpy as np

        iris = datasets.load_iris()
        data1 = pd.DataFrame(data= np.c_[iris['data'], iris['target']],
                            columns= ['sepal_length','sepal_width','petal_length','petal_width','target'])

        from sklearn.model_selection import train_test_split
        train, test = train_test_split(data1, test_size = 0.4, random_state = 42)

        X_train = train[['sepal_length','sepal_width','petal_length','petal_width']]
        y_train = train.target
        X_test = test[['sepal_length','sepal_width','petal_length','petal_width']]
        y_test = test.target

        svc = svm.SVC(kernel="rbf", C=2,probability=True)
        model=svc.fit(X_train,y_train)

        model.score(X_test, y_test)
        y_pred = model.predict(X_test)
        y_pred_prob = model.predict_proba(X_test)


        metrics.mean_squared_error(y_test, y_pred)
        metrics.mean_absolute_error(y_test, y_pred)


        r2_score_data1 = metrics.r2_score(y_test, y_pred)
        recall_score_data1 = metrics.recall_score(y_test, y_pred, average="macro")
        r2_score_data2 = metrics.r2_score(y_test, y_pred)
        lor_score_data1 = model.score(X_test, y_test)
        recall_score2_data2 = metrics.recall_score(y_test, y_pred, average="micro")

        software_spec_uid = self.wml_client.software_specifications.get_id_by_name("default_py3.7_opence")
        print("Software Specification ID: {}".format(software_spec_uid))

        model_props = {
                self.wml_client._models.ConfigurationMetaNames.NAME:"{}".format(self.asset_name),
                self.wml_client._models.ConfigurationMetaNames.TYPE: "scikit-learn_0.23",
                self.wml_client._models.ConfigurationMetaNames.SOFTWARE_SPEC_UID: software_spec_uid,
                self.wml_client._models.ConfigurationMetaNames.LABEL_FIELD:"target",
            }

        #self.facts_client=self.facts_auth_client
        self.facts_client.export_facts.prepare_model_meta(wml_client=self.wml_client,meta_props=model_props)

        print("Storing model .....")

        published_model_details = self.wml_client.repository.store_model(model=model, meta_props=model_props, training_data=data1.drop(["target"], axis=1), training_target=data1.target)
        self.asset_uid  = self.wml_client.repository.get_model_id(published_model_details)
        print("Done")
        print("Model ID: {}".format(self.asset_uid))


        self.facts_client.runs.log_metric(self.facts_client.runs.get_current_run_id(), "mae", .77)
        self.facts_client.export_facts.export_payload(self.facts_client.runs.get_current_run_id())


class MulticlassIrisPipeline(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisPipeline,self).__init__(name="Scikit Iris pipeline",
            asset_name="Scikit Iris pipeline",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        import pandas as pd
        from sklearn import model_selection
        from sklearn import metrics
        from sklearn.linear_model import LinearRegression
        from sklearn import svm, datasets
        import numpy as np
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        pipe = Pipeline([("scaler", StandardScaler()), ("lr", LinearRegression())])


        iris = datasets.load_iris()
        data1 = pd.DataFrame(data= np.c_[iris['data'], iris['target']],
                            columns= ['sepal_length','sepal_width','petal_length','petal_width','target'])

        from sklearn.model_selection import train_test_split
        train, test = train_test_split(data1, test_size = 0.4, random_state = 42)

        X_train = train[['sepal_length','sepal_width','petal_length','petal_width']]
        y_train = train.target
        X_test = test[['sepal_length','sepal_width','petal_length','petal_width']]
        y_test = test.target

        pipe.fit(X_train,y_train)

        # pipe.score(X_test, y_test)
        # y_pred = model.predict(X_test)
        # y_pred_prob = model.predict_proba(X_test)

        # metrics.mean_squared_error(y_test, y_pred)
        # metrics.mean_absolute_error(y_test, y_pred)

class MulticlassIrisGridCV(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisGridCV,self).__init__(name="Scikit Iris hyperparams",
            asset_name="Scikit Iris hyperparams",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        import pandas as pd
        from sklearn import model_selection
        from sklearn import metrics
        from sklearn.linear_model import LinearRegression
        from sklearn import svm, datasets
        import numpy as np

        from sklearn.model_selection import GridSearchCV

        iris = datasets.load_iris()
        data1 = pd.DataFrame(data= np.c_[iris['data'], iris['target']],
                            columns= ['sepal_length','sepal_width','petal_length','petal_width','target'])

        from sklearn.model_selection import train_test_split
        train, test = train_test_split(data1, test_size = 0.4, random_state = 42)

        X_train = train[['sepal_length','sepal_width','petal_length','petal_width']]
        y_train = train.target
        X_test = test[['sepal_length','sepal_width','petal_length','petal_width']]
        y_test = test.target

        parameters = {"kernel": ("linear", "rbf"), "C": [1, 2]}
        svc = svm.SVR()
        clf = GridSearchCV(svc, parameters, cv=3)
        clf.fit(X_train, y_train)