# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# OCO Source Materials
# 5900-A3Q, 5737-J33
# Copyright IBM Corp. 2022
# The source code for this program is not published or other-wise divested of its trade 
# secrets, irrespective of what has been deposited with the U.S.Copyright Office.
# ----------------------------------------------------------------------------------------------------

import logging
import unittest
from tests.utils.fixtures import *
from tests.utils.assets.scikit import MulticlassIris,MulticlassIrisGridCV,MulticlassIrisPipeline
from tests.utils.config import *

LOGGER = logging.getLogger(__name__)

def clean_folder(path):
    # check if folder exists
    if os.path.exists(path):
        # remove if exists
        shutil.rmtree(path)


clean_folder("./mlruns")
clean_folder("./logs")


# class TestAIOpenScaleClient(unittest.TestCase):

#     facts_client = None
#     model_uid= None
#     test_uid = str(uuid.uuid4())

#     @classmethod
#     def setUpClass(cls):
#         cls.facts_creds=facts_client_credentials()
#         cls.facts_client=AIGovFactsClient(
#             api_key=cls.facts_creds["apikey"], experiment_name=cls.facts_creds[
#                 "exp_name"], container_type=cls.facts_creds["container_type"], container_id=cls.facts_creds["container_id"]
#         )
#         cls.deployment = MulticlassIris(cls.facts_client)
       
#     def test_01_get_model_ids(self):
#         TestAIOpenScaleClient.model_uid = self.deployment.get_asset_id()
#         print("model asset_id : {}".format(TestAIOpenScaleClient.model_uid))

# if __name__ == '__main__':
#     unittest.main()

cls=GlobalVars
def test_01_init_client(facts_client_credentials):
    cls.facts_client=AIGovFactsClient(
                api_key=facts_client_credentials["apikey"], experiment_name=facts_client_credentials[
                    "exp_name"], container_type=facts_client_credentials["container_type"], container_id=facts_client_credentials["container_id"]
            )

def test_02_get_facts(caplog):
    caplog.set_level(logging.INFO)
    deployment = MulticlassIris(cls.facts_client)
    assert 'Successfully logged results to Factsheet service' in caplog.text
    model_uid = deployment.get_asset_id()
    print("model asset_id : {}".format(model_uid))


def test_03_get_facts_pipeline(caplog):
    MulticlassIrisPipeline(cls.facts_client)
    assert 'Successfully logged results to Factsheet service' in caplog.text


def test_04_get_facts_hyperparams(caplog):
    MulticlassIrisGridCV(cls.facts_client)
    assert 'Successfully logged results to Factsheet service' in caplog.text