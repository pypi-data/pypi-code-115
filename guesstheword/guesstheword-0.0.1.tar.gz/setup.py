import setuptools

__version__ = "0.0.1"
__description__ = 'The package targets to help user in playing the game wordle'
__author__ = 'ASK Jennie Developer <saurabh@ask-jennie.com>'

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='guesstheword',
     version=__version__,
     author="ASK Jennie",
     py_modules=["jennie"],
     install_requires=['requests'],
     entry_points={
        'console_scripts': [
            'wordlehelper=wordlehelper:execute'
        ],
     },
     author_email=__author__,
     description= __description__,
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/dextrop/guesstheword",
     packages=setuptools.find_packages(),
     classifiers=[
         "License :: OSI Approved :: MIT License",
         "Programming Language :: Python :: 3",
         "Programming Language :: Python :: 3.7",
     ],
 )