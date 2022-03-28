import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ptsamesite",
    description="Same Site Scripting Tester",
    author="Penterep",
    author_email="info@penterep.com",
    url="https://www.penterep.com/",
    version="0.0.4",
    license="GPLv3+",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Environment :: Console"
    ],
    python_requires='>=3.6',
    install_requires=["dnspython>=2.1", "tldextract", "ptlibs>=0.0.6", "ptthreads"],
    entry_points = {'console_scripts': ['ptsamesite = ptsamesite.ptsamesite:main']},
    include_package_data= True,
    long_description=long_description,
    long_description_content_type="text/markdown",
)