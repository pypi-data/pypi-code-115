
import setuptools

setuptools.setup(
    name="smart-django-glitter",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['Django>=1.8,<1.10', 'django-mptt>=0.7', 'django-mptt-admin>=0.3', 'sorl-thumbnail>=12.2', 'django-taggit>=0.21.3', 'python-dateutil>=2.6.0'],
)
