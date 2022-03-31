"""
Type annotations for personalize service client paginators.

[Open documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/)

Usage::

    ```python
    from boto3.session import Session

    from mypy_boto3_personalize.client import PersonalizeClient
    from mypy_boto3_personalize.paginator import (
        ListBatchInferenceJobsPaginator,
        ListCampaignsPaginator,
        ListDatasetExportJobsPaginator,
        ListDatasetGroupsPaginator,
        ListDatasetImportJobsPaginator,
        ListDatasetsPaginator,
        ListEventTrackersPaginator,
        ListFiltersPaginator,
        ListRecipesPaginator,
        ListSchemasPaginator,
        ListSolutionVersionsPaginator,
        ListSolutionsPaginator,
    )

    session = Session()
    client: PersonalizeClient = session.client("personalize")

    list_batch_inference_jobs_paginator: ListBatchInferenceJobsPaginator = client.get_paginator("list_batch_inference_jobs")
    list_campaigns_paginator: ListCampaignsPaginator = client.get_paginator("list_campaigns")
    list_dataset_export_jobs_paginator: ListDatasetExportJobsPaginator = client.get_paginator("list_dataset_export_jobs")
    list_dataset_groups_paginator: ListDatasetGroupsPaginator = client.get_paginator("list_dataset_groups")
    list_dataset_import_jobs_paginator: ListDatasetImportJobsPaginator = client.get_paginator("list_dataset_import_jobs")
    list_datasets_paginator: ListDatasetsPaginator = client.get_paginator("list_datasets")
    list_event_trackers_paginator: ListEventTrackersPaginator = client.get_paginator("list_event_trackers")
    list_filters_paginator: ListFiltersPaginator = client.get_paginator("list_filters")
    list_recipes_paginator: ListRecipesPaginator = client.get_paginator("list_recipes")
    list_schemas_paginator: ListSchemasPaginator = client.get_paginator("list_schemas")
    list_solution_versions_paginator: ListSolutionVersionsPaginator = client.get_paginator("list_solution_versions")
    list_solutions_paginator: ListSolutionsPaginator = client.get_paginator("list_solutions")
    ```
"""
import sys
from typing import Generic, Iterator, TypeVar

from botocore.paginate import PageIterator
from botocore.paginate import Paginator as Boto3Paginator

from .type_defs import (
    ListBatchInferenceJobsResponseTypeDef,
    ListCampaignsResponseTypeDef,
    ListDatasetExportJobsResponseTypeDef,
    ListDatasetGroupsResponseTypeDef,
    ListDatasetImportJobsResponseTypeDef,
    ListDatasetsResponseTypeDef,
    ListEventTrackersResponseTypeDef,
    ListFiltersResponseTypeDef,
    ListRecipesResponseTypeDef,
    ListSchemasResponseTypeDef,
    ListSolutionsResponseTypeDef,
    ListSolutionVersionsResponseTypeDef,
    PaginatorConfigTypeDef,
)

if sys.version_info >= (3, 9):
    from typing import Literal
else:
    from typing_extensions import Literal


__all__ = (
    "ListBatchInferenceJobsPaginator",
    "ListCampaignsPaginator",
    "ListDatasetExportJobsPaginator",
    "ListDatasetGroupsPaginator",
    "ListDatasetImportJobsPaginator",
    "ListDatasetsPaginator",
    "ListEventTrackersPaginator",
    "ListFiltersPaginator",
    "ListRecipesPaginator",
    "ListSchemasPaginator",
    "ListSolutionVersionsPaginator",
    "ListSolutionsPaginator",
)


_ItemTypeDef = TypeVar("_ItemTypeDef")


class _PageIterator(Generic[_ItemTypeDef], PageIterator):
    def __iter__(self) -> Iterator[_ItemTypeDef]:
        """
        Proxy method to specify iterator item type.
        """


class ListBatchInferenceJobsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListBatchInferenceJobs)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listbatchinferencejobspaginator)
    """

    def paginate(
        self, *, solutionVersionArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListBatchInferenceJobsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListBatchInferenceJobs.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listbatchinferencejobspaginator)
        """


class ListCampaignsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListCampaigns)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listcampaignspaginator)
    """

    def paginate(
        self, *, solutionArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListCampaignsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListCampaigns.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listcampaignspaginator)
        """


class ListDatasetExportJobsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasetExportJobs)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetexportjobspaginator)
    """

    def paginate(
        self, *, datasetArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListDatasetExportJobsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasetExportJobs.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetexportjobspaginator)
        """


class ListDatasetGroupsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasetGroups)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetgroupspaginator)
    """

    def paginate(
        self, *, PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListDatasetGroupsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasetGroups.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetgroupspaginator)
        """


class ListDatasetImportJobsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasetImportJobs)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetimportjobspaginator)
    """

    def paginate(
        self, *, datasetArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListDatasetImportJobsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasetImportJobs.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetimportjobspaginator)
        """


class ListDatasetsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasets)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetspaginator)
    """

    def paginate(
        self, *, datasetGroupArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListDatasetsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListDatasets.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listdatasetspaginator)
        """


class ListEventTrackersPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListEventTrackers)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listeventtrackerspaginator)
    """

    def paginate(
        self, *, datasetGroupArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListEventTrackersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListEventTrackers.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listeventtrackerspaginator)
        """


class ListFiltersPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListFilters)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listfilterspaginator)
    """

    def paginate(
        self, *, datasetGroupArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListFiltersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListFilters.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listfilterspaginator)
        """


class ListRecipesPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListRecipes)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listrecipespaginator)
    """

    def paginate(
        self,
        *,
        recipeProvider: Literal["SERVICE"] = ...,
        PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListRecipesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListRecipes.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listrecipespaginator)
        """


class ListSchemasPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListSchemas)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listschemaspaginator)
    """

    def paginate(
        self, *, PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListSchemasResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListSchemas.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listschemaspaginator)
        """


class ListSolutionVersionsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListSolutionVersions)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listsolutionversionspaginator)
    """

    def paginate(
        self, *, solutionArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListSolutionVersionsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListSolutionVersions.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listsolutionversionspaginator)
        """


class ListSolutionsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListSolutions)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listsolutionspaginator)
    """

    def paginate(
        self, *, datasetGroupArn: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListSolutionsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/personalize.html#Personalize.Paginator.ListSolutions.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_personalize/paginators/#listsolutionspaginator)
        """
