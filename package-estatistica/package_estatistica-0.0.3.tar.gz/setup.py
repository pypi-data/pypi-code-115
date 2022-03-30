from setuptools import setup, find_packages

with open("README.md", "r") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="package_estatistica",
    version="0.0.3",
    author="Alessandro_Miranda_Goncalves",
    author_email="alessandro.inovacao@gmail.com",
    description="Engenheiro de dados e desenvolvedor de software",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alessandromirandagoncalves/package_estatistica.git",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.0',
)