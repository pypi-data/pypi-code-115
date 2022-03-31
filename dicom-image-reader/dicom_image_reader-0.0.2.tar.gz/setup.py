from setuptools import setup, find_packages

VERSION = '0.0.2'
DESCRIPTION = 'Python package to read images from DICOM files'
LONG_DESCRIPTION = 'Read pixel data from DICOM files like an image'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="dicom_image_reader",
        version=VERSION,
        author="Dibakar Saha",
        author_email="dibakarsaha1234@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['pydicom', 'pylibjpeg-libjpeg', 'python-gcm'], # add any additional packages that
        # needs to be installed along with your package. Eg: 'caer'

        keywords=['python', 'first package'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)
