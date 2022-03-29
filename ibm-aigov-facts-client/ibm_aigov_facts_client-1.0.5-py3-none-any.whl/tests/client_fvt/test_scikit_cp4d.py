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


cls=GlobalVars
def test_01_init_client(facts_client_credentials_cp4d):
    cls.facts_client=AIGovFactsClient(
                 experiment_name=facts_client_credentials_cp4d[
                    "exp_name"], container_type=facts_client_credentials_cp4d["container_type"]
                    , container_id=facts_client_credentials_cp4d["container_id"]
                    , cloud_pak_for_data_configs=CloudPakforDataConfig(service_url=facts_client_credentials_cp4d["service_url"]
                                                                        ,username=facts_client_credentials_cp4d["username"]
                                                                        ,password=facts_client_credentials_cp4d["password"]
                                                                        ,disable_ssl_verification=facts_client_credentials_cp4d["disable_ssl_verification"])

            )

def test_02_get_facts(caplog):
    caplog.set_level(logging.INFO)
    deployment = MulticlassIris(cls.facts_client,is_cp4d=True)
    assert 'Successfully logged results to Factsheet service' in caplog.text
    model_uid = deployment.get_asset_id()
    print("model asset_id : {}".format(model_uid))

def test_03_get_facts_pipeline(caplog):
    MulticlassIrisPipeline(cls.facts_client,is_cp4d=True)
    assert 'Successfully logged results to Factsheet service' in caplog.text


def test_04_get_facts_hyperparams(caplog):
    MulticlassIrisGridCV(cls.facts_client,is_cp4d=True)
    assert 'Successfully logged results to Factsheet service' in caplog.text