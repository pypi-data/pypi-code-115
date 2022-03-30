
import setuptools

setuptools.setup(
    name="smart-spartacus",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['pyscrypt', 'pyaes', 'openpyxl==2.5.14', 'click', 'sqlparse', 'tabulate', 'bs4', 'lxml', 'Pillow', 'pyexcel', 'pyexcel-xls', 'pyexcel-xlsx', 'cryptography'],
)
