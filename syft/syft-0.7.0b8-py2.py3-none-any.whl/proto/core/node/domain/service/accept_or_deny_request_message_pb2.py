# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto/core/node/domain/service/accept_or_deny_request_message.proto
"""Generated protocol buffer code."""
# third party
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


# syft absolute
from syft.proto.core.common import (
    common_object_pb2 as proto_dot_core_dot_common_dot_common__object__pb2,
)
from syft.proto.core.io import address_pb2 as proto_dot_core_dot_io_dot_address__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\nCproto/core/node/domain/service/accept_or_deny_request_message.proto\x12\x1dsyft.core.node.domain.service\x1a%proto/core/common/common_object.proto\x1a\x1bproto/core/io/address.proto"\xa6\x01\n\x1a\x41\x63\x63\x65ptOrDenyRequestMessage\x12%\n\x06msg_id\x18\x01 \x01(\x0b\x32\x15.syft.core.common.UID\x12&\n\x07\x61\x64\x64ress\x18\x02 \x01(\x0b\x32\x15.syft.core.io.Address\x12)\n\nrequest_id\x18\x03 \x01(\x0b\x32\x15.syft.core.common.UID\x12\x0e\n\x06\x61\x63\x63\x65pt\x18\x04 \x01(\x08\x62\x06proto3'
)


_ACCEPTORDENYREQUESTMESSAGE = DESCRIPTOR.message_types_by_name[
    "AcceptOrDenyRequestMessage"
]
AcceptOrDenyRequestMessage = _reflection.GeneratedProtocolMessageType(
    "AcceptOrDenyRequestMessage",
    (_message.Message,),
    {
        "DESCRIPTOR": _ACCEPTORDENYREQUESTMESSAGE,
        "__module__": "proto.core.node.domain.service.accept_or_deny_request_message_pb2"
        # @@protoc_insertion_point(class_scope:syft.core.node.domain.service.AcceptOrDenyRequestMessage)
    },
)
_sym_db.RegisterMessage(AcceptOrDenyRequestMessage)

if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _ACCEPTORDENYREQUESTMESSAGE._serialized_start = 171
    _ACCEPTORDENYREQUESTMESSAGE._serialized_end = 337
# @@protoc_insertion_point(module_scope)
