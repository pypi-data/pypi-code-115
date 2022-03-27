# Copyright GlitterClient GmbH and GlitterClient contributors
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from glitter_sdk.transport import Transport
from glitter_sdk.utils import normalize_nodes

class GlitterClient:
    """A :class: `driver.GlitterClient` is python client  for glitter.

    """

    def __init__(self, *nodes, headers=None, transport_class=Transport, timeout=20):
        """Initialize a :class:`~driver.GlitterClient` driver instance.

        Args:
            *nodes:(list of (str or dict)): Glitter nodes to connect to.
            headers (dict): Optional headers that will be passed with each request
            transport_class: Optional transport class to use.
            timeout (int): Optional timeout in seconds that will be passed to each request.
        """
        self._nodes = normalize_nodes(*nodes, headers=headers)
        self._transport = transport_class(*self._nodes, timeout=timeout)
        self._db = DataBase(self)
        self._chain = Chain(self)
        self._admin = Admin(self)
        self.api_prefix = '/v1'

    @property
    def nodes(self):
        """:obj:`tuple` of :obj:`str`:
         URLs of connected nodes.
        """
        return self._nodes

    @property
    def transport(self):
        """:class:`~driver.Transport`:
         Object responsible for forwarding requests to a :class:`~driver.Connection` instance (node).
        """
        return self._transport

    @property
    def chain(self):
        """:class:`~driver.Chain`:
        query block or transaction info.
        """
        return self._chain

    @property
    def admin(self):
        """:class:`~driver.Admin`:
        Exposes functionalities of the ``'/admin'`` endpoint.
        """
        return self._admin

    @property
    def db(self):
        """:class:`~driver.DataBase` put or search doc from glitter.
        """
        return self._db


class NamespacedDriver:
    """Base class for creating endpoints (namespaced objects) that can be added
    under the :class:`~driver.GlitterClient` driver.
    """

    PATH = '/'

    def __init__(self, driver):
        """Initializes an instance of
        :class:`~GlitterClient_driver.driver.NamespacedDriver` with the given
        driver instance.

        Args:
            driver (GlitterClient): Instance of
                :class:`~GlitterClient_driver.driver.GlitterClient`.
        """
        self.driver = driver

    @property
    def transport(self):
        return self.driver.transport

    @property
    def api_prefix(self):
        return self.driver.api_prefix

    @property
    def path(self):
        return self.api_prefix + self.PATH


