

import io
import struct
from typing import Any, Dict, List, Literal, overload


class DataItem:
    def __init__(self, data : bytes = None):
        self.data = data
    
    def set(self, value : Any):
        if isinstance(value, bytes):
            self.data = value
        elif isinstance(value, str):
            self.data = value.encode("utf-8")
        elif isinstance(value, int):
            if abs(value) > 2147483647:
                raise ValueError("Value too large")
            else:
                self.data = struct.pack("<i", value)
        elif isinstance(value, float):
            self.data = struct.pack("<f", value)
        elif isinstance(value, list):
            if len(value) == 0:
                self.data = b""
            elif isinstance(value[0], int):
                buf = io.BytesIO()
                for v in value:
                    buf.write(struct.pack("<i", v))
                self.data = buf.getvalue()
            elif isinstance(value[0], float):
                buf = io.BytesIO()
                for v in value:
                    buf.write(struct.pack("<f", v))
                self.data = buf.getvalue()
            else:
                raise ValueError("Invalid list type")
        else:
            raise ValueError("Invalid type: " + str(type(value)))
    
    @overload
    def get(self, type : Literal["str"]) -> str: ...
    
    @overload
    def get(self, type : Literal["int"]) -> int: ...

    @overload
    def get(self, type : Literal["float"]) -> float: ...

    @overload
    def get(self, type : Literal["ints"]) -> List[int]: ...

    @overload
    def get(self, type : Literal["floats"]) -> List[float]: ...

    def get(self, type : str) -> Any:
        if type == "str":
            return self.data.decode("utf-8")
        elif type == "bytes":
            return self.data
        elif type == "int":
            return struct.unpack("<i", self.data)[0]
        elif type == "float":
            return struct.unpack("<f", self.data)[0]
        elif type == "ints":
            buf = io.BytesIO(self.data)
            count = len(self.data) // 4
            return [struct.unpack("<i", buf.read(4))[0] for _ in range(count)]
        elif type == "floats":
            buf = io.BytesIO(self.data)
            count = len(self.data) // 4
            return [struct.unpack("<f", buf.read(4))[0] for _ in range(count)]
        else:
            raise ValueError("Invalid type")      

    def __len__(self) -> int:
        return len(self.data)

class Data:
    def __init__(self) -> None:
        self._data : Dict[str, DataItem] = {}
    
    def __getitem__(self, key : str) -> DataItem:
        return self._data[key]
    
    def __setitem__(self, key : str, value : Any) -> None:
        if isinstance(value, DataItem):
            self._data[key] = value
        else:
            v = DataItem()
            v.set(value)
            self._data[key] = v
    
    def __delitem__(self, key : str) -> None:
        del self._data[key]
    
    def __repr__(self) -> str:
        return repr(self._data)

    @staticmethod
    def from_bytes(data : bytes) -> "Data":
        buf = io.BytesIO(data)
        d = Data()
        num_items = struct.unpack("<I", buf.read(4))[0]
        for _ in range(num_items):
            len_kw = struct.unpack("<I", buf.read(4))[0]
            key = buf.read(len_kw).decode("utf-8")
            len_data = struct.unpack("<I", buf.read(4))[0]
            d[key] = DataItem(buf.read(len_data))
        return d


    def build(self) -> bytes:
        buf = io.BytesIO()
        buf.write(struct.pack("<I", len(self._data)))
        for key, value in self._data.items():
            kw = key.encode("utf-8")
            buf.write(struct.pack("<I", len(kw)))
            buf.write(kw)
            buf.write(struct.pack("<I", len(value)))
            buf.write(value.data)
        return buf.getvalue()
        

