import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='fingerprints-unam-colab',  
     version='0.22',
     author="Arturo Curiel",
     author_email="me@arturocuriel.com",
     description="Extraction of fingerprint and palm data from grayscale images.",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/forensics-colab-unam/fingerprints-unam-colab",
     packages=['huellas'],
     package_dir={'huellas' : 'huellas'},
     package_data={
         "huellas" : ["resources/images/*.png"],
     },
     install_requires=['wheel', 'numpy', 'scipy', 'matplotlib', 'opencv-python', 'pandas', 'scikit-image', 'sklearn', 'wxpython'],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     entry_points = {
         'console_scripts': ['fp_unam=huellas.gui:entry_point', 'extract_fp=huellas.extract_fp:entry_point'],
     },
 )
