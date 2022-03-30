import os
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import joblib
import numpy as np
from pkg_resources import resource_filename
import fire


class Regbot:
  reg_model_path = resource_filename(__name__, 'finalized_model.h5') 
  model_scaler_path = resource_filename(__name__, 'logscaler.gz') 


  def __init__(self,*args):
  	pass



  @classmethod  
  def loadmodel(cls):
    loaded_model = joblib.load(open(f'{cls.reg_model_path}', 'rb'))
    return loaded_model


  @classmethod  
  def prepareInput(cls,opening,closing,volume):
    avr = closing*volume/(opening + closing)
    bvr = opening*volume/(opening + closing)
    testdata = np.array([[avr,bvr]])
    scaler = joblib.load(f'{cls.model_scaler_path}')
    testdata = scaler.transform(testdata)

    return testdata


  @classmethod
  def buySignalGenerator(cls,opening,closing,volume):
    scalledInput = cls.prepareInput(opening,closing,volume)
    return (cls.loadmodel().predict_proba(scalledInput)[:,1] >= 0.0625).astype(int)
    





def signal(opening,closing,volume):
  try:
    return Regbot.buySignalGenerator(opening,closing,volume)[0]
  except Exception as e:
    print(e)


if __name__ == '__main__':
  fire.Fire(signal)
