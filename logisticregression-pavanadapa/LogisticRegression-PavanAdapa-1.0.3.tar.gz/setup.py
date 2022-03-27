import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="LogisticRegression-PavanAdapa",
    version="1.0.3",
    author="Pavan Kumar Adapa",
    author_email="Pavan.adapa@uconn.edu",
    description="Package containing functions for logistic Regression",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pavanadapa/LogisticRegression",
    project_urls={
        "Git": "https://github.com/pavanadapa/LogisticRegression",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    include_package_data=True
)