class DataBase(NamespacedDriver):
    """Exposes the data of glitter db.
    """

    def list_schema(self):
        """
        Args:
            headers(dict): http header

        Returns:
            :obj:`dic`: list all schema.

        Examples:
            the schema is json string,the return like::

                ```json
                {
                   "code": 200,
                   "message": "ok",
                   "data": {
                     "lib_gen": "{\"mappings\":{\"_source\":{\"includes\":[],\"excludes\":[]},\"properties\":{\"author\":{\"type\":\"text\",\"analyzer\":\"ik_max_word\",\"search_analyzer\":\"ik_max_word\"},\"issn\":{\"type\":\"keyword\"},\"language\":{\"type\":\"keyword\"},\"publisher\":{\"type\":\"text\"},\"series\":{\"type\":\"text\"},\"md5\":{\"type\":\"keyword\"},\"title\":{\"type\":\"text\",\"analyzer\":\"ik_max_word\",\"search_analyzer\":\"ik_max_word\"},\"tags\":{\"type\":\"keyword\"},\"ipfs_cid\":{\"type\":\"keyword\",\"index\":false}}}}",
                     "magnet": "{\"mappings\":{\"_source\":{\"includes\":[],\"excludes\":[]},\"properties\":{\"doc_id\":{\"type\":\"keyword\"},\"status\":{\"type\":\"short\",\"index\":\"false\"},\"data_create_time\":{\"type\":\"long\",\"index\":\"false\"},\"update_time\":{\"type\":\"long\",\"index\":\"false\"},\"file_name\":{\"type\":\"text\",\"analyzer\":\"ik_max_word\",\"search_analyzer\":\"ik_max_word\"},\"creator\":{\"type\":\"keyword\"},\"category\":{\"type\":\"keyword\"},\"extension\":{\"type\":\"keyword\"},\"file_size\":{\"type\":\"long\",\"index\":\"false\"},\"current_count\":{\"type\":\"long\",\"index\":\"false\"},\"total_count\":{\"type\":\"long\",\"index\":\"false\"},\"cid\":{\"type\":\"keyword\"},\"pin_status\":{\"type\":\"text\",\"index\":\"false\"}}}}",
                     "sci": "{\"mappings\":{\"_source\":{\"includes\":[],\"excludes\":[]},\"properties\":{\"author\":{\"type\":\"text\",\"analyzer\":\"ik_max_word\",\"search_analyzer\":\"ik_max_word\"},\"md5\":{\"type\":\"keyword\"},\"doi\":{\"type\":\"keyword\"},\"title\":{\"type\":\"text\",\"analyzer\":\"ik_max_word\",\"search_analyzer\":\"ik_max_word\"},\"ipfs_cid\":{\"type\":\"keyword\",\"index\":false},\"file_name\":{\"type\":\"keyword\",\"index\":false}}}}"
                   }
                }
                ```
        """
        path = '/list_schema'

        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            headers=headers,
        )

    def app_status(self):
        path = '/app_status'

        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
        )

    def put_doc(self, schema_name, doc_id, doc_value):
        """Put document to glitter.

        Args:
            schema_name(str): the name of schema. (e.g.: ``'sci','libgen','magnet'``).
            doc_id(str): main key of document,must be uniq.
            doc_value(:obj:`dic`):doc content.

        Returns:
            :obj:`dic`: transaction id.

        Examples:
            The examples show how to use method::

               sci_doc = {
                'title': 'abcd1234',
                'doi': '10.1080/00219444.1951.10532850',
                'author': ["Clarkson, C. W.", "Chang, C. ", "Stolfi, A.", "George, W. J.", "Yamasaki, S.", "Pickoff, A. S."],
                'md5': "2fac9c0079cea4f63862d8c30e6e8b29",
                'ipfs_cid': "bafybeigs2ynpydzly3yobo2vn4rpky6bqest7gtym3klt6mzv7zvvrk4ea",
                'file_name': "088de5471205cff0e100b6c49603db13.pdf"
               }
               url = 'http://127.0.0.1:26659'
               glitter = GlitterClient(url)
               res = glitter_client.db.put_doc("sci", "2fac9c0079cea4f63862d8c30e6e8b29", sci_doc)
               print(res)

               ```json
                {
                    'code': 200,
                    'message': 'ok',
                    'tx_hash': 'DC6128F7801993319C91EFACA2A19F0AA73AF3769D0711DA876D10E6E0EF8979',
                    'data': ''
                }
                ```
        """
        path = '/put_doc'
        body = {
            "schema_name": schema_name,
            "doc_id": doc_id,
            "doc_data": doc_value,
        }
        return self.transport.forward_request(
            method='POST',
            path=self.api_prefix + path,
            json=body,
        )

    def get_docs(self, schema_name, doc_ids):
        """Get documents from glitter by doc ids.

        Args:
            schema_name(str): the name of schema. (e.g.: ``'sci','libgen','magnet'``).
            doc_id(list of str): main key of document,must be uniq.
            header(:obj:`dic`): http header, must contain access_token key.

        Returns:
            :obj:`dic`: .

        Examples:
            The examples show how to use method::

                url = 'http://127.0.0.1:26659'
                glitter = GlitterClient(url)
                header = {"access_token": "my_token"}
                doc_ids = ["2fac9c0079cea4f63862d8c30e6e8b29"]
                res = glitter_client.db.get_docs("libgen", doc_ids,header)
                print(res)
                .. code-block:: json
                {
                    'code': 200,
                    'message': 'ok',
                    'data': {
                        'Total': 1,
                         Hits': {'my_token_2fac9c0079cea4f63862d8c30e6e8b29': {
                            'doc_id': '2fac9c0079cea4f63862d8c30e6e8b29', 'title': 'Mechanical Modelling and Computational Issues in Civil Engineering', 'series': ['Lecture Notes in Applied and Computational Mechanics 23'], 'author': ['Michel Fremond (editor)',' Franco Maceri (editor)'], 'publisher': 'Springer', 'language': ['English'], 'tags': ['Vibration, Dynamical Systems, Control', 'Civil Engineering','Mechanics','Numerical Analysis'], 'ipfs_cid': 'bafykbzacedq5bhvqpbuyd4lkop7fpv7wutjzjvzzdkprfgkecbyucrb4sz6io', 'extension': 'pdf'}
                            }
                         }
                }
                :param json: json object
        """
        path = '/get_docs'
        return self.transport.forward_request(
            method='POST',
            path=self.api_prefix + path,
            json={"schema_name": schema_name, "doc_ids": doc_ids},
        )

    def simple_search(self, index, query, order_by="", limit=10, page=1):
        """ search from glitter

            Args:
            index(str): index name (e.g.: ``'libgen','sci','magnet'``).
            query(str): query word
            order_by(str): order by field (e.g.: ``'update_time'``).
            limit(int): limit
            page(int): page number,begin from 1

            Returns:
            :obj:`dic`: the documents match query words.

            Examples:
                The exaples show how to search::

                    glitter_client = GlitterClient('http://127.0.0.1:26659')
                    res = glitter_client.db.simple_search("libgen", "Springer")
                    print(res)
                    ```json
                    {
                        "code": 200,
                        "message": "ok",
                        "data": {
                            "search_time": 4,
                            "index": "libgen",
                            "meta": {"page":{"current_page":1,"total_pages":6,"total_results":5,"size":1,"sorted_by":""}},
                            "items": [{"highlight":{"publisher":["<span>Springer</span>"]},"data":{"doc_id":"2fac9c0079cea4f63862d8c30e6e8b29","title":"Mechanical Modelling and Computational Issues in Civil Engineering","series":[""],"author":["Michel Fremond (editor)", " Franco Maceri (editor)"],"publisher":"Springer","language":["English"],"md5":"2fac9c0079cea4f63862d8c30e6e8b29","tags":["Vibration, Dynamical Systems, Control","Civil Engineering","Mechanics","Numerical Analysis"],"ipfs_cid":"bafykbzacedq5bhvqpbuyd4lkop7fpv7wutjzjvzzdkprfgkecbyucrb4sz6io","extension":"pdf"}}],
                            "sorted_by_field": [{"field":"extension","type":"term"},{"field":"author","type":"term"}],
                            "facet": {"issn":[],"language":[{"type":"term","field":"language","value":"English","from":0,"to":0,"doc_count":4},{"type":"term","field":"language","value":"Latin","from":0,"to":0,"doc_count":1}],"tags":[{"type":"term","field":"tags","value":"","from":0,"to":0,"doc_count":3},{"type":"term","field":"tags","value":"Анатомия","from":0,"to":0,"doc_count":2}]}
                        }
                    }
                ```
            """

        path = '/search'
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={"index": index, "query": query, "order_by": order_by, "limit": limit, "page": page},
        )

    def complex_search(self, index, query, filters, order_by="", limit=10, page=1, header=None):
        """ search from glitter,with more args.

        Args:
            index(str): index name (e.g.: ``'libgen','sci','magnet'``).
            query(str): query word
            filters(:obj:`list` of :obj:`dic`): filter condition, examples:[{"type":"term","field":"language","value":"english","from":0.5,"to":1,"doc_count":100}] this affect score only.
            order_by(str): order field
            limit(int): limit
            page(int): page number,begin from 1
            header(:obj:`dic`): http header

        Returns:
            :obj:`dic`: the documents match query words.

        Examples:
            The exaples show how to search::

                glitter_client = GlitterClient('http://127.0.0.1:26659')
                filter_cond = [{"type": "term", "field": "language", "value": "English", "from": 0.9, "to": 1, "doc_count": 100}]
                res = glitter_client.db.complex_search("libgen", "Springer", filter_cond)
                print(json.dumps(res))
                ```json
                {
                    "code": 200,
                    "message": "ok",
                    "data": {
                        "search_time": 10,
                        "index": "libgen",
                        "meta": {"page":{"current_page":1,"total_pages":1,"total_results":5,"size":10,"sorted_by":""}},
                        "items": [{"highlight":{"publisher":["<span>Springer</span>"]},"data":{"doc_id":"2fac9c0079cea4f63862d8c30e6e8b29","title":"Mechanical Modelling and Computational Issues in Civil Engineering","series":[""],"author":["Michel Fremond (editor)", " Franco Maceri (editor)"],"publisher":"Springer","language":["Latin","English"],"md5":"2fac9c0079cea4f63862d8c30e6e8b29","tags":["Vibration, Dynamical Systems, Control","Civil Engineering","Mechanics","Numerical Analysis"],"ipfs_cid":"bafykbzacedq5bhvqpbuyd4lkop7fpv7wutjzjvzzdkprfgkecbyucrb4sz6io","extension":"pdf"}}],
                        "sorted_by_field": [{"field":"extension","type":"term"},{"field":"author","type":"term"}],
                        "facet": {"issn":[],"language":[{"type":"term","field":"language","value":"English","from":0,"to":0,"doc_count":4},{"type":"term","field":"language","value":"Latin","from":0,"to":0,"doc_count":1}],"tags":[{"type":"term","field":"tags","value":"","from":0,"to":0,"doc_count":3},{"type":"term","field":"tags","value":"Анатомия","from":0,"to":0,"doc_count":2}]}
                    }
                }
            ```
        """

        path = '/search'
        return self.transport.forward_request(
            method='POST',
            path=self.api_prefix + path,
            json={"index": index, "query": query, "filters": filters, "order_by": order_by, "limit": limit,
                  "page": page},
            headers=header,
        )

