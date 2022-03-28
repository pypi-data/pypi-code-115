from setuptools import setup, find_packages
from setuptools.command.install import install

setup(
    name='themesaver',
    version='1.2',
    description='A python script to manage your rices',
    url='https://github.com/techcoder20/themesaver',
    author='RPICoder',
    author_email='rpicoder@protonmail.com',
    license='GNU GENERAL PUBLIC LICENSE V3',
    packages=find_packages(),
    install_requires=[
        'Click',
        'pyqt5',
        'python-dotenv',
        'tqdm'
    ],
    entry_points={
        'console_scripts': [
            'themesaver = themesaver.themesaver:group',
        ],
    }
)

