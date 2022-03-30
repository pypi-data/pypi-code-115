import setuptools


setuptools.setup(
    name="rflow_test",
    version="0.0.0",
    description ="Rflow CLI",
    packages = setuptools.find_packages('src'),
    package_dir={'':'src'},
    author="LI, FUU",
    author_email = "rflowteam@rakuten.com",
    licence="",
    install_requires=['click', 'jwt','requests'],

)

