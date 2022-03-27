import pandas as pd
from mpstemmer import MPStemmer
from nltk.corpus import stopwords

stemmer = MPStemmer()
indonesia_s = stopwords.words('indonesian')
english_s = stopwords.words('english')
pos=pd.read_csv('https://raw.githubusercontent.com/faridrizqi46/Sociolla/main/sociolla/kata_positif.txt', sep="\t", header=None)[0].tolist() 
neg=pd.read_csv('https://raw.githubusercontent.com/faridrizqi46/Sociolla/main/sociolla/kata_negatif.txt', sep="\t", header=None)[0].tolist()