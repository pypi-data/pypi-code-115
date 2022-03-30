import base64
import hashlib
import hmac
import json
import binascii

class MoneyMadeConnect:
  def __init__(self, public_key, private_key):
    if public_key == '' or public_key is None:
      raise ValueError('Argument public_key is required!')

    if private_key == '' or private_key is None:
      raise ValueError('Argument private_key is required!')

    self.public_key = public_key
    self.private_key = private_key
  
  def base64_to_dict(self, base64_payload):
    try:
      decoded = base64.b64decode(base64_payload)
      decoded = decoded.decode("UTF-8")
      
      return json.loads(decoded)
    except Exception as e:
      raise ValueError("Can't decode base64 to dict: " + str(e))
  
  def js_encode_float(self, float_str):
    float_value = float(float_str)
    
    if float_value % 1 == 0:
      return int(float_value)
    
    return float(float_value)
  
  def dict_to_js_json(self, dict_var):
    dumped = json.dumps(dict_var)
    loaded = json.loads(dumped, parse_float=self.js_encode_float)
    
    return json.dumps(loaded, separators=(',', ':'))

  def dict_to_base64(self, dict_payload):
    if type(dict_payload) is not dict:
      raise ValueError('dict_payload must be dict!')

    json_string_payload = self.dict_to_js_json(dict_payload)
    
    payload_bytes = json_string_payload.encode("ascii")
    base64_bytes = base64.b64encode(payload_bytes)
    base64_payload = base64_bytes.decode("ascii")
    
    return base64_payload

  def generate_signature(self, dict_payload):
    base64_payload = self.dict_to_base64(dict_payload)
    signature_body = bytes(
            "{}{}{}".format(
                self.public_key,
                base64_payload,
                self.public_key,
            ),
            "UTF-8",
        )
    
    generated_signature = hmac.new(
        bytes(self.private_key, "UTF-8"),
        signature_body,
        hashlib.sha256,
    ).hexdigest()
    
    return generated_signature