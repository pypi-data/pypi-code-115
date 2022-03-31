from setuptools import setup

setup(
    name='ndmspc-api',
    version='0.0.2',    
    description='FastAPI Executor API',
    url='https://gitlab.com/ndmspc/api',
    author='Dominik Matis',
    author_email='domosino44@gmail.com',
    license='BSD 2-clause',
    packages=['executor'],
    install_requires=['fastapi==0.75.0']
)
