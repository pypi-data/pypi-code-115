"""Wordclouds services
"""
from typing import Optional

from relevanceai.package_utils.base import _Base


class WordcloudsClient(_Base):
    def __init__(self, project: str, api_key: str, firebase_uid: str):
        self.project = project
        self.api_key = api_key
        self.firebase_uid = firebase_uid

        super().__init__(project=project, api_key=api_key, firebase_uid=firebase_uid)

    def wordclouds(
        self,
        dataset_id: str,
        fields: list,
        n: int = 2,
        most_common: int = 5,
        page_size: int = 20,
        select_fields: Optional[list] = None,
        include_vector: bool = False,
        filters: Optional[list] = None,
        additional_stopwords: Optional[list] = None,
    ):
        """
        Get frequency n-gram frequency counter from the wordcloud.

        Parameters
        ----------
        dataset_id : string
            Unique name of dataset
        fields: list
            The field on which to build NGrams
        n: int
            The number of words fo combine
        most_common: int
            The most common number of n-gram terms
        page_size: int
            Size of each page of results
        select_fields : list
            Fields to include in the search results, empty array/list means all fields.
        include_vector: bool
            Include vectors in the search results
        filters: list
            Query for filtering the search results
        additional_stopwords: list
            Additional stopwords to add
        """
        select_fields = [] if select_fields is None else select_fields
        filters = [] if filters is None else filters
        additional_stopwords = (
            [] if additional_stopwords is None else additional_stopwords
        )

        return self.make_http_request(
            f"/services/wordclouds/wordclouds",
            method="POST",
            parameters={
                "dataset_id": dataset_id,
                "fields": fields,
                "n": n,
                "most_common": most_common,
                "page_size": page_size,
                "select_fields": select_fields,
                "include_vector": include_vector,
                "filters": filters,
                "additional_stopwords": additional_stopwords,
            },
        )
