from setuptools import setup, find_packages

with open("README.md", "r") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="package_operacoes",
    version="0.0.2",
    author="nelson_lara",
    author_email="nelsonlarajr@gmail.com",
    description="Operações de Soma e Subtração",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/laranelson/project_calc_package.git",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
)