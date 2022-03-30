from setuptools import setup, find_packages


setup(
    name='cellulant_checkout_encryption',
    version='1.0.0',
    license='MIT',
    author="Narayan Solanki",
    author_email='platforms@cellulant.io',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://app.tingg.africa/cas/login',
    keywords='cellulant checkout encryption',
    install_requires=[
          'pycryptodome',
      ],

)
