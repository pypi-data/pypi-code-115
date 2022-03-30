
import setuptools

setuptools.setup(
    name="smart-docker-cron-cli",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['requests >= 2.6.1, < 2.8', 'docker', 'python-crontab'],
)
