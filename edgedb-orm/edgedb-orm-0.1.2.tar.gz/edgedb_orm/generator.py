import json
import re
import typing as T
from enum import Enum
import os
from pathlib import Path
from black import format_str, FileMode
import edgedb
from pydantic import BaseModel
from devtools import debug
from .introspection import (
    introspect_objects,
    introspect_scalars,
    ObjectType,
    ScalarType,
    Link,
    Property,
    Cardinality,
)

PATH_TO_MODULE = "edgedb_orm"
DEFAULT_INDENT = "    "
CONFIG_NAME = "GraphORM"


class GeneratorException(Exception):
    pass


def indent_lines(s: str, indent: str = DEFAULT_INDENT) -> str:
    chunks = s.split("\n")
    return indent + f"\n{indent}".join(chunks)


def imports() -> str:
    lines = [
        "from __future__ import annotations",
        "import typing as T",
        "from enum import Enum",
        "from datetime import datetime, date, timedelta",
        "from uuid import UUID",
        "from decimal import Decimal",
        "from edgedb import RelativeDuration, AsyncIOClient, create_async_client",
        "from pydantic import BaseModel, Field, PrivateAttr",
        f"from {PATH_TO_MODULE} import Node, Resolver, NodeException, ResolverException, UpdateOperation, Batch, Unset, ComputedPropertyException, is_unset",
    ]
    return "\n".join(lines)


async def build_enums(client: edgedb.AsyncIOClient) -> str:
    scalar_types = await introspect_scalars(client)
    enum_strs: T.List[str] = []
    for scalar in scalar_types:
        if not scalar.enum_values:
            continue
        enum_value_strs: T.List[str] = [f'{e} = "{e}"' for e in scalar.enum_values]
        enum_value_str = "\n".join(enum_value_strs)
        s = f"class {scalar.node_name}(str, Enum):\n{indent_lines(enum_value_str)}"
        enum_strs.append(s)
    return "\n".join(enum_strs)


def build_node_link_function_str(link: Link) -> str:
    link_resolver_name = f"{link.target.model_name}Resolver"
    return f"""
async def {link.name}(
    self,
    resolver: {link_resolver_name} = None,
    refresh: bool = False,
    force_use_stale: bool = False,
) -> {link.type_str}:
    return await self.resolve(
        edge_name="{link.name}",
        edge_resolver=resolver or {link_resolver_name}(),
        refresh=refresh,
        force_use_stale=force_use_stale,
    )
    """


def build_resolver_link_function_str(node_resolver_name: str, link: Link) -> str:
    link_resolver_name = f"{link.target.model_name}Resolver"
    return f"""
def {link.name}(self, _: T.Optional[{link_resolver_name}] = None, /) -> {node_resolver_name}:
    if "{link.name}" in self._nested_resolvers:
        raise ResolverException("A resolver for `{link.name}` has already been provided.")
    self._nested_resolvers["{link.name}"] = _ or {link_resolver_name}()
    return self
    """


def build_get_functions_str(node_name: str, exclusive_field_names: T.Set[str]) -> str:
    exclusive_field_names = sorted(list(exclusive_field_names))
    params_fields_str = ", ".join(
        [f"{f}: T.Optional[T.Any] = None" for f in exclusive_field_names]
    )
    dict_fields_str = ", ".join([f'"{f}": {f}' for f in exclusive_field_names])
    get_str = f"""
async def get(self, given_client: AsyncIOClient = None, {params_fields_str}) -> T.Optional[{node_name}]:
    return await super().get(given_client=given_client, **{{{dict_fields_str}}})
    """
    gerror_str = f"""
async def gerror(self, given_client: AsyncIOClient = None, {params_fields_str}) -> {node_name}:
    return await super().gerror(given_client=given_client, **{{{dict_fields_str}}})
    """
    return f"{get_str}\n{gerror_str}"


