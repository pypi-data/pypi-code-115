# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: start.proto

import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor.FileDescriptor(
    name='start.proto',
    package='',
    syntax='proto2',
    serialized_options=None,
    serialized_pb=_b('\n\x0bstart.proto\"\x18\n\x05start\x12\x0f\n\x07scan_id\x18\x01 \x02(\x05')
)

_START = _descriptor.Descriptor(
    name='start',
    full_name='start',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='scan_id', full_name='start.scan_id', index=0,
            number=1, type=5, cpp_type=1, label=2,
            has_default_value=False, default_value=0,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto2',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=15,
    serialized_end=39,
)

DESCRIPTOR.message_types_by_name['start'] = _START
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

start = _reflection.GeneratedProtocolMessageType('start', (_message.Message,), dict(
    DESCRIPTOR=_START,
    __module__='start_pb2'
    # @@protoc_insertion_point(class_scope:start)
))
_sym_db.RegisterMessage(start)

# @@protoc_insertion_point(module_scope)
