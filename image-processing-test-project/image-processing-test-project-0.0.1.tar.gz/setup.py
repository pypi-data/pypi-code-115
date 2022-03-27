from setuptools import find_packages, setup

with open("README.md", "r") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="image-processing-test-project",
    version="0.0.1",
    author="Fernando Ventura",
    author_email="fernando_sventura@outlook.com",
    description="Test Version - Image Processing - Projeto Karina Kato",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Fehventura12/Image-Processing",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
)