def build_update_function_str(node_resolver_name: str, links: T.List[Link]) -> str:
    link_strs: T.List[str] = []
    link_names: T.List[str] = []
    for link in links:
        if link.readonly:
            continue
        link_strs.append(
            f"{link.name}: T.Optional[{link.target.model_name}Resolver] = None"
        )
        link_names.append(link.name)
    link_params_str = ", ".join(link_strs)
    return f"""
async def update(
    self,
    given_resolver: {node_resolver_name} = None,
    error_if_no_update: bool = False,
    batch: Batch = None,
    given_client: AsyncIOClient = None,
    {link_params_str}
) -> None:
    set_links_d = {{{", ".join([f'"{link_name}": {link_name}' for link_name in link_names])}}}
    set_links_d = {{key: val for key, val in set_links_d.items() if val is not None}}

    return await super().update(
        given_resolver=given_resolver,
        error_if_no_update=error_if_no_update,
        set_links_d=set_links_d,
        batch=batch,
        given_client=given_client
    )
    """


def add_quotes(lst: T.Iterable[str]) -> T.Iterable[str]:
    return [f'"{o}"' for o in lst]


def build_orm_config(
    model_name: str, updatable_fields: T.Set[str], exclusive_fields: T.Set[str]
) -> str:
    return f"""
class {CONFIG_NAME}:
    model_name = "{model_name}"
    client = client
    updatable_fields: T.Set[str] = {{{', '.join(add_quotes(sorted(list(updatable_fields))))}}}
    exclusive_fields: T.Set[str] = {{{', '.join(add_quotes(sorted(list(exclusive_fields))))}}}
    """


def stringify_dict(d: T.Union[T.Dict[str, str], str]) -> str:
    if type(d) is not dict:
        s = f"{d}"
        if type(d) is not bool:
            s = f'"{s}"'
        return s
    inner = [f'"{k}":{stringify_dict(v)}' for k, v in d.items()]
    return f"{{{','.join(inner)}}}"


def stringify_set(s: T.Set[str]) -> str:
    strs: T.List[str] = [f'"{i}"' for i in s]
    return "{" + ",".join(strs) + "}"


def edgedb_conversion_type_from_prop(prop: Property) -> str:
    s = prop.target.name
    pattern = r"default::\w+"
    s = re.sub(pattern, "std::str", s)
    return s


