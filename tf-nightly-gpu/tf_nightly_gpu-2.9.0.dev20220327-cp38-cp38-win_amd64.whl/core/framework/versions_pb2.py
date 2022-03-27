# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: tensorflow/core/framework/versions.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='tensorflow/core/framework/versions.proto',
  package='tensorflow',
  syntax='proto3',
  serialized_options=_b('\n\030org.tensorflow.frameworkB\016VersionsProtosP\001ZOgithub.com/tensorflow/tensorflow/tensorflow/go/core/framework/versions_go_proto\370\001\001'),
  serialized_pb=_b('\n(tensorflow/core/framework/versions.proto\x12\ntensorflow\"K\n\nVersionDef\x12\x10\n\x08producer\x18\x01 \x01(\x05\x12\x14\n\x0cmin_consumer\x18\x02 \x01(\x05\x12\x15\n\rbad_consumers\x18\x03 \x03(\x05\x42\x80\x01\n\x18org.tensorflow.frameworkB\x0eVersionsProtosP\x01ZOgithub.com/tensorflow/tensorflow/tensorflow/go/core/framework/versions_go_proto\xf8\x01\x01\x62\x06proto3')
)




_VERSIONDEF = _descriptor.Descriptor(
  name='VersionDef',
  full_name='tensorflow.VersionDef',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='producer', full_name='tensorflow.VersionDef.producer', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='min_consumer', full_name='tensorflow.VersionDef.min_consumer', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bad_consumers', full_name='tensorflow.VersionDef.bad_consumers', index=2,
      number=3, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
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
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=56,
  serialized_end=131,
)

DESCRIPTOR.message_types_by_name['VersionDef'] = _VERSIONDEF
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

VersionDef = _reflection.GeneratedProtocolMessageType('VersionDef', (_message.Message,), {
  'DESCRIPTOR' : _VERSIONDEF,
  '__module__' : 'tensorflow.core.framework.versions_pb2'
  # @@protoc_insertion_point(class_scope:tensorflow.VersionDef)
  })
_sym_db.RegisterMessage(VersionDef)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
