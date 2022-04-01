"""

SporeStack API request/response models

"""


from typing import List, Optional

from pydantic import BaseModel

from .models import NetworkInterface, Payment


class TokenEnable:
    url = "/token/{token}/enable"
    method = "POST"

    class Request(BaseModel):
        currency: str
        dollars: int

    class Response(BaseModel):
        token: str
        payment: Payment


class TokenAdd:
    url = "/token/{token}/add"
    method = "POST"

    class Request(BaseModel):
        currency: str
        dollars: int

    class Response(BaseModel):
        token: str
        payment: Payment


class TokenBalance:
    url = "/token/{token}/balance"
    method = "GET"

    class Response(BaseModel):
        token: str
        cents: int
        usd: str


class ServerLaunch:
    url = "/server/{machine_id}/launch"
    method = "POST"

    class Request(BaseModel):
        machine_id: str
        days: int
        currency: str
        flavor: str
        ssh_key: str
        operating_system: str
        region: Optional[str]
        organization: Optional[str]
        settlement_token: Optional[str]
        affiliate_amount: Optional[int]
        affiliate_token: Optional[str]

    class Response(BaseModel):
        created_at: Optional[int]
        payment: Payment
        expiration: Optional[int]
        machine_id: str
        network_interfaces: List[NetworkInterface]
        region: str
        latest_api_version: int
        created: bool
        paid: bool
        warning: Optional[str]
        txid: Optional[str]
        operating_system: str
        flavor: str


class ServerTopup:
    url = "/server/{machine_id}/topup"
    method = "POST"

    class Request(BaseModel):
        machine_id: str
        days: int
        currency: str
        settlement_token: Optional[str]
        affiliate_amount: Optional[int]
        affiliate_token: Optional[str]

    class Response(BaseModel):
        machine_id: str
        payment: Payment
        paid: bool
        warning: Optional[str]
        expiration: int
        txid: Optional[str]
        latest_api_version: int


class ServerInfo:
    url = "/server/{machine_id}/info"
    method = "GET"

    class Response(BaseModel):
        created_at: int
        expiration: int
        running: bool
        machine_id: str
        network_interfaces: List[NetworkInterface]
        region: str


class ServerStart:
    url = "/server/{machine_id}/start"
    method = "POST"


class ServerStop:
    url = "/server/{machine_id}/stop"
    method = "POST"


class ServerDelete:
    url = "/server/{machine_id}/delete"
    method = "POST"


class ServerRebuild:
    url = "/server/{machine_id}/rebuild"
    method = "POST"
