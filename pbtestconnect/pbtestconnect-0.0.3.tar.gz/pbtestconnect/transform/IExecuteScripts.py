from typing import BinaryIO
from pydantic import BaseModel

class Pipeline(BaseModel):
    name:str
    """
    The name of the pipeline for the current execution context.
    """
    version:int
    """
    The version of the pipeline for the current execution context.
    """
    reservedMetadata:dict = None

class ExecutionContext(BaseModel):
    """
    Provides contextual information for the script execution. The context can 
    tell you related metadata about the script execution, such as
    the name of the pipeline that has invoked it.
    """
    tenant:str
    """
    The alias of the tenant for this particular script execution.
    """
    domain:str
    """
    The domain/host name for this particular script execution.
    """
    metadata:dict
    """
    Key Value pairs that are present in the current Connect Transform pipeline execution.
    Setting metadata tags allows you to annotate the data.
    Changes to metadata will be propagated back to the pipeline.
    """
    pipeline:Pipeline = None
    """
    Information regarding the current pipeline when a script runs as part of a Connect Transform pipeline.
    """
    connectionId:str = None
    """
    Optional connectionId for utilization with Connectors.
    """

class ScriptContent(BaseModel):
    inputStream:BinaryIO
    """
    A file like stream to read the input data as bytes.
    """
    contentType:str
    """
    The expected content type for the data contained in inputStream.
    If the content type was not set, this will be defaulted to 'application/octet-stream'
    """
    length:int
    """
    The length of inputStream.
    """
    class Config:
        arbitrary_types_allowed = True

class IExecuteScripts:
    def execute(self, context: ExecutionContext, inputContent: ScriptContent, outputStream: BinaryIO) -> None:
        """Interface for script execution. Consumers should implement this informal interface and register
        with the @register() decorator.  
        
        Input can be read from the inputStream, and any output should be written to outputStream.

        Scripts can annotate the data with metadata by setting key value pairs in the context metadata.
        
        Keyword arguments:

        context - contains Connect Transform contextual information regarding the script run. For example, the tenant alias. 
        inputContent - descriptor that provides content type, length, and a file like binary stream. Input data into your script must be
        read from the stream parameter in the descriptor.
        outputStream - a file like binary stream. output data from your script, if applicable,
        should be written to this stream.
        """
        pass




