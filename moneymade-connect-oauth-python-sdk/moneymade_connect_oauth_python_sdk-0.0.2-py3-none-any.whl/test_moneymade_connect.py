import unittest
import moneymade_connect

public_key = 'publicKey'
private_key = 'privateKey'
base64_payload = 'eyJ1c2VySWQiOiJhYmNkZWYtYWJjZGVmLWFiY2RlZi1hYmNkZWYtYWJjZGVmIiwiYWNjb3VudHMiOlt7ImlkIjoyLCJuYW1lIjoiUmVwYWlkIiwiYW1vdW50IjoxMDAwfV19'

dict_payload = {
    "userId": "abcdef-abcdef-abcdef-abcdef-abcdef",
    "accounts": [
        {"id": 2, "name": "Repaid", "amount": 1000.0},
    ],
}

signature = 'a604c5d3610dd5e3bf0548c26c75587b92fea1573a6d0921c7969b0913f7771b'

class TestMoneyMadeConnect(unittest.TestCase):
  sdk = moneymade_connect.MoneyMadeConnect(public_key, private_key)

  def test_init(self):
    self.assertRaises(TypeError, moneymade_connect.MoneyMadeConnect)
    self.assertRaises(ValueError, moneymade_connect.MoneyMadeConnect, '', '')
    
    with self.assertRaises(ValueError):
      moneymade_connect.MoneyMadeConnect(None, None)

  def test_base64_to_dict(self):
    with self.assertRaises(ValueError):
      self.sdk.base64_to_dict('base64_payload')

    decoded_dict = self.sdk.base64_to_dict(base64_payload)
    self.assertDictEqual(decoded_dict, dict_payload)
    
  def test_dict_to_js_json(self):
    self.assertEqual(self.sdk.dict_to_js_json({ "test": 1.0 }), '{"test":1}')
    self.assertEqual(self.sdk.dict_to_js_json({ "test": 1.1 }), '{"test":1.1}')

  def test_dict_to_base64(self):
    with self.assertRaises(ValueError):
      self.sdk.dict_to_base64('string')
    
    self.assertEqual(self.sdk.dict_to_base64(dict_payload), base64_payload)
  
  def test_generate_signature(self):
    self.assertEqual(self.sdk.generate_signature(dict_payload), signature)