import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="myqqa",
    version="0.0.1",
    author="pythonnic",
    author_email="2696047693@qq.com",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.kancloud.cn/pythonnic/python/2682628",
    project_urls={
        "Bug Tracker": "https://github.com/maisge/myqq/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)