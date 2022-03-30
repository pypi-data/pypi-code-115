
import setuptools

setuptools.setup(
    name="smart-tripleo-heat-templates",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['pbr!=2.1.0,>=2.0.0', 'PyYAML>=3.12', 'Jinja2>=2.10', 'six>=1.10.0', 'tripleo-common>=7.1.0', 'paunch>=4.2.0'],
)
