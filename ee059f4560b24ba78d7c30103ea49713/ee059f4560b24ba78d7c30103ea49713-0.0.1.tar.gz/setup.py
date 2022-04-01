from distutils.core import setup

setup(
    name='ee059f4560b24ba78d7c30103ea49713',
    packages=['ee059f4560b24ba78d7c30103ea49713'],
    version='0.0.1',
    license='gpl-3.0',
    description='ee059f4560b24ba78d7c30103ea49713',
    long_description=open('README.md').read(),
    author='Username',
    # author_email='username@example.com',
    url='https://pypi.python.org/pypi/ee059f4560b24ba78d7c30103ea49713/',
    scripts=['bin/generate-text.py'],
    install_requires=[
        "python-lorem>=1.1.2",
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        # 'Intended Audience :: Developers',
        # 'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
    ],
)
