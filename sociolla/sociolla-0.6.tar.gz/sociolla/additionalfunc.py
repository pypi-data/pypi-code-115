import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
from sociolla.supportvar import *


def clean_text(df, column):
    """
    param:
    df: dataframe yang dipilh, biasanya adalah dataframe detail
    column: kolom dari dataframe, biasanya kolom details

    return: List dari komentar yang sudah bersih

    Fungsi ini dipakai untuk membersihkan/merapihkan komentar dari para user
    """
    cleans = []
    for comment in df[column]:
        lower = comment.lower()
        preclean = re.sub(r"[0-9]\s?in\s?1", "komplit", lower)
        preclean = re.sub(r"\b(parah)\b", "", preclean)
        clean = re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|(\d+)", "", preclean)
        clean2 = re.sub("\s+", ' ', clean).strip()
        no_stop_ind = ' '.join([token for token in word_tokenize(clean2) if token not in indonesia_s])
        no_stop_eng = ' '.join([token for token in word_tokenize(no_stop_ind) if token not in english_s])
        stem   = stemmer.stem_kalimat(no_stop_eng)
        cleans.append(stem)
    return cleans

def itterate_text(word_token):
    word_p, word_n = [], [] 
    for i,text in enumerate(word_token):
        for neg_text in neg:
            if text == neg_text:
                if word_token[i-1] == 'tidak' or word_token[i-1] == 'kurang':
                    word_p.append('tidak' + text)
                else:
                    word_n.append(text)
        for pos_text in pos:
            if text == pos_text:
                if word_token[i-1] == 'tidak' or word_token[i-1] == 'kurang':
                    word_n.append('tidak' + text)
                else:
                    word_p.append(text)
    return word_p, word_n

def comment_sentiment(clean_text, df_ref, treshold = 2):
    """
    param:
    clean_text: teks yang sudah dibersihkan dalam bentuk list
    df_ref: dataframe dan kolom yang merupakan asal dari teks yang sudah dibersihkan, cth:df_detail['details']

    return: dataframe komentar asli(yg belum dibersihkan) dan hasil sentimentnya

    Fungsi ini dipakai untuk memberikan nilai sentimen dari komentar user
    """
    word_p, word_n, sentiment = [], [], []
    for comment,rating in zip(clean_text,df_ref['rating']):
#             count_p = 0 #nilai positif
        count_n = 0 #nilai negatif
        word_token = word_tokenize(comment)
        if rating >= 4.0:
            sentiment.append('Positive')
            word_p2, word_n2 = itterate_text(word_token)
            word_p.extend(word_p2)
            word_n.extend(word_n2)
        elif (rating >= 3.0) and (rating<=3.99): 
            for i,text in enumerate(word_token):
                for neg_text in neg:
                    if text == neg_text:
                        if word_token[i-1] == 'tidak' or word_token[i-1] == 'kurang':
                            count_n += 0
                            word_p.append('tidak' + text)
                        if word_token[i-1] == 'mudah' or word_token[i-1] == 'gampang':
                            if word_token[i-2] == 'tidak':
                                count_n += 0
                                word_p.append('tidakmudah' + text)
                            else:
                                word_n.append('mudah'+text)
                                count_n += 1
                        else:
                            word_n.append(text)
                            count_n += 1
                for pos_text in pos:
                    if text == pos_text:
                        if word_token[i-1] == 'tidak' or word_token[i-1] == 'kurang':
                            word_n.append('tidak' + text)
                            count_n += 1
                        else:
                            word_p.append(text)

            if count_n > treshold:
                sentiment.append('Negative')
            else:
                sentiment.append('Positive')
        elif rating < 3.0:
            sentiment.append('Negative')
            word_p2, word_n2 = itterate_text(word_token)
            word_p.extend(word_p2)
            word_n.extend(word_n2)
    df_sentiment = pd.DataFrame({'comment': df_ref['detail'].tolist(),'clean_comment':clean_text, 'sentiment':sentiment})
    return df_sentiment, word_n, word_p

