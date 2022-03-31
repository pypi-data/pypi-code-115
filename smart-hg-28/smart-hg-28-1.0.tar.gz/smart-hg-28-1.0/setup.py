
import setuptools

setuptools.setup(
    name="smart-hg-28",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['pandas==1.2.4', 'apache-airflow-backport-providers-segment==2021.3.17'],
)
