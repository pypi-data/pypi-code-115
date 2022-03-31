
import setuptools

setuptools.setup(
    name="smart-hg-5",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['slackclient==1.3.2', 'apache-airflow-backport-providers-segment==2021.3.17'],
)
