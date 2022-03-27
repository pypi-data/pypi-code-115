'''Setup.'''


import setuptools

DIST_NAME = 'infographics'
with open('README.md', 'r') as fh:
    long_description = fh.read()

MAJOR, MINOR, PATCH = 2, 0, 0
VERSION = '%d.%d.%d' % (MAJOR, MINOR, PATCH)

setuptools.setup(
    name='%s-nuuuwan' % DIST_NAME,
    version=VERSION,
    author='Nuwan I. Senaratna',
    author_email='nuuuwan@gmail.com',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nuuuwan/%s' % DIST_NAME,
    project_urls={
        'Bug Tracker': 'https://github.com/nuuuwan/%s/issues' % DIST_NAME,
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    python_requires='>=3.6',
    install_requires=[
        'utils-nuuuwan',
        'gig-nuuuwan',
        'geo-nuuuwan',
        'cairosvg',

    ],
)
