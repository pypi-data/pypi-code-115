import setuptools


with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="oilprop",
    version="0.0.1",
    author="Buzovskyi Vitalii",
    author_email="buzovskiy.v@gmail.com",
    description="Oil properties calculator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        'Project on GitHub': "https://github.com/Buzovskiy/oilprop/releases/tag/v0.0.1",
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires='>=3.8',
)
