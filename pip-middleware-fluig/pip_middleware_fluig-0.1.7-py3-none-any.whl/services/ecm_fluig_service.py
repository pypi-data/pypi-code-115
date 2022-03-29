from typing import List
from pip_middleware_fluig.domain.ecm_services import ECMDatasetService
from pip_middleware_fluig.interface.ecm_dataset import DatasetQueryParams


class FluigECMService:
    def __init__(self, wsdl_url: str) -> None:
        self._domain_ecm_service = ECMDatasetService(wsdl_url)

    def get_dataset(self, dataset_params: dict) -> List[dict]:
        
        # Returns the object result dataset service wsdl.

        # Parameters:
        #    dataset_params (dict): filter query constraints example {"fildname": "foo", "value": "bar"}

        # Returns:
        #    list(dict):Contem object return query dataset service wsdl.

        params = DatasetQueryParams(**dataset_params)
        return self._domain_ecm_service.execute_query_dataset(params)
