import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdk_pigeon.core",
    "version": "0.1.0",
    "description": "AWS Synthetics Canary alternative built for minimal cost ",
    "license": "Apache-2.0",
    "url": "https://github.com/thomasstep/cdk-pigeon.git",
    "long_description_content_type": "text/markdown",
    "author": "Thomas Step<tstep916@gmail.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/thomasstep/cdk-pigeon.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdk_pigeon.core",
        "cdk_pigeon.core._jsii"
    ],
    "package_data": {
        "cdk_pigeon.core._jsii": [
            "cdk-pigeon@0.1.0.jsii.tgz"
        ],
        "cdk_pigeon.core": [
            "py.typed"
        ]
    },
    "python_requires": ">=3.6",
    "install_requires": [
        "aws-cdk-lib>=2.18.0, <3.0.0",
        "constructs>=10.0.0, <11.0.0",
        "jsii>=1.55.1, <2.0.0",
        "publication>=0.0.3"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Typing :: Typed",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved"
    ],
    "scripts": [
        "src/cdk_pigeon/core/_jsii/bin/cdk-pigeon"
    ]
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
