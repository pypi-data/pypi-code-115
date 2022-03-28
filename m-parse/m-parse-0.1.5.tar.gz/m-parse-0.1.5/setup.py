from setuptools import setup, find_packages

install_requires = ['json', 'argparse', 'xlwt']

setup(name="m-parse",
    version="0.1.5",
    packages=find_packages('./m_parse'),
    package_dir={"":"m_parse"},
    include_package_data=False,
    package_data={"data":[]},
    description="该工具用于解析json,输出csv,excel格式的数据",
    author="miaoxin",
    author_email="miaorulai@gmail.com",
    url='',
    license="MIT",
    install_requires=[],
    entry_points = {'console_scripts': "m-parse = main:main"}
)
