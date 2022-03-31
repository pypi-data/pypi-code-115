
import setuptools

setuptools.setup(
    name="smart-hg-37",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['apache-airflow-backport-providers-exasol==2021.3.3'],
)
