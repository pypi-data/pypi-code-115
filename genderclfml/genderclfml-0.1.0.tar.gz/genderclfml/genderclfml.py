import os
import joblib
import warnings
warnings.filterwarnings('ignore')

PACKAGE_DIR = os.path.dirname(__file__)

class GenderClassifier(object):
    """Docstring"""
    def __init__(self, name=None):
        super(GenderClassifier, self).__init__()
        self.name = name

    def __repr__(self):
        return "GenderClassifier(name={})".format(self.name)

    def predict(self):
        # Load vectorizer
        gender_vectorizer = open(os.path.join(PACKAGE_DIR, "models/gender_vectorizer.pkl"), "rb")
        gender_cv = joblib.load(gender_vectorizer)

        # Load models
        gender_nv_model = open(os.path.join(PACKAGE_DIR, "models/gender_nv_model.pkl"), "rb")
        gender_classifier = joblib.load(gender_nv_model)

        # Vectorization of test data
        vectorized_data = gender_cv.transform([self.name]).toarray()

        prediction = gender_classifier.predict(vectorized_data)

        if prediction[0] == 0:
            prediction = 'Female'
        elif prediction[0] == 1:
            prediction = 'Male'

        return prediction

    def load_model(self, model_type):
        if model_type == 'nv':
            gender_nv_model = open(os.path.join(PACKAGE_DIR, "models/gender_nv_model.pkl"), "rb")
            gender_classifier = joblib.load(gender_nv_model)
        elif model_type == 'logit':
            gender_logit_model = open(os.path.join(PACKAGE_DIR, "models/gender_logit_model.pkl"), "rb")
            gender_classifier = joblib.load(gender_logit_model)
        elif model_type == 'dtree':
            gender_dtree_model = open(os.path.join(PACKAGE_DIR, "models/gender_dTree_model.pkl"), "rb")
            gender_classifier = joblib.load(gender_dtree_model)
        else:
            return 'Please enter correct model type [\'nv\': Naive Bayes, \'logit\': Logistic Regression, \'dtree\': Decision Tree]'

        return gender_classifier  

    def classify(self, new_name=None):
        if new_name is not None:
            self.name = new_name
        prediction = self.predict()
        return prediction

    def is_female(self, new_name=None):
        if new_name is not None:
            self.name = new_name
        prediction = self.predict()
        return bool(prediction=='Female')        

    def is_male(self, new_name=None):
        if new_name is not None:
            self.name = new_name
        prediction = self.predict()
        return bool(prediction=='Male')      