from posixpath import dirname
from textwrap import indent
from typing import *
from susc import SusFile
from susc.things import *
from os import makedirs, path, write
from susc import log
from colorama import Fore

LICENSE = """ * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
 * associated documentation files (the “Software”), to deal in the Software without restriction,
 * including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 *
 * THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
 * LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
 * NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

def snake_to_pascal(name: str) -> str:
    words = name.split("_")
    return "".join(w[0].upper() + w[1:] for w in words)
def snake_to_camel(name: str) -> str:
    pascal = snake_to_pascal(name)
    return pascal[0].lower() + pascal[1:]

def regex_flags(pattern: re.Pattern):
    fstr = ""
    if pattern.flags & re.I: fstr += "i"
    if pattern.flags & re.M: fstr += "m"
    if pattern.flags & re.S: fstr += "s"
    return fstr
def type_validators(type_: SusType):
    vals = []
    for validator in type_.validators:
        val = validator.param + ": "
        restr = validator.restriction
        if isinstance(restr, re.Pattern): val += f"/{restr.pattern}/{regex_flags(restr)}"
        elif isinstance(restr, int): val += str(restr)
        elif isinstance(restr, str): val += restr
        elif isinstance(restr, range): val += f"[{restr[0]}, {restr[-1]}]"
        vals.append(val)
    if len(vals) == 0:
        return "{}"
    return "{ " + ', '.join(vals) + " }"
def type_to_amogus(type_: SusType, obj_types: Dict[str, str]) -> str:
    if type_.name == "List":
        elements = type_to_amogus(type_.args[0], obj_types)
        return f"new amogus.repr.List({elements}, {type_.args[1]}, {type_validators(type_)})"

    if type_.name in obj_types:
        t_name = {
            "entities": "SpecificEntity",
            "bitfields": "EnumOrBf",
            "enums": "EnumOrBf",
            "confirmations": "Confirmation"
        }[obj_types[type_.name]]
        if t_name == "EnumOrBf":
            return f"new amogus.repr.EnumOrBf<{type_.name}>({type_.name}_SIZE)"
        return f"new amogus.repr.{t_name}({type_.name})"

    return f"new amogus.repr.{type_.name}({', '.join([str(x) for x in type_.args] + [''])}{type_validators(type_)})"

def write_output(root_file: SusFile, target_dir: str) -> None:
    proj_name = path.splitext(path.basename(root_file.path))[0]
    header = ("/* Generated by AMOGUS SUS (https://github.com/portasynthinca3/amogus)\n"
    f" * Project name: {proj_name}\n *\n"
    "" + LICENSE + "\n */\n\n")

    # display lib notice
    # log.info(f"TypeScript: Install the {Fore.GREEN}'amogus-driver'{Fore.WHITE} library from npm to make use of this output")

    # construct a name-to-type mapping
    objs = {}
    for thing in root_file.things:
        name = type(thing).__name__[3:].lower() + "s"
        if name == "entitys": # correct plural form
            name = "entities"
        objs[thing.name] = name

    with open(path.join(target_dir, "index.ts"), "w") as f:
        f.write(header)
        f.write("import * as amogus from \"amogus-driver\";\n\n")

        # write enums
        enums_and_bfs = [t for t in root_file.things if isinstance(t, (SusEnum, SusBitfield))]
        for thing in enums_and_bfs:
            write_docstr(f, thing)
            f.write(f"export enum {thing.name} {'{'}\n")
            for member in thing.members:
                write_docstr(f, member, 1)
                prefix = "" if isinstance(thing, SusEnum) else "1 << "
                f.write(f"\t{member.name} = {prefix}{member.value},\n")
            f.write("}\n")
            f.write(f"export const {thing.name}_SIZE = {thing.size};\n\n\n")

        # write confirmation
        confirmations = [t for t in root_file.things if isinstance(t, SusConfirmation)]
        for conf in confirmations:
            # write spec
            name = snake_to_pascal(conf.name)
            f.write(f"const {name}Spec = {'{'}\n")
            f.write("\trequest: {\n")
            write_field_array(f, conf.req_parameters, objs)
            f.write("\t},\n")
            f.write("\tresponse: {\n")
            write_field_array(f, conf.resp_parameters, objs)
            f.write("\t}\n")
            f.write("};\n")
            # write class
            write_docstr(f, conf)
            f.write(f"export class {name} extends amogus.Confirmation<typeof {name}Spec> {'{'}\n")
            f.write("\tconstructor() {\n")
            f.write(f"\t\tsuper({name}Spec, {conf.value});\n")
            f.write("\t}\n")
            f.write("}\n")

        # write global methods
        methods = [t for t in root_file.things if isinstance(t, SusMethod)]
        for method in methods:
            # write spec
            name = snake_to_pascal(method.name)
            f.write(f"const {name}Spec = {'{'}\n")
            f.write("\tparams: {\n")
            write_field_array(f, method.parameters, objs)
            f.write("\t},\n")
            f.write("\treturns: {\n")
            write_field_array(f, method.returns, objs)
            f.write("\t},\n")
            conf_names = ", ".join(f"new {snake_to_pascal(conf)}()" for conf in method.confirmations)
            f.write(f"\tconfirmations: [{conf_names}]\n")
            f.write("};\n")
            # write class
            write_docstr(f, method)
            f.write(f"export class {name} extends amogus.Method<typeof {name}Spec> {'{'}\n")
            f.write("\tconstructor() {\n")
            f.write(f"\t\tsuper({name}Spec, {method.value}, undefined);\n")
            f.write("\t}\n")
            f.write("}\n")
            # write function
            write_docstr(f, method)
            f.write(f"async function {snake_to_camel(method.name)}(\n")
            f.write("\tthis: any | amogus.session.BoundSession,\n")
            f.write(f"\tparams: amogus.FieldValue<typeof {name}Spec[\"params\"]>,\n")
            f.write(f"\tconfirm?: amogus.session.ConfCallback<{name}>,\n")
            f.write("\tsession?: amogus.session.Session\n")
            f.write(f"): Promise<amogus.FieldValue<typeof {name}Spec[\"returns\"]>> {'{'}\n")
            f.write(f"\tconst method = new {name}();\n")
            f.write(f"\tmethod.params = params;\n")
            f.write(f"\treturn await (session ?? this.session).invokeMethod(method, confirm);\n")
            f.write("}\n\n\n")

        # write entities
        entities = [t for t in root_file.things if isinstance(t, SusEntity)]
        for entity in entities:
            # write method specs and classes
            for method in entity.methods:
                name = f"{entity.name}_{snake_to_pascal(method.name)}"
                f.write(f"const {name}Spec = {'{'}\n")
                f.write("\tparams: {\n")
                write_field_array(f, method.parameters, objs)
                f.write("\t},\n")
                f.write("\treturns: {\n")
                write_field_array(f, method.returns, objs)
                f.write("\t},\n")
                conf_names = ", ".join(f"new {snake_to_pascal(conf)}()" for conf in method.confirmations)
                f.write(f"\tconfirmations: [{conf_names}]\n")
                f.write("};\n")
                write_docstr(f, method)
                f.write(f"export class {name} extends amogus.Method<typeof {name}Spec> {'{'}\n")
                f.write("\tconstructor() {\n")
                f.write(f"\t\tsuper({name}Spec, {method.value + (128 if method.static else 0)}, {entity.value});\n")
                f.write("\t}\n")
                f.write("}\n")

            # write spec
            name = entity.name
            f.write(f"const {name}Spec = {'{'}\n")
            f.write("\tfields: {\n")
            write_field_array(f, entity.fields, objs)
            f.write("\t},\n")
            f.write("\tmethods: {\n")
            for method in entity.methods:
                val = method.value + (128 if method.static else 0)
                f.write(f"\t\t{val}: new {entity.name}_{snake_to_pascal(method.name)}(),\n")
            f.write("\t}\n")
            f.write("};\n")
            # write class
            write_docstr(f, entity)
            f.write(f"export class {name} extends amogus.Entity<typeof {name}Spec> {'{'}\n")
            f.write("\tprotected static readonly session?: amogus.session.Session;\n")
            f.write("\tprotected readonly dynSession?: amogus.session.Session;\n\n")
            f.write(f"\tconstructor(value?: amogus.FieldValue<typeof {name}Spec[\"fields\"]>) {'{'}\n")
            f.write(f"\t\tsuper({name}Spec, {entity.value}, value);\n")
            f.write("\t}\n")

            # write method functions
            for method in entity.methods:
                name = f"{entity.name}_{snake_to_pascal(method.name)}"
                write_docstr(f, method, 1)
                static = "static " if method.static else ""
                f.write(f"\n\t{static}async {snake_to_camel(method.name)}(\n")
                f.write(f"\t\tparams: amogus.FieldValue<typeof {name}Spec[\"params\"]>,\n")
                f.write(f"\t\tconfirm?: amogus.session.ConfCallback<{name}>,\n")
                f.write("\t\tsession?: amogus.session.Session\n")
                f.write(f"\t): Promise<amogus.FieldValue<typeof {name}Spec[\"returns\"]>> {'{'}\n")
                f.write(f"\t\tconst method = new {name}();\n")
                f.write(f"\t\tmethod.params = params;\n")
                if method.static:
                    f.write("\t\treturn await (session ?? this.session)!.invokeMethod(method, confirm);\n")
                else:
                    f.write("\t\tif(!this.value) throw new Error(\"Entity must have a value\");\n")
                    f.write("\t\tmethod.entityId = this.value.id;\n")
                    f.write("\t\treturn await (session ?? this.dynSession)!.invokeMethod(method, confirm);\n")
                f.write("\t}\n")
            f.write("}\n\n\n")

        # write spec space
        f.write("\nexport const $specSpace = {\n")
        f.write("\tspecVersion: 1,\n")
        f.write("\tglobalMethods: {\n")
        for method in methods:
            f.write(f"\t\t{method.value}: new {snake_to_pascal(method.name)}(),\n")
        f.write("\t},\n")
        f.write("\tentities: {\n")
        for entity in entities:
            f.write(f"\t\t{entity.value}: new {entity.name}(),\n")
        f.write("\t},\n")
        f.write("\tconfirmations: {\n")
        for confirmation in confirmations:
            f.write(f"\t\t{confirmation.value}: new {confirmation.name}(),\n")
        f.write("\t}\n")
        f.write("};\n\n\n")

        # write bind()
        f.write("\nexport function $bind(session: amogus.session.Session) {\n")
        f.write("\treturn {\n")
        f.write("\t\tsession,\n")
        f.write("\t\t$close: async () => await session.stop(),\n")
        f.write("\t\t/*** METHODS ***/\n\n")
        for method in methods:
            write_docstr(f, method, 2)
            f.write(f"\t\t{snake_to_camel(method.name)},\n")
        f.write("\n\t\t/*** ENTITIES ***/\n\n")
        for entity in entities:
            write_docstr(f, entity, 2)
            f.write(f"\t\t{entity.name}: class extends {entity.name} {'{'}\n")
            f.write("\t\t\tprotected readonly dynSession = session;\n")
            f.write("\t\t\tprotected static readonly session = session;\n")
            f.write("\t\t},\n")
        f.write("\n\t\t/*** ENUMS AND BITFIELDS ***/\n\n")
        for thing in enums_and_bfs:
            write_docstr(f, thing, 2)
            f.write(f"\t\t{thing.name},\n")
        f.write("\t};\n")
        f.write("}\n")


def write_field_array(f, fields, objs, indent=2):
    indent = "\t" * indent

    f.write(f"{indent}required: {'{'}\n")
    for field in [f for f in fields if f.optional is None]:
        write_docstr(f, field, len(indent) + 1)
        f.write(f"{indent}\t{field.name}: {type_to_amogus(field.type_, objs)},\n")
    f.write(f"{indent}{'}'},\n")

    f.write(f"{indent}optional: {'{'}\n")
    for field in [f for f in fields if f.optional is not None]:
        write_docstr(f, field, len(indent) + 1)
        type_ = type_to_amogus(field.type_, objs)
        repr_class = type_[:type_.find("(")]
        repr_class = repr_class[4:] # remove "new "
        f.write(f"{indent}\t{field.name}: [{field.optional}, {type_}] as [number, {repr_class}],\n")
    f.write(f"{indent}{'}'}\n")


def write_docstr(f, thing: SusThing, indent=0):
    indent = "\t" * indent
    if not thing.docstring:
        return

    if thing.docstring.count("\n") == 0:
        f.write(f"{indent}// {thing.docstring}\n")
        return

    f.write(f"{indent}/*\n")
    for line in thing.docstring.split("\n"):
        f.write(f"{indent} * {line}\n")
    f.write(f"{indent} */\n")