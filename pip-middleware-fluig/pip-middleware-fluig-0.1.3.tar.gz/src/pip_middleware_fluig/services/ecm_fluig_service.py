from __future__ import absolute_import

from domain.ecm_services import ECMDatasetService
from interface.ecm_dataset import DatasetQueryParams


class FluigECMService:
    def __init__(self) -> None:
        self._domain_ecm_service = ECMDatasetService()

    def get_dataset(self, dataset_params: dict) -> List[dict]:

        params = DatasetQueryParams(**dataset_params)
        return self._domain_ecm_service.execute_query_dataset(params)
