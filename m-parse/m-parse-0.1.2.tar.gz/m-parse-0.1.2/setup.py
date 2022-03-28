from setuptools import setup, find_packages


setup(name="m-parse",
    version="0.1.2",
    packages=find_packages(where="./src/"),
    package_dir={"":"src"},
    include_package_data=False,
    package_data={"data":[]},
    description="该工具用于解析json,输出csv,excel格式的数据",
    author="miaoxin",
    author_email="miaorulai@gmail.com",
    url='',
    license="MIT",
    install_requires=[],
    entry_points = {'console_scripts': "m-parse = src.main:main"}
)
