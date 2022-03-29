from typing import Optional, List

from pip_middleware_fluig.repositories.soap import ClientFluig
from pip_middleware_fluig.interface.ecm_dataset import DatasetQuery, StructConstraint
from pip_middleware_fluig.utils.common_functions import convert_zeep_object


class ECMDatasetService:
    def __init__(self, wsdl_url:str, client: ClientFluig = None) -> None:
        self._client = client or ClientFluig(wsdl_url=wsdl_url)

    def constraints(self, constraints: List[StructConstraint]):
        constraint_array_element = self._client.get_element_in_xml(element="ns0:searchConstraintDtoArray")
        constraint_element = self._client.get_element_in_xml(element="ns0:searchConstraintDto")
        items = []
        for value in constraints:
            items.append(
                constraint_element(
                    value.constraint_type,
                    value.field_name,
                    value.init_value,
                    value.final_value,
                    value.like_search,
                )
            )
        return constraint_array_element(items)

    def execute_query_dataset(self, dataset: DatasetQuery) -> List[dict]:
        query_result = self._client.soap_intance.service.getDataset(
            dataset.company_id,
            dataset.user_name,
            dataset.password,
            dataset.dataset_name,
            dataset.fields,
            self.constraints(constraints=dataset.constraints),
            dataset.order,
        )

        response = convert_zeep_object(query_result)

        serialize_result = []
        items = {}
        for value in response["values"]:
            for k, v in zip(response["columns"], value["value"]):
                items.update({k: v})

            serialize_result.append(items)
        return serialize_result
