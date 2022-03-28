

import os
from hoshi.i18n import TranslationManager

from ebs.linuxnode.core.basemixin import BaseMixin
from ebs.linuxnode.core.config import ConfigMixin
from ebs.linuxnode.core.log import NodeLoggingMixin


class i18nMixin(NodeLoggingMixin, ConfigMixin, BaseMixin):
    _supported_languages = ['en_US']

    def __init__(self, *args, **kwargs):
        super(i18nMixin, self).__init__(*args, **kwargs)
        self._i18n = None

    @property
    def _i18n_catalog_dirs(self):
        return [os.path.join(x, 'locale') for x in self.config.roots]

    @property
    def i18n_supported_languages(self):
        """
        Return the list of languages supported by the application. The list contains
        locale codes of the form 'en_US'. This is largely intended for use by code
        which requires i18n support. Such code should use this list to create and
        install a suitable set of i18n_contexts.
        """
        return self._supported_languages

    @property
    def i18n(self):
        return self._i18n

    def install(self):
        super(i18nMixin, self).install()
        self._i18n = TranslationManager(self.i18n_supported_languages,
                                        self._i18n_catalog_dirs)
        self._i18n.install()
