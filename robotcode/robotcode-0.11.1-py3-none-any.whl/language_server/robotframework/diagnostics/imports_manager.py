from __future__ import annotations

import ast
import asyncio
import os
import sys
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    cast,
    final,
)

from ....utils.async_tools import Lock, async_tasking_event, create_sub_task
from ....utils.logging import LoggingDescriptor
from ....utils.path import path_is_relative_to
from ....utils.uri import Uri
from ...common.decorators import language_id
from ...common.lsp_types import FileChangeType, FileEvent
from ...common.parts.workspace import FileWatcherEntry, Workspace
from ...common.text_document import TextDocument
from ..configuration import RobotConfig
from ..utils.async_ast import walk
from ..utils.robot_path import find_file_ex
from ..utils.version import get_robot_version
from .entities import CommandLineVariableDefinition, VariableDefinition

if TYPE_CHECKING:
    from ..protocol import RobotLanguageServerProtocol
    from .namespace import Namespace

from ..utils.process_pool import get_process_pool
from .library_doc import (
    ROBOT_LIBRARY_PACKAGE,
    ArgumentSpec,
    CompleteResult,
    Error,
    KeywordArgumentDoc,
    KeywordDoc,
    KeywordStore,
    LibraryDoc,
    VariablesDoc,
    complete_library_import,
    complete_resource_import,
    complete_variables_import,
    find_file,
    find_library,
    find_variables,
    get_library_doc,
    get_variables_doc,
    is_embedded_keyword,
    is_library_by_path,
    is_variables_by_path,
    resolve_variable,
)

RESOURCE_EXTENSIONS = (".resource", ".robot", ".txt", ".tsv", ".rst", ".rest")
REST_EXTENSIONS = (".rst", ".rest")


LOAD_LIBRARY_TIME_OUT = 30
FIND_FILE_TIME_OUT = 10
COMPLETE_LIBRARY_IMPORT_TIME_OUT = COMPLETE_RESOURCE_IMPORT_TIME_OUT = COMPLETE_VARIABLES_IMPORT_TIME_OUT = 10


@dataclass()
class _LibrariesEntryKey:
    name: str
    args: Tuple[Any, ...]

    def __hash__(self) -> int:
        return hash((self.name, self.args))


class _ImportEntry(ABC):
    def __init__(
        self,
        parent: ImportsManager,
    ) -> None:
        self.parent = parent
        self.references: weakref.WeakSet[Any] = weakref.WeakSet()
        self.file_watchers: List[FileWatcherEntry] = []
        self._lock = Lock()

    @staticmethod
    async def __remove_filewatcher(workspace: Workspace, entry: FileWatcherEntry) -> None:
        await workspace.remove_file_watcher_entry(entry)

    def __del__(self) -> None:
        try:
            if self.file_watchers is not None and asyncio.get_running_loop():
                for watcher in self.file_watchers:
                    create_sub_task(_ImportEntry.__remove_filewatcher(self.parent.parent_protocol.workspace, watcher))
        except RuntimeError:
            pass

    async def _remove_file_watcher(self) -> None:
        if self.file_watchers is not None:
            for watcher in self.file_watchers:
                await self.parent.parent_protocol.workspace.remove_file_watcher_entry(watcher)
        self.file_watchers = []

    @abstractmethod
    async def check_file_changed(self, changes: List[FileEvent]) -> Optional[FileChangeType]:
        ...

    @final
    async def invalidate(self) -> None:
        async with self._lock:
            await self._invalidate()

    @abstractmethod
    async def _invalidate(self) -> None:
        ...

    @abstractmethod
    async def _update(self) -> None:
        ...

    @abstractmethod
    async def is_valid(self) -> bool:
        ...


