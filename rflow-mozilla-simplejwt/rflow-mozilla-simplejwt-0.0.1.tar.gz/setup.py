import setuptools

setuptools.setup(
    name="rflow-mozilla-simplejwt",
    version="0.0.1",
    description="rflow-rest-framework-simplejwt",
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    author="LI, FUU，SOTA",
    author_email="rflowteam@rakuten.com",
    licence="",
    install_requires=["django",
                      "djangorestframework",
                      "pyjwt>=1.7.1,<3", ],

)
