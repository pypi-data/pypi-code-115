################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R
# (c) Copyright IBM Corp. 2020, 2022. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from sklearn.pipeline import Pipeline


class AutoaiTSPipeline(Pipeline):
    # def __init__(self, steps, *, memory=None, verbose=False):
    def __init__(self, steps, **kwargs):
        super().__init__(steps, **kwargs)

    def predict(self, X=None, **predict_params):
        return super().predict(X, **predict_params)

    def name(self):
        return "AutoaiTSPipeline"