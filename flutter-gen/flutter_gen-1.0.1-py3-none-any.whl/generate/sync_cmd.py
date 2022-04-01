# coding=utf-8

from flutter_gen.generate.generate_router_cmd import GenerateRouterCommand
from .generate_image_cmd import GenerateImageCommand
from .generate_localization_cmd import GenerateLocalizationCommand
from .generate_object_mapper_cmd import GenerateObjectMapperCommand
from ..core.command import Command
import os


class SyncCommand(Command):
    def __init__(self):
        super(SyncCommand, self).__init__()

    def run(self):
        GenerateImageCommand().run()
        GenerateLocalizationCommand().run()
        GenerateRouterCommand().run()
        # GenerateObjectMapperCommand().run()
        # GenerateStreamDebugCommand().run()
