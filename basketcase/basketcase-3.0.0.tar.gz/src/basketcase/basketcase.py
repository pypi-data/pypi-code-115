from . import extractor
from . import storage
from . import authenticator

from pathlib import Path
from datetime import datetime
import requests

class BasketCase:
    def __init__(self):
        # Create application data directory
        self._data_directory = f'{Path.home()!s}/.basketcase'
        Path(self._data_directory).mkdir(parents=True, exist_ok=True)

        # Set output path
        self._output_base = f'{Path.cwd()!s}/basketcase_{datetime.now()!s}'
        self._output_images = self._output_base + '/images'
        self._output_videos = self._output_base + '/videos'

        # Initialize dependencies
        self._storage = storage.Storage(self._data_directory)
        self._http_client = requests.Session()
        self.authenticator = authenticator.Authenticator(self._http_client, self._storage)

        self._extractor = extractor.Extractor(
            http_client=self._http_client,
            output_dir_images=self._output_images,
            output_dir_videos=self._output_videos
        )

    def fetch(self, target_urls):
        resources = self._extractor.scan(target_urls)

        if resources['images'] or resources['videos']:
            # Create media output directories
            Path(self._output_images).mkdir(parents=True, exist_ok=True)
            Path(self._output_videos).mkdir(parents=True, exist_ok=True)

            for index, resource in resources['images'].items():
                self._extractor.get_image(resource)
            
            self._extractor.get_videos(resources['videos'])
        else:
            print('Nothing to download.')