from cement import App, TestApp, init_defaults
from cement.core.exc import CaughtSignal

from .core.exc import OpenApi2AwsApiGatewayError
from .controllers.base import Base
from .controllers.add import Add
from .controllers.remove import Remove

# configuration defaults
CONFIG = init_defaults('openapi2awsapigateway')
CONFIG['openapi2awsapigateway']['foo'] = 'bar'


class OpenApi2AwsApiGateway(App):
    """OpenAPI to AWS API Gateway primary application."""

    class Meta:
        label = 'openapi2awsapigateway'

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'yaml',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        # register handlers
        handlers = [
            Base,
            Add,
            Remove,
        ]


class OpenApi2AwsApiGatewayTest(TestApp,OpenApi2AwsApiGateway):
    """A sub-class of OpenApi2AwsApiGateway that is better suited for testing."""

    class Meta:
        label = 'openapi2awsapigateway'


def main():
    with OpenApi2AwsApiGateway() as app:
        try:
            app.args.add_argument('--from',
                                  action='store',
                                  dest='file')

            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except OpenApi2AwsApiGatewayError as e:
            print('OpenApi2AwsApiGatewayError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
