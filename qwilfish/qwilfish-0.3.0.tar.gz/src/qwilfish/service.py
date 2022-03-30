# Standard library imports
from concurrent import futures
import threading
import importlib.util
import sys
import os.path
import re
import logging

# Third-party imports
import grpc
import psutil

# Local imports
from qwilfish.generated.feedback_interface_pb2 import (
    FeedbackDataResponse, ProcessFeedbackData,
    TerminateResponse
)
from qwilfish.generated.feedback_interface_pb2_grpc import (
    FeedbackInterfaceServicer, add_FeedbackInterfaceServicer_to_server
)

log = logging.getLogger(__name__)

class QwilfishGrpcServicer(FeedbackInterfaceServicer):

    DEFAULT_STANDALONE_FUNC_NAME = "run"
    CACHE_COUNTER_MAX = 100

    def __init__(self, terminate_event):
        self.terminate_event = terminate_event
        # Due to the nature of psutil.cpu_usage(), we will use a cache
        # in order to get more stable readings.
        self.cpu_usage_cache = {}
        self.cache_refresh_counter = 0

    def GetFeedbackData(self, request, context):
        '''Dummy implementation, replace with your own code'''
        if request.standalone_worker: # Execute user-specified module
            response = self.handle_request_standalone(request, context)
        else: # Execute implementation native to this package
            response = self.handle_request(request, context)

        return response

    def Terminate(self, request, context):
        self.terminate_event.set()
        return TerminateResponse()

    def handle_request_standalone(self, request, context):
        # Assume standalone worker is on the form "/path/script.py[:func]"
        worker = request.standalone_worker.split(":")
        if len(worker) >= 2: # Function specified in standalone worker string
            file_path = worker[0]
            func_name = worker[1]
        elif len(worker) == 1: # No function was specified, assume default name
            file_path = worker[0]
            func_name = QwilfishGrpcServicer.DEFAULT_STANDALONE_FUNC_NAME

        # Load specified module for standalone worker
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Ensure function we're calling exists, is callable and returns a dict
        if not hasattr(module, func_name):
            raise AttributeError("Module '" + module_name +
                                 "' has no attribute '" + func_name + "'")

        func = getattr(module, func_name)

        if not callable(func):
            raise AttributeError("Attribute '" + func_name + "' in module '" +
                                 module_name + "' is not callable")

        retval = func(request.process_list)

        # Falsy values are ok, we interpret this as no monitorable processes
        # were found.
        if not retval:
            return FeedbackDataResponse()

        if not isinstance(retval, dict):
            raise AttributeError("'" + func_name + "' in module '" +
                                 module_name + "did not return a dict")

        process_data_list = []
        for pname, pdata in retval.items():
            # Assume retval is a "dict of dicts" where the first level is
            # process names, and the second is the data for every process name
            data = ProcessFeedbackData(process_name=pname)
            for dname,dval in pdata.items():
                setattr(data, dname, dval)
            process_data_list.append(data)

        return FeedbackDataResponse(data=process_data_list)

    def handle_request(self, request, context):
        '''
        Basic reference implementation. Replace with your own code or
        use a standalone worker script.
        '''
        response = FeedbackDataResponse()

        for pname in request.process_list:
            # Find executing process with matching name
            proc = None
            for p in psutil.process_iter(['name']):
                if p.info['name'] == pname:
                    proc = p
                    break # Assume first match is what we want

            # Initialize data for this process, assume it is unavailable
            pdata = ProcessFeedbackData(process_name=pname, process_state=0)

            if proc:
                try:
                    # Get virtual memory size
                    pdata.mem_usage = proc.memory_info().vms

                    # Check if it's time to refresh the cache
                    if self.cache_refresh_counter == \
                       QwilfishGrpcServicer.CACHE_COUNTER_MAX:
                        self.cache_refresh_counter = 0
                        self.cpu_usage_cache = {}
                    else:
                        self.cache_refresh_counter += 1

                    # pname was not in cache, do a reading!
                    if pname not in self.cpu_usage_cache.keys():
                        self.cpu_usage_cache[pname] = proc.cpu_percent()

                    # Use cached value
                    pdata.cpu_usage = self.cpu_usage_cache[pname]

                    # Process was available!
                    pdata.process_state = 1
                except (psutil.NoSuchProcess):
                    log.debug(f"Could not fetch info on process '{pname}'")
            else:
                log.debug(f"Could not find process '{pname}'")

            response.data.append(pdata)

        return response

def start_service(address, port):
    # Create objects for termination event and gRPC server
    terminate_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Create the qwilfish servicer and add it to the gRPC server
    add_FeedbackInterfaceServicer_to_server(
        QwilfishGrpcServicer(terminate_event), server)

    # Start the server
    server.add_insecure_port(address + ":" + str(port))
    server.start()
    log.info("Service started on port %s!", str(port))

    # Block this thread until a handler signals to terminate
    terminate_event.wait()
    log.info("Shutting down service on port %s...", str(port))

    # 1 second grace time then goodbye
    server.stop(1)
    log.info("Bye!")

    return 0
