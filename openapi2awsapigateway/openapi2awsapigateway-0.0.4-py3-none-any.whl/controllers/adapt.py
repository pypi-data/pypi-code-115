import json
import yaml
from cement import Controller, ex


class Adapt(Controller):
    class Meta:
        label = 'adapt'
        stacked_type = 'embedded'
        stacked_on = 'base'

    valid_extensions = ['json', 'yaml', 'yml']
    valid_methods = ['get', 'post', 'put', 'patch', 'delete']

    @ex(
        help='adapt specs to aws api gateway integration'
    )
    def adapt(self):
        print('hello')
        extension = self.app.pargs.file.split('.')[-1]
        if extension not in self.valid_extensions:
            print('File extension is not valid')
            return False

        file = open(self.app.pargs.file)
        data = dict()
        if extension == 'json':
            data = json.load(file)
        elif extension == 'yaml' or extension == 'yml':
            data = yaml.safe_load(file)

        if 'openapi' not in data:
            print('File is not an OpenAPI standard')
            return False

        for resource in data['paths']:
            for method in data['paths'][resource]:
                if method not in self.valid_methods:
                    continue

                if self.app.pargs.type == 'swagger-router-controller':
                    data['paths'][resource][method]['x-swagger-router-controller'] = 'Default'

                if self.app.pargs.type == 'amazon-apigateway-integration':
                    responses = []
                    for response in data['paths'][resource][method]['responses']:
                        responses.append({
                            response: {
                                'statusCode': response
                            }
                        })
                    integration = {
                        'type': 'http',
                        'httpMethod': method.upper(),
                        'uri': {
                            'Fn::Sub': 'http://${LuxautoApiBackendUri}' + resource,
                        },
                        'responses': responses,
                        'passthroughBehavior': 'when_no_match'
                    }
                    data['paths'][resource][method]['x-amazon-apigateway-integration'] = integration

        with open(self.app.pargs.file, 'w+') as result:
            if extension == 'json':
                print(json.dumps(data), file=result)
            else:
                print(yaml.dump(data), file=result)
