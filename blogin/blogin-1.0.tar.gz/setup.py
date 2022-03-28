import setuptools



with open("README.md", "r") as fh:

    long_description = fh.read()



setuptools.setup(

    name="blogin", 

    version="1.0",

    author="BotolMehedi",

    author_email="Botol@email.com",

    description="Login",

    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
    long_description_content_type='text/markdown',

    url="https://github.com/BotolMehedi/bdroid",
    
    packages=setuptools.find_packages(),

    classifiers=[

        "Programming Language :: Python :: 2",

        "License :: OSI Approved :: MIT License",

        "Operating System :: OS Independent",

    ],

    python_requires='>=2.7',
    entry_points={'console_scripts': ['blogin=blogin.__init__:blogin']}

)
