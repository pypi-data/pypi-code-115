from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from ..._version import __version__
from ...jsonrpc2.protocol import (
    JsonRPCErrorException,
    JsonRPCErrors,
    ProtocolPartDescriptor,
)
from ...utils.dataclasses import from_dict
from ...utils.logging import LoggingDescriptor
from ..common.lsp_types import InitializeError, Model
from ..common.parts.document_symbols import symbol_information_label
from ..common.protocol import LanguageServerProtocol
from .parts.codelens import RobotCodeLensProtocolPart
from .parts.completion import RobotCompletionProtocolPart
from .parts.debugging_utils import RobotDebuggingUtilsProtocolPart
from .parts.diagnostics import RobotDiagnosticsProtocolPart
from .parts.discovering import DiscoveringProtocolPart
from .parts.document_highlight import RobotDocumentHighlightProtocolPart
from .parts.document_symbols import RobotDocumentSymbolsProtocolPart
from .parts.documents_cache import DocumentsCache
from .parts.folding_range import RobotFoldingRangeProtocolPart
from .parts.formatting import RobotFormattingProtocolPart
from .parts.goto import RobotGotoProtocolPart
from .parts.hover import RobotHoverProtocolPart
from .parts.references import RobotReferencesProtocolPart
from .parts.robocop_diagnostics import RobotRoboCopDiagnosticsProtocolPart
from .parts.robot_workspace import RobotWorkspaceProtocolPart
from .parts.semantic_tokens import RobotSemanticTokenProtocolPart
from .parts.signature_help import RobotSignatureHelpProtocolPart
from .utils.process_pool import shutdown_process_pool
from .utils.version import get_robot_version

if TYPE_CHECKING:
    from .server import RobotLanguageServer


class RobotCodeException(Exception):
    pass


class RobotModuleNotFoundError(RobotCodeException):
    pass


class RobotVersionDontMatchError(RobotCodeException):
    pass


def check_robotframework() -> None:
    try:
        __import__("robot")
    except ImportError as e:
        raise RobotModuleNotFoundError(
            "RobotFramework not installed in current Python environment, please install it."
        ) from e

    if get_robot_version() < (4, 0):
        raise RobotVersionDontMatchError("Wrong RobotFramework version. Expect version >= 4.0")


@dataclass
class Options(Model):
    storage_uri: Optional[str] = None
    global_storage_uri: Optional[str] = None


@symbol_information_label("robotframework")
class RobotLanguageServerProtocol(LanguageServerProtocol):
    _logger = LoggingDescriptor()

    documents_cache = ProtocolPartDescriptor(DocumentsCache)
    robot_diagnostics = ProtocolPartDescriptor(RobotDiagnosticsProtocolPart)
    robot_folding_ranges = ProtocolPartDescriptor(RobotFoldingRangeProtocolPart)
    robot_goto = ProtocolPartDescriptor(RobotGotoProtocolPart)
    robot_hover = ProtocolPartDescriptor(RobotHoverProtocolPart)
    robot_completion = ProtocolPartDescriptor(RobotCompletionProtocolPart)
    robot_signature_help = ProtocolPartDescriptor(RobotSignatureHelpProtocolPart)
    robot_document_symbols = ProtocolPartDescriptor(RobotDocumentSymbolsProtocolPart)
    robot_robocop_diagnostics = ProtocolPartDescriptor(RobotRoboCopDiagnosticsProtocolPart)
    robot_formatting = ProtocolPartDescriptor(RobotFormattingProtocolPart)
    robot_semantic_tokens = ProtocolPartDescriptor(RobotSemanticTokenProtocolPart)
    robot_references = ProtocolPartDescriptor(RobotReferencesProtocolPart)
    robot_document_highlight = ProtocolPartDescriptor(RobotDocumentHighlightProtocolPart)
    robot_codelens = ProtocolPartDescriptor(RobotCodeLensProtocolPart)
    robot_workspace = ProtocolPartDescriptor(RobotWorkspaceProtocolPart)

    robot_discovering = ProtocolPartDescriptor(DiscoveringProtocolPart)
    robot_debuggin_utils = ProtocolPartDescriptor(RobotDebuggingUtilsProtocolPart)

    name = "RobotCode"
    version = __version__

    file_extensions = {"robot", "resource", "py"}

    def __init__(self, server: "RobotLanguageServer"):
        super().__init__(server)
        self.options = Options()
        self.on_initialize.add(self._on_initialize)
        self.on_shutdown.add(self._on_shutdown)

    @_logger.call
    async def _on_shutdown(self, sender: Any) -> None:
        shutdown_process_pool()

    @_logger.call
    async def _on_initialize(self, sender: Any, initialization_options: Optional[Any] = None) -> None:
        try:
            check_robotframework()
        except RobotCodeException as e:
            raise JsonRPCErrorException(
                JsonRPCErrors.INTERNAL_ERROR, f"Can't start language server: {e}", InitializeError(retry=False)
            ) from e

        if initialization_options is not None:
            self.options = from_dict(initialization_options, Options)

        self._logger.debug(f"initialized with {repr(self.options)}")
