
import setuptools

setuptools.setup(
    name="smart-django-elasticsearch-dsl-drf",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['six>=1.9', 'django-nine>=0.1.10', 'django-elasticsearch-dsl>=0.3', 'elasticsearch-dsl', 'elasticsearch', 'djangorestframework'],
)
