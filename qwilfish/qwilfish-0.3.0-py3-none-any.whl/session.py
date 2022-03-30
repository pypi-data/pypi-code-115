# Standard lib imports
import datetime
import logging
import time

# Local imports
from qwilfish.results_db.dataclasses import ResultsDbDatatypes
from qwilfish.results_db.dataclasses import ResultsDbTableDefinition
from qwilfish.results_db.dataclasses import ResultsDbReport

log = logging.getLogger(__name__)

RESULT_FAIL = "'FAIL'" # Test was executed successfully, but SUT failed somehow
RESULT_PASS = "'PASS'" # Test was executed successfully, and SUT withstood 
RESULT_UNKN = "'UNKN'" # Test was not executed successfully, result unknown
RESULT_DRYR = "'DRYR'" # Test was a dry run, an oracle is requesting holdoff

MAIN_TABLE_NAME = "main_results"
CASENO_KEY = "caseno"
TIMESTAMP_KEY = "timestamp"
INPUT_KEY = "input"
RESULT_KEY = "result"

TAKE_BREAK_TIME = 3 # A few seconds break if needed

session_main_result_table = ResultsDbTableDefinition(MAIN_TABLE_NAME,
    {
        CASENO_KEY:    ResultsDbDatatypes.INTEGER, # Testcase number
        TIMESTAMP_KEY: ResultsDbDatatypes.TEXT,    # Timestamp for the testcase
        INPUT_KEY :    ResultsDbDatatypes.TEXT,    # Input used in the testcase
        RESULT_KEY:    ResultsDbDatatypes.TEXT     # Testcase result
    }
)

def start_session(fuzzer, courier, results_db, oracles, n_test_cases):
    log.info("Session started at %s", str(datetime.datetime.now()))
    timestamp_start = time.time()

    # Add columns for the probablistic weights in the grammar to the main table
    for k in fuzzer.get_probabilities().keys():
        new_col = {prob_key_string(k): ResultsDbDatatypes.REAL}
        log.info(f"Adding new column for probability: {new_col}")
        session_main_result_table.columns.update(new_col)

    # Initialize the courier
    courier.init()

    # Open a connection to the DB and create the main results table
    results_db.open()
    results_db.create_table(session_main_result_table)

    # Create a table for every oracle in use for storing their reports
    for o in oracles:
        table = o.get_table()
        table.columns.update({CASENO_KEY: ResultsDbDatatypes.INTEGER})
        results_db.create_table(table)

    for i in range(1, n_test_cases+1):
        # Check if any oracles are requesting a holdoff
        is_dryrun = any(filter(lambda o: o.needs_holdoff(), oracles))

        # Place to store the oracle reports
        oracle_reports = []

        # Set to true if input delivery was attempted and successful
        delivery_ok = False

        # Prepare the main results table for this test case
        main_results = ResultsDbReport(MAIN_TABLE_NAME, {})
        main_results.columns.update({CASENO_KEY: i})
        main_results.columns.update(
            {TIMESTAMP_KEY: f"'{str(time.time() - timestamp_start)}'"})

        # Add the probabilistic weights used for generation
        for k,v in fuzzer.get_probabilities().items():
            main_results.columns.update({prob_key_string(k): f"'{str(v)}'"})

        if is_dryrun: # An oracle has requested holdoff, this will be a dry run
            pass
        else: # No oracles requested holdoff after last iteration
            fuzz_data, fuzz_metadata = fuzzer.fuzz()
            delivery_ok = courier.deliver(fuzz_data)
            main_results.columns.update({INPUT_KEY: f"'{str(fuzz_data)}'"})

        for oracle in oracles:
            report = oracle.report()
            report.columns.update({CASENO_KEY: i})
            oracle_reports.append(report)

        if is_dryrun: # This was a dry run
            main_results.columns.update({RESULT_KEY: RESULT_DRYR})
        elif delivery_ok:
            main_results.columns.update({RESULT_KEY: arbiter(oracle_reports)})
            update_grammar(fuzz_metadata, fuzzer, oracle_reports)
        else: # Wasn't a dry run but failed to deliver input data to SUT
            log.warning("Couldn't deliver test case input to the target!")
            main_results.columns.update({RESULT_KEY: RESULT_UNKN})

        # Write main results and oracle reports to db
        results_db.write(main_results)
        for report in oracle_reports:
            results_db.write(report)

        # Dry run or delivery went wrong, take a break before trying again
        if is_dryrun or not delivery_ok:
            msg = f"Taking a break. is_dryrun: {is_dryrun}, "
            msg += f"delivery_ok: {delivery_ok}, test case: {i}"
            log.info(msg)
            time.sleep(TAKE_BREAK_TIME)
            log.info("Woke up from break!")


    courier.destroy()
    results_db.close()
    log.info("# Session ended at %s", str(datetime.datetime.now()))

    return 0

def arbiter(reports):
    for report in reports:
        for k,v in report.columns.items():
            if k.endswith("process_state") and not v: # Missing process, FAIL
                return RESULT_FAIL

    return RESULT_PASS

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def prob_key_string(k):
    return f"'prob.{k}'"

@static_vars(previous_report=None, threshold=0.05)
def update_grammar(fuzz_metadata, fuzzer, oracle_reports):
    # First time, don't do anything except store report
    if not update_grammar.previous_report:
        update_grammar.previous_report = oracle_reports
        return

    update = False
    for prev,curr in zip(update_grammar.previous_report, oracle_reports):
        if not curr.name.startswith("GrpcOracle") or prev.name != curr.name:
            continue # Only care about GrpcOracle reports

        for (pk,pv),(ck,cv) in zip(prev.columns.items(), curr.columns.items()):
            if not pk.endswith("usage") or pk != ck:
                continue # Only care about cpu_usage and mem_usage

            # Update if delta relative to prev value is more than "threshold"
            if pv-cv == 0:
                rel_delta = 0
            else:
                rel_delta = abs((pv-cv)/pv) if pv != 0 else float("inf")
            if rel_delta > update_grammar.threshold:
                update = True



    if update: # TODO calculate condition for updating grammar
        fuzzer.update_grammar_probabilities(fuzz_metadata)
        fuzzer.check_grammar()

    update_grammar.previous_report = oracle_reports

    return
