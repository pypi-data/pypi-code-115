from setuptools import setup

with open('requirements.txt', 'r') as myfile:
    for line in myfile:
        result = [item for item in line.strip().split()]
setup(
    name="omltesi",
    packages=["omltesi"],
    version="0.1.0",
    description="put your description here",
    install_requires=result
)

