import setuptools

setuptools.setup(
    name="simple_pass_manager",
    version="0.0.4",
    author="Zhmishenko Valery Albertovich",
    author_email="my_real_email@zhopa.com",
    description="A small description like my d",
    long_description="my supa mega fancy lib big description like my d",
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=["setuptools>=42", "cryptography>=36.0.2"],
    python_requires=">=3.9.7",
)
