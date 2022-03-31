import pandas as pd


#make function to clean text column of dataframe with texthero
def pulisci_testo(df, colonna):
    from texthero.clean import clean
    df[colonna] = df[colonna].apply(clean)
    return(df)

#make function to lower text column of dataframe with texthero
def trasforma_in_minuscolo(df, colonna):
    from texthero.clean import clean
    df[colonna] = df[colonna].apply(clean)
    df[colonna] = df[colonna].apply(lambda x: x.lower())
    return(df)

#make function to remove punctuation from text column of dataframe with texthero
def rimuovi_caratteri_speciali(df, colonna):
    from texthero.clean import clean
    df[colonna] = df[colonna].apply(clean)
    df[colonna] = df[colonna].apply(lambda x: x.translate(str.maketrans('', '', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')))
    return(df)

#make function to remove punctuation and digits from text column of dataframe with texthero
def rimuovi_caratteri_speciali_e_cifre(df, colonna):
    from texthero.clean import clean
    df[colonna] = df[colonna].apply(clean)
    df[colonna] = df[colonna].apply(lambda x: x.translate(str.maketrans('', '', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~0123456789')))
    return(df)

#make function to remove stopwords from text column of dataframe with texthero
def rimuovi_stopwords(df, colonna):
    from texthero.clean import clean
    from texthero.stopwords import stopwords
    df[colonna] = df[colonna].apply(clean)
    df[colonna] = df[colonna].apply(lambda x: ' '.join([word for word in x.split() if word not in stopwords]))
    return(df)

#make function to remove italian stopwords from text column of dataframe
def rimuovi_stopwords_italiane(df, colonna):
    from texthero.clean import clean
    from texthero.stopwords import stopwords
    from texthero.stopwords import italian_stopwords
    df[colonna] = df[colonna].apply(clean)
    df[colonna] = df[colonna].apply(lambda x: ' '.join([word for word in x.split() if word not in stopwords and word not in italian_stopwords]))
    return(df)

#make function to vectorize text column of dataframe with texthero
def vettorizza_testo(df, colonna):
    from texthero.vectorize import vectorize
    df[colonna] = df[colonna].apply(vectorize)
    return(df)

#make function to add principal components from text column of dataframe with texthero
def aggiungi_principali_componenti(df, colonna):
    from texthero.pca import pca
    df["pca"] = df[colonna].apply(pca)
    return(df)

#make function to return bag of words from text column of dataframe with sklearn
def bag_of_words(df, colonna):
    from sklearn.feature_extraction.text import CountVectorizer
    count_vectorizer = CountVectorizer()
    count_vectorizer.fit(df[colonna])
    bag_of_words = count_vectorizer.transform(df[colonna])
    return(bag_of_words)