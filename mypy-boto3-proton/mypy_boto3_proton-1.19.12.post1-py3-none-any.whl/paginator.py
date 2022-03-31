"""
Type annotations for proton service client paginators.

[Open documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/)

Usage::

    ```python
    from boto3.session import Session

    from mypy_boto3_proton.client import ProtonClient
    from mypy_boto3_proton.paginator import (
        ListEnvironmentAccountConnectionsPaginator,
        ListEnvironmentTemplateVersionsPaginator,
        ListEnvironmentTemplatesPaginator,
        ListEnvironmentsPaginator,
        ListServiceInstancesPaginator,
        ListServiceTemplateVersionsPaginator,
        ListServiceTemplatesPaginator,
        ListServicesPaginator,
        ListTagsForResourcePaginator,
    )

    session = Session()
    client: ProtonClient = session.client("proton")

    list_environment_account_connections_paginator: ListEnvironmentAccountConnectionsPaginator = client.get_paginator("list_environment_account_connections")
    list_environment_template_versions_paginator: ListEnvironmentTemplateVersionsPaginator = client.get_paginator("list_environment_template_versions")
    list_environment_templates_paginator: ListEnvironmentTemplatesPaginator = client.get_paginator("list_environment_templates")
    list_environments_paginator: ListEnvironmentsPaginator = client.get_paginator("list_environments")
    list_service_instances_paginator: ListServiceInstancesPaginator = client.get_paginator("list_service_instances")
    list_service_template_versions_paginator: ListServiceTemplateVersionsPaginator = client.get_paginator("list_service_template_versions")
    list_service_templates_paginator: ListServiceTemplatesPaginator = client.get_paginator("list_service_templates")
    list_services_paginator: ListServicesPaginator = client.get_paginator("list_services")
    list_tags_for_resource_paginator: ListTagsForResourcePaginator = client.get_paginator("list_tags_for_resource")
    ```
"""
from typing import Generic, Iterator, Sequence, TypeVar

from botocore.paginate import PageIterator
from botocore.paginate import Paginator as Boto3Paginator

from .literals import (
    EnvironmentAccountConnectionRequesterAccountTypeType,
    EnvironmentAccountConnectionStatusType,
)
from .type_defs import (
    EnvironmentTemplateFilterTypeDef,
    ListEnvironmentAccountConnectionsOutputTypeDef,
    ListEnvironmentsOutputTypeDef,
    ListEnvironmentTemplatesOutputTypeDef,
    ListEnvironmentTemplateVersionsOutputTypeDef,
    ListServiceInstancesOutputTypeDef,
    ListServicesOutputTypeDef,
    ListServiceTemplatesOutputTypeDef,
    ListServiceTemplateVersionsOutputTypeDef,
    ListTagsForResourceOutputTypeDef,
    PaginatorConfigTypeDef,
)

__all__ = (
    "ListEnvironmentAccountConnectionsPaginator",
    "ListEnvironmentTemplateVersionsPaginator",
    "ListEnvironmentTemplatesPaginator",
    "ListEnvironmentsPaginator",
    "ListServiceInstancesPaginator",
    "ListServiceTemplateVersionsPaginator",
    "ListServiceTemplatesPaginator",
    "ListServicesPaginator",
    "ListTagsForResourcePaginator",
)


_ItemTypeDef = TypeVar("_ItemTypeDef")


class _PageIterator(Generic[_ItemTypeDef], PageIterator):
    def __iter__(self) -> Iterator[_ItemTypeDef]:
        """
        Proxy method to specify iterator item type.
        """


class ListEnvironmentAccountConnectionsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironmentAccountConnections)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmentaccountconnectionspaginator)
    """

    def paginate(
        self,
        *,
        requestedBy: EnvironmentAccountConnectionRequesterAccountTypeType,
        environmentName: str = ...,
        statuses: Sequence[EnvironmentAccountConnectionStatusType] = ...,
        PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListEnvironmentAccountConnectionsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironmentAccountConnections.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmentaccountconnectionspaginator)
        """


class ListEnvironmentTemplateVersionsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironmentTemplateVersions)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmenttemplateversionspaginator)
    """

    def paginate(
        self,
        *,
        templateName: str,
        majorVersion: str = ...,
        PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListEnvironmentTemplateVersionsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironmentTemplateVersions.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmenttemplateversionspaginator)
        """


class ListEnvironmentTemplatesPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironmentTemplates)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmenttemplatespaginator)
    """

    def paginate(
        self, *, PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListEnvironmentTemplatesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironmentTemplates.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmenttemplatespaginator)
        """


class ListEnvironmentsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironments)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmentspaginator)
    """

    def paginate(
        self,
        *,
        environmentTemplates: Sequence["EnvironmentTemplateFilterTypeDef"] = ...,
        PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListEnvironmentsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListEnvironments.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listenvironmentspaginator)
        """


class ListServiceInstancesPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServiceInstances)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listserviceinstancespaginator)
    """

    def paginate(
        self, *, serviceName: str = ..., PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListServiceInstancesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServiceInstances.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listserviceinstancespaginator)
        """


class ListServiceTemplateVersionsPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServiceTemplateVersions)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listservicetemplateversionspaginator)
    """

    def paginate(
        self,
        *,
        templateName: str,
        majorVersion: str = ...,
        PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListServiceTemplateVersionsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServiceTemplateVersions.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listservicetemplateversionspaginator)
        """


class ListServiceTemplatesPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServiceTemplates)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listservicetemplatespaginator)
    """

    def paginate(
        self, *, PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListServiceTemplatesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServiceTemplates.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listservicetemplatespaginator)
        """


class ListServicesPaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServices)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listservicespaginator)
    """

    def paginate(
        self, *, PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListServicesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListServices.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listservicespaginator)
        """


class ListTagsForResourcePaginator(Boto3Paginator):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListTagsForResource)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listtagsforresourcepaginator)
    """

    def paginate(
        self, *, resourceArn: str, PaginationConfig: "PaginatorConfigTypeDef" = ...
    ) -> _PageIterator[ListTagsForResourceOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/proton.html#Proton.Paginator.ListTagsForResource.paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_proton/paginators/#listtagsforresourcepaginator)
        """
