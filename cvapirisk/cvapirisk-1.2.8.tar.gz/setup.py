import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cvapirisk",
    version=os.environ.get("VER", "1.2.8"),
    author="CloudVector",
    author_email="support@cloudvector.com",
    description="API Specification Analysis for Risks and Compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3',
    entry_points = {
        'console_scripts':
        ['cvapirisk=cvsvc_apirisk.score.spec_security.cv_apirisk_assessment:main',
         'cvapiriskserver=cvsvc_apirisk.score.spec_security.cv_apirisk_server:main']
    },
    install_requires = [
        "openapi-spec-validator==0.2.8",
        "openapi3==1.0.0",
        "prance==0.19.0",
        "numpy==1.17.3",
        "networkx==2.4",
        "parsimonious==0.8.1",
        "sanic==20.3.0",
        "jinja2==2.11.3",
    ],
    include_package_data=True,
)
