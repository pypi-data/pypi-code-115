"""
Type annotations for networkmanager service client.

[Open documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/)

Usage::

    ```python
    from boto3.session import Session
    from mypy_boto3_networkmanager.client import NetworkManagerClient

    session = Session()
    client: NetworkManagerClient = session.client("networkmanager")
    ```
"""
import sys
from typing import Any, Dict, Mapping, Sequence, Type, overload

from botocore.client import BaseClient, ClientMeta

from .literals import RouteStateType, RouteTypeType
from .paginator import (
    DescribeGlobalNetworksPaginator,
    GetConnectionsPaginator,
    GetCustomerGatewayAssociationsPaginator,
    GetDevicesPaginator,
    GetLinkAssociationsPaginator,
    GetLinksPaginator,
    GetNetworkResourceCountsPaginator,
    GetNetworkResourceRelationshipsPaginator,
    GetNetworkResourcesPaginator,
    GetNetworkTelemetryPaginator,
    GetSitesPaginator,
    GetTransitGatewayConnectPeerAssociationsPaginator,
    GetTransitGatewayRegistrationsPaginator,
)
from .type_defs import (
    AssociateCustomerGatewayResponseTypeDef,
    AssociateLinkResponseTypeDef,
    AssociateTransitGatewayConnectPeerResponseTypeDef,
    AWSLocationTypeDef,
    BandwidthTypeDef,
    CreateConnectionResponseTypeDef,
    CreateDeviceResponseTypeDef,
    CreateGlobalNetworkResponseTypeDef,
    CreateLinkResponseTypeDef,
    CreateSiteResponseTypeDef,
    DeleteConnectionResponseTypeDef,
    DeleteDeviceResponseTypeDef,
    DeleteGlobalNetworkResponseTypeDef,
    DeleteLinkResponseTypeDef,
    DeleteSiteResponseTypeDef,
    DeregisterTransitGatewayResponseTypeDef,
    DescribeGlobalNetworksResponseTypeDef,
    DisassociateCustomerGatewayResponseTypeDef,
    DisassociateLinkResponseTypeDef,
    DisassociateTransitGatewayConnectPeerResponseTypeDef,
    GetConnectionsResponseTypeDef,
    GetCustomerGatewayAssociationsResponseTypeDef,
    GetDevicesResponseTypeDef,
    GetLinkAssociationsResponseTypeDef,
    GetLinksResponseTypeDef,
    GetNetworkResourceCountsResponseTypeDef,
    GetNetworkResourceRelationshipsResponseTypeDef,
    GetNetworkResourcesResponseTypeDef,
    GetNetworkRoutesResponseTypeDef,
    GetNetworkTelemetryResponseTypeDef,
    GetRouteAnalysisResponseTypeDef,
    GetSitesResponseTypeDef,
    GetTransitGatewayConnectPeerAssociationsResponseTypeDef,
    GetTransitGatewayRegistrationsResponseTypeDef,
    ListTagsForResourceResponseTypeDef,
    LocationTypeDef,
    RegisterTransitGatewayResponseTypeDef,
    RouteAnalysisEndpointOptionsSpecificationTypeDef,
    RouteTableIdentifierTypeDef,
    StartRouteAnalysisResponseTypeDef,
    TagTypeDef,
    UpdateConnectionResponseTypeDef,
    UpdateDeviceResponseTypeDef,
    UpdateGlobalNetworkResponseTypeDef,
    UpdateLinkResponseTypeDef,
    UpdateNetworkResourceMetadataResponseTypeDef,
    UpdateSiteResponseTypeDef,
)

if sys.version_info >= (3, 9):
    from typing import Literal
else:
    from typing_extensions import Literal


__all__ = ("NetworkManagerClient",)


class BotocoreClientError(BaseException):
    MSG_TEMPLATE: str

    def __init__(self, error_response: Mapping[str, Any], operation_name: str) -> None:
        self.response: Dict[str, Any]
        self.operation_name: str