class _LibrariesEntry(_ImportEntry):
    def __init__(
        self,
        name: str,
        args: Tuple[Any, ...],
        parent: ImportsManager,
        get_libdoc_coroutine: Callable[[], Coroutine[Any, Any, LibraryDoc]],
        ignore_reference: bool = False,
    ) -> None:
        super().__init__(parent)
        self.name = name
        self.args = args
        self._get_libdoc_coroutine = get_libdoc_coroutine
        self._lib_doc: Optional[LibraryDoc] = None
        self.ignore_reference = ignore_reference

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}(name={repr(self.name)}, "
            f"args={repr(self.args)}, file_watchers={repr(self.file_watchers)}, id={repr(id(self))}"
        )

    async def check_file_changed(self, changes: List[FileEvent]) -> Optional[FileChangeType]:
        async with self._lock:
            if self._lib_doc is None:
                return None

            for change in changes:
                uri = Uri(change.uri)
                if uri.scheme != "file":
                    continue

                path = uri.to_path()
                if self._lib_doc is not None and (
                    (
                        self._lib_doc.module_spec is not None
                        and self._lib_doc.module_spec.submodule_search_locations is not None
                        and any(
                            path_is_relative_to(path, Path(e).absolute())
                            for e in self._lib_doc.module_spec.submodule_search_locations
                        )
                    )
                    or (
                        self._lib_doc.module_spec is not None
                        and self._lib_doc.module_spec.origin is not None
                        and path_is_relative_to(path, Path(self._lib_doc.module_spec.origin).parent)
                    )
                    or (self._lib_doc.source and path_is_relative_to(path, Path(self._lib_doc.source).parent))
                    or (
                        self._lib_doc.module_spec is None
                        and not self._lib_doc.source
                        and self._lib_doc.python_path
                        and any(path_is_relative_to(path, Path(e).absolute()) for e in self._lib_doc.python_path)
                    )
                ):
                    await self._invalidate()

                    return change.type

            return None

    async def _update(self) -> None:
        self._lib_doc = await self._get_libdoc_coroutine()

        source_or_origin = (
            self._lib_doc.source
            if self._lib_doc.source is not None
            else self._lib_doc.module_spec.origin
            if self._lib_doc.module_spec is not None
            else None
        )

        # we are a module, so add the module path into file watchers
        if self._lib_doc.module_spec is not None and self._lib_doc.module_spec.submodule_search_locations is not None:
            self.file_watchers.append(
                await self.parent.parent_protocol.workspace.add_file_watchers(
                    self.parent.did_change_watched_files,
                    [
                        str(Path(location).absolute().joinpath("**"))
                        for location in self._lib_doc.module_spec.submodule_search_locations
                    ],
                )
            )

            if source_or_origin is not None and Path(source_or_origin).parent in [
                Path(loc).absolute() for loc in self._lib_doc.module_spec.submodule_search_locations
            ]:
                return

        # we are a file, so put the parent path to filewatchers
        if source_or_origin is not None:
            self.file_watchers.append(
                await self.parent.parent_protocol.workspace.add_file_watchers(
                    self.parent.did_change_watched_files, [str(Path(source_or_origin).parent.joinpath("**"))]
                )
            )

            return

        # we are not found, so put the pythonpath to filewatchers
        if self._lib_doc.python_path is not None:
            self.file_watchers.append(
                await self.parent.parent_protocol.workspace.add_file_watchers(
                    self.parent.did_change_watched_files,
                    [str(Path(s).joinpath("**")) for s in self._lib_doc.python_path],
                )
            )

    async def _invalidate(self) -> None:
        if self._lib_doc is None and len(self.file_watchers) == 0:
            return

        await self._remove_file_watcher()
        self._lib_doc = None

    async def is_valid(self) -> bool:
        async with self._lock:
            return self._lib_doc is not None

    async def get_libdoc(self) -> LibraryDoc:
        if self._lib_doc is None:
            async with self._lock:
                if self._lib_doc is None:
                    await self._update()

                assert self._lib_doc is not None

        return self._lib_doc


@dataclass()
class _ResourcesEntryKey:
    name: str

    def __hash__(self) -> int:
        return hash(self.name)


