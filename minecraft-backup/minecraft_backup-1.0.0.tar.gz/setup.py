# -*- coding: utf-8 -*-
import textwrap
from pathlib import Path
from setuptools import setup, find_packages

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text()

setup(
    name="minecraft_backup",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.6.8",
    entry_points={
        "console_scripts": {
            "minecraft-backup=minecraft_backup.main:main"
        }
    },
    description=textwrap.dedent("""\
        This is a backup management library for Minecraft servers.
        It should be run and used on a regular basis using cron or similar.
    """),
    author="Heitor Hirose",
    author_email="Heitorhirose@gmail.com",
    url="https://github.com/HEKUCHAN/minecraft_server_backup_python",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Programming Language :: Python :: 3.6",
    ],
    include_package_data=True,
    keywords=[
        "Image Registration"
    ],
    license="MIT License",
    install_requires=[
        "pathlib",
        "argparse",
        "fabric3"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
