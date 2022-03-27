import itertools
from json import dump

import tensorflow_datasets as tfds
from dotenv import load_dotenv
import hashlib

# noinspection PyUnresolvedReferences
import sign_language_datasets.datasets

# noinspection PyUnresolvedReferences
import sign_language_datasets.datasets.dgs_corpus
from sign_language_datasets.datasets.config import SignDatasetConfig

load_dotenv()

config = SignDatasetConfig(name="for-firestore2", version="1.0.0", include_video=False)
sign2mint = tfds.load(name='sign2_mint', builder_kwargs={"config": config})

full_data = []

for datum in sign2mint["train"]:
    name = datum['fachbegriff'].numpy().decode('utf-8')
    fsw = datum['gebaerdenschrift']['fsw'].numpy().decode('utf-8')
    url = datum['video'].numpy().decode('utf-8')
    uid_raw = "sign2mint" + datum['id'].numpy().decode('utf-8')
    uid = 's2m' + hashlib.md5(uid_raw.encode()).hexdigest()

    doc = {
        "uid": uid,
        "url": url,
        "meta": {
            "name": "Sign2MINT: " + name,
            "language": "gsg",
            "userId": "1aGEJfRxDqdpIbOnjU5i5X0quYu2"
        }
    }

    captions = [
        {"language": "de", "transcription": name},
        {"language": "Sgnw", "transcription": fsw},
    ]

    full_data.append({
        "doc": doc,
        "captions": captions
    })

with open("sign2mint.json", "w") as f:
    dump(full_data, f)

