from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='jjlog',
    version='0.1',
    packages=['jjlog'],
    url='https://gitlab.com/mhliu8/jjlog',
    license='MIT',
    author='John Jang',
    author_email='mhliu8@gmail.com',
    description='logger with standard/common format',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
