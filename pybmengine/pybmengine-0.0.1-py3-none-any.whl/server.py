import asyncio
import io
from typing import Any, Dict, List, Tuple, Union
import fastapi
import struct 
from .data import Data
from pydantic import BaseModel
import logging

class ConfigItem(BaseModel):
    device_id : int
    memory_limit : int

class ActivateRequest(BaseModel):
    config : List[ConfigItem]

BMENGINE_MAGIC = 0x5448554E

class Server:
    def __init__(self, app : fastapi.FastAPI, host : str, port : int) -> None:
        self.host = host
        self.port = port
        self.app = app

        self._bind_app()
    
    def _bind_app(self):
        app = self.app
        app.on_event("startup")(self._init)
        @app.get("/health")
        async def health():
            if await self.alive():
                return {"code": 0, "data": "ok"}
            else:
                return {"code": 10005, "data": "error"}

        @app.get("/version")
        async def version():
            ret = await self.version()
            if ret is not None:
                return {"code": 0, "data": ret}
            else:
                return {"code": 10005, "data": "error"}

        @app.get("/usage")
        async def usage():
            ret = await self.usage()
            if ret is not None:
                return {"code": 0, "data": ret}
            else:
                return {"code": 10005, "data": "error"}

        @app.get("/list")
        async def list_processors():
            ret = await self.list_processes()
            if ret is not None:
                return {"code": 0, "data": ret}
            else:
                return {"code": 10005, "data": "error"}

        @app.put("/processors/{name}")
        async def activate_processor(name : str, req : ActivateRequest):
            d_req = []
            for config in req.config:
                d_req.append({"idx": config.device_id, "memory_limit": config.memory_limit})
            if await self.activate(name, d_req):
                return {"code": 0, "data": "ok"}
            else:
                return {"code": 10005, "data": "error"}
        
        @app.delete("/processors/{name}")
        async def deactivate_processor(name : str):
            if await self.deactivate(name):
                return {"code": 0, "data": "ok"}
            else:
                return {"code": 10005, "data": "error"}
    
    def register(self, processor_name : str, *args, **kwargs):
        if processor_name.find("/") != -1:
            raise Exception("Invalid processor name")
        return self.app.post(f"/processors/{processor_name}", *args, **kwargs)

    async def _init(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.tracks : Dict[int, asyncio.Future] = {}
        self.track_id = list(range(65536))

        loop = asyncio.get_running_loop()
        loop.create_task(self._serve_recv())

    async def _serve_recv(self):
        while True:
            header = b""
            while len(header) < 16:
                tmp = await self.reader.read(16 - len(header))
                if len(tmp) == 0:
                    raise Exception("Connection closed")
                header += tmp
            
            magic, version, size, track_id = struct.unpack("<IIII", header)
            if magic != BMENGINE_MAGIC:
                raise Exception("Invalid magic")
            if version != 1:
                raise Exception("Invalid version")
            if size < 0:
                raise Exception("Invalid size")
            
            if track_id not in self.tracks:
                raise Exception("Invalid track id")

            buffer = io.BytesIO()
            while buffer.tell() < size:
                tmp = await self.reader.read(size - buffer.tell())
                if len(tmp) == 0:
                    raise Exception("Connection closed")
                buffer.write(tmp)
            self.tracks[track_id].set_result(buffer.getvalue())
            del self.tracks[track_id]
    
    async def send(self, data : bytes) -> Tuple[int, Union[bytes, None]]:
        track_id = self.track_id[-1]
        self.track_id = self.track_id[:-1]

        fut = asyncio.Future()
        self.tracks[track_id] = fut
        
        buffer = io.BytesIO()
        buffer.write(struct.pack("<IIII", BMENGINE_MAGIC, 1, len(data), track_id))
        buffer.write(data)

        self.writer.write(buffer.getvalue())
        ret_bytes = await fut
        self.track_id.append(track_id)

        status = struct.unpack("<I", ret_bytes[:4])[0]
        if len(ret_bytes) > 4:
            return status, ret_bytes[4:]
        else:
            return status, None

    async def activate(self, name : str, configs) -> bool:
        buffer = io.BytesIO()
        byte_name = name.encode("utf-8")
        buffer.write(struct.pack("<I", 4))  # OP_ID
        buffer.write(struct.pack("<I", len(byte_name)))
        buffer.write(byte_name)
        buffer.write(struct.pack("<I", len(configs)))
        for config in configs:
            buffer.write(struct.pack("<I", config["idx"]))
            buffer.write(struct.pack("<I", 0))  # padding
            buffer.write(struct.pack("<q", config["memory_limit"]))
        status, _ = await self.send(buffer.getvalue())
        if status == 0:
            return True
        else:
            return False

    async def alive(self) -> bool:
        buffer = io.BytesIO()
        buffer.write(struct.pack("<I", 0))  # OP_ID
        status, _ = await self.send(buffer.getvalue())
        if status == 0:
            return True
        else:
            return False
    
    async def deactivate(self, name : str) -> bool:
        buffer = io.BytesIO()
        byte_name = name.encode("utf-8")
        buffer.write(struct.pack("<I", 5))  # OP_ID
        buffer.write(struct.pack("<I", len(byte_name)))
        buffer.write(byte_name)
        status, _ = await self.send(buffer.getvalue())
        if status == 0:
            return True
        else:
            return False
    
    async def list_processes(self) -> Union[None, List[Dict[str, Any]]]:
        buffer = io.BytesIO()
        buffer.write(struct.pack("<I", 3))
        status, ret_bytes = await self.send(buffer.getvalue())
        if status == 0:
            buffer = io.BytesIO(ret_bytes)
            num_processors = struct.unpack("<I", buffer.read(4))[0]
            processors = []
            for i in range(num_processors):
                name_len = struct.unpack("<I", buffer.read(4))[0]
                name = buffer.read(name_len).decode("utf-8")
                state = struct.unpack("<I", buffer.read(4))[0]
                processors.append({
                    "name": name,
                    "state": ["active", "inactive", "loading", 'unloading', "error"][state]
                })
            return processors
        else:
            return None
    
    async def usage(self) -> Union[None, List[Dict[str, int]]]:
        buffer = io.BytesIO()
        buffer.write(struct.pack("<I", 2))
        status, ret_bytes = await self.send(buffer.getvalue())
        if status == 0:
            buffer = io.BytesIO(ret_bytes)
            num_gpus = struct.unpack("<I", buffer.read(4))[0]
            ret = []
            for i in range(num_gpus):
                idx, cc, total_mem, used_mem = struct.unpack("<IIQQ", buffer.read(24))
                ret.append({
                    "idx": idx,
                    "cc": cc,
                    "total": total_mem,
                    "used": used_mem
                })
            return ret
        else:
            return None

    async def version(self) -> Union[None, Dict[str, int]]:
        buffer = io.BytesIO()
        buffer.write(struct.pack("<I", 1))
        status, ret_bytes = await self.send(buffer.getvalue())
        if status == 0:
            buffer = io.BytesIO(ret_bytes)
            version = struct.unpack("<I", buffer.read(4))[0]
            major = (version >> 24) & 0xff
            minor = (version >> 16) & 0xff
            patch = (version >> 8) & 0xff
            build = version & 0xff
            return {
                "major": major,
                "minor": minor,
                "patch": patch,
                "build": build
            }
        else:
            return None
    
    async def call_operator(self, name : str, data : Data) -> Union[None, Data]:
        buffer = io.BytesIO()
        byte_name = name.encode("utf-8")
        buffer.write(struct.pack("<I", 6))  # OP_ID
        buffer.write(struct.pack("<I", len(byte_name)))
        buffer.write(byte_name)
        buffer.write(data.build())
        status, ret_bytes = await self.send(buffer.getvalue())
        if status == 0:
            return Data.from_bytes(ret_bytes)
        else:
            return None
