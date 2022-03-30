import json
import yaml
from cement import Controller, ex


valid_extensions = ['json', 'yaml', 'yml']
valid_methods = ['get', 'post', 'put', 'patch', 'delete']


class Remove(Controller):
    class Meta:
        label = 'remove'
        stacked_type = 'embedded'
        stacked_on = 'base'

    @ex(
        help='Remove the key from the endpoint in the specified open api spec file',
        arguments=[
            (
                ['--key'],
                {
                    'help': 'the name of the key to be removed',
                    'action': 'store',
                    'dest': 'key'
                }
            ),
            (
                    ['--from'],
                    {
                        'help': 'the open api spec file',
                        'action': 'store',
                        'dest': 'file'
                    }
            )
        ]
    )
    def remove(self):
        extension = self.app.pargs.file.split('.')[-1]
        if extension not in valid_extensions:
            print('File extension is not valid')
            return False

        specs = open(self.app.pargs.file)
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

                del data['paths'][resource][method][self.app.pargs.key]

        with open(self.app.pargs.file, 'w+') as result:
            if extension == 'json':
                print(json.dumps(data, indent=2), file=result)
            else:
                print(yaml.dump(data), file=result)
