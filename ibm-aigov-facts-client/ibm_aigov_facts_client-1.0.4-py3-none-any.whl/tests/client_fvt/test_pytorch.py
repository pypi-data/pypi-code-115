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
from tests.utils.assets.pytorch import MulticlassIrisPytorch
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
def test_01_init_client(facts_client_credentials):
    cls.facts_client=AIGovFactsClient(
                api_key=facts_client_credentials["apikey"], experiment_name=facts_client_credentials[
                    "exp_name"], container_type=facts_client_credentials["container_type"], container_id=facts_client_credentials["container_id"]
            )

def test_02_get_facts_pytorch(caplog):
    # caplog.set_level(logging.INFO)
    MulticlassIrisPytorch(cls.facts_client)
    #assert 'Successfully logged results to Factsheet service' in caplog.text
