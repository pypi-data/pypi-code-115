# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# OCO Source Materials
# 5900-A3Q, 5737-J33
# Copyright IBM Corp. 2022
# The source code for this program is not published or other-wise divested of its trade 
# secrets, irrespective of what has been deposited with the U.S.Copyright Office.
# ----------------------------------------------------------------------------------------------------

from tests.utils.fixtures import *


def clean_folder(path):
    # check if folder exists
    if os.path.exists(path):
        # remove if exists
        shutil.rmtree(path)


clean_folder("./mlruns")
clean_folder("./logs")


def test_01_init_client(facts_client_credentials):
    facts_client = AIGovFactsClient(
        api_key=facts_client_credentials["apikey"], experiment_name=facts_client_credentials[
            "exp_name"], container_type=facts_client_credentials["container_type"], container_id=facts_client_credentials["container_id"]
    )

    assert facts_client is not None
    assert facts_client._authenticator is not None
    assert facts_client.export_facts is not None

    assert facts_client_credentials['exp_name'] in str(
        facts_client.experiment_name)

    assert facts_client_credentials['container_type'] in str(
        facts_client._container_type)

    assert facts_client_credentials['container_id'] in str(
        facts_client._container_id)

    facts_client.version
