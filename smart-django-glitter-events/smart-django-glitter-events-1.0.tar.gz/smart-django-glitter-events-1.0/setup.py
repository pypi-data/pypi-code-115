
import setuptools

setuptools.setup(
    name="smart-django-glitter-events",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['django-glitter', 'django-taggit>=0.21.3'],
)
