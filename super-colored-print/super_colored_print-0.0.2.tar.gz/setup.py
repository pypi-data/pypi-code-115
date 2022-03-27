from setuptools import setup, find_packages

with open("README.md", "r") as f:
    page_description = f.read()



setup(
    name="super_colored_print",
    version="0.0.2",
    author="Victor Stein",
    author_email="victor.stein@outlook.com",
    description="Um pacote para facilitar a impressão de textos coloridos",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vitorStein/super-print-package",
    packages=find_packages(),
    install_requires=[],
    python_requires='>=3.8',
)