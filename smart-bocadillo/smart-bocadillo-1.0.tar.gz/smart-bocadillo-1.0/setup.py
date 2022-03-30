
import setuptools

setuptools.setup(
    name="smart-bocadillo",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['starlette>=0.12.2, <0.13', 'uvicorn>=0.7, <0.9', 'typesystem>=0.2.2', 'jinja2>=2.10.1', 'whitenoise', 'requests', 'python-multipart', 'aiodine>=1.2.5, <2.0'],
)
