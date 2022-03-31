from ._data_provider import DataProvider, ContentValidator


class EndpointValidator(ContentValidator):
    def validate_content_data(self, data):
        return True


endpoint_data_provider = DataProvider(validator=EndpointValidator())
