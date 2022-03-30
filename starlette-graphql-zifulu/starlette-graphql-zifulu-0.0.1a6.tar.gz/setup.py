import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="starlette-graphql-zifulu", # Replace with your own username
    version="0.0.1a6",
    author="zifulu",
    author_email="zifulu@zifulu.com",
    description="GraphQL Server via Starlette",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'graphql-core==3.1.0',
        'python-gql==0.1.2',
        'starlette==0.13.3',
        'typing-extensions==3.7.4.2',
        'gql-subscriptions==0.0.2'
    ]
)