def rating(df):
    """
    param:
    df: dataframe yang dipilih untuk dihitung ratingnya


    fungsi ini dipakai untuk menghitung rating dari suatu produk
    """
    overall_rating = round(df['rating'].mean(),2)
    long_wear = round(df['long_wear'].mean(),2)
    packaging = round(df['packaging'].mean(),2)
    pigmentation = round(df['pigmentation'].mean(),2)
    texture = round(df['texture'].mean(),2)
    value_for_money = round(df['value_for_money'].mean(),2)
    return pd.DataFrame({'ovr_rating':overall_rating, 'long_wear':long_wear, 'packaging':packaging, 'pigmentation':pigmentation, 'texture':texture, 'value_for_money':value_for_money}, index=['Rating']).T

def plot_top10_skin(df, column, top=10):
    """
    param:
    df: dataframe yang dipilh, biasanya adalah dataframe skin
    column: kolom dari dataframe
    top: jumlah data yang akan ditampilkan

    fungsi ini dipakai untuk membuat bar_plot dari jenis kulit user
    """
    top10 = df[column].value_counts().iloc[:top].index
    sns.countplot(data=df, y=column, order=top10)
    return plt.show()

def plot_repurchase(df, column):
    labels = df.groupby(column)[column].count().sort_values(ascending=False).reset_index(name='count')[column].tolist()
    fig= plt.figure()
    fig.patch.set_facecolor('white')
    plt.pie(df[column].value_counts(), autopct='%.2f%%', labels=labels)
    plt.show()

def barPerc_without_hue_h(ax, feature):
    total = sum(feature)
    for p in ax.patches:
        percentage = '{:.1f}%'.format(100 * p.get_height()/total)
        x = p.get_x() + p.get_width() - 0.5
        y = p.get_y() + p.get_height()
        ax.annotate(percentage, (x, y), size = 12)

def plot_age(df, column):
    groupbyx = df.groupby('age_range')['age_range'].count().reset_index(name='count')
    sum1 = groupbyx['count'].values
    ax = sns.barplot(data=groupbyx, x='age_range', y='count')
    barPerc_without_hue_h(ax, sum1)
    plt.show()


def wordcloud(word_n, word_p, top_n=10, top_p=10):
    """
    param:
    word_n: list kalimat negatif yang ada di komentar
    word_p: list kalimat positif yang ada di komentar
    top_n: jumlah kalimat negatif yang ingin ditampilkan
    top_p: jumlah kalimat positif yang ingin ditampilkan
    """
    count_word_n = pd.DataFrame({'word':word_n}).groupby('word')['word'].count().sort_values(ascending=False).head(top_n).reset_index(name='count')
    count_word_p = pd.DataFrame({'word':word_p}).groupby('word')['word'].count().sort_values(ascending=False).head(top_p).reset_index(name='count')
    join_p = ' '.join(count_word_p['word'])
    join_n = ' '.join(count_word_n['word'])
    wordcloud_p = WordCloud(width=1600, height=800, max_font_size=200,max_words=top_n, background_color="white").generate(join_p)
    wordcloud_n = WordCloud(width=1600, height=800, max_font_size=200,max_words=top_p, background_color="white").generate(join_n)
    fig, axs = plt.subplots(1,2, figsize=(30,30))
    axs[0].imshow(wordcloud_n, interpolation='bilinear')
    axs[0].axis('off')
    axs[0].set_title('Negative Word')
    axs[1].imshow(wordcloud_p, interpolation='bilinear')
    axs[1].axis('off')
    axs[1].set_title('Positive Word')
    return plt.show()

def sentiment_summary(df, column):
    labels = df.groupby(column)[column].count().sort_values(ascending=False).reset_index(name='count')[column].tolist()
    fig= plt.figure()
    fig.patch.set_facecolor('white')
    plt.pie(df[column].value_counts(), autopct='%.2f%%', labels=labels)
    plt.show()

    print("Positive Comment:")
    try:
        print(df[df[column]=='Positive']['comment'].sample(1).tolist(), '\n')
    except:
        print('Info : Tidak ada comment Positive')
    print("Negative Comment:")
    try:
        print(df[df[column]=='Negative']['comment'].sample(1).tolist(), '\n')
    except:
        print('Info : Tidak ada comment Negative')
