# PYTHON_ARGCOMPLETE_OK

import sys
from arghandler import subcmd, ArgumentHandler


from flutter_gen.figma.generate_text import FigmaGenerateTextCommand
from flutter_gen.config.config_cmd import ConfigCommand
from flutter_gen.generate.generate_image_cmd import GenerateImageCommand
from flutter_gen.generate.generate_localization_cmd import GenerateLocalizationCommand
from flutter_gen.generate.generate_object_mapper_cmd import GenerateObjectMapperCommand
from flutter_gen.generate.generate_stream_debug import GenerateStreamDebugCommand
from flutter_gen.generate.generate_router_cmd import GenerateRouterCommand
from flutter_gen.generate.sync_cmd import SyncCommand
from flutter_gen.create.create_cmd import CreateCommand
from flutter_gen.generate.watch_cmd import WatchCommand
from flutter_gen.rename.rename_cmd import RenameCommand
from flutter_gen.template.template_cmd import TemplateCommand
from flutter_gen.utils.intellij import Intellij
from . import __version__

# @subcmd("create", help="")
# def cmd_create(parser, context, args):
#     parser.description = ""
#     CreateCommand().create_app()


# @subcmd("rename", help="")
# def cmd_rename(parser, context, args):
#     parser.description = ""
#     args = parser.parse_args(args)
#     RenameCommand().rename_app()

@subcmd("template", help="")
def cmd_template(parser, context, args):
    parser.description = "."
    parser.add_argument("type", nargs=1, choices=[
                        "base"], help="template type")
    parser.add_argument("name", nargs=1, help="scene name")
    parser.add_argument(
        "--navigator", required=False, action="store_true", help="Register navigator"
    )
    args = parser.parse_args(args)
    template_name = args.type[0]
    scene_name = args.name[0]
    options = {
        "navigator": args.navigator
    }
    TemplateCommand(template_name, scene_name, options).create_files()


@subcmd("gen", help="code generator")
def cmd_generate(parser, context, args):
    parser.description = "code generator"
    parser.add_argument(
        "type",
        nargs=1,
        choices=["image", "localization", "object_mapper", "router"],
        help="type",
    )
    args = parser.parse_args(args)
    type = args.type[0]
    if type == "image":
        GenerateImageCommand().run()
    elif type == "localization":
        GenerateLocalizationCommand().run()
    elif type == "object_mapper":
        GenerateObjectMapperCommand().run()
    elif type == "router":
        GenerateRouterCommand().run()
    else:
        print("Invalid command")


@subcmd("sync", help="")
def cmd_template(parser, context, args):
    parser.description = ""
    SyncCommand().run()


@subcmd("watch", help="")
def cmd_template(parser, context, args):
    parser.description = ""
    WatchCommand().run()

# @subcmd("figma", help="create template files for a scene")
# def cmd_figma(parser, context, args):
#     parser.description = "Create template files for a scene."
#     parser.add_argument(
#         "type",
#         nargs=1,
#         choices=["text"],
#         help="type",
#     )
#     parser.add_argument("input", nargs=1, help="input text")
#     args = parser.parse_args(args)
#     type = args.type[0]
#     input = args.input[0]
#     if type == "text":
#         FigmaGenerateTextCommand(input).run()
#     else:
#         print("Invalid command")


# @subcmd("config", help="project")
# def cmd_config(parser, context, args):
#     parser.description = "image"
#     parser.add_argument("key", nargs="?", help="configuration key")
#     args = parser.parse_args(args)
#     key = args.key
#     cmd = ConfigCommand()
#     if key is None:
#         cmd.info()
#     elif key == "project":
#         cmd.create_config()
#     else:
#         print("Invalid command")


def exit_handler():
    Intellij.getInstance().to_file()


def main():
    handler = ArgumentHandler(
        use_subcommand_help=True,
        enable_autocompletion=True,
        epilog="Get help on a subcommand: flutter_gen subcommand -h",
    )
    handler.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
        help="show the version number",
    )
    if len(sys.argv) == 1:
        handler.run(["-h"])
    else:
        handler.run()
    exit_handler()


if __name__ == "__main__":
    main()
