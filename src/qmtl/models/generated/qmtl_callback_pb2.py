# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: qmtl_callback.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13qmtl_callback.proto\x12\rqmtl.callback\"\xe0\x01\n\x13NodeCallbackRequest\x12\x0f\n\x07node_id\x18\x01 \x01(\t\x12\x36\n\rcallback_type\x18\x02 \x01(\x0e\x32\x1f.qmtl.callback.NodeCallbackType\x12\x0b\n\x03url\x18\x03 \x01(\t\x12\x42\n\x08metadata\x18\x04 \x03(\x0b\x32\x30.qmtl.callback.NodeCallbackRequest.MetadataEntry\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"M\n\x14NodeCallbackResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x13\n\x0b\x63\x61llback_id\x18\x03 \x01(\t\"\xf2\x01\n\x11NodeCallbackEvent\x12\x0f\n\x07node_id\x18\x01 \x01(\t\x12\x36\n\rcallback_type\x18\x02 \x01(\x0e\x32\x1f.qmtl.callback.NodeCallbackType\x12I\n\revent_payload\x18\x03 \x03(\x0b\x32\x32.qmtl.callback.NodeCallbackEvent.EventPayloadEntry\x12\x14\n\x0ctriggered_at\x18\x04 \x01(\x03\x1a\x33\n\x11\x45ventPayloadEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01*E\n\x10NodeCallbackType\x12\x0e\n\nON_EXECUTE\x10\x00\x12\x0b\n\x07ON_STOP\x10\x01\x12\x14\n\x10ON_REFCOUNT_ZERO\x10\x02\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'qmtl_callback_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _NODECALLBACKREQUEST_METADATAENTRY._options = None
  _NODECALLBACKREQUEST_METADATAENTRY._serialized_options = b'8\001'
  _NODECALLBACKEVENT_EVENTPAYLOADENTRY._options = None
  _NODECALLBACKEVENT_EVENTPAYLOADENTRY._serialized_options = b'8\001'
  _globals['_NODECALLBACKTYPE']._serialized_start=589
  _globals['_NODECALLBACKTYPE']._serialized_end=658
  _globals['_NODECALLBACKREQUEST']._serialized_start=39
  _globals['_NODECALLBACKREQUEST']._serialized_end=263
  _globals['_NODECALLBACKREQUEST_METADATAENTRY']._serialized_start=216
  _globals['_NODECALLBACKREQUEST_METADATAENTRY']._serialized_end=263
  _globals['_NODECALLBACKRESPONSE']._serialized_start=265
  _globals['_NODECALLBACKRESPONSE']._serialized_end=342
  _globals['_NODECALLBACKEVENT']._serialized_start=345
  _globals['_NODECALLBACKEVENT']._serialized_end=587
  _globals['_NODECALLBACKEVENT_EVENTPAYLOADENTRY']._serialized_start=536
  _globals['_NODECALLBACKEVENT_EVENTPAYLOADENTRY']._serialized_end=587
# @@protoc_insertion_point(module_scope)