def build_node_and_resolver(object_type: ObjectType, hydrate: bool) -> str:
    # need to sort props and links by required, exclusive, no default, rest
    object_type.properties.sort(
        key=lambda x: f"{not x.is_computed}-{x.required}-{x.is_exclusive}-{x.default}",
        reverse=True,
    )
    object_type.links.sort(
        key=lambda x: f"{not x.is_computed}-{x.required}-{x.is_exclusive}-{x.default}",
        reverse=True,
    )
    # start with the properties
    node_resolver_name = f"{object_type.node_name}Resolver"
    property_strs: T.List[str] = []
    insert_property_strs: T.List[str] = []
    updatable_fields: T.Set[str] = set()
    exclusive_fields: T.Set[str] = set()

    node_edgedb_conversion_map: T.Dict[str, T.Dict[str, str]] = {}
    insert_edgedb_conversion_map: T.Dict[str, T.Dict[str, str]] = {}

    computed_properties: T.Set[str] = set()
    computed_property_getter_strs: T.List[str] = []

    for prop in object_type.properties:
        conversion_type = edgedb_conversion_type_from_prop(prop)
        node_edgedb_conversion_map[prop.name] = {
            "cast": conversion_type,
            "cardinality": prop.cardinality.value,
            "readonly": prop.readonly,
        }
        if prop.is_computed:
            computed_properties.add(prop.name)
        if not prop.readonly and not prop.is_computed:
            updatable_fields.add(prop.name)
        if prop.is_exclusive:
            exclusive_fields.add(prop.name)
        default_value_str = "..." if prop.required else "None"
        allow_mutation_str = (
            f"allow_mutation={not prop.readonly and not prop.is_computed}"
        )
        if not prop.is_computed:
            property_strs.append(
                f"{prop.name}: {prop.type_str} = Field({default_value_str}, {allow_mutation_str})"
            )
        else:
            property_strs.append(
                f"_{prop.name}: T.Union[Unset, {prop.type_str}] = PrivateAttr(default_factory=Unset)"
            )
            computed_property_getter_strs.append(
                f"""
@property
def {prop.name}(self) -> {prop.type_str}:
    if is_unset(self._{prop.name}):
        if "{prop.name}" in self.extra:
            self._{prop.name} = self.extra["{prop.name}"]
        else:
            raise ComputedPropertyException("{prop.name} is unset")
    return self._{prop.name}
                """
            )
        # for insert type
        if prop.name != "id":
            if not prop.is_computed and not prop.not_insertable:
                insert_edgedb_conversion_map[prop.name] = {
                    "cast": conversion_type,
                    "cardinality": prop.cardinality.value,
                    "readonly": prop.readonly,
                }
                insert_type_str = prop.type_str
                # if required but has default, add optional back
                if prop.required and prop.default:
                    insert_type_str = f"T.Optional[{insert_type_str}]"
                default_value_str = (
                    " = None" if insert_type_str.startswith("T.Optional[") else ""
                )
                insert_property_strs.append(
                    f"{prop.name}: {insert_type_str}{default_value_str}"
                )
    link_function_strs: T.List[str] = []
    resolver_function_strs: T.List[str] = []
    updatable_links: T.Set[str] = set()
    exclusive_links: T.Set[str] = set()
    link_conversion_map: T.Dict[str, T.Dict[str, str]] = {}

    for link in object_type.links:
        if link.name == "__type__":
            continue
        link_conversion_map[link.name] = {
            "cast": link.target.model_name,
            "cardinality": link.cardinality.value,
            "readonly": link.readonly,
            "required": link.required,
        }
        if not link.readonly and not link.is_computed:
            updatable_links.add(link.name)
        if link.is_exclusive:
            exclusive_links.add(link.name)
        link_function_strs.append(build_node_link_function_str(link))
        resolver_function_strs.append(
            build_resolver_link_function_str(
                node_resolver_name=node_resolver_name, link=link
            )
        )
        # for insert
        if not link.is_computed and not link.not_insertable:
            insert_resolver_str = f"{link.target.model_name}Resolver"
            if (not link.required) or (link.required and link.default):
                insert_resolver_str = f"T.Optional[{insert_resolver_str}]"
            default_value_str = (
                " = None" if insert_resolver_str.startswith("T.Optional[") else ""
            )
            insert_property_strs.append(
                f"{link.name}: {insert_resolver_str}{default_value_str}"
            )
    orm_config_str = build_orm_config(
        model_name=object_type.node_name,
        updatable_fields={*updatable_fields, *updatable_links},
        exclusive_fields={*exclusive_fields, *exclusive_links},
    )

    insert_model_name = f"{object_type.node_name}Insert"

    # insert type
    insert_inner_str = "\n".join(insert_property_strs)
    insert_conversion_map_str = f"_edgedb_conversion_map: T.ClassVar[T.Dict[str, str]] = {stringify_dict(insert_edgedb_conversion_map)}"
    insert_s = f"class {insert_model_name}(BaseModel):\n{indent_lines(insert_inner_str)}\n\n{indent_lines(insert_conversion_map_str)}"

    # node
    node_properties_str = "\n".join(property_strs)
    computed_property_getter_str = "\n".join(computed_property_getter_strs)
    node_conversion_map_str = f"_edgedb_conversion_map: T.ClassVar[T.Dict[str, str]] = {stringify_dict(node_edgedb_conversion_map)}"
    insert_link_conversion_map_str = f"_link_conversion_map: T.ClassVar[T.Dict[str, str]] = {stringify_dict(link_conversion_map)}"
    computed_properties_str = f"_computed_properties: T.ClassVar[T.Set[str]] = {stringify_set(computed_properties)}"
    node_link_functions_str = "\n".join(link_function_strs)
    update_function_str = build_update_function_str(
        node_resolver_name=node_resolver_name, links=object_type.links
    )
    node_inner_strs = [
        node_properties_str,
        "\n",
        computed_property_getter_str,
        node_conversion_map_str,
        insert_link_conversion_map_str,
        computed_properties_str,
        node_link_functions_str,
        update_function_str,
        orm_config_str,
    ]
    node_inner_str = "\n".join(node_inner_strs)
    inherits = (
        f"Node[{insert_model_name}]"
        if not hydrate
        else f"{object_type.node_name}Hydrated"
    )
    node_s = (
        f"class {object_type.node_name}({inherits}):\n{indent_lines(node_inner_str)}"
    )

    # resolver
    resolver_properties_str = f"_node = {object_type.node_name}"
    resolver_link_functions_str = "\n".join(resolver_function_strs)
    resolver_get_functions_str = build_get_functions_str(
        node_name=object_type.node_name, exclusive_field_names=exclusive_fields
    )
    resolver_inner_strs = [
        resolver_properties_str,
        resolver_link_functions_str,
        resolver_get_functions_str,
    ]
    resolver_inner_str = "\n".join(resolver_inner_strs)
    resolver_s = f"class {node_resolver_name}(Resolver[{object_type.node_name}]):\n{indent_lines(resolver_inner_str)}"

    final_s = (
        f"{object_type.node_name}.{CONFIG_NAME}.resolver_type = {node_resolver_name}"
    )
    return f"{insert_s}\n{node_s}\n{resolver_s}\n{final_s}"


