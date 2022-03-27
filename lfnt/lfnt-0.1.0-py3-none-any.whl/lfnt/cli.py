import click
import os
from pprint import pprint
from click_configfile import ConfigFileReader, Param, SectionSchema
from click_configfile import matches_section


class ConfigSectionSchema(object):
    """Describes all config sections of this configuration file."""

    @matches_section("profile")
    class Profile(SectionSchema):
        name = Param(type=str)
        email = Param(type=str)
        git_provider = Param(type=str)
        config_repo = Param(type=str)


class ConfigFileProcessor(ConfigFileReader):
    home = os.getenv("HOME")
    config_files = [f"{home}/.lfntrc"]
    config_section_schemas = [
        ConfigSectionSchema.Profile,
    ]


CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor.read_config())


@click.group(context_settings=CONTEXT_SETTINGS)
def lfnt():
    """A python package for eating elephants."""
    pass


lfnt_group = lfnt.group(context_settings=CONTEXT_SETTINGS)
lfnt_command = lfnt.command(context_settings=CONTEXT_SETTINGS)


# init
@lfnt_command
def init():
    """Initialize a .lfntrc file."""
    pass


# install
@lfnt_command
def install():
    """Install a package or application and add to .lfntrc file."""
    pass


@lfnt_command
def uninstall():
    """Uninstall a package or application and remove from .lfntrc file."""
    pass


# sync
@lfnt_command
def sync():
    """Sync local workstation with .lfntrc file."""
    pass


# config
@lfnt_group
def config():
    """Lfnt configuration commands."""
    pass


config_command = config.command(context_settings=CONTEXT_SETTINGS)


@config_command
def show():
    pprint(CONTEXT_SETTINGS["default_map"])


if __name__ == "__main__":
    lfnt()
