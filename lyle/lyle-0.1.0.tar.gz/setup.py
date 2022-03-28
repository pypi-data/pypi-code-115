import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lyle",
    version="0.1.0",
    author="Lyle Okoth",
    author_email="lyleokoth@gmail.com",
    description="Demo your first Pip package.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lyleokoth/pypi-package-template",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords='pip-demo lyle',
    project_urls={
        'Homepage': 'https://github.com/lyleokoth/pypi-package-template',
    },

)