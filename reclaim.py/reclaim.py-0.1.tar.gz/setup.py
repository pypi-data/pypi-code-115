from setuptools import setup, find_packages

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='reclaim.py',
    url='https://github.com/lars-re/reclaim.py',
    author='Lars',
    author_email='45080708+lars-re@users.noreply.github.com',
    install_requires=['google-api-python-client', "google-auth-httplib2", "google-auth-oauthlib"],
    packages=find_packages(),
    long_description_content_type="text/markdown",
    version='0.1',
    license='MIT',
    description='Unofficial reclaim.ai Python Library for creating tasks which go into reclaim.ai',
    long_description=open('README.md').read(),
)
