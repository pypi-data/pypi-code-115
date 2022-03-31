from setuptools import setup

setup(
    name='ndmspc-api',
    version='0.0.1',    
    description='FastAPI Executor API',
    url='https://gitlab.com/ndmspc/api',
    author='Dominik Matis',
    author_email='domosino44@gmail.com',
    license='BSD 2-clause',
    packages=['executor'],
    install_requires=['fastapi==0.75.0'],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)