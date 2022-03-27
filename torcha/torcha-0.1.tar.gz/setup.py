from distutils.core import setup
setup(
  name = 'torcha',         
  py_modules=["torcha", "context"],  
  version = '0.1',     
  license='MIT',       
  description = 'Torcha is a poor python module to work with tor, torcha automatically switch to new to clean circuits while you are doing your job.',   
  author = 'papacrouz',                  
  author_email = 'impapacrouz@gmail.com',     
  url = 'https://github.com/papacrouz/torcha',   
  download_url = 'https://github.com/papacrouz/torcha/archive/v0.1.tar.gz',
  keywords = ['python', 'tor', 'controller', "stem", 'new ip', 'circuits', 'clear', 'newnym', 'signal'],   
  classifiers=[
    'Development Status :: 3 - Alpha',      
    'Topic :: Software Development :: Build Tools',    'License :: OSI Approved :: MIT License',   
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
  ],
)