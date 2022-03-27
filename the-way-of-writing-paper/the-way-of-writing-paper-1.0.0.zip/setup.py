from setuptools import setup

def readme_file():
      with open("README.rst", encoding="utf-8") as rf:
            return rf.read()
setup(name="the-way-of-writing-paper", version="1.0.0", description="これは論文の書き方の掟",
      packages=["xzz"], py_modules=["Tool"],author="xzz",author_email="xiaozz98@yeah.net",
      long_description=readme_file(), url="https://github.com/xiaozezhong/Python_code", license="MIT")
