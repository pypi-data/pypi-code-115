import pandas as pd
import pickle
import requests
import sys
import subprocess

from config import config

def get_wheel_url(simulation_id):
  return config["WHEEL_BASE_URL"] + "/" + str(simulation_id) + "/" + config["WHEEL_NAME"]

def import_csv(file_name, simulation_id=None):
  if simulation_id is not None:
    print(get_wheel_url(simulation_id))
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', get_wheel_url(simulation_id)])

  raw = pd.read_csv(file_name)
  df = pd.DataFrame()
  for idx, row in raw.iterrows():
    df = df.append(pickle.loads(bytes.fromhex(row['data'])))

  return df