from bson.json_util import dumps
from bson.json_util import loads

from transformHealthEventHubModels.utils import *


class DataStandardisationTriggerObject(object):

    def __init__(self, file_id, client_id, upload_file_name, template_id, upload_file_location, file_source, share_name):
        self.file_id = file_id
        self.clientID = client_id
        self.uploadFileName = upload_file_name
        self.templateId = template_id
        self.uploadFileLocation = upload_file_location
        self.fileSource = file_source
        self.shareName = share_name

    def json(self):
        return {
            "file_id": dumps(self.file_id, sort_keys=True, default=str),
            "client_id": dumps(self.clientID, sort_keys=True, default=str),
            "upload_file_name": self.uploadFileName,
            "template_id": dumps(self.templateId, sort_keys=True, default=str),
            "upload_file_location": self.uploadFileLocation,
            "file_source": self.fileSource,
            "share_name": self.shareName
        }

    @classmethod
    def load_object(cls, json_data):
        return cls(
            loads(decodeUTFString(json_data[b'file_id'])),
            loads(decodeUTFString(json_data[b'client_id'])),
            decodeUTFString(json_data[b'upload_file_name']),
            loads(decodeUTFString(json_data[b'template_id'])),
            decodeUTFString(json_data[b'upload_file_location']),
            decodeUTFString(json_data[b'file_source']),
            decodeUTFString(json_data[b'share_name'])
        )
