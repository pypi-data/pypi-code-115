# coding: utf-8
import json
import os
import time
import inspect
import random
import atexit
import subprocess

from hashlib import md5
from datetime import datetime
from .Log import Logger

DEFAULT_LOG_PATH = 'nlutils/params'

################################################################################
# Some useful util functions
def get_md5_hash(obj):
    md5_obj = md5()
    md5_obj.update(obj.encode('utf8'))
    return md5_obj.hexdigest()

def retrieve_name(var):
    for fi in reversed(inspect.stack()):
        names = [var_name for var_name, var_val in fi.frame.f_locals.items() if var_val is var]
        if len(names) > 0:
            return names[0]

def get_commit_id():
    return subprocess.getoutput("git log -1 | grep commit | awk '{print $2}'")


################################################################################
# Check whether it is a numpy array or tensor, if it is, convert it to a list
def check_dict(obj):
    for k, v in obj.items():
        if type(v) is dict:
            obj[k] = check_dict(v)
        else:
            if 'tolist' in dir(v):
                obj[k] = v.tolist()
    return obj

def merge_files():
    whole_text = '['
    for root, _, files in os.walk(DEFAULT_LOG_PATH):
        for file in files:
            if file.endswith('.json'):
                if 'fail' not in os.path.abspath(os.path.join(root, file)):
                    with open(os.path.join(root, file), 'r') as f:
                        whole_text += f.read() + ','
    whole_text = whole_text[:-1] + ']'
    with open('all_log.json', 'w') as f:
        f.write(whole_text)
################################################################################
# Implementation of ParameterWatcher
class ParameterWatcher(object):
    
    def __new__(cls,*args,**kwargs):
        if not hasattr(cls, 'WATCHER_QUEUE'):
            pass
        return super().__new__(cls)

    def __init__(self, name, rank=0, local_save=True):
        if rank != 0:
            return
        atexit.register(self.close_save)
        self.parameters = dict()
        self.shown_parameter_names = []
        self.models = dict()
        self.results = dict()
        self.id = get_md5_hash(f'{name}-{time.time()}-{random.random()}')
        self.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.start_time_stamp = time.time()
        self.name = name
        self.description = name
        self.save_dir = f'{DEFAULT_LOG_PATH}/{self.name}' # Avoid sudo access requirement
        self.local_save = local_save

    def close_save(self):
        if not self.local_save:
            return

        ################################################################################
        # Determine whether it is a failure training by checking the results and create necessary folders
        if len(self.results) == 0:
            if 'fail' in self.save_dir:
                pass
            else:
                self.save_dir = f'{self.save_dir}/fail'
                Logger.get_logger().warning("No results saved, experiment could be interrupted during the training...")
        os.makedirs(self.save_dir, exist_ok=True)
        if 'fail' not in self.save_dir:
            os.makedirs(f'{self.save_dir}/{self.time[:10]}', exist_ok=True)
        
        ################################################################################
        # Wrap all parameters into a single dict
        clip_decimal = lambda x: int(x * 1000) / 1000
        whole_data = dict()
        basic_data = dict()
        basic_data['name'] = self.name
        basic_data['description'] = self.description
        basic_data['time'] = self.time
        basic_data['start_time_stamp'] = clip_decimal(self.start_time_stamp)
        basic_data['end_time_stamp'] = clip_decimal(time.time())
        basic_data['time_cost'] = clip_decimal(basic_data['end_time_stamp'] - basic_data['start_time_stamp'])
        basic_data['id'] = self.id
        basic_data['commit_id'] = get_commit_id()
        whole_data['parameters'] = self.parameters
        whole_data['models'] = self.models
        whole_data['results'] = self.results
        basic_data['hash_code'] = get_md5_hash(whole_data.__str__())
        whole_data['basic_info'] = basic_data
        whole_data = check_dict(whole_data)

        ################################################################################
        # Save to file
        if 'fail' in self.save_dir:
            with open(f"{self.save_dir}/{self.name}-{self.time}-{self.id}.json", "w") as f:
                json.dump(whole_data, f)
        else:
            with open(f"{self.save_dir}/{self.time[:10]}/{self.name}-{self.time}-{self.id}.json", "w") as f:
                json.dump(whole_data, f)
    
    def insert_shown_parameter_names(self, name):
        self.shown_parameter_names.append(retrieve_name(name))
    
    def insert_batch_shown_parameter_names(self, names:list):
        self.shown_parameter_names.extend(map(lambda x: retrieve_name(x), names))
    
    def disable_local_save(self):
        self.local_save = False

    def enable_local_save(self):
        self.local_save = True

    def set_parameter_by_argparser(self, args):
        parameters = {f'{key}': val for key, val in args._get_kwargs()}
        self.set_parameters(parameters)
    
    def set_parameters_by_dict(self, dict):
        for k, v in dict.items():
            self.insert_parameters(k, v)
    
    def set_parameters(self, parameters):
        self.parameters = parameters
    
    def insert_update(self, container, key, value):
        container[key] = value if str(value) != 'NaN' else 'NaN'

    def insert_parameters(self, key, value):
        self.insert_update(self.parameters, key, value)
    
    def insert_batch_parameters(self, parameters_list):
        for param in parameters_list:
            param_name = retrieve_name(param)
            self.insert_update(self.parameters, param_name, param)

    def insert_models(self, key, value):
        self.models[key] = value

    def insert_results(self, key, value):
        if key in self.results.keys():
            print("Warning: key {} already exists in results, will be overwritten...".format(key))
        self.insert_update(self.results, key, value)
    
    def insert_batch_results(self, result_list):
        for result in result_list:
            result_name = retrieve_name(result)
            self.insert_update(self.results, result_name, result)

    def set_description(self, description):
        self.description = description

if __name__ == '__main__':
    ...