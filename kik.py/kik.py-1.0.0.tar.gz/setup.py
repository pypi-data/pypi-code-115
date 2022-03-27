from setuptools import setup, find_packages

with open("README.md", "r") as stream:
    long_description = stream.read()

requirements = [
    "requests",
    "json_minify", 
    "six"
]

setup(
    name="kik.py",
    license='MIT',
    author="Minori",
    version="1.0.0",
    author_email="",
    description="Library for Kik. Discord - https://discord.gg/Bf3dpBRJHj",
    packages=find_packages(),
    long_description=long_description,
    install_requires=requirements,
    keywords=[
        'aminoapps',
        'kik',
        'kik-bot',
        'narvii',
        'api',
        'python',
        'python3',
        'python3.x',
        'minori'
    ],
    python_requires='>=3.6',
)
