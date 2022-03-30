# Standard lib imports
import random

# Third-party imports
import psutil

def run(process_list):
    '''
    This function can be used to generate dummy gRPC responses by specifying a
    standalone worker for the gRPC Oracle:

    > qwilfish grpc-oracle -s /some/path/standalone_worker_example.py)

    Make sure a qwilfish-service instance is running and that this script
    exists in the filesystem of whatever machine the gRPC Oracle is connecting
    to (probably your fuzzing target).
    '''
    process_data = {}

    for p in process_list:
        pdata = {"cpu_usage": random.randint(1, 100),
                 "mem_usage": random.randint(1000, 10000),
                 "process_state": random.randint(0,1)}
        process_data[p] = pdata

    return process_data

def run_bad(process_list):
    '''
    A bad standalone worker function. For testing only.
    Invoke by:

    > qwilfish grpc-oracle -s /some/path/standalone_worker_example.py:run_bad)

    Otherwise, details are the same as above
    '''
    return [1, 2]

def run_unstable(process_list):
    '''
    A standalone worker that sometimes return an empty dict, mimicking that no
    monitorable process was found (maybe due to a crash or reset, who knows?).
    '''

    if random.randint(0,100) > 20: # 80 % chance of success
        return run(process_list)
    else:
        return None

def run_psutil(process_list):

    process_data = {}

    for pname in process_list:
        p = find_procs_by_name(pname)

        if p: # Matching processes found
            p = p[0] # Assume first match is what we want
            pdata = {}

            try:
                pdata.update({"cpu_usage": p.cpu_percent()})
                pdata.update({"mem_usage": int(p.memory_info().vms)})
                pdata.update({"process_state": 1}) # Available
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                pdata.update({"process_state": 0}) # Not available

            process_data[pname] = pdata

    return process_data

def find_procs_by_name(name):
    '''
    Inspired by https://psutil.readthedocs.io/en/latest/#recipes
    '''

    ls = []
    for p in psutil.process_iter(['name']):
        if p.info['name'] == name:
            ls.append(p)

    return ls
