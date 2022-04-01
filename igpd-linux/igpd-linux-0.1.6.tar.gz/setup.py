from setuptools import setup,find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_args = dict(
    name="igpd-linux", # Replace with your own username
    version="0.1.6",
    author='Ashwin.B',
    license='MIT',
    author_email = 'ahnashwin1305@gmail.com',
    url = 'https://github.com/ahn1305/igpd-linux',
    description="Download almost everything from instagram, from public accounts and from your followers",
    long_description = long_description,
    long_description_content_type= "text/markdown",
    py_modules = ["igpd_l","features"],
    package_dir = {'': 'src'},

    classifiers=[
 
    'Programming Language :: Python :: 3.6',      
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'License :: OSI Approved :: MIT License',  
    'Operating System :: POSIX :: Linux',
  ],
)


install_requires = [
	'instaloader==4.5.5',
	'printtools==1.2',
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)
