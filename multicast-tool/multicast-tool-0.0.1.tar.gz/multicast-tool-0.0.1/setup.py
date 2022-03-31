import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="multicast-tool",
    version="0.0.1",
    author="Michael Barry",
    author_email="mbarry@packetdriving.com",
    description="Multicast Sender and Receiver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/barryCrunch/multicast-tool",
    project_urls={
        "Bug Tracker": "https://github.com/barryCrunch/multicast-tool/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8.2",
)
