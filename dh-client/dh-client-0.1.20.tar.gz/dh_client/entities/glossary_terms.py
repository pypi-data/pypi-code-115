import time
from typing import List, Union, Iterator, Dict

import datahub.metadata.schema_classes as models
from datahub.emitter.mce_builder import make_dataset_urn, make_term_urn
from datahub.ingestion.source.metadata.business_glossary import make_glossary_term_urn
from datahub.metadata.schema_classes import (
    AuditStampClass,
    EditableSchemaFieldInfoClass,
    EditableSchemaMetadataClass,
    GlossaryTermAssociationClass,
    GlossaryTermsClass,
)

from dh_client import utils
from dh_client.entities import Entity, datasets
from dh_client.utils import str_or_md_file


class GlossaryTerm(Entity):
    """
    Examples:

    The standard way:

        >>> client.glossary_term.upsert(
        ...   definition="foo", add_to=[{"dataset": "dataset_x", "column": "column_y"}],
        ...   documentation="The **actual** markdown documentation"
        ... )

    Modify dataset using a JSON file:

        $ cat glossary-terms.json
        [{
            "name": "foo",
            "add_to": [
               {"dataset": "netdata-analytics-bi.posthog.user360_latest", "column": "posthog_first_distinct_id"}
            ],
            "documentation": "**Markdown** documentation"
        }]
        $ cat glossary-terms-2.json
        [{
            "name": "foo",
            "add_to": [
               {"dataset": "netdata-analytics-bi.posthog.user360_latest", "column": "posthog_first_distinct_id"}
            ],
            "documentation": "/path/to/markdown-file.md"
        }]
        >>> client.glossary_term.upsert(file_pattern="glossary_term*.json")
    """

    entity_type: str = "glossaryTerm"
    aspect_name: str = "glossaryTermInfo"

    def _create_mpc(
        self,
        definition: str,
        name: str = None,
        term_source: str = "INTERNAL",
        custom_properties: dict = None,
        parent_node: str = None,
        source_url: str = None,
        source_ref: str = None,
        add_to: List[Dict[str, str]] = None,
        documentation: str = None,
    ) -> List[dict]:
        """Create a tag mpc.

        Args:
            definition: glossary term definition.
            name: glossary term name.
            term_source: Term source.
            custom_properties: Dictionary with custom properties.
            parent_node: The parent node.
            source_url: The source url.
            source_ref: Source reference.
            add_to: Add to list of dataset columns.
            documentation: Term markdown documentation.

        Returns: A list with a single mpc dictionary.
        """
        term_urn = make_term_urn(definition)

        mpcs = [
            dict(
                entityType=GlossaryTerm.entity_type,
                entityUrn=term_urn,
                aspectName=GlossaryTerm.aspect_name,
                aspect=models.GlossaryTermInfoClass(
                    definition=definition,
                    termSource=term_source,
                    name=name,
                    customProperties=custom_properties,
                    parentNode=parent_node,
                    sourceUrl=source_url,
                    sourceRef=source_ref,
                ),
            )
        ]
        if add_to:
            mpcs.extend(list(self.create_mpc_column_association(term_urn, add_to)))
        if documentation:
            mpcs.append(
                self.create_mpc_documentation(
                    term_urn,
                    str_or_md_file(documentation),
                )
            )
        return mpcs

    def create_mpc_column_association(
        self, term_to_add: str, dataset_columns: List[Dict[str, str]]
    ) -> Iterator[dict]:
        for dataset_column in dataset_columns:
            column = dataset_column["column"]
            dataset_urn = make_dataset_urn(
                dataset_column.get("platform", self.emmiter.dataset_platform),
                dataset_column["dataset"],
                dataset_column.get("env", self.emmiter.env),
            )
            current_editable_schema_metadata = self.emmiter.graph.get_aspect_v2(
                entity_urn=dataset_urn,
                aspect="editableSchemaMetadata",
                aspect_type=EditableSchemaMetadataClass,
            )

            # Some pre-built objects to help all the conditional pathways
            now = int(time.time() * 1000)  # milliseconds since epoch
            current_timestamp = AuditStampClass(
                time=now, actor=self.emmiter.datahub_actor
            )

            term_association_to_add = GlossaryTermAssociationClass(urn=term_to_add)
            term_aspect_to_set = GlossaryTermsClass(
                terms=[term_association_to_add], auditStamp=current_timestamp
            )
            field_info_to_set = EditableSchemaFieldInfoClass(
                fieldPath=column, glossaryTerms=term_aspect_to_set
            )

            need_write = False
            field_match = False
            if current_editable_schema_metadata:
                for (
                    fieldInfo
                ) in current_editable_schema_metadata.editableSchemaFieldInfo:
                    if (
                        utils.get_simple_field_path_from_v2_field_path(
                            fieldInfo.fieldPath
                        )
                        == column
                    ):
                        # we have some editable schema metadata for this field
                        field_match = True
                        if fieldInfo.glossaryTerms:
                            if term_to_add not in [
                                x.urn for x in fieldInfo.glossaryTerms.terms
                            ]:
                                # this tag is not present
                                fieldInfo.glossaryTerms.terms.append(
                                    term_association_to_add
                                )
                                need_write = True
                        else:
                            fieldInfo.glossaryTerms = term_aspect_to_set
                            need_write = True

                if not field_match:
                    # this field isn't present in the editable schema metadata aspect, add it
                    field_info = field_info_to_set
                    current_editable_schema_metadata.editableSchemaFieldInfo.append(
                        field_info
                    )
                    need_write = True

            else:
                # create a brand new editable schema metadata aspect
                current_editable_schema_metadata = EditableSchemaMetadataClass(
                    editableSchemaFieldInfo=[field_info_to_set],
                    created=current_timestamp,
                )
                need_write = True

            if need_write:
                yield dict(
                    entityType=datasets.Dataset.entity_type,
                    entityUrn=dataset_urn,
                    aspectName="editableSchemaMetadata",
                    aspect=current_editable_schema_metadata,
                    use_graph=True,
                )

    @staticmethod
    def create_mpc_association(
        entity_type: str,
        entity_urn,
        glossary_terms: List[Union[str, List[str]]],
        actor: str,
    ) -> dict:
        """Create a glossary terms MPC dictionary.

        Args:
             entity_type: The entity type.
             entity_urn: The entity URN.
             glossary_terms: The list of custom properties.
             actor: The actor.

        Return:
            The MPC dictionary.
        """
        return GlossaryTerm._create_mpc_dict(
            entity_type,
            entity_urn,
            "glossaryTerms",
            models.GlossaryTermsClass(
                terms=[
                    models.GlossaryTermAssociationClass(
                        make_glossary_term_urn(
                            [term] if isinstance(term, str) else term
                        )
                    )
                    for term in glossary_terms
                ],
                auditStamp=models.AuditStampClass(time=0, actor=actor),
            ),
        )

    @staticmethod
    def create_mpc_documentation(
        glossary_term_urn: str,
        markdown: str,
    ) -> dict:
        """Create term documentation mpc"""
        return {
            "use_graphql": True,
            "operationName": "updateDescription",
            "variables": {
                "input": {
                    "description": markdown,
                    "resourceUrn": glossary_term_urn,
                }
            },
            "query": "mutation updateDescription($input: DescriptionUpdateInput!) {updateDescription(input: $input)}",
        }
