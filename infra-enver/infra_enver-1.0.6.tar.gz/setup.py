from setuptools import find_packages, setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "readme.md").read_text()

setup(
    name='infra_enver',
    packages=find_packages(include=['infra_enver']),
    version='1.0.6',
    description='Infra Enver',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Daniil Vladimirov',
    license='MIT',
    install_requires=['requests', 'pydantic', 'redis'],
)