class _ResourcesEntry(_ImportEntry):
    def __init__(
        self,
        name: str,
        parent: ImportsManager,
        get_document_coroutine: Callable[[], Coroutine[Any, Any, TextDocument]],
    ) -> None:
        super().__init__(parent)
        self.name = name
        self._get_document_coroutine = get_document_coroutine
        self._document: Optional[TextDocument] = None
        self._lib_doc: Optional[LibraryDoc] = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}(name={repr(self.name)}, "
            f"file_watchers={repr(self.file_watchers)}, id={repr(id(self))}"
        )

    async def check_file_changed(self, changes: List[FileEvent]) -> Optional[FileChangeType]:
        async with self._lock:
            if self._document is None or self._document._version is None:
                return None

            for change in changes:
                uri = Uri(change.uri)
                if uri.scheme != "file":
                    continue

                path = uri.to_path()
                if (
                    self._document is not None
                    and (path.resolve() == self._document.uri.to_path().resolve())
                    or self._document is None
                ):
                    await self._invalidate()

                    return change.type

            return None

    def __close_document(self, document: TextDocument) -> None:
        try:
            if asyncio.get_running_loop():
                create_sub_task(self.parent.parent_protocol.documents.close_document(document))
        except RuntimeError:
            pass

    async def _update(self) -> None:
        self._document = await self._get_document_coroutine()

        for r in self.references:
            self._document.references.add(r)

            weakref.finalize(r, self.__close_document, self._document)

        if self._document._version is None:
            self.file_watchers.append(
                await self.parent.parent_protocol.workspace.add_file_watchers(
                    self.parent.did_change_watched_files,
                    [str(self._document.uri.to_path())],
                )
            )

    async def _invalidate(self) -> None:
        if self._document is None and len(self.file_watchers) == 0:
            return

        await self._remove_file_watcher()

        self._document = None
        self._lib_doc = None

    async def is_valid(self) -> bool:
        async with self._lock:
            return self._document is not None

    async def get_document(self) -> TextDocument:
        if self._document is None:
            async with self._lock:
                await self._get_document()

        assert self._document is not None

        return self._document

    async def _get_document(self) -> TextDocument:
        if self._document is None:
            await self._update()

        assert self._document is not None

        return self._document

    async def get_namespace(self) -> Namespace:
        return await self.parent.parent_protocol.documents_cache.get_resource_namespace(await self.get_document())

    async def get_libdoc(self) -> LibraryDoc:
        if self._lib_doc is None:
            async with self._lock:
                if self._lib_doc is None:
                    self._lib_doc = await (await self.get_namespace()).get_library_doc()
        return self._lib_doc


@dataclass()
class _VariablesEntryKey:
    name: str
    args: Tuple[Any, ...]

    def __hash__(self) -> int:
        return hash((self.name, self.args))


class _VariablesEntry(_ImportEntry):
    def __init__(
        self,
        name: str,
        args: Tuple[Any, ...],
        parent: ImportsManager,
        get_variables_doc_coroutine: Callable[[], Coroutine[Any, Any, VariablesDoc]],
    ) -> None:
        super().__init__(parent)
        self.name = name
        self.args = args
        self._get_variables_doc_coroutine = get_variables_doc_coroutine
        self._lib_doc: Optional[VariablesDoc] = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}(name={repr(self.name)}, "
            f"args={repr(self.args)}, file_watchers={repr(self.file_watchers)}, id={repr(id(self))}"
        )

    async def check_file_changed(self, changes: List[FileEvent]) -> Optional[FileChangeType]:
        async with self._lock:
            if self._lib_doc is None:
                return None

            for change in changes:
                uri = Uri(change.uri)
                if uri.scheme != "file":
                    continue

                path = uri.to_path()
                if self._lib_doc.source and path.resolve().samefile(Path(self._lib_doc.source).resolve()):
                    await self._invalidate()

                    return change.type

            return None

    async def _update(self) -> None:
        self._lib_doc = await self._get_variables_doc_coroutine()

        if self._lib_doc is not None:
            self.file_watchers.append(
                await self.parent.parent_protocol.workspace.add_file_watchers(
                    self.parent.did_change_watched_files,
                    [str(self._lib_doc.source)],
                )
            )

    async def _invalidate(self) -> None:
        if self._lib_doc is None and len(self.file_watchers) == 0:
            return

        await self._remove_file_watcher()

        self._lib_doc = None

    async def is_valid(self) -> bool:
        async with self._lock:
            return self._lib_doc is not None

    async def get_libdoc(self) -> VariablesDoc:
        if self._lib_doc is None:
            async with self._lock:
                if self._lib_doc is None:
                    await self._update()

                assert self._lib_doc is not None

        return self._lib_doc


