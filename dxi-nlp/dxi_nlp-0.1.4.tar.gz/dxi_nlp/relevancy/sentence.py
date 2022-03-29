"""Module to extract relevant sentences and their scores."""
from typing import Union
import re
import gc
from pathlib import Path
import pandas as pd
from .relevancy_utils import nlp_lg, split_clean_paragraphs, split_clean_sentences, compute_relevancy_score_for_content, compute_relevancy_score_for_title


def get_relevant_sentences_from_lexis(
        df: Union[str, Path, pd.DataFrame],
        file_type: str = 'parquet',
        multiprocess: bool = False,
        n_process: int = 1,
        batch_size: int = 1000) -> pd.DataFrame:

    read_fn = {
        'parquet': pd.read_parquet, 'feather': pd.read_feather,
        'csv': pd.read_csv, 'json': pd.read_json
    }

    if not isinstance(df, pd.DataFrame):
        if file_type == 'json':
            df = read_fn[file_type](df, lines=True)
        df = read_fn[file_type](df)

    df['article_word_count'] = df.content.apply(lambda x: len(x.split()))

    df['brand_in_title'] = df.apply(
        lambda x: 1 if x.brand_2.lower() in x.title.lower() or x.brand.lower() in x.title.lower() else 0, axis=1)

    df['paragraphs'] = df.apply(split_clean_paragraphs, axis=1)

    df_exploded = df.explode('paragraphs')
    df_exploded = df_exploded[~df_exploded.paragraphs.isna(
    )]
    df_exploded.paragraphs = df_exploded.paragraphs.apply(
        lambda x: re.sub('\n\n', ' : ', re.sub(' +', ' ', x)))
    df_exploded['brand_in_paragraph'] = df_exploded.apply(
        lambda x: 1 if x.brand_2.lower() in x.paragraphs.lower(
        ) or x.brand.lower() in x.paragraphs.lower() else 0,
        axis=1)

    df_brand_in_paragraph = df_exploded[
        [
            'brand_article_id', 'brand', 'brand_2', 'paragraphs'
        ]
    ][df_exploded.brand_in_paragraph == 1]
    df_brand_in_paragraph.drop_duplicates(
        subset=['brand', 'brand_2', 'brand_article_id', 'paragraphs'], inplace=True)
    df_brand_in_paragraph.reset_index(inplace=True, drop=True)

    del df_exploded
    gc.collect()

    paragraph_list = df_brand_in_paragraph.paragraphs.tolist()

    if multiprocess:
        paragraph_doc = list(nlp_lg.pipe(
            paragraph_list, n_process=n_process, batch_size=batch_size))
    else:
        paragraph_doc = list(nlp_lg.pipe(paragraph_list))

    df_brand_in_paragraph['paragraph_doc'] = paragraph_doc

    del paragraph_doc, paragraph_list
    gc.collect()

    df_brand_in_paragraph['sentence'] = df_brand_in_paragraph.apply(
        lambda x: split_clean_sentences(x.paragraph_doc, x.brand, x.brand_2), axis=1)
    df_brand_in_paragraph = df_brand_in_paragraph.explode('sentence')
    df_brand_in_paragraph = df_brand_in_paragraph[~df_brand_in_paragraph.sentence.isna(
    )]
    df_brand_in_paragraph.drop_duplicates(
        subset=['brand', 'brand_2', 'sentence', 'brand_article_id'], inplace=True)
    df_brand_in_paragraph.reset_index(inplace=True, drop=True)

    df_brand_in_paragraph['brand_article_relevancy_score'] = df_brand_in_paragraph.apply(
        lambda x: compute_relevancy_score_for_content(x.sentence, x.brand, x.brand_2), axis=1)

    return df_brand_in_paragraph
