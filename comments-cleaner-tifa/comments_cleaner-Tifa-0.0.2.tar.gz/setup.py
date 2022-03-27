import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="comments_cleaner-Tifa",
    version="0.0.2",
    author="Tifa",
    author_email="tiphereth-a@qq.com",
    description="Comments cleaner, Support C/C++",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tiphereth-A/cmcleaner",
    project_urls={
        "Bug Tracker": "https://github.com/Tiphereth-A/cmcleaner/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    license="GNU General Public License v3.0",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
