from setuptools import setup

setup(
    name='py_sonify',
    url='https://github.com/Marwolfer/pyson',
    author='Marco Wolfer',
    author_email = "marcowolfer42@gmail.com",
    version = "0.1.0",
    packages=['py_sonify'],
    install_requires=[
        'matplotlib',
        "numpy",
        "scipy",
        "mingus",
        "pydub"],
)