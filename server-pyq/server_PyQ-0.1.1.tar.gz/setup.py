from setuptools import setup, find_packages

setup(name="server_PyQ",
      version="0.1.1",
      description="server_PyQ files",
      author="D.P.",
      author_email="969@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
