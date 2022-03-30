from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'Hi Kyong!'
LONG_DESCRIPTION = 'A pythonic way to say hi to our prof, prof Kyong. Inspired by https://github.com/tsivinsky/hi-mom.'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="hikyong", 
        version=VERSION,
        author="Yieh Yuheng",
        author_email="yiehyuheng@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=[], 
        
        keywords=['python', 'first package'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)