class Exceptions:
    AccessDeniedException: Type[BotocoreClientError]
    ClientError: Type[BotocoreClientError]
    ConflictException: Type[BotocoreClientError]
    InternalServerException: Type[BotocoreClientError]
    ResourceNotFoundException: Type[BotocoreClientError]
    ServiceQuotaExceededException: Type[BotocoreClientError]
    ThrottlingException: Type[BotocoreClientError]
    ValidationException: Type[BotocoreClientError]


class NetworkManagerClient(BaseClient):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client)
    [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/)
    """

    meta: ClientMeta

    @property
    def exceptions(self) -> Exceptions:
        """
        NetworkManagerClient exceptions.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.exceptions)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#exceptions)
        """

    def associate_customer_gateway(
        self, *, CustomerGatewayArn: str, GlobalNetworkId: str, DeviceId: str, LinkId: str = ...
    ) -> AssociateCustomerGatewayResponseTypeDef:
        """
        Associates a customer gateway with a device and optionally, with a link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.associate_customer_gateway)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#associate_customer_gateway)
        """

    def associate_link(
        self, *, GlobalNetworkId: str, DeviceId: str, LinkId: str
    ) -> AssociateLinkResponseTypeDef:
        """
        Associates a link to a device.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.associate_link)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#associate_link)
        """

    def associate_transit_gateway_connect_peer(
        self,
        *,
        GlobalNetworkId: str,
        TransitGatewayConnectPeerArn: str,
        DeviceId: str,
        LinkId: str = ...
    ) -> AssociateTransitGatewayConnectPeerResponseTypeDef:
        """
        Associates a transit gateway Connect peer with a device, and optionally, with a
        link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.associate_transit_gateway_connect_peer)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#associate_transit_gateway_connect_peer)
        """

    def can_paginate(self, operation_name: str) -> bool:
        """
        Check if an operation can be paginated.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.can_paginate)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#can_paginate)
        """

    def create_connection(
        self,
        *,
        GlobalNetworkId: str,
        DeviceId: str,
        ConnectedDeviceId: str,
        LinkId: str = ...,
        ConnectedLinkId: str = ...,
        Description: str = ...,
        Tags: Sequence["TagTypeDef"] = ...
    ) -> CreateConnectionResponseTypeDef:
        """
        Creates a connection between two devices.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.create_connection)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#create_connection)
        """

    def create_device(
        self,
        *,
        GlobalNetworkId: str,
        AWSLocation: "AWSLocationTypeDef" = ...,
        Description: str = ...,
        Type: str = ...,
        Vendor: str = ...,
        Model: str = ...,
        SerialNumber: str = ...,
        Location: "LocationTypeDef" = ...,
        SiteId: str = ...,
        Tags: Sequence["TagTypeDef"] = ...
    ) -> CreateDeviceResponseTypeDef:
        """
        Creates a new device in a global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.create_device)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#create_device)
        """

    def create_global_network(
        self, *, Description: str = ..., Tags: Sequence["TagTypeDef"] = ...
    ) -> CreateGlobalNetworkResponseTypeDef:
        """
        Creates a new, empty global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.create_global_network)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#create_global_network)
        """

    def create_link(
        self,
        *,
        GlobalNetworkId: str,
        Bandwidth: "BandwidthTypeDef",
        SiteId: str,
        Description: str = ...,
        Type: str = ...,
        Provider: str = ...,
        Tags: Sequence["TagTypeDef"] = ...
    ) -> CreateLinkResponseTypeDef:
        """
        Creates a new link for a specified site.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.create_link)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#create_link)
        """

    def create_site(
        self,
        *,
        GlobalNetworkId: str,
        Description: str = ...,
        Location: "LocationTypeDef" = ...,
        Tags: Sequence["TagTypeDef"] = ...
    ) -> CreateSiteResponseTypeDef:
        """
        Creates a new site in a global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.create_site)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#create_site)
        """

    def delete_connection(
        self, *, GlobalNetworkId: str, ConnectionId: str
    ) -> DeleteConnectionResponseTypeDef:
        """
        Deletes the specified connection in your global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.delete_connection)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#delete_connection)
        """

    def delete_device(self, *, GlobalNetworkId: str, DeviceId: str) -> DeleteDeviceResponseTypeDef:
        """
        Deletes an existing device.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.delete_device)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#delete_device)
        """

    def delete_global_network(self, *, GlobalNetworkId: str) -> DeleteGlobalNetworkResponseTypeDef:
        """
        Deletes an existing global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.delete_global_network)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#delete_global_network)
        """

    def delete_link(self, *, GlobalNetworkId: str, LinkId: str) -> DeleteLinkResponseTypeDef:
        """
        Deletes an existing link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.delete_link)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#delete_link)
        """

    def delete_site(self, *, GlobalNetworkId: str, SiteId: str) -> DeleteSiteResponseTypeDef:
        """
        Deletes an existing site.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.delete_site)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#delete_site)
        """

    def deregister_transit_gateway(
        self, *, GlobalNetworkId: str, TransitGatewayArn: str
    ) -> DeregisterTransitGatewayResponseTypeDef:
        """
        Deregisters a transit gateway from your global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.deregister_transit_gateway)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#deregister_transit_gateway)
        """

    def describe_global_networks(
        self, *, GlobalNetworkIds: Sequence[str] = ..., MaxResults: int = ..., NextToken: str = ...
    ) -> DescribeGlobalNetworksResponseTypeDef:
        """
        Describes one or more global networks.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.describe_global_networks)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#describe_global_networks)
        """

    def disassociate_customer_gateway(
        self, *, GlobalNetworkId: str, CustomerGatewayArn: str
    ) -> DisassociateCustomerGatewayResponseTypeDef:
        """
        Disassociates a customer gateway from a device and a link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.disassociate_customer_gateway)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#disassociate_customer_gateway)
        """

    def disassociate_link(
        self, *, GlobalNetworkId: str, DeviceId: str, LinkId: str
    ) -> DisassociateLinkResponseTypeDef:
        """
        Disassociates an existing device from a link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.disassociate_link)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#disassociate_link)
        """

    def disassociate_transit_gateway_connect_peer(
        self, *, GlobalNetworkId: str, TransitGatewayConnectPeerArn: str
    ) -> DisassociateTransitGatewayConnectPeerResponseTypeDef:
        """
        Disassociates a transit gateway Connect peer from a device and link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.disassociate_transit_gateway_connect_peer)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#disassociate_transit_gateway_connect_peer)
        """

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: Mapping[str, Any] = ...,
        ExpiresIn: int = 3600,
        HttpMethod: str = ...,
    ) -> str:
        """
        Generate a presigned url given a client, its method, and arguments.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.generate_presigned_url)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#generate_presigned_url)
        """

    def get_connections(
        self,
        *,
        GlobalNetworkId: str,
        ConnectionIds: Sequence[str] = ...,
        DeviceId: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetConnectionsResponseTypeDef:
        """
        Gets information about one or more of your connections in a global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_connections)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_connections)
        """

    def get_customer_gateway_associations(
        self,
        *,
        GlobalNetworkId: str,
        CustomerGatewayArns: Sequence[str] = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetCustomerGatewayAssociationsResponseTypeDef:
        """
        Gets the association information for customer gateways that are associated with
        devices and links in your global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_customer_gateway_associations)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_customer_gateway_associations)
        """

    def get_devices(
        self,
        *,
        GlobalNetworkId: str,
        DeviceIds: Sequence[str] = ...,
        SiteId: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetDevicesResponseTypeDef:
        """
        Gets information about one or more of your devices in a global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_devices)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_devices)
        """

    def get_link_associations(
        self,
        *,
        GlobalNetworkId: str,
        DeviceId: str = ...,
        LinkId: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetLinkAssociationsResponseTypeDef:
        """
        Gets the link associations for a device or a link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_link_associations)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_link_associations)
        """

    def get_links(
        self,
        *,
        GlobalNetworkId: str,
        LinkIds: Sequence[str] = ...,
        SiteId: str = ...,
        Type: str = ...,
        Provider: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetLinksResponseTypeDef:
        """
        Gets information about one or more links in a specified global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_links)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_links)
        """

    def get_network_resource_counts(
        self,
        *,
        GlobalNetworkId: str,
        ResourceType: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetNetworkResourceCountsResponseTypeDef:
        """
        Gets the count of network resources, by resource type, for the specified global
        network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_network_resource_counts)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_network_resource_counts)
        """

    def get_network_resource_relationships(
        self,
        *,
        GlobalNetworkId: str,
        RegisteredGatewayArn: str = ...,
        AwsRegion: str = ...,
        AccountId: str = ...,
        ResourceType: str = ...,
        ResourceArn: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetNetworkResourceRelationshipsResponseTypeDef:
        """
        Gets the network resource relationships for the specified global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_network_resource_relationships)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_network_resource_relationships)
        """

    def get_network_resources(
        self,
        *,
        GlobalNetworkId: str,
        RegisteredGatewayArn: str = ...,
        AwsRegion: str = ...,
        AccountId: str = ...,
        ResourceType: str = ...,
        ResourceArn: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetNetworkResourcesResponseTypeDef:
        """
        Describes the network resources for the specified global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_network_resources)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_network_resources)
        """

    def get_network_routes(
        self,
        *,
        GlobalNetworkId: str,
        RouteTableIdentifier: "RouteTableIdentifierTypeDef",
        ExactCidrMatches: Sequence[str] = ...,
        LongestPrefixMatches: Sequence[str] = ...,
        SubnetOfMatches: Sequence[str] = ...,
        SupernetOfMatches: Sequence[str] = ...,
        PrefixListIds: Sequence[str] = ...,
        States: Sequence[RouteStateType] = ...,
        Types: Sequence[RouteTypeType] = ...,
        DestinationFilters: Mapping[str, Sequence[str]] = ...
    ) -> GetNetworkRoutesResponseTypeDef:
        """
        Gets the network routes of the specified global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_network_routes)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_network_routes)
        """

    def get_network_telemetry(
        self,
        *,
        GlobalNetworkId: str,
        RegisteredGatewayArn: str = ...,
        AwsRegion: str = ...,
        AccountId: str = ...,
        ResourceType: str = ...,
        ResourceArn: str = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetNetworkTelemetryResponseTypeDef:
        """
        Gets the network telemetry of the specified global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_network_telemetry)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_network_telemetry)
        """

    def get_route_analysis(
        self, *, GlobalNetworkId: str, RouteAnalysisId: str
    ) -> GetRouteAnalysisResponseTypeDef:
        """
        Gets information about the specified route analysis.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_route_analysis)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_route_analysis)
        """

    def get_sites(
        self,
        *,
        GlobalNetworkId: str,
        SiteIds: Sequence[str] = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetSitesResponseTypeDef:
        """
        Gets information about one or more of your sites in a global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_sites)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_sites)
        """

    def get_transit_gateway_connect_peer_associations(
        self,
        *,
        GlobalNetworkId: str,
        TransitGatewayConnectPeerArns: Sequence[str] = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetTransitGatewayConnectPeerAssociationsResponseTypeDef:
        """
        Gets information about one or more of your transit gateway Connect peer
        associations in a global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_transit_gateway_connect_peer_associations)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_transit_gateway_connect_peer_associations)
        """

    def get_transit_gateway_registrations(
        self,
        *,
        GlobalNetworkId: str,
        TransitGatewayArns: Sequence[str] = ...,
        MaxResults: int = ...,
        NextToken: str = ...
    ) -> GetTransitGatewayRegistrationsResponseTypeDef:
        """
        Gets information about the transit gateway registrations in a specified global
        network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_transit_gateway_registrations)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_transit_gateway_registrations)
        """

    def list_tags_for_resource(self, *, ResourceArn: str) -> ListTagsForResourceResponseTypeDef:
        """
        Lists the tags for a specified resource.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.list_tags_for_resource)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#list_tags_for_resource)
        """

    def register_transit_gateway(
        self, *, GlobalNetworkId: str, TransitGatewayArn: str
    ) -> RegisterTransitGatewayResponseTypeDef:
        """
        Registers a transit gateway in your global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.register_transit_gateway)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#register_transit_gateway)
        """

    def start_route_analysis(
        self,
        *,
        GlobalNetworkId: str,
        Source: "RouteAnalysisEndpointOptionsSpecificationTypeDef",
        Destination: "RouteAnalysisEndpointOptionsSpecificationTypeDef",
        IncludeReturnPath: bool = ...,
        UseMiddleboxes: bool = ...
    ) -> StartRouteAnalysisResponseTypeDef:
        """
        Starts analyzing the routing path between the specified source and destination.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.start_route_analysis)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#start_route_analysis)
        """

    def tag_resource(self, *, ResourceArn: str, Tags: Sequence["TagTypeDef"]) -> Dict[str, Any]:
        """
        Tags a specified resource.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.tag_resource)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#tag_resource)
        """

    def untag_resource(self, *, ResourceArn: str, TagKeys: Sequence[str]) -> Dict[str, Any]:
        """
        Removes tags from a specified resource.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.untag_resource)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#untag_resource)
        """

    def update_connection(
        self,
        *,
        GlobalNetworkId: str,
        ConnectionId: str,
        LinkId: str = ...,
        ConnectedLinkId: str = ...,
        Description: str = ...
    ) -> UpdateConnectionResponseTypeDef:
        """
        Updates the information for an existing connection.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.update_connection)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#update_connection)
        """

    def update_device(
        self,
        *,
        GlobalNetworkId: str,
        DeviceId: str,
        AWSLocation: "AWSLocationTypeDef" = ...,
        Description: str = ...,
        Type: str = ...,
        Vendor: str = ...,
        Model: str = ...,
        SerialNumber: str = ...,
        Location: "LocationTypeDef" = ...,
        SiteId: str = ...
    ) -> UpdateDeviceResponseTypeDef:
        """
        Updates the details for an existing device.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.update_device)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#update_device)
        """

    def update_global_network(
        self, *, GlobalNetworkId: str, Description: str = ...
    ) -> UpdateGlobalNetworkResponseTypeDef:
        """
        Updates an existing global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.update_global_network)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#update_global_network)
        """

    def update_link(
        self,
        *,
        GlobalNetworkId: str,
        LinkId: str,
        Description: str = ...,
        Type: str = ...,
        Bandwidth: "BandwidthTypeDef" = ...,
        Provider: str = ...
    ) -> UpdateLinkResponseTypeDef:
        """
        Updates the details for an existing link.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.update_link)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#update_link)
        """

    def update_network_resource_metadata(
        self, *, GlobalNetworkId: str, ResourceArn: str, Metadata: Mapping[str, str]
    ) -> UpdateNetworkResourceMetadataResponseTypeDef:
        """
        Updates the resource metadata for the specified global network.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.update_network_resource_metadata)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#update_network_resource_metadata)
        """

    def update_site(
        self,
        *,
        GlobalNetworkId: str,
        SiteId: str,
        Description: str = ...,
        Location: "LocationTypeDef" = ...
    ) -> UpdateSiteResponseTypeDef:
        """
        Updates the information for an existing site.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.update_site)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#update_site)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["describe_global_networks"]
    ) -> DescribeGlobalNetworksPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(self, operation_name: Literal["get_connections"]) -> GetConnectionsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_customer_gateway_associations"]
    ) -> GetCustomerGatewayAssociationsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(self, operation_name: Literal["get_devices"]) -> GetDevicesPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_link_associations"]
    ) -> GetLinkAssociationsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(self, operation_name: Literal["get_links"]) -> GetLinksPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_network_resource_counts"]
    ) -> GetNetworkResourceCountsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_network_resource_relationships"]
    ) -> GetNetworkResourceRelationshipsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_network_resources"]
    ) -> GetNetworkResourcesPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_network_telemetry"]
    ) -> GetNetworkTelemetryPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(self, operation_name: Literal["get_sites"]) -> GetSitesPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_transit_gateway_connect_peer_associations"]
    ) -> GetTransitGatewayConnectPeerAssociationsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """

    @overload
    def get_paginator(
        self, operation_name: Literal["get_transit_gateway_registrations"]
    ) -> GetTransitGatewayRegistrationsPaginator:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/networkmanager.html#NetworkManager.Client.get_paginator)
        [Show boto3-stubs documentation](https://vemel.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/client/#get_paginator)
        """
