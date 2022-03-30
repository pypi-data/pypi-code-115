# Third-party imports
import grpc
import inspect

# Local imports
from qwilfish.base_oracle import BaseOracle
from qwilfish.results_db.dataclasses import ResultsDbTableDefinition
from qwilfish.results_db.dataclasses import ResultsDbReport
from qwilfish.results_db.dataclasses import ResultsDbDatatypes
from qwilfish.generated.feedback_interface_pb2 import (
    FeedbackDataRequest, FeedbackDataResponse, ProcessFeedbackData
)
from qwilfish.generated.feedback_interface_pb2_grpc import (
    FeedbackInterfaceStub
)

class GrpcOracle(BaseOracle):

    # Must agree with ProcessFeedbackData in feedback_interface.proto
    per_process_data = {
        "process_state": ResultsDbDatatypes.INTEGER,
        "cpu_usage": ResultsDbDatatypes.REAL,
        "mem_usage": ResultsDbDatatypes.INTEGER
    }

    def __init__(self, address="127.0.0.1", port=54545, worker=None,
                 process_list=None):
        super().__init__()
        self.address = address
        self.port = port
        self.worker = worker
        self.process_list = process_list
        self.reportTableDef = self.build_table()
        self.holdoff = False

    def report(self) -> ResultsDbReport:
        report = None

        with grpc.insecure_channel(self.address + ":" +
                                   str(self.port)) as channel:
            stub = FeedbackInterfaceStub(channel)

            request = FeedbackDataRequest()

            if self.worker:
                request.standalone_worker = self.worker

            if self.process_list:
                request.process_list.extend(self.process_list)

            process_data = stub.GetFeedbackData(request=request)

            columns = {}

            for pd in process_data.data:
                for k in GrpcOracle.per_process_data.keys():
                    columns.update({f"{pd.process_name}_{k}": getattr(pd, k)})

            # gRPC response was empty, possibly because there were to processes
            # to monitor. Request a holdoff to give them some time.
            if columns:
                self.holdoff = False
            else:
                self.holdoff = True

            # For all the processes where no monitored values where found,
            # report the state as unavailable, i.e. zero
            for pname in self.process_list:
                if not f"{pname}_process_state" in columns:
                    columns.update({f"{pname}_process_state": 0})

            report = ResultsDbReport(self.get_uid(), columns)

        return report

    def get_table(self) -> ResultsDbTableDefinition:
        return self.reportTableDef

    def needs_holdoff(self) -> bool:
        return self.holdoff

    def build_table(self):
        columns = {}

        for p in self.process_list:
            for k,v in GrpcOracle.per_process_data.items():
                columns.update({f"{p}_{k}": v})

        return ResultsDbTableDefinition(self.get_uid(), columns)
