from setuptools import setup

with open("readme.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='cuboid_sphere',
    version='0.1.0',
    packages=['cuboid_sphere'],
    url='https://github.com/bendangnuksung/cuboid_sphere',
    license='MIT License',
    author='bendangnuksung',
    author_email='bendangnuksungimsong@gmail.com',
    description='Finding Cuboid and Sphere in 3D Image and 2D image',
    install_requires=required,
    long_description_content_type="text/markdown",
    long_description=long_description,
    classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ],

)