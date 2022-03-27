# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['src', 'src.deiteo_kafka', 'src.deiteo_kafka.producer']

package_data = \
{'': ['*']}

install_requires = \
['aiokafka==0.7.1']

setup_kwargs = {
    'name': 'deiteo-kafka-client',
    'version': '0.0.1a0',
    'description': 'Python Kafka Client Developed By Deiteo Organisation',
    'long_description': '# Deiteo Kafka Client\n\n![example workflow](https://github.com/deiteo/deiteo-kafka-client/actions/workflows/merge.yaml/badge.svg)\n![example workflow](https://github.com/deiteo/deiteo-kafka-client/actions/workflows/pr.yaml/badge.svg)\n\nA library creating an interface on top of `AIOKafkaProducer`. To handle specific needs of\nprojects within open source Deiteo organisation.\n\n## Library Usage\n\n\n### DeiteoKafkaAioProducer\n* The `produce` method will accept topic content of type `str` or `Dict[str, Any]`, and will\nconvert this into a `byte string` to produce to topic.\n* The `DeiteoKafkaAioProducer` will create its own event `loop`, or you can inject one.\n\n\n#### Without providing loop\n```python\nfrom deiteo_kafka.producer.deiteo_kafka_aio_producer import DeiteoKafkaAioProducer\n\nbootstrap_servers = "localhost:1234"\ntopic = "deiteo-input-feed"\n\ntopic_content = {"A": 0, "B": "a-string", "C": 0.1}\ndeiteo_kafka_aio_producer = DeiteoKafkaAioProducer(\n    bootstrap_servers=bootstrap_servers,\n    topic=topic,\n)\nawait deiteo_kafka_aio_producer.producer.start()\nawait deiteo_kafka_aio_producer.produce(topic_content=topic_content)\n```\n\n#### Providing loop\n```python\nimport asyncio\nfrom deiteo_kafka.producer.deiteo_kafka_aio_producer import DeiteoKafkaAioProducer\n\nloop = asyncio.get_event_loop()\nbootstrap_servers = "localhost:1234"\ntopic = "deiteo-input-feed"\n\ntopic_content = {"A": 0, "B": "a-string", "C": 0.1}\ndeiteo_kafka_aio_producer = DeiteoKafkaAioProducer(\n    bootstrap_servers=bootstrap_servers,\n    topic=topic,\n    loop=loop,\n)\nawait deiteo_kafka_aio_producer.producer.start()\nawait deiteo_kafka_aio_producer.produce(topic_content=topic_content)\n```\n\nYou can then stop the producer if needed by:\n\n```python\nawait deiteo_kafka_aio_producer.producer.stop()\n```\n\n## Setup From Scratch\n\n### Requirement\n\n* ^python3.8\n* poetry 1.1.13\n* make (GNU Make 3.81)\n\n### Setup\n\n```bash\nmake setup-environment\n```\n\nUpdate package\n```bash\nmake update\n```\n\n### Test\n\n```bash\nmake test type=unit/integration\n```\n\n### Docker\n\nThe reason `docker` is used in the source code here, is to be able to build up an encapsulated\nenvironment of the codebase, and do `unit/integration and load tests`.\n\n```bash\nmake build-container-image\n```\n\n```bash\nmake get-container-info-environment\nmake run-container-tests type=unit\n```\n',
    'author': 'Simon Thelin',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/deiteo/deiteo-kafka-client',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
