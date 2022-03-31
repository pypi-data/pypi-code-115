import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hjxdataconverter", 
    version="1.0.0",
    author="Isabel Sandstrøm",
    author_email="isabel@hermit.no",
    description="Python command line program for converting data between json, html and excel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=['programs'],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'hjxdataconverter = programs.hjxdataconverter:main',
            'excel2json = programs.excel2json:main', 
            'html2json = programs.html2json:main',
            'json2excel = programs.json2excel:main',
            'json2html = programs.json2html:main'
            ]        
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)   