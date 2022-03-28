
from setuptools import setup, find_packages
from openapi2awsapigateway.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='openapi2awsapigateway',
    version=VERSION,
    description='Adapt OpenAPI and Swagger files to include AWS API Gateway Integrations',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Joao Lopes',
    author_email='joao.lopes@athome.eu',
    url='https://github.com/athomegroup/openapi2awsapigateway',
    license='unlicensed',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    install_requires=[
        'cement==3.0.6',
        'jinja2',
        'pyyaml==6.0',
        'colorlog',
    ],
    package_data={'openapi2awsapigateway': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        openapi2awsapigateway = openapi2awsapigateway.main:main
    """,
)
