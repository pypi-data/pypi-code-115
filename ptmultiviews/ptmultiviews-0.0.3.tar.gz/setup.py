import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ptmultiviews",
    version="0.0.3",
    description="Apache Multiviews Detection & Enumeration Tool",
    author="Penterep",
    author_email="info@penterep.com",
    url="https://www.penterep.com/",
    license="GPLv3+",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Environment :: Console"
    ],
    python_requires='>=3.6',
    install_requires=["ptlibs", "requests", "ptthreads"],
    entry_points = {'console_scripts': ['ptmultiviews = ptmultiviews.ptmultiviews:main']},
    long_description=long_description,
    long_description_content_type="text/markdown",
)
