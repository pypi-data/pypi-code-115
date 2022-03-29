from setuptools import setup, find_packages

def readme():
	with codecs.open('README.md','r',encoding='utf-8') as f:
		return f.read()

setup(name='nameseer',
      version='0.1',
      description='Thai person name classifier',
      url='',
      author='Pucktada Treeratpituk',
      author_email='pucktadt@bot.or.th',
      license='Apache Software License 2.0',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      package_data={'': ['*.pk']},
	include_package_data=True,
      zip_safe=False)