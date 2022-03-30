import json
import yaml
from cement import Controller, ex


valid_extensions = ['json', 'yaml', 'yml']
valid_methods = ['get', 'post', 'put', 'patch', 'delete']


def handle_file(*args, **kwargs):
    def inner(func):
        file = kwargs['file']

        extension = file.split('.')[-1]
        if extension not in valid_extensions:
            print('File extension is not valid')
            return False

        specs = open(file)
        data = dict()
        if extension == 'json':
            data = json.load(specs)
        elif extension == 'yaml' or extension == 'yml':
            data = yaml.safe_load(specs)

        if 'openapi' not in data:
            print('File is not an OpenAPI standard')
            return False

        for resource in data['paths']:
            for method in data['paths'][resource]:
                if method not in valid_methods:
                    continue

                data = func(data, resource, method)

        with open(file, 'w+') as result:
            if extension == 'json':
                print(json.dumps(data, indent=2), file=result)
            else:
                print(yaml.dump(data), file=result)

    return inner


class Add(Controller):
    class Meta:
        label = 'add'
        stacked_type = 'nested'
        stacked_on = 'base'

        arguments = [
            (['--from'],
             {'help': 'the open api spec file',
              'action': 'store',
              'dest': 'file',
              }
             ),
        ]

    @ex(
        help='Add x-swagger-router-controller to the open api specs',
        arguments=[
            (
                ['--value'],
                {
                    'help': 'the value of x-swagger-router-controller extensions',
                    'action': 'store',
                    'dest': 'value'
                }
            )
        ]
    )
    def swagger_router_controller(self):
        @handle_file(file=self.app.pargs.file)
        def handle_data(data, resource, method):
            data['paths'][resource][method]['x-swagger-router-controller'] = self.app.pargs.value
            return data

        return handle_data

    @ex(
        help='Add x-amazon-apigateway-integration to the open api specs',
        arguments=[
            (
                ['--uri'],
                {
                    'help': 'the value of x-amazon-apigateway-integration extensions',
                    'action': 'store',
                    'dest': 'uri'
                }
            ),
            (
                ['--type'],
                {
                    'help': 'the type of integration (usually http_proxy)',
                    'action': 'store',
                    'dest': 'type'
                }
            )
        ]
    )
    def amazon_apigateway_integration(self):
        @handle_file(file=self.app.pargs.file)
        def handle_data(data, resource, method):
            responses = []
            for response in data['paths'][resource][method]['responses']:
                responses.append({
                    response: {
                        'statusCode': response
                    }
                })
            integration = {
                'type': self.app.pargs.type,
                'httpMethod': method.upper(),
                'uri': {
                    'Fn::Sub': self.app.pargs.uri + resource,
                },
                'responses': responses,
                'passthroughBehavior': 'when_no_match',
                'requestParameters': {}
            }
            data['paths'][resource][method]['x-amazon-apigateway-integration'] = integration
            return data

        return handle_data

    @ex(
        help='Add x-amazon-apigateway-integration to the open api specs',
        arguments=[
            (
                    ['--header'],
                    {
                        'help': 'the header name',
                        'action': 'store',
                        'dest': 'header'
                    }
            ),
            (
                    ['--value'],
                    {
                        'help': 'the header value',
                        'action': 'store',
                        'dest': 'value'
                    }
            )
        ]
    )
    def add_header_to_integration(self):
        @handle_file(file=self.app.pargs.file)
        def handle_data(data, resource, method):
            data['paths'][resource][method]['x-amazon-apigateway-integration']['requestParameters'][f'integration.request.header.{self.app.pargs.header}'] = self.app.pargs.value
            return data

        return handle_data

