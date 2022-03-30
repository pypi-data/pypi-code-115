
import setuptools

setuptools.setup(
    name="smart-auto_crawler_ptt_beauty_image",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['requests==2.21.0', 'beautifulsoup4==4.7.0', 'schedule==0.5.0', 'psycopg2==2.7.6.1', 'SQLAlchemy==1.2.15', 'urllib3'],
)
