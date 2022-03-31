from setuptools import setup
descr = open('README.md').read()

setup(name='pyvector',
      version='0.1.3',
      description='Simple classes for SVG generation',
      long_description=descr,
      long_description_content_type='text/markdown',
      url='http://github.com/thoelken/pyvector',
      author='Clemens Thölken',
      author_email='code@tholken.org',
      license='MIT',
      packages=['pyvector'],
      keywords='SVG vector graphics',
      zip_safe=False)
