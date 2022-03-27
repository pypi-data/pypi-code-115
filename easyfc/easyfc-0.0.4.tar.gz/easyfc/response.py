import json


class response:
    def __init__(self, data: dict, msg: str, code: str):
        self.data = data
        self.msg = msg
        self.code = code

    def parseJonsByte(self):
        dic_ = {
            'data': self.data,
            'msg': self.msg,
            'code': self.code
        }
        json_ = json.dumps(dic_)
        json_byte = bytes(json_, encoding="utf8")
        return [json_byte]
