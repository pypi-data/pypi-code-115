import setuptools



setuptools.setup(
    name='newsp',
    version='0.15',
    scripts=['newsp'],
    author="Thanh Hoa",
    author_email="getmoneykhmt3@gmail.com",
    description="A Des of newsp",
    long_description="newsp",
    long_description_content_type="text/markdown",
    url="https://github.com/vtandroid/newsp",
    packages=setuptools.find_packages(),
    py_modules=['newspp'],
    install_requires=[
       'newspaper3k','awesome-slugify','pillow','spacy'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
 )