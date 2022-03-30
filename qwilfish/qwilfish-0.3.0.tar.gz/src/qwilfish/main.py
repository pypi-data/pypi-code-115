# Standard lib imports
import importlib.resources
import logging
from logging.config import dictConfig

# Third-party imports
import yaml

# Local imports
from qwilfish.qwilfuzzer import QwilFuzzer
from qwilfish.session import start_session
from qwilfish.parser import parse_arguments
from qwilfish.service import start_service
from qwilfish.simple_client import start_simple_client
from qwilfish.grpc_oracle import GrpcOracle
from qwilfish.results_db.database import ResultsDb
import qwilfish.configuration # Conf files have their own subpackage
from qwilfish import session_builder
from qwilfish import plugin_loader

def main():
    args = parse_arguments("normal")

    log_conf = _logging_setup(args)
    log = logging.getLogger(__name__)
    dictConfig(log_conf)

    # Load plugins
    plugin_loader.load_plugins()

    # TODO Read conf into a dict
    session_conf = _read_session_conf(args)
    log.debug(f"Session configuration read: {session_conf}")

    # Choose a grammar to generate packets from
    grammar = session_builder.build_grammar(**session_conf["grammar"])

    # Create the fuzzer engine from the grammar
    fuzzer = QwilFuzzer(grammar, unguided_fuzzing=args.unguided)

    # Create a courier that delivers the fuzzy input by sending it on a socket
    courier = session_builder.build_courier(**session_conf["courier"])

    # Create the database for logging the test results, if enabled
    results_db = ResultsDb(args.outfile, args.dont_store_results)

    # Create a gRPC oracle if it was requested
    oracles = []
    if args.oracle == "grpc-oracle": # TODO plugin architecture for oracles
        oracles.append(GrpcOracle(args.grpc_address,
                                  args.grpc_port,
                                  args.worker,
                                  args.process_list))

    return start_session(fuzzer, courier, results_db, oracles, args.count)

def main_service():
    args = parse_arguments("service")

    log_conf = _logging_setup(args)
    dictConfig(log_conf)

    return start_service(args.address, args.port)

def main_simple_client():
    args = parse_arguments("simple-client")

    log_conf = _logging_setup(args)
    dictConfig(log_conf)

    return start_simple_client(args.message_type, args.address, args.port,
                               worker=args.worker,
                               process_list=args.process_list)

def _logging_setup(args):
    if args.log_conf:
        log_conf_src = args.log_conf
    else: # TODO importlib.resources.path will be deprecated in Python 3.11
        with importlib.resources.path(qwilfish.configuration,
                                      "default_log_conf.yaml") as p:
            log_conf_src = p

    with open(log_conf_src) as f:
        log_conf = yaml.safe_load(f)

    if args.debug:
        log_conf.get("handlers").get("console").update({"level": "DEBUG"})

    return log_conf

def _read_session_conf(args):
    if args.session_conf:
        session_conf_src = args.session_conf
    else: # TODO importlib.resources.path will be deprecated in Python 3.11
        with importlib.resources.path(qwilfish.configuration,
                                      "default_session_conf.yaml") as p:
            session_conf_src = p

    with open(session_conf_src) as f:
        session_conf = yaml.safe_load(f)

    return session_conf
