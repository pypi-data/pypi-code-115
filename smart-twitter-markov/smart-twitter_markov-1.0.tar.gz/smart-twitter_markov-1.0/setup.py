
import setuptools

setuptools.setup(
    name="smart-twitter_markov",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['twitter_bot_utils>=0.11.6.post1,<0.12', 'markovify>=0.2.4,<0.4', 'python-Levenshtein>=0.12.0, <0.13', 'wordfilter>=0.1.8', 'pyyaml', 'tweepy', 'six'],
)
