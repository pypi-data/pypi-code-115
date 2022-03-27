# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from funppy import debugtalk_pb2 as debugtalk__pb2


class DebugTalkStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetNames = channel.unary_unary(
                '/proto.DebugTalk/GetNames',
                request_serializer=debugtalk__pb2.Empty.SerializeToString,
                response_deserializer=debugtalk__pb2.GetNamesResponse.FromString,
                )
        self.Call = channel.unary_unary(
                '/proto.DebugTalk/Call',
                request_serializer=debugtalk__pb2.CallRequest.SerializeToString,
                response_deserializer=debugtalk__pb2.CallResponse.FromString,
                )


class DebugTalkServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetNames(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Call(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DebugTalkServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetNames': grpc.unary_unary_rpc_method_handler(
                    servicer.GetNames,
                    request_deserializer=debugtalk__pb2.Empty.FromString,
                    response_serializer=debugtalk__pb2.GetNamesResponse.SerializeToString,
            ),
            'Call': grpc.unary_unary_rpc_method_handler(
                    servicer.Call,
                    request_deserializer=debugtalk__pb2.CallRequest.FromString,
                    response_serializer=debugtalk__pb2.CallResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'proto.DebugTalk', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class DebugTalk(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetNames(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/proto.DebugTalk/GetNames',
            debugtalk__pb2.Empty.SerializeToString,
            debugtalk__pb2.GetNamesResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Call(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/proto.DebugTalk/Call',
            debugtalk__pb2.CallRequest.SerializeToString,
            debugtalk__pb2.CallResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
