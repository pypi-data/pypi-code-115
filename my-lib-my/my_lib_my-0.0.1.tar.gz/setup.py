from setuptools import setup

# Qy2b-fTLDn3x_KPfnXRM
VERSION = '0.0.1'

setup(
    name="my_lib_my",
    author="Dmitriy Ignatiev",
    author_email="dmitriy.ignatiev83@gmail.com",
    version=VERSION,
    py_modules=["my_lib"],
    description="Пакет",
    long_description="""
    Пакет
    """,
    install_requires=[
        "loguru"
    ]
)