class Chain(NamespacedDriver):
    PATH = '/chain/'

    def status(self):
        """ Get Tendermint status including node info, pubkey, latest block hash, app hash, block height, current max peer height, and time.

        Returns:
            :obj:`json`:Details of the HTTP API provided by the tendermint server.

        Examples:

            >>>
            glitter_client = GlitterClient('http://127.0.0.1:26659')
            res = glitter_client.chain.status()
            printf(res)
            .. code-block:: json
            {
              "jsonrpc": "2.0",
              "id": -1,
              "result": {
                "node_info": {
                  "protocol_version": {
                    "p2p": "8",
                    "block": "11",
                    "app": "1"
                  },
                  "id": "70a32f3df5cb649f120275115d2426b98ade1643",
                  "listen_addr": "tcp://0.0.0.0:26656",
                  "network": "chain-LNTnFa",
                  "version": "unreleased-v0.35.15-patch-89300ca52122d077b0cc0dd774077b815c261f4e",
                  "channels": "40202122233038606100",
                  "moniker": "sg1.testnet.glitter.link",
                  "other": {
                    "tx_index": "on",
                    "rpc_address": "tcp://0.0.0.0:26657"
                  }
                },
                "sync_info": {
                  "latest_block_hash": "74B611416B4AA4CEF785731D1E1CFE32B5DACC35A49DC462321E98662F4E8385",
                  "latest_app_hash": "",
                  "latest_block_height": "466717",
                  "latest_block_time": "2022-02-26T14:31:14.37088966Z",
                  "earliest_block_hash": "7864542D842D7B10280C23621B295330745C3034DE7DDB9F8C6496FCC903237E",
                  "earliest_app_hash": "",
                  "earliest_block_height": "1",
                  "earliest_block_time": "2022-02-19T12:22:04.289435469Z",
                  "catching_up": false
                },
                "validator_info": {
                  "address": "8A380491EEC814F390C113E622258F5FA46B2765",
                  "pub_key": {
                    "type": "tendermint/PubKeyEd25519",
                    "value": "fBqygqcjcMoYIyHHsWeWYnP9jUkY+6PZPmJRGzzJRX0="
                  },
                  "voting_power": "1"
                }
              }
            }
            :param json: json object
        """
        path = "/chain/status"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
        )

    def tx_search(self, query, page=1, per_page=30, order_by="\"desc\"", prove=True):
        """ Search for transactions their results

        Args:
            query(str): query words. (e.g: ``tx.height=1000, tx.hash='xxx', update_doc.token='eliubin'``)
            page(int): page number
            per_page(int): number of entries per page (max: 100)
            order_by(str): Order in which transactions are sorted ("asc" or "desc"), by height & index. If empty, default sorting will be still applied.
            prove(bool): Include proofs of the transactions inclusion in the block
            headers(:obj:`dic`): http header
        Returns:
            :obj"`json`: transaction info

        Examples:

            >>>
            glitter_client = GlitterClient('http://127.0.0.1:26659')
            res = glitter_client.chain.tx_search(query="update_doc.token='my_token'")
            print(res)
            .. code-block:: json
            {
              "jsonrpc": "2.0",
              "id": -1,
              "result": {
                "txs": [
                  {
                    "hash": "ACB6696C22B601D544FE05C8899090B4C1E98EF87636AA07EBCD63548786B561",
                    "height": "460844",
                    "index": 0,
                    "tx_result": {
                      "code": 0,
                      "data": null,
                      "log": "",
                      "info": "",
                      "gas_wanted": "0",
                      "gas_used": "0",
                      "events": [
                        {
                          "type": "update_doc",
                          "attributes": [
                            {
                              "key": "dG9rZW4=",
                              "value": "bXlfdG9rZW4=",
                              "index": true
                            }
                          ]
                        }
                      ],
                      "codespace": ""
                    },
                    "tx": "CghteV90b2tlbhrRBxIGbGliZ2VuGiA1MTczMjc1ZjAyOWE3ZjBiNzhiZGNhY2EzNGE2ZGFjYyKkB3sidGl0bGUiOiAiXHUwNDFjXHUwNDM1XHUwNDM2XHUwNDM0XHUwNDQzXHUwNDNkXHUwNDMwXHUwNDQwXHUwNDNlXHUwNDM0XHUwNDNkXHUwNDMwXHUwNDRmIFx1MDQzMFx1MDQzZFx1MDQzMFx1MDQ0Mlx1MDQzZVx1MDQzY1x1MDQzOFx1MDQ0N1x1MDQzNVx1MDQ0MVx1MDQzYVx1MDQzMFx1MDQ0ZiBcdTA0M2RcdTA0M2VcdTA0M2NcdTA0MzVcdTA0M2RcdTA0M2FcdTA0M2JcdTA0MzBcdTA0NDJcdTA0NDNcdTA0NDBcdTA0MzAgKFBhcmlzaWFuYSBub21pbmEgYW5hdG9taWNhKSIsICJzZXJpZXMiOiBbIiJdLCAiYXV0aG9yIjogWyJcdTA0MWNcdTA0MzhcdTA0NDVcdTA0MzBcdTA0MzlcdTA0M2JcdTA0M2VcdTA0MzIgXHUwNDIxLlx1MDQyMS4gKFx1MDQ0MFx1MDQzNVx1MDQzNC4pIl0sICJwdWJsaXNoZXIiOiAiXHUwNDFjXHUwNDM1XHUwNDM0XHUwNDM4XHUwNDQ2XHUwNDM4XHUwNDNkXHUwNDMwIiwgImxhbmd1YWdlIjogWyJSdXNzaWFuIl0sICJtZDUiOiAiIiwgInRhZ3MiOiBbIlx1MDQxMVx1MDQzOFx1MDQzZVx1MDQzYlx1MDQzZVx1MDQzM1x1MDQzOFx1MDQ0N1x1MDQzNVx1MDQ0MVx1MDQzYVx1MDQzOFx1MDQzNSBcdTA0MzRcdTA0MzhcdTA0NDFcdTA0NDZcdTA0MzhcdTA0M2ZcdTA0M2JcdTA0MzhcdTA0M2RcdTA0NGIiLCAiXHUwNDEwXHUwNDNkXHUwNDMwXHUwNDQyXHUwNDNlXHUwNDNjXHUwNDM4XHUwNDRmIiwgIlx1MDQyMVx1MDQzYlx1MDQzZVx1MDQzMlx1MDQzMFx1MDQ0MFx1MDQzOCBcdTA0MzggXHUwNDQwXHUwNDMwXHUwNDM3XHUwNDMzXHUwNDNlXHUwNDMyXHUwNDNlXHUwNDQwXHUwNDNkXHUwNDM4XHUwNDNhXHUwNDM4Il0sICJpc3NuIjogIiIsICJpcGZzX2NpZCI6ICJiYWZ5a2J6YWNlZGptMjd5bWFwdDRqdDRoMnVlanJveWkydmw2cW4zcW9lMm9zcWUzamphN2E3bzZsbmtseSIsICJleHRlbnNpb24iOiAiZGp2dSJ9",
                    "proof": {
                      "root_hash": "711715C5DD2D929F5FA6128E73E63690C4CE876D92BE120040F379B50897E567",
                      "data": "CghteV90b2tlbhrRBxIGbGliZ2VuGiA1MTczMjc1ZjAyOWE3ZjBiNzhiZGNhY2EzNGE2ZGFjYyKkB3sidGl0bGUiOiAiXHUwNDFjXHUwNDM1XHUwNDM2XHUwNDM0XHUwNDQzXHUwNDNkXHUwNDMwXHUwNDQwXHUwNDNlXHUwNDM0XHUwNDNkXHUwNDMwXHUwNDRmIFx1MDQzMFx1MDQzZFx1MDQzMFx1MDQ0Mlx1MDQzZVx1MDQzY1x1MDQzOFx1MDQ0N1x1MDQzNVx1MDQ0MVx1MDQzYVx1MDQzMFx1MDQ0ZiBcdTA0M2RcdTA0M2VcdTA0M2NcdTA0MzVcdTA0M2RcdTA0M2FcdTA0M2JcdTA0MzBcdTA0NDJcdTA0NDNcdTA0NDBcdTA0MzAgKFBhcmlzaWFuYSBub21pbmEgYW5hdG9taWNhKSIsICJzZXJpZXMiOiBbIiJdLCAiYXV0aG9yIjogWyJcdTA0MWNcdTA0MzhcdTA0NDVcdTA0MzBcdTA0MzlcdTA0M2JcdTA0M2VcdTA0MzIgXHUwNDIxLlx1MDQyMS4gKFx1MDQ0MFx1MDQzNVx1MDQzNC4pIl0sICJwdWJsaXNoZXIiOiAiXHUwNDFjXHUwNDM1XHUwNDM0XHUwNDM4XHUwNDQ2XHUwNDM4XHUwNDNkXHUwNDMwIiwgImxhbmd1YWdlIjogWyJSdXNzaWFuIl0sICJtZDUiOiAiIiwgInRhZ3MiOiBbIlx1MDQxMVx1MDQzOFx1MDQzZVx1MDQzYlx1MDQzZVx1MDQzM1x1MDQzOFx1MDQ0N1x1MDQzNVx1MDQ0MVx1MDQzYVx1MDQzOFx1MDQzNSBcdTA0MzRcdTA0MzhcdTA0NDFcdTA0NDZcdTA0MzhcdTA0M2ZcdTA0M2JcdTA0MzhcdTA0M2RcdTA0NGIiLCAiXHUwNDEwXHUwNDNkXHUwNDMwXHUwNDQyXHUwNDNlXHUwNDNjXHUwNDM4XHUwNDRmIiwgIlx1MDQyMVx1MDQzYlx1MDQzZVx1MDQzMlx1MDQzMFx1MDQ0MFx1MDQzOCBcdTA0MzggXHUwNDQwXHUwNDMwXHUwNDM3XHUwNDMzXHUwNDNlXHUwNDMyXHUwNDNlXHUwNDQwXHUwNDNkXHUwNDM4XHUwNDNhXHUwNDM4Il0sICJpc3NuIjogIiIsICJpcGZzX2NpZCI6ICJiYWZ5a2J6YWNlZGptMjd5bWFwdDRqdDRoMnVlanJveWkydmw2cW4zcW9lMm9zcWUzamphN2E3bzZsbmtseSIsICJleHRlbnNpb24iOiAiZGp2dSJ9",
                      "proof": {
                        "total": "1",
                        "index": "0",
                        "leaf_hash": "cRcVxd0tkp9fphKOc+Y2kMTOh22SvhIAQPN5tQiX5Wc=",
                        "aunts": []
                      }
                    }
                  }
                ],
                "total_count": "1"
              }
            }
            :param json: json object
        """

        path = "/chain/tx_search"
        query = "\"" + query + "\""
        prove = "true" if prove else "false"

        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={'query': query, 'page': page, 'per_page': per_page, 'order_by': order_by, 'prove': prove},
        )

    def block_search(self, query, page=1, per_page=30, order_by="\"desc\""):
        """Search for blocks by BeginBlock and EndBlock events

        Args:
            query(str): query condition. (e.g: ``block.height > 1000 AND valset.changed > 0``)
            page(int): page number
            per_page(int): number of entries per page (max: 100)
            order_by(str): order in which blocks are sorted ("asc" or "desc"), by height. If empty, default sorting will be still applied.
        Returns:
            :obj:`json`: block info

        Examples:
            the example like::

                glitter_client = GlitterClient('http://127.0.0.1:26659')
                res = glitter_client.chain.block_search(query="block.height=1000")
                print(res)
                .. code-block:: json

                {
                   "jsonrpc": "2.0",
                   "id": -1,
                   "result": {
                     "blocks": [
                       {
                         "block_id": {
                           "hash": "10AB4DBCC0E8BA06381A6580197AAB68EAACDEA64BBAB50FB36B00F99A8191CB",
                           "parts": {
                             "total": 1,
                             "hash": "1734A94A2C210C9EE19B1DB15D116666CF9B68FB1DCE69883E27DA935712D449"
                           }
                         },
                         "block": {
                           "header": {
                             "version": {
                               "block": "11",
                               "app": "1"
                             },
                             "chain_id": "chain-LNTnFa",
                             "height": "1000",
                             "time": "2022-02-19T12:44:25.390486401Z",
                             "last_block_id": {
                               "hash": "DDEC58156107A30971C4A5BAF87C9CDD807597E686BEE1E344F477DD09C73DFB",
                               "parts": {
                                 "total": 1,
                                 "hash": "6CCC27C8A8BCA4C0E47F38B88D6E3FC4DE714380A9ABED1B498F8DB3FF18DE15"
                               }
                             },
                             "last_commit_hash": "601649850FBE9681EB9C1A2F294BA841321BD0E2D7826244B6540C435FFDABD7",
                             "data_hash": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                             "validators_hash": "E49055092750BE7A2533BD17E226E80A5E030A105E068D063D9BF46E6AED504F",
                             "next_validators_hash": "E49055092750BE7A2533BD17E226E80A5E030A105E068D063D9BF46E6AED504F",
                             "consensus_hash": "048091BC7DDC283F77BFBF91D73C44DA58C3DF8A9CBC867405D8B7F3DAADA22F",
                             "app_hash": "",
                             "last_results_hash": "6E340B9CFFB37A989CA544E6BB780A2C78901D3FB33738768511A30617AFA01D",
                             "evidence_hash": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                             "proposer_address": "E54A63CD67AA32386894EDE5839767F4CD6EC121"
                           },
                           "data": {
                             "txs": []
                           },
                           "evidence": {
                             "evidence": []
                           },
                           "last_commit": {
                             "height": "999",
                             "round": 0,
                             "block_id": {
                               "hash": "DDEC58156107A30971C4A5BAF87C9CDD807597E686BEE1E344F477DD09C73DFB",
                               "parts": {
                                 "total": 1,
                                 "hash": "6CCC27C8A8BCA4C0E47F38B88D6E3FC4DE714380A9ABED1B498F8DB3FF18DE15"
                               }
                             },
                             "signatures": [
                               {
                                 "block_id_flag": 2,
                                 "validator_address": "1F690E3E9C072133F3B897B358C0F2F127F16704",
                                 "timestamp": "2022-02-19T12:44:25.390486401Z",
                                 "signature": "2Zw73NO8ZDiujWHWg4mIKquf1q+aWlE1pMZp9xQ32QZNkG8++XnNin7gQRfmPIjeTnVGSvYtyxXArb2LDKnUAQ=="
                               },
                               {
                                 "block_id_flag": 2,
                                 "validator_address": "7CE3A03CBCDD77187D9AFD0C242ED0AB910B6ACD",
                                 "timestamp": "2022-02-19T12:44:25.391515882Z",
                                 "signature": "xauumFCrfeGClZnZuEEnGKu65L4gHj/S1wI+RZF74RaFB4QVz72GLdeEv5GJ1gkWH5GwCt9nnBSMsvaPAzOxCA=="
                               },
                               {
                                 "block_id_flag": 2,
                                 "validator_address": "88839061A231E8A1C8285B67EF8BCBE97C3D94BF",
                                 "timestamp": "2022-02-19T12:44:25.39137696Z",
                                 "signature": "UWmIjOSplfmUGbbbv9v0VXJIK+qypiMahC0YHCGgNjJm1rmJ43IXMD9jDttgjpn/qCkGcjCcmzVuEmxgG2YvCA=="
                               },
                               {
                                 "block_id_flag": 2,
                                 "validator_address": "8A380491EEC814F390C113E622258F5FA46B2765",
                                 "timestamp": "2022-02-19T12:44:25.390398641Z",
                                 "signature": "68WuIwIggTlpuJWzQBT8/76e9WvooeAyuRWvZ/raTHrQEiiXEA8KU2u7/H3EjKXSOWGtvXwY1vtsviSeBvfdDA=="
                               },
                               {
                                 "block_id_flag": 2,
                                 "validator_address": "E54A63CD67AA32386894EDE5839767F4CD6EC121",
                                 "timestamp": "2022-02-19T12:44:25.390518133Z",
                                 "signature": "E5M9LRCeONpiM+NRu/x6UuGelcE+EYN3MvfUYw6DRdAS33WEsUDGeZ6B3BYlw/ehd3ecclg/sCShVRk2xHoGDA=="
                               }
                             ]
                           }
                         }
                       }
                     ],
                     "total_count": "1"
                   }
                }
                :param json: json object
        """
        path = "/chain/block_search"
        query = "\"" + query + "\""

        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={'query': query, 'page': page, 'per_page': per_page, 'order_by': order_by},
        )

    def block(self, height=None):
        """ Get block at a specified height

        Args:
            height(int): height

        Returns:
            :obj:`json`:height to return. If no height is provided, it will fetch the latest block.

        """
        path = "/chain/block"
        params = {}
        if height is not None:
            params["height"] = height
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params=params,
        )

    def health(self):
        """ Get node health.

        Returns:
            Details of the HTTP API provided by the tendermint server, empty result (200 OK) on success, no response - in case of an error.
        """
        path = "/chain/health"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
        )

    def net_info(self):
        """ Get network info.

        Returns:
            Details of the HTTP API provided by the tendermint server.

        """
        path = "/chain/net_info"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
        )

    def blockchain(self, min_height=1, max_height=20):
        """ Get block headers for minHeight <= height maxHeight.
        If maxHeight does not yet exist, blocks up to the current height will be returned. If minHeight does not exist (due to pruning), earliest existing height will be used.
        At most 20 items will be returned. Block headers are returned in descending order (highest first).

        Args:
            min_height(int): Minimum block height to return
            max_height(bool): Maximum block height to return

        Returns:
            Block headers, returned in descending order (highest first).
        """

        path = "/chain/blockchain"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={"minHeight": min_height, "maxHeight": max_height}
        )

    def header(self, height=1):
        """ Retrieve the block header corresponding to a specified height.

        Args:
            height(int): height to return. If no height is provided, it will fetch the latest height.

        Returns:
            Header information.

        """
        path = "/chain/header"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={"height": height},
        )

    def header_by_hash(self, header_hash):
        """ Retrieve the block header corresponding to a block hash.

        Args:
            header_hash(str): header hash
        Returns:
        """
        path = "/chain/header_by_hash"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={"hash": header_hash},
        )

    def block_by_hash(self, *, header_hash):
        """ Get block by hash

        Args:
            header_hash(str): block hash. example: "0xD70952032620CC4E2737EB8AC379806359D8E0B17B0488F627997A0B043ABDED"

        Returns:

        """
        path = "/chain/header_by_hash"
        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params={"hash": header_hash},
        )


