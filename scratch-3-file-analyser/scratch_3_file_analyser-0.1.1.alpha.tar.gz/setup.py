import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
  name="scratch_3_file_analyser",
  version="0.1.1 alpha",
  author="chishudexiong",
  author_email="2326311571@qq.com",
  description="A analyzer for Scratch3 files",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/A-bear-eating-books/scratch_3_file_analyser",
  packages=setuptools.find_packages(),
  classifiers=[
  "Programming Language :: Python :: 3.10",
  "Development Status :: 3 - Alpha",
  "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
  "Natural Language :: Chinese (Simplified)"
  ],
)