class ImportsManager:
    _logger = LoggingDescriptor()

    def __init__(self, parent_protocol: RobotLanguageServerProtocol, folder: Uri, config: RobotConfig) -> None:
        super().__init__()
        self.parent_protocol = parent_protocol
        self.folder = folder
        self.config: RobotConfig = config
        self._libaries_lock = Lock()
        self._libaries: OrderedDict[_LibrariesEntryKey, _LibrariesEntry] = OrderedDict()
        self._resources_lock = Lock()
        self._resources: OrderedDict[_ResourcesEntryKey, _ResourcesEntry] = OrderedDict()
        self._variables_lock = Lock()
        self._variables: OrderedDict[_VariablesEntryKey, _VariablesEntry] = OrderedDict()
        self.file_watchers: List[FileWatcherEntry] = []
        self.parent_protocol.documents.did_change.add(self.resource_document_changed)
        self._command_line_variables: Optional[List[VariableDefinition]] = None

        self.process_pool = get_process_pool()
        self._python_path: Optional[List[str]] = None
        self._environment: Optional[Mapping[str, str]] = None

    @property
    def environment(self) -> Mapping[str, str]:
        if self._environment is None:
            self._environment = dict(os.environ)

            self._environment.update(self.config.env)

        return self._environment

    @property
    def python_path(self) -> List[str]:
        if self._python_path is None:
            self._python_path = sys.path

            file = Path(__file__).resolve()
            top = file.parents[3]
            for p in filter(lambda v: path_is_relative_to(v, top), sys.path.copy()):
                self._python_path.remove(p)

        for p in self.config.python_path:
            absolute_path = str(Path(p).absolute())
            if absolute_path not in self._python_path:
                self._python_path.insert(0, absolute_path)

        return self._python_path or []

    @_logger.call
    async def get_command_line_variables(self) -> List[VariableDefinition]:
        from robot.utils.text import split_args_from_name_or_path

        if self._command_line_variables is None:
            if self.config is None:
                self._command_line_variables = []
            else:
                self._command_line_variables = [
                    CommandLineVariableDefinition(0, 0, 0, 0, "", f"${{{k}}}", None, has_value=True, value=(v,))
                    for k, v in self.config.variables.items()
                ]
                for variable_file in self.config.variable_files:
                    name, args = split_args_from_name_or_path(variable_file)
                    try:
                        lib_doc = await self.get_libdoc_for_variables_import(
                            name, tuple(args), str(self.folder.to_path()), self
                        )
                        if lib_doc is not None:
                            self._command_line_variables += lib_doc.variables

                    except (SystemExit, KeyboardInterrupt, asyncio.CancelledError):
                        raise
                    except BaseException as e:
                        self._logger.exception(e)

        return self._command_line_variables

    @async_tasking_event
    async def libraries_changed(sender, libraries: List[LibraryDoc]) -> None:  # NOSONAR
        ...

    @async_tasking_event
    async def resources_changed(sender, resources: List[LibraryDoc]) -> None:  # NOSONAR
        ...

    @async_tasking_event
    async def variables_changed(sender, variables: List[LibraryDoc]) -> None:  # NOSONAR
        ...

    @language_id("robotframework")
    async def resource_document_changed(self, sender: Any, document: TextDocument) -> None:
        resource_changed: List[LibraryDoc] = []

        async with self._resources_lock:
            for r_entry in self._resources.values():
                lib_doc: Optional[LibraryDoc] = None
                try:
                    if not await r_entry.is_valid():
                        continue

                    uri = (await r_entry.get_document()).uri
                    result = uri == document.uri
                    if result:
                        lib_doc = await r_entry.get_libdoc()
                        await r_entry.invalidate()

                except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
                    raise
                except BaseException:
                    result = True

                if result and lib_doc is not None:
                    resource_changed.append(lib_doc)

        if resource_changed:
            await self.resources_changed(self, resource_changed)

    async def did_change_watched_files(self, sender: Any, changes: List[FileEvent]) -> None:
        libraries_changed: List[LibraryDoc] = []
        resource_changed: List[LibraryDoc] = []
        variables_changed: List[LibraryDoc] = []

        lib_doc: Optional[LibraryDoc]

        async with self._libaries_lock:
            for l_entry in self._libaries.values():
                lib_doc = None
                if await l_entry.is_valid():
                    lib_doc = await l_entry.get_libdoc()
                result = await l_entry.check_file_changed(changes)
                if result is not None and lib_doc is not None:
                    libraries_changed.append(lib_doc)

        async with self._resources_lock:
            for r_entry in self._resources.values():
                lib_doc = None
                if await r_entry.is_valid():
                    lib_doc = await r_entry.get_libdoc()
                result = await r_entry.check_file_changed(changes)
                if result is not None and lib_doc is not None:
                    resource_changed.append(await r_entry.get_libdoc())

        async with self._variables_lock:
            for v_entry in self._variables.values():
                lib_doc = None
                if await v_entry.is_valid():
                    lib_doc = await v_entry.get_libdoc()
                result = await v_entry.check_file_changed(changes)
                if result is not None and lib_doc is not None:
                    variables_changed.append(await v_entry.get_libdoc())

        if libraries_changed:
            await self.libraries_changed(self, libraries_changed)

        if resource_changed:
            await self.resources_changed(self, resource_changed)

        if variables_changed:
            await self.variables_changed(self, variables_changed)

    def __remove_library_entry(self, entry_key: _LibrariesEntryKey, entry: _LibrariesEntry) -> None:
        async def remove(k: _LibrariesEntryKey, e: _LibrariesEntry) -> None:
            if len(e.references) == 0:
                self._logger.debug(lambda: f"Remove Library Entry {k}")
                async with self._libaries_lock:
                    if len(e.references) == 0:
                        e1 = self._libaries.get(k, None)
                        if e1 == e:
                            self._libaries.pop(k, None)

                            await e.invalidate()
                self._logger.debug(lambda: f"Library Entry {k} removed")

        try:
            if asyncio.get_running_loop():
                create_sub_task(remove(entry_key, entry))
        except RuntimeError:
            pass

    def __remove_resource_entry(self, entry_key: _ResourcesEntryKey, entry: _ResourcesEntry) -> None:
        async def remove(k: _ResourcesEntryKey, e: _ResourcesEntry) -> None:
            if len(e.references) == 0:
                self._logger.debug(lambda: f"Remove Resource Entry {k}")
                async with self._resources_lock:
                    if len(e.references) == 0:
                        e1 = self._resources.get(k, None)
                        if e1 == e:
                            self._resources.pop(k, None)

                            await e.invalidate()
                self._logger.debug(lambda: f"Resource Entry {k} removed")

        try:
            if asyncio.get_running_loop():
                create_sub_task(remove(entry_key, entry))
        except RuntimeError:
            pass

    def __remove_variables_entry(self, entry_key: _VariablesEntryKey, entry: _VariablesEntry) -> None:
        async def remove(k: _VariablesEntryKey, e: _VariablesEntry) -> None:
            if len(e.references) == 0:
                self._logger.debug(lambda: f"Remove Variables Entry {k}")
                async with self._variables_lock:
                    if len(e.references) == 0:
                        e1 = self._variables.get(k, None)
                        if e1 == e:
                            self._variables.pop(k, None)

                            await e.invalidate()
                self._logger.debug(lambda: f"Variables Entry {k} removed")

        try:
            if asyncio.get_running_loop():
                create_sub_task(remove(entry_key, entry))
        except RuntimeError:
            pass

    @_logger.call
    async def find_library(self, name: str, base_dir: str, variables: Optional[Dict[str, Any]] = None) -> str:
        from robot.libraries import STDLIBS
        from robot.variables.search import contains_variable

        if contains_variable(name, "$@&%"):
            return await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    self.process_pool,
                    find_library,
                    name,
                    str(self.folder.to_path()),
                    base_dir,
                    self.config.python_path if self.config is not None else None,
                    self.config.env if self.config is not None else None,
                    self.config.variables if self.config is not None else None,
                    variables,
                ),
                FIND_FILE_TIME_OUT,
            )

        if name in STDLIBS:
            result = ROBOT_LIBRARY_PACKAGE + "." + name
        else:
            result = name

        if is_library_by_path(result):
            result = find_file_ex(result, base_dir, self.python_path, "Library")

        return result

    @_logger.call
    async def find_variables(self, name: str, base_dir: str, variables: Optional[Dict[str, Any]] = None) -> str:
        from robot.variables.search import contains_variable

        if contains_variable(name, "$@&%"):
            return await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    self.process_pool,
                    find_variables,
                    name,
                    str(self.folder.to_path()),
                    base_dir,
                    self.config.python_path if self.config is not None else None,
                    self.config.env if self.config is not None else None,
                    self.config.variables if self.config is not None else None,
                    variables,
                ),
                FIND_FILE_TIME_OUT,
            )

        if get_robot_version() >= (5, 0):

            if is_variables_by_path(name):
                return str(find_file_ex(name, base_dir, self.python_path, "Library"))

            return name

        return str(find_file_ex(name, base_dir, self.python_path, "Library"))

    @_logger.call
    async def get_libdoc_for_library_import(
        self,
        name: str,
        args: Tuple[Any, ...],
        base_dir: str,
        sentinel: Any = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> LibraryDoc:
        source = await self.find_library(
            name,
            base_dir,
            variables,
        )

        async def _get_libdoc() -> LibraryDoc:
            self._logger.debug(lambda: f"Load Library {source}{repr(args)}")

            result = await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    self.process_pool,
                    get_library_doc,
                    name,
                    args,
                    str(self.folder.to_path()),
                    base_dir,
                    self.config.python_path if self.config is not None else None,
                    self.config.env if self.config is not None else None,
                    self.config.variables if self.config is not None else None,
                    variables,
                ),
                LOAD_LIBRARY_TIME_OUT,
            )

            if result.stdout:
                self._logger.warning(lambda: f"stdout captured at loading library {name}{repr(args)}:\n{result.stdout}")

            return result

        entry_key = _LibrariesEntryKey(source, args)

        if entry_key not in self._libaries:
            async with self._libaries_lock:
                if entry_key not in self._libaries:
                    self._libaries[entry_key] = _LibrariesEntry(
                        name, args, self, _get_libdoc, ignore_reference=sentinel is None
                    )

        entry = self._libaries[entry_key]

        if not entry.ignore_reference and sentinel is not None and sentinel not in entry.references:
            entry.references.add(sentinel)
            weakref.finalize(sentinel, self.__remove_library_entry, entry_key, entry)

        return await entry.get_libdoc()

    @_logger.call
    async def get_libdoc_from_model(
        self,
        model: ast.AST,
        source: str,
        model_type: str = "RESOURCE",
        scope: str = "GLOBAL",
        append_model_errors: bool = True,
    ) -> LibraryDoc:

        from robot.errors import DataError
        from robot.libdocpkg.robotbuilder import KeywordDocBuilder
        from robot.running.builder.transformers import ResourceBuilder
        from robot.running.model import ResourceFile
        from robot.running.usererrorhandler import UserErrorHandler
        from robot.running.userkeyword import UserLibrary

        from ..utils.ast_utils import HasError, HasErrors

        errors: List[Error] = []

        async for node in walk(model):
            error = node.error if isinstance(node, HasError) else None
            if error is not None:
                errors.append(Error(message=error, type_name="ModelError", source=source, line_no=node.lineno))
            if append_model_errors:
                node_errors = node.errors if isinstance(node, HasErrors) else None
                if node_errors is not None:
                    for e in node_errors:
                        errors.append(Error(message=e, type_name="ModelError", source=source, line_no=node.lineno))

        res = ResourceFile(source=source)

        ResourceBuilder(res).visit(model)

        class MyUserLibrary(UserLibrary):
            current_kw: Any = None

            def _log_creating_failed(self, handler: UserErrorHandler, error: BaseException) -> None:
                err = Error(
                    message=f"Creating keyword '{handler.name}' failed: {str(error)}",
                    type_name=type(error).__qualname__,
                    source=self.current_kw.source if self.current_kw is not None else None,
                    line_no=self.current_kw.lineno if self.current_kw is not None else None,
                )
                errors.append(err)

            def _create_handler(self, kw: Any) -> Any:
                self.current_kw = kw
                try:
                    handler = super()._create_handler(kw)
                    setattr(handler, "errors", None)
                except DataError as e:
                    err = Error(
                        message=str(e),
                        type_name=type(e).__qualname__,
                        source=kw.source,
                        line_no=kw.lineno,
                    )
                    errors.append(err)

                    handler = UserErrorHandler(e, kw.name, self.name)
                    handler.source = kw.source
                    handler.lineno = kw.lineno

                    setattr(handler, "errors", [err])

                return handler

        lib = MyUserLibrary(res)

        libdoc = LibraryDoc(
            name=lib.name or "",
            doc=lib.doc,
            type=model_type,
            scope=scope,
            source=source,
            line_no=1,
            errors=errors,
        )

        libdoc.keywords = KeywordStore(
            source=libdoc.name,
            source_type=libdoc.type,
            keywords=[
                KeywordDoc(
                    name=kw[0].name,
                    args=tuple(KeywordArgumentDoc.from_robot(a) for a in kw[0].args),
                    doc=kw[0].doc,
                    tags=tuple(kw[0].tags),
                    source=kw[0].source,
                    line_no=kw[0].lineno,
                    libname=libdoc.name,
                    is_embedded=is_embedded_keyword(kw[0].name),
                    errors=getattr(kw[1], "errors") if hasattr(kw[1], "errors") else None,
                    is_error_handler=isinstance(kw[1], UserErrorHandler),
                    error_handler_message=str(cast(UserErrorHandler, kw[1]).error)
                    if isinstance(kw[1], UserErrorHandler)
                    else None,
                    arguments=ArgumentSpec.from_robot_argument_spec(kw[1].arguments),
                )
                for kw in [(KeywordDocBuilder(resource=True).build_keyword(lw), lw) for lw in lib.handlers]
            ],
        )

        return libdoc

    @_logger.call
    async def get_libdoc_for_variables_import(
        self,
        name: str,
        args: Tuple[Any, ...],
        base_dir: str,
        sentinel: Any = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> VariablesDoc:
        source = await self.find_variables(
            name,
            base_dir,
            variables,
        )

        async def _get_libdoc() -> VariablesDoc:
            self._logger.debug(lambda: f"Load variables {source}{repr(args)}")

            result = await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    self.process_pool,
                    get_variables_doc,
                    name,
                    args,
                    str(self.folder.to_path()),
                    base_dir,
                    self.config.python_path if self.config is not None else None,
                    self.config.env if self.config is not None else None,
                    self.config.variables if self.config is not None else None,
                    variables,
                ),
                LOAD_LIBRARY_TIME_OUT,
            )

            if result.stdout:
                self._logger.warning(
                    lambda: f"stdout captured at loading variables {name}{repr(args)}:\n{result.stdout}"
                )
            return result

        entry_key = _VariablesEntryKey(source, args)

        if entry_key not in self._variables:
            async with self._variables_lock:
                if entry_key not in self._variables:
                    self._variables[entry_key] = _VariablesEntry(name, args, self, _get_libdoc)

        entry = self._variables[entry_key]

        if sentinel is not None and sentinel not in entry.references:
            entry.references.add(sentinel)
            weakref.finalize(sentinel, self.__remove_variables_entry, entry_key, entry)

        return await entry.get_libdoc()

    @_logger.call
    async def find_resource(
        self, name: str, base_dir: str, file_type: str = "Resource", variables: Optional[Dict[str, Any]] = None
    ) -> str:
        from robot.variables.search import contains_variable

        # if contains_variable(name, "$@&%"):
        #     name = name.replace("%{CI_PROJECT_DIR}", self.environment["CI_PROJECT_DIR"])

        if contains_variable(name, "$@&%"):
            return await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    self.process_pool,
                    find_file,
                    name,
                    str(self.folder.to_path()),
                    base_dir,
                    self.config.python_path if self.config is not None else None,
                    self.config.env if self.config is not None else None,
                    self.config.variables if self.config is not None else None,
                    variables,
                    file_type,
                ),
                FIND_FILE_TIME_OUT,
            )

        return str(find_file_ex(name, base_dir, self.python_path, file_type))

    @_logger.call
    async def _get_entry_for_resource_import(
        self, name: str, base_dir: str, sentinel: Any = None, variables: Optional[Dict[str, Any]] = None
    ) -> _ResourcesEntry:
        source = await self.find_resource(name, base_dir, variables=variables)

        async def _get_document() -> TextDocument:
            self._logger.debug(lambda: f"Load resource {name} from source {source}")

            source_path = Path(source).resolve()
            extension = source_path.suffix
            if extension.lower() not in RESOURCE_EXTENSIONS:
                raise ImportError(
                    f"Invalid resource file extension '{extension}'. "
                    f"Supported extensions are {', '.join(repr(s) for s in RESOURCE_EXTENSIONS)}."
                )

            return await self.parent_protocol.robot_workspace.get_or_open_document(source_path, "robotframework")

        entry_key = _ResourcesEntryKey(source)

        if entry_key not in self._resources:
            async with self._resources_lock:

                if entry_key not in self._resources:
                    self._resources[entry_key] = _ResourcesEntry(name, self, _get_document)

        entry = self._resources[entry_key]

        if sentinel is not None and sentinel not in entry.references:
            entry.references.add(sentinel)
            weakref.finalize(sentinel, self.__remove_resource_entry, entry_key, entry)

        return entry

    async def get_namespace_and_libdoc_for_resource_import(
        self,
        name: str,
        base_dir: str,
        sentinel: Any = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Tuple["Namespace", LibraryDoc]:
        entry = await self._get_entry_for_resource_import(name, base_dir, sentinel, variables)

        return await entry.get_namespace(), await entry.get_libdoc()

    async def get_namespace_for_resource_import(
        self,
        name: str,
        base_dir: str,
        sentinel: Any = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> "Namespace":
        entry = await self._get_entry_for_resource_import(name, base_dir, sentinel, variables)

        return await entry.get_namespace()

    async def get_libdoc_for_resource_import(
        self, name: str, base_dir: str, sentinel: Any = None, variables: Optional[Dict[str, Any]] = None
    ) -> LibraryDoc:
        entry = await self._get_entry_for_resource_import(name, base_dir, sentinel, variables)

        return await entry.get_libdoc()

    async def complete_library_import(
        self, name: Optional[str], base_dir: str = ".", variables: Optional[Dict[str, Any]] = None
    ) -> Optional[List[CompleteResult]]:
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                self.process_pool,
                complete_library_import,
                name,
                str(self.folder.to_path()),
                base_dir,
                self.config.python_path if self.config is not None else None,
                self.config.env if self.config is not None else None,
                self.config.variables if self.config is not None else None,
                variables,
            ),
            COMPLETE_LIBRARY_IMPORT_TIME_OUT,
        )

        return result

    async def complete_resource_import(
        self, name: Optional[str], base_dir: str = ".", variables: Optional[Dict[str, Any]] = None
    ) -> Optional[List[CompleteResult]]:
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                self.process_pool,
                complete_resource_import,
                name,
                str(self.folder.to_path()),
                base_dir,
                self.config.python_path if self.config is not None else None,
                self.config.env if self.config is not None else None,
                self.config.variables if self.config is not None else None,
                variables,
            ),
            COMPLETE_RESOURCE_IMPORT_TIME_OUT,
        )

        return result

    async def complete_variables_import(
        self, name: Optional[str], base_dir: str = ".", variables: Optional[Dict[str, Any]] = None
    ) -> Optional[List[CompleteResult]]:
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                self.process_pool,
                complete_variables_import,
                name,
                str(self.folder.to_path()),
                base_dir,
                self.config.python_path if self.config is not None else None,
                self.config.env if self.config is not None else None,
                self.config.variables if self.config is not None else None,
                variables,
            ),
            COMPLETE_VARIABLES_IMPORT_TIME_OUT,
        )

        return result

    async def resolve_variable(
        self, name: str, base_dir: str = ".", variables: Optional[Dict[str, Any]] = None, ignore_errors: bool = True
    ) -> Any:
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                self.process_pool,
                resolve_variable,
                name,
                str(self.folder.to_path()),
                base_dir,
                self.config.python_path if self.config is not None else None,
                self.config.env if self.config is not None else None,
                self.config.variables if self.config is not None else None,
                variables,
                ignore_errors,
            ),
            COMPLETE_VARIABLES_IMPORT_TIME_OUT,
        )

        return result
