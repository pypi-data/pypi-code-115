from setuptools import setup

setup(
    name='request_rotate',
    version='1.0',    
    description='Scrape and test proxies until one works. requests adapter',
    url='https://github.com/9sv/request-rotate',
    author='Surtains',
    author_email='surtains@riseup.net',
    packages=['request_rotate'],
    install_requires=['requests', 'beautifulsoup4', 'pandas', 'lxml', 'html5lib'],
)
