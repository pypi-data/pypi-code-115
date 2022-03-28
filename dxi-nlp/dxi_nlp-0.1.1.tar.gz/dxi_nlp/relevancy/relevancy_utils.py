from typing import Iterable, Generator
import gc
import re
import spacy
from spacy import Language
import pandas as pd
import numpy as np


nlp_lg = spacy.load('en_core_web_lg', exclude=['lemmatizer', 'ner'])
# nlp_trf = spacy.load('en_core_web_trf', exclude=['lemmatizer', 'ner'])


@Language.component('set_custom_boundaries')
def set_custom_boundaries(doc: spacy.tokens.doc.Doc) -> spacy.tokens.doc.Doc:
    """set_custom_boundaries adds custom characters for sentence segmentation.
    Args:
        doc (spacy.tokens.doc.Doc): spacy language document.
    Returns:
        spacy.tokens.doc.Doc: spacy language document.
    """
    # Adds support to use `` as the delimiter for sentence detection
    for delim in ['|', ':', ':::']:
        for token in doc[:-1]:
            if token.text == delim:
                doc[token.i+1].is_sent_start = True
    return doc


# nlp_trf.add_pipe('set_custom_boundaries', before='parser')
nlp_lg.add_pipe('set_custom_boundaries', before='parser')


def flatten(nest: Iterable) -> Generator:
    """Flatten takes a nested iterator and yields from a flattened generator.
    Args:
        nest (Iterable): nested iterator
    Yields:
        Iterator[Generator]: flattened generator
    """
    for element in nest:
        if isinstance(element, Iterable) and not isinstance(element, (str, bytes)):
            yield from flatten(element)
        else:
            yield element


def split_clean_paragraphs(iterrow: Iterable) -> list:
    """split_clean_paragraphs splits an article into paragraphs and removes additional newlines and spaces.
        Args:
            iterrow (Iterable): a pandas row object
        Returns:
            list: list of cleaned generated paragraphs
        """
    if iterrow.article_word_count <= 250:
        return [iterrow.content]
    splitted_paragraphs = re.split(r"\.\s*\n\s*\n", iterrow.content)
    splitted_paragraphs = [re.split(r"\n\n", i) if len(
        i.split()) > 1000 else i for i in splitted_paragraphs]
    return list(set(list(flatten(splitted_paragraphs))))


def split_clean_sentences(doc: spacy.tokens.doc.Doc, brand: str, brand_2: str, require_verb: bool = True) -> list:
    """split_clean_sentences breaks a document into sentences and cleans the text for faster processings.
    Args:
        doc (spacy.tokens.doc.Doc): spacy language document.
        brand (str): brand name.
        brand_2 (str): simplified brand name.
        require_verb (bool, optional): if true sentences without 'VERB' pos are removed. Defaults to True.
    Returns:
        list: list of clean sentences (spacy span objects).
    """
    if brand_2.split('-'):
        brand_2 = brand_2.split('-')[-1]
    elif len(brand_2.split()) > 1:
        brand_2 = brand_2.split()[0]
    clean_sentences = [sent for sent in doc.sents if bool(
        re.search('[a-z0-9]', sent.text, re.IGNORECASE))]
    clean_sentences = [
        sent for sent in clean_sentences
        if len(re.sub('[^A-Za-z0-9]+', ' ', re.sub(' +', ' ', sent.text).replace(
            ' |', ' ').replace(':::', ' ').replace('\n', ' ').strip()).split()) > 1
    ]
    if require_verb:
        clean_sentences = [sent for sent in clean_sentences if 'VERB' in [
            token.pos_ for token in sent]]
    clean_sentences = [
        sent for sent in clean_sentences if brand.lower() in
        sent.text.lower() or brand_2.lower() in sent.text.lower()
    ]
    return clean_sentences


