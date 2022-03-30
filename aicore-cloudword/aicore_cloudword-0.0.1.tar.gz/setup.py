import setuptools

setuptools.setup(
    name="aicore_cloudword",
    version="0.0.1",
    author="Ivan Ying",
    author_email="ivan@theaicore.com",
    description="A simple package to generate wordclouds from Google Sheets",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[
          'pandas',
          'numpy',
          'gspread',
          'oauth2client',
          'requests',
          'psycopg2-binary',
          'sqlalchemy',
          'PyYaml',
          'slack-sdk']
)