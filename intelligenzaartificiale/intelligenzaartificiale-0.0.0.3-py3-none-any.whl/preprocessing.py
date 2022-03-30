
import numpy as np
import pandas as pd

#make function to label encoding categorical values
def label_encoding(df, colonna):
    return(df[colonna].astype('category').cat.codes)

#make function to label encoding categorical values with scikit-learn
def label_encoding_sklearn(df, colonna):
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    return(le.fit_transform(df[colonna]))

#make function to onehot encoding categorical values
def onehot_encoding(df, colonna):
    return(pd.get_dummies(df[colonna]))

#make function to replace missing values with passed value
def sostituisci_nan(df, valore):
    return(df.fillna(valore))

#make function to replace missing values in column with mean value
def sostituisci_nan_media(df, colonna):
    return(df[colonna].fillna(df[colonna].mean()))

#make function to replace missing values in column with most frequent value
def sostituisci_nan_frequenti(df, colonna):
    return(df[colonna].fillna(df[colonna].mode()[0]))

#make function to remove from dataframe rows with missing values
def rimuovi_nan(df):
    return(df.dropna())

#make function to remove column if missing values are more than passed value
def rimuovi_colonna_se_nan(df, colonna, valore):
    return(df.dropna(subset=[colonna], thresh=valore))

#make function to return dataframe without outliers
def rimuovi_outliers(df, colonna):
    return(df[(np.abs(df[colonna] - df[colonna].mean()) <= (3 * df[colonna].std()))])

#make function to return dataframe without outliers and missing values
def rimuovi_outliers_nan(df, colonna):
    return(df[(np.abs(df[colonna] - df[colonna].mean()) <= (3 * df[colonna].std())) & (df[colonna].isnull() == False)])

#make function to normalize dataframe
def normalizza(df):
    return(df.apply(lambda x: (x - np.min(x)) / (np.max(x) - np.min(x))))

#make function to scaling dataframe
def scaling(df):
    return(df.apply(lambda x: (x - np.mean(x)) / (np.std(x))))

#make function to return X_train, X_test, y_train, y_test train test split of dataframe
def dividi_train_test(df, colonna_y, test_size):
    from sklearn.model_selection import train_test_split
    X = df.drop(colonna_y, axis=1)
    y = df[colonna_y]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
    return(X_train, X_test, y_train, y_test)

#make function to return list of column with best correlation with passed column
def classifica_correlazione_colonna(df, colonna):
    return(df.corr()[colonna].sort_values(ascending=False).index)

#make function to return a list of column name with best correlation with passed column
def classifica_correlazione_colonna_nome(df, colonna):
    return(df.corr()[colonna].sort_values(ascending=False).index.tolist())

#make function to return dataframe with list columns passed
def seleziona_colonne(df, lista_colonne):
    return(df[lista_colonne])