def compute_relevancy_score_for_content(sentence: spacy.tokens.span.Span, brand: str, brand_2: str) -> float:
    # sourcery skip: remove-redundant-if
    """compute_relevancy_score_for_content assigns a relevancy score based on the grammatical importance of brank in article content.
    Args:
        sentence (spacy.tokens.span.Span): spacy span object (doc.sents).
        brand (str): brand name.
        brand_2 (str): simplified brand name.
    Returns:
        float: relevancy score.
    """
    if brand_2.split('-'):
        brand_2 = brand_2.split('-')[-1]
    if brand_2.split("'s"):
        brand_2 = brand_2.split("'s")[0]
    if len(brand_2.split()) > 1:
        brand_2 = brand_2.split()[0]

    relevancy_score = 0
    for token in sentence:
        if any(i.lower() in token.text.lower() for i in ['.com', '•', '@']):
            condition = brand_2.lower() in token.text.lower()
        else:
            condition = brand_2.lower() == token.text.lower()
        if token.text.lower() == brand.lower() or condition:
            brand_dep = token.dep_
            brand_ancestor_dep = [a.dep_ for a in token.ancestors]
            brand_children_dep = [c.dep_ for c in token.children]
            subj_idx_ancestor = [idx for idx, dep in enumerate(
                brand_ancestor_dep) if 'subj' in dep]
            subj_idx_children = [idx for idx, dep in enumerate(
                brand_children_dep) if 'subj' in dep]
            # subject rules
            if 'subj' in brand_dep:
                # print('subj rule success')
                relevancy_score += 1
            # dep tree rule
            elif any(i < 2 for i in subj_idx_ancestor) or any(i < 2 for i in subj_idx_children):
                # print('dep tree rule success')
                relevancy_score += 1
            elif any(i < 4 for i in subj_idx_ancestor) or any(i < 4 for i in subj_idx_children):
                # print('dep tree rule success')
                relevancy_score += 0.5
            # conjunction rules
            elif brand_dep == 'conj':
                # print('conj rule success')
                conjunct_with_dep = [
                    (idx, c, c.dep_)
                    for idx, c in enumerate(token.conjuncts)
                ]
                if any('subj' in i for i in [c[-1] for c in conjunct_with_dep]):
                    # print('conj-subj rule success')
                    relevancy_score += 1
                elif any('dobj' in i for i in [c[-1] for c in conjunct_with_dep]):
                    # print('conj-dobj rule success')
                    relevancy_score += 0.5
                elif any('appos' in i for i in [c[-1] for c in conjunct_with_dep]):
                    # print('conj-appos rule success')
                    relevancy_score += 0.25
                else:
                    # print('conj other rule success')
                    relevancy_score += 0.25
            # compound rules
            elif brand_dep == 'compound':
                # print('compound rule success')
                if any(i <= 3 for i in subj_idx_ancestor) or any(i <= 2 for i in subj_idx_children):
                    relevancy_score += 1
                # elif len(subj_idx_ancestor) != 0 or len(subj_idx_ancestor) != 0:
                #     relevancy_score += 0.25
                elif any(i == 'dobj' for i in brand_ancestor_dep[:2]):
                    relevancy_score += 0.5
                else:
                    relevancy_score += 0.25
            # appositional rules
            elif brand_dep == 'appos':
                # print('appos rule success')
                if any(i < 2 for i in subj_idx_children) or any(i < 2 for i in subj_idx_ancestor):
                    relevancy_score += 1
                # elif len(subj_idx_children) != 0:
                #     relevancy_score += 0.5
                elif brand_ancestor_dep[0] == 'dobj':
                    relevancy_score += 0.5
                else:
                    relevancy_score += 0.25
            # posseive rules
            elif brand_dep == 'poss':
                # print('poss rule success')
                if any(i < 2 for i in subj_idx_ancestor):
                    relevancy_score += 1
                else:
                    relevancy_score += 0.25
            # direct object rules
            elif brand_dep == 'dobj':
                # print('dobj rule success')
                relevancy_score += 0.5
            # prepositional object rules
            elif brand_dep == 'pobj':
                # print('pobj rule success')
                relevancy_score += 0.25
            else:
                relevancy_score += 0.25
    if brand_2.lower() == 'Johnson'.lower():
        relevancy_score /= 2
    return relevancy_score


def compute_relevancy_score_for_title(title: str, brand: str, brand_2: str) -> float:
    """compute_relevancy_score_for_title assigns a relevancy score based on the grammatical importance of brank in article title.
    Args:
        title (str): title of the article.
        brand (str): brand name.
        brand_2 (str): simplified brand name.
    Returns:
        float: relevancy score
    """
    title_doc = nlp_lg(title)
    sentences = split_clean_sentences(
        title_doc, brand, brand_2, require_verb=False)
    brand_dep = [
        (
            token.dep_,
            [
                a.dep_ for a in token.ancestors
            ][:2],
            [
                c.dep_ for c in token.children
            ][:2],
            [
                c.dep_ for c in token.conjuncts
            ]
        ) for sentence in sentences
        for token in sentence if token.text.lower() in
        [brand.lower(), brand_2.lower()]]

    brand_dep = list(flatten(brand_dep))

    # return sentences, brand_dep, relevancy_score
    return 2 if any('subj' in i for i in brand_dep) else 1
