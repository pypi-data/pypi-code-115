import time
from typing import List, Iterator, Dict

import datahub.emitter.mce_builder as builder
import datahub.metadata.schema_classes as models
from datahub.emitter.mce_builder import make_dataset_urn, make_tag_urn
from datahub.metadata.schema_classes import (
    AuditStampClass,
    EditableSchemaFieldInfoClass,
    EditableSchemaMetadataClass,
    GlobalTagsClass,
)
from datahub.metadata.schema_classes import TagAssociationClass

from dh_client import utils
from dh_client.entities import Entity


class Tag(Entity):
    """This class allows you to modify tags.

    Examples:

    The standard way:

        >>> client.tag.upsert(name="foo")  # create a tag
        >>> client.tag.upsert(name="foo", add_to=[{"dataset": "dataset_x", "column": "column_y"}])

    Modify dataset using a JSON file:

        $ ls *.json
        tags.json
        $ cat glossary-terms.json
        [{
            "name": "foo",
            "add_to": [
               {"dataset": "netdata-analytics-bi.posthog.user360_latest", "column": "posthog_first_distinct_id"}
            ]
        }]
        >>> client.tag.upsert(file_pattern="*.json")
    """

    entity_type: str = "tag"
    aspect_name: str = "tagProperties"

    def _create_mpc(
        self, name: str, description: str = "", add_to: List[Dict[str, str]] = None
    ) -> List[dict]:
        """Create a tag mpc.

        Args:
            name: tag name.
            description: tag description.
            add_to: Add tag to list of entities.

        Returns: A list with a single mpc dictionary.
        """
        tag_urn = make_tag_urn(name)

        mpcs = [
            dict(
                entityType=Tag.entity_type,
                entityUrn=tag_urn,
                aspectName=Tag.aspect_name,
                aspect=models.TagPropertiesClass(name=name, description=description),
            )
        ]
        if add_to:
            mpcs.extend(list(self.create_mpc_column_association(tag_urn, add_to)))

        return mpcs

    @staticmethod
    def create_mpc_association(
        entity_type: str, entity_urn: str, tags: List[str]
    ) -> dict:
        """Create an MPC tags association dictionary.

        Args:
            entity_type: The entity type.
            entity_urn: The entity URN.
            tags: The list of tags.

        Return: The MPC dictionary.
        """
        return Tag._create_mpc_dict(
            entity_type,
            entity_urn,
            "globalTags",
            models.GlobalTagsClass(
                tags=[
                    models.TagAssociationClass(builder.make_tag_urn(tag))
                    for tag in tags
                ]
            ),
        )

    def create_mpc_column_association(
        self, tag_to_add: str, dataset_columns: List[Dict[str, str]]
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

            tag_association_to_add = TagAssociationClass(tag=tag_to_add)
            tags_aspect_to_set = GlobalTagsClass(tags=[tag_association_to_add])
            field_info_to_set = EditableSchemaFieldInfoClass(
                fieldPath=column, globalTags=tags_aspect_to_set
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
                        if fieldInfo.globalTags:
                            if tag_to_add not in [
                                x.tag for x in fieldInfo.globalTags.tags
                            ]:
                                # this tag is not present
                                fieldInfo.globalTags.tags.append(tag_association_to_add)
                                need_write = True
                        else:
                            fieldInfo.globalTags = tags_aspect_to_set
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
                now = int(time.time() * 1000)  # milliseconds since epoch
                current_timestamp = AuditStampClass(
                    time=now, actor=self.emmiter.datahub_actor
                )
                current_editable_schema_metadata = EditableSchemaMetadataClass(
                    editableSchemaFieldInfo=[field_info_to_set],
                    created=current_timestamp,
                )
                need_write = True

            if need_write:
                yield dict(
                    entityType="dataset",
                    entityUrn=dataset_urn,
                    aspectName="editableSchemaMetadata",
                    aspect=current_editable_schema_metadata,
                    use_graph=True,
                )
