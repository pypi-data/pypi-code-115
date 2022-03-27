from distutils.core import setup

setup(
  name = 'sociolla',         # How you named your package folder (MyLib)
  packages = ['sociolla'],   # Chose the same as "name"
  version = '0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Scrap Sociolla',   # Give a short description about your library
  author = 'Farid Rizqi',                   # Type in your name
  author_email = 'faridrizqi46@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/faridrizqi46/Sociolla',   # Provide either the link to your github or to your website
  keywords = ['Sociolla', 'Scrap', 'Compas'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'numpy',
          'matplotlib',
          'seaborn',
          'pandas',
          'nltk',
          'scikit-learn',
          'wordcloud',
          'beautifulsoup4',
          'sastrawi',
          'git+https://github.com/ariaghora/mpstemmer.git',
          'python-Levenshtein'
          
          
      ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)