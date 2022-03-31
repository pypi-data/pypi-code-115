# -*- coding: utf-8 -*-
import emoji
import numpy as np
import spacy
from spacy import tokens
from itertools import groupby


def token_filter(token: spacy.tokens.Token) -> bool:
    is_stop: bool = (token.is_stop & (token.pos_ != 'NOUN')) or \
                    (token.is_stop & (token.pos_ != 'VERB')) or \
                    (token.is_stop & (token.pos_ != 'ADJ')) or \
                    token.is_oov or \
                    len(token.shape_) <= 3 and not token._.is_emoji

    is_punctuation: bool = token.is_punct or \
                           token.is_left_punct or \
                           token.is_right_punct or \
                           token.is_bracket or \
                           token.is_quote

    is_block: bool = token.like_url or \
                     token.like_email or \
                     token.like_num or \
                     token.is_digit or \
                     token.pos_ == 'NUM'

    is_undefined: bool = token.pos_ == 'X'

    return (not is_stop) and (not is_punctuation) and (not is_undefined) and (not is_block)


def triple_filter(s: str):
    return ''.join(map(lambda x: ''.join(x) if len(x) <= 2 else x[0], map(lambda x: list(x[1]), groupby(s))))


def lemmatize(nlp, m):
    return [t.lemma_ for t in nlp(m.lower()) if token_filter(t)]


def demojize(m):
    return [emoji.demojize(t) for t in m]
