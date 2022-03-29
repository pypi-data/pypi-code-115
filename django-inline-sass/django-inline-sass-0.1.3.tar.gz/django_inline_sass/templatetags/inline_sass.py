import hashlib

from django import template
from django.conf import settings
from django.template.utils import get_app_template_dirs
from django.core.cache import cache

register = template.Library()


@register.tag
def sass(parser, token):
    nodelist = parser.parse(('endsass', ))
    parser.delete_first_token()
    return SASSNode(nodelist)


class SASSNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        import sass as libsass
        cache_enabled = getattr(settings, 'DJANGO_INLINE_SASS_CACHE', False)
        sass_string = self.nodelist.render(context)
        cache_key = 'django_inline_sass_' + hashlib.md5(sass_string.encode('utf-8')).hexdigest()
        dir = getattr(settings, 'DJANGO_INLINE_SASS_DIR', 'sass')
        css = cache_enabled and cache.get(cache_key) or None

        if not css:
            css = libsass.compile(
                string=sass_string,
                output_style=getattr(settings, 'DEBUG', False) and 'compressed' or 'nested',
                include_paths=[str(path) for path in get_app_template_dirs(dir)]
            )
            if cache_enabled:
                cache.set(cache_key, css, getattr(settings, 'DJANGO_INLINE_SASS_CACHE_TIMEOUT', 60 * 60 * 24))

        return css
