from typing import Iterable

from python.contek_viper.execution.execution_service_pb2 import SubmitTargetPositionsRequest
from python.contek_viper.execution.execution_service_pb2_grpc import ExecutionServiceStub
from python.contek_viper.execution.target_position_pb2 import TargetPosition


class AccountSession:

    def __init__(
        self,
        exchange: str,
        account: str,
        stub: ExecutionServiceStub,
    ) -> None:
        self._exchange = exchange
        self._account = account
        self._stub = stub

    def submit(self, target_positions: Iterable[TargetPosition]) -> None:
        self._stub.SubmitTargetPositions(
            SubmitTargetPositionsRequest(
                target_position=list(target_positions),
                exchange=self._exchange,
                account=self._account,
            ))
