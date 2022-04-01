from distutils.core import setup
try:
    import pypandoc
    ld = pypandoc.convert("README.md", "rst")
except (IOError, ImportError):
    ld = open("README.md").read()
setup(
    name='ADtkclock',
    packages=['ADtkclock'],
    version='1.0',
    license='MIT',

    description='ADtkclock can use for simple timer, digital clock and stopwatch',
    long_description=ld,
    author='Shivang Srivastava',
    author_email='iamshivangsrivastava@gmail.com',
    keywords="python,tkinter,clock,timer,stopwatch,shivang,ADtkclock".split(","),
    download_url = 'https://github.com/PyDoceo/ADtkclock',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
)
