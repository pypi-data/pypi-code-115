

import os

from twisted.internet import reactor
from ebs.linuxnode.core.basenode import BaseIoTNode
from ebs.linuxnode.core import config
from ebs.linuxnode.i18n.mixin import i18nMixin


class ExampleNode(i18nMixin, BaseIoTNode):
    _supported_languages = ['en_US', 'hi_IN']

    def i18n_example(self):
        # Create the _ object in a meaningful place. Technically, it
        # doesn't need to exist as you can use self.i18n.translator directly.
        # In practice, _("") is a sufficiently common motif that having it is
        # likely to enhance rather than degrade maintainability.
        _ = self.i18n.translator('default')
        s = 'Hello World'
        for lang in self._supported_languages:
            # Use set_global_language or set_language to control the language.
            # Depending on the use case, you could also manually specify target
            # languages for each translation call. See hoshi docs.
            self.i18n.set_global_language(lang)
            print("{} : {}".format(lang, _(s)))
        self.stop()

    def install(self):
        # Register the application's local root, so the catalog dir
        # will be created here instead of in some other core library
        # Generally, either specify the catalog_dir manually in
        # i18n.install_context or ensure the target root is the last
        # one to have been registered.
        self.config.register_application_root(
            os.path.abspath(os.path.dirname(__file__))
        )
        super(ExampleNode, self).install()
        for lang in self._supported_languages:
            self.i18n.install_context('default', lang)

    def start(self):
        self.install()
        super(ExampleNode, self).start()
        reactor.callLater(10, self.i18n_example)
        reactor.run()

    def stop(self):
        super(ExampleNode, self).stop()
        reactor.stop()


def main():
    nodeconfig = config.IoTNodeConfig()
    config.current_config = nodeconfig

    node = ExampleNode(reactor=reactor)
    node.start()


if __name__ == '__main__':
    main()
