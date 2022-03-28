from distutils.core import setup
setup(
  name = 'pytgcallscoef',         # How you named your package folder (MyLib)
  packages = ['pytgcallscoef'],   # Chose the same as "name"
  version = '1.0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'This is Mod Of Pytgcalls',   # Give a short description about your library
  author = 'Alfa and Fery',                   # Type in your name
  author_email = 'ubayyubaid@gmail.com',      # Type in your E-Mail
  keywords = ['telegram', 'pytgcalls', 'musiclib'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'validators',
          'beautifulsoup4',
          'tgcalls==3.0.0.dev5',
          'av==8.1.0',
          'opencv-python-headless==4.5.5.62',
          'numpy>=1.14.5',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
  ],
)