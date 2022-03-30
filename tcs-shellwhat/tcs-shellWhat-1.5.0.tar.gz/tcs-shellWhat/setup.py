import setuptools
with open(r'S:\programning\translate\shellwhatTranslated\shellwhatTranslated\README.md', 'r', encoding='utf-8') as fh:
	long_description = fh.read()

setuptools.setup(
	name='shellwhataTranslate',
	version='1.0.0',
	author='4rtess',
	author_email='artemlatorcev@mail.ru',
	description='rus shellwhat',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/4rtess/shellwhat/',
	packages=['checks'],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.6',
)