async def build_nodes_and_resolvers(
    client: edgedb.AsyncIOClient, nodes_to_hydrate: T.Set[str]
) -> str:
    object_types = await introspect_objects(client)
    node_strs: T.List[str] = []
    for object_type in object_types:
        node_strs.append(
            build_node_and_resolver(
                object_type, hydrate=object_type.node_name in nodes_to_hydrate
            )
        )
    update_forward_refs_str = "\n".join(
        [f"{o.node_name}Insert.update_forward_refs()" for o in object_types]
    )
    nodes_str = "\n".join(node_strs)
    return f"{nodes_str}\n\n{update_forward_refs_str}"


class DBVendor(str, Enum):
    edgedb = "edgedb"


class TLSSecurity(str, Enum):
    insecure = "insecure"


class NodeConfig(BaseModel):
    module_path: str


class DBConfig(BaseModel):
    vendor: DBVendor
    host: str
    password: str
    port: int = 5656
    tls_security: TLSSecurity
    hydrate: bool = False
    nodes: T.Dict[str, NodeConfig] = dict()


def build_client(db_config: DBConfig) -> str:
    return f"""
client = create_async_client(
    tls_security="{db_config.tls_security.value}",
    host="{db_config.host}",
    password="{db_config.password}", 
    port={db_config.port}
)
    """


def validate_output_path(path: Path) -> None:
    if not os.path.isdir(path):
        if os.path.isfile(path):
            raise GeneratorException(
                f"output path {path=} must be a directory, not a file."
            )
        if not os.path.exists(path):
            os.makedirs(path)


def build_hydrate_imports(db_config: DBConfig) -> str:
    import_strs: T.List[str] = []
    for node_name, config in db_config.nodes.items():
        if config.module_path:
            hydrated_name = f"{node_name}Hydrated"
            import_strs.append(
                f"from {config.module_path} import {node_name} as {hydrated_name}"
            )
            # idk why i have the part below, was just copying from dgraph_orm, seems unecessary and wrong
            # import_strs.append(
            #     f"{hydrated_name}.{CONFIG_NAME}.resolver._node = {hydrated_name}"
            # )
    return "\n".join(import_strs)


def get_nodes_to_hydrate(db_config: DBConfig) -> T.Set[str]:
    node_names: T.Set[str] = set()
    for node_name, config in db_config.nodes.items():
        if config.module_path:
            node_names.add(node_name)
    return node_names


async def build_from_config(db_config_d: dict, hydrate: bool = False) -> str:
    db_config = DBConfig.parse_obj(db_config_d)
    client = edgedb.create_async_client(
        tls_security=db_config.tls_security,
        host=db_config.host,
        password=db_config.password,
        port=db_config.port,
    )
    imports_str = imports()
    client_str = build_client(db_config)
    hydrate_imports = "" if not hydrate else build_hydrate_imports(db_config)
    enums_str = await build_enums(client)
    nodes_and_resolvers_str = await build_nodes_and_resolvers(
        client,
        nodes_to_hydrate=set() if not hydrate else get_nodes_to_hydrate(db_config),
    )

    s = "\n".join(
        [imports_str, client_str, hydrate_imports, enums_str, nodes_and_resolvers_str]
    )
    s = format_str(s, mode=FileMode())
    return s


async def generate(config_path: Path, output_path: Path) -> None:
    validate_output_path(output_path)
    for db_name, db_config_d in json.loads(open(config_path).read()).items():
        s = await build_from_config(db_config_d=db_config_d)
        open(output_path / f"{db_name}.py", "w").write(s)
        if db_config_d.get("hydrate", False):
            s = await build_from_config(db_config_d=db_config_d, hydrate=True)
            open(output_path / f"{db_name}_hydrated.py", "w").write(s)