class Admin(NamespacedDriver):
    """Exposes functionality of the ``'/admin'`` endpoint.
    """

    def update_validator(self, pub_key, power=0, headers=None):
        """ update validator set

        Args:
            pub_key (str): public key
            power (int): power
            headers (dict): http header

        Returns:
            :obj:`dic`:

            {"code":200,message:"","tx_hash":"","data":{}}


        """
        path = "/admin/update_validator"
        return self.transport.forward_request(
            method='POST',
            path=self.api_prefix + path,
            params={'pub_key': pub_key, 'power': power},
            headers=headers
        )

    def validators(self, height=None, page=1, per_page=100):
        """Get validator set at a specified height

        Args:
            height(int): height to return. If no height is provided, it will fetch validator set which corresponds to the latest block.
            page(int): Page number (1-based)
            per_page(int): Number of entries per page (max: 100)

        Returns:
            :obj:`json`: Validators. Validators are sorted first by voting power (descending), then by address (ascending).

        Examples:
            the exmple like::

                glitter_client = GlitterClient('http://127.0.0.1:26659')
                res = glitter_client.chain.validators()
                print(res)
                 .. code-block:: json
                {
                  "jsonrpc": "2.0",
                  "id": -1,
                  "result": {
                    "block_height": "468323",
                    "validators": [
                      {
                        "address": "1F690E3E9C072133F3B897B358C0F2F127F16704",
                        "pub_key": {
                          "type": "tendermint/PubKeyEd25519",
                          "value": "NLmuSxM3ajCX1qNyiwZVXwv16KfFa2I2TRXGuWaAt0w="
                        },
                        "voting_power": "1",
                        "proposer_priority": "-2"
                      },
                      {
                        "address": "7CE3A03CBCDD77187D9AFD0C242ED0AB910B6ACD",
                        "pub_key": {
                          "type": "tendermint/PubKeyEd25519",
                          "value": "ijED7uyHJH4dc3uF7PJM1//b7L+EcAP8E0NOrk6aDdA="
                        },
                        "voting_power": "1",
                        "proposer_priority": "-2"
                      },
                      {
                        "address": "88839061A231E8A1C8285B67EF8BCBE97C3D94BF",
                        "pub_key": {
                          "type": "tendermint/PubKeyEd25519",
                          "value": "tV6rC04s6/EQU6e7J/wFH+g/jSblGSnaDUhTHCHzBEI="
                        },
                        "voting_power": "1",
                        "proposer_priority": "-2"
                      },
                      {
                        "address": "8A380491EEC814F390C113E622258F5FA46B2765",
                        "pub_key": {
                          "type": "tendermint/PubKeyEd25519",
                          "value": "fBqygqcjcMoYIyHHsWeWYnP9jUkY+6PZPmJRGzzJRX0="
                        },
                        "voting_power": "1",
                        "proposer_priority": "3"
                      },
                      {
                        "address": "E54A63CD67AA32386894EDE5839767F4CD6EC121",
                        "pub_key": {
                          "type": "tendermint/PubKeyEd25519",
                          "value": "3yyODkAeja03IIz37bp2ufmSau8CQ5oqc2qrKxo3YlA="
                        },
                        "voting_power": "1",
                        "proposer_priority": "3"
                      }
                    ],
                    "count": "5",
                    "total": "5"
                  }
                }
            :param json: json object
        """
        path = "/chain/validators"
        params = {"page": page, "per_page": per_page}
        if height is not None:
            params["height"] = height

        return self.transport.forward_request(
            method='GET',
            path=self.api_prefix + path,
            params=params,
        )
