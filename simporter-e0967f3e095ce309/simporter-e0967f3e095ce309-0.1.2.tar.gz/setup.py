import io
import re

import setuptools

with io.open("flask_jwt_auth/__init__.py", encoding="utf-8") as f:
    version = re.search(r"__version__ = \"(.+)\"", f.read()).group(1)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='simporter-e0967f3e095ce309',
    version=version,
    author='Yaroslav Kikvadze',
    author_email='yaroslav.k@simporter.com',
    description='Flask JWT auth utils',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Simporter/flask-jwt-auth',
    license='MIT',
    packages=['flask_jwt_auth'],
    install_requires=['Flask>=1.1.4', 'PyJWT>=2.0.0'],
    python_requires=">=3.8",
)
