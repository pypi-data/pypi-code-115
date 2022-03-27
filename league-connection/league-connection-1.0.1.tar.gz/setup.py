import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='league-connection',
    version='1.0.1',
    author='Pradish Bijukchhe',
    author_email='pradishbijukchhe@gmail.com',
    description='Python package to communicate to riot client and league client',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sandbox-pokhara/league-connection',
    project_urls={
        'Bug Tracker': 'https://github.com/sandbox-pokhara/league-connection/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
    package_dir={'': '.'},
    packages=setuptools.find_packages(where='.'),
    python_requires='>=3.6',
    install_requires=['requests'],
)
