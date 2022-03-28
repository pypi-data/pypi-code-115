import setuptools

# with open("README.md", "r", encoding="utf-8") as fh:
#     long_description = fh.read()

with open("LICENSE.txt", "r", encoding="utf-8") as fh:
	license_content = fh.read()



setuptools.setup(
    name="aislab",
    version="0.0.14",
    author="Alexander Efremov",
    author_email="",
    description="AISLAB - AI System Laboratory - module for development of AI systems.",
#    long_description=long_description,
    long_description_content_type="text/markdown",
    license = license_content,
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy',	# 
        'copy',		# when x = y
        'os',		# for cmpr() 
        'warnings',	# 
        'time',		# tic(), toc()...
        'pandas',	# for input as data frame and for vidualization
        
    ],
    classifiers=[],
    python_requires='>=3.6',
)
