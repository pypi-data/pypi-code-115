from typing import Dict, Any

import datahub.metadata.schema_classes as models

from dh_client.entities import Entity


class CustomProperty(Entity):
    @staticmethod
    def create_mpc_association(
        entity_type: str = None, entity_urn: str = None, custom_properties: dict = None
    ) -> Dict[str, Any]:
        """Create a custom properties MPC dictionary.

        Args:
             entity_type: The entity type.
             entity_urn: The entity URN.
             custom_properties: The dictionary with the custom properties.

        Return:
            The MPC dictionary.
        """
        return CustomProperty._create_mpc_dict(
            entity_type,
            entity_urn,
            "datasetProperties",
            models.DatasetPropertiesClass(customProperties=custom_properties),
        )
