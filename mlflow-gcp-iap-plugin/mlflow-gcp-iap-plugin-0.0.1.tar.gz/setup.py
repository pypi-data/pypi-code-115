from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mlflow-gcp-iap-plugin",
    version="0.0.1",
    author="Nathan Price",
    author_email="nathan@abridge.com",
    description="Test plugin for MLflow.  Allows using URI which is behind IAP by setting environment variable of 'MLFLOW_IAP_CLIENT_ID' to the client id of the IAP.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/abridge-ai/mlflow-gcp-iap-plugin",
    packages=find_packages(where="src"),
    install_requires=["mlflow", "google-auth", "google-oauth"],
    project_urls={
        "Bug Tracker": "https://bitbucket.org/abridge-ai/mlflow-gcp-iap-plugin/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    entry_points={
        # Define a RequestHeaderProvider plugin. The entry point name for request header providers
        "mlflow.request_header_provider": "https=src.mlflow_gcp_iap_plugin.request_header_provider:PluginRequestHeaderProvider",  # pylint: disable=line-too-long
    },
    python_requires=">=3.6",
)
