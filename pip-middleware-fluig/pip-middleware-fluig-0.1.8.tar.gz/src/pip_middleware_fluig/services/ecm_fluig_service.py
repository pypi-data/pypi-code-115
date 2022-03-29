from typing import List
from pip_middleware_fluig.domain.ecm_services import ECMDatasetService
from pip_middleware_fluig.interface.ecm_dataset import DatasetQueryParams, DatasetQuery, StructConstraint


class FluigECMService:
    def __init__(self, *, wsdl_url: str) -> None:
        self._domain_ecm_service = ECMDatasetService(wsdl_url)

    def get_dataset(
        self, company_id: str, user_name: str, password: str, dataset_name: str, dataset_params: dict
    ) -> List[dict]:

        # Returns the object result dataset service wsdl.

        # Parameters:
        #    dataset_params (dict): filter query constraints example {"fildname": "foo", "value": "bar"}

        # Returns:
        #    list(dict):Contem object return query dataset service wsdl.

        params = DatasetQueryParams(**dataset_params)
        constraint = StructConstraint(
            constraint_type="MUST", field_name=params.field_name, init_value=params.value, final_value=params.value
        )
        query = DatasetQuery(
            company_id=company_id,
            user_name=user_name,
            password=password,
            dataset_name=dataset_name,
            fields=[],
            constraints=[constraint],
            order=[],
        )

        return self._domain_ecm_service.execute_query_dataset(query)
