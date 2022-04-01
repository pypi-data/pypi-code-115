from setuptools import setup

setup(
    name='cryptounifier',
    version='1.0.0',
    description='CryptoUnifier API Python Integration.',
    url='https://cryptounifier.io/',
    author='https://cryptounifier.io/',
    license='MIT License',
    packages=['cryptounifier'],
    install_requires=['requests'],

    package_dir={"": "src"},

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
