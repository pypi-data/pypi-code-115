from django import template
from django.template import Node

register = template.Library()


@register.filter('niceseconds')
def niceseconds(seconds):
    try:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%dh:%02dm:%02ds" % (h, m, s)
    except TypeError:
        return ''


@register.filter()
def get_visited_status(object, user):
    return object.get_visited_status(user)


@register.filter()
def did_user_visit(object, user):    
    return object.did_user_vote(user)


@register.filter
def truncatesmart(value, limit=80):
    """
    Truncates a string after a given number of chars keeping whole words.
    
    Usage:
        {{ string|truncatesmart }}
        {{ string|truncatesmart:50 }}
    """
    
    try:
        limit = int(limit)
    # invalid literal for int()
    except ValueError:
        # Fail silently.
        return value
    
    # Make sure it's string
    value = str(value)
    
    # Return the string itself if length is smaller or equal to the limit
    if len(value) <= limit:
        return value
    
    # Cut the string
    value = value[:limit]
    
    # Break into words and remove the last
    words = value.split(' ')[:-1]
    
    # Join the words and return
    return ' '.join(words) + '...'


@register.filter
def truncatewords_by_chars(value, arg):
    """Truncate the text when it exceeds a certain number of characters.
    Delete the last word only if partial.
    Adds '...' at the end of the text.

    Example:

        {{ text|truncatewords_by_chars:25 }}
    """
    try:
        length = int(arg)
    except ValueError:
        return value

    if len(value) > length:
        if value[length:length + 1].isspace():
            return value[:length].rstrip() + '...'
        else:
            return value[:length].rsplit(' ', 1)[0].rstrip() + '...'
    else:
        return value


class RangeNode(Node):
    def __init__(self, parser, range_args, context_name):
        self.template_parser = parser
        self.range_args = range_args
        self.context_name = context_name

    def render(self, context):

        resolved_ranges = []
        for arg in self.range_args:
            compiled_arg = self.template_parser.compile_filter(arg)
            resolved_ranges.append(compiled_arg.resolve(context, ignore_failures=True))
        context[self.context_name] = range(*resolved_ranges)
        return ""


@register.filter(is_safe=False)
def divide(value, arg):
    """Divides the value by argument."""
    try:
        return float(value) / float(arg)
    except ZeroDivisionError:
        return float(value)
    except (ValueError, TypeError):
        return ''


@register.filter(is_safe=False)
def multiply(value, arg):
    """Multiplies the value by argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter(is_safe=False)
def add(value, arg):
    """Adds the arg to the value."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter(is_safe=False)
def subtract(value, arg):
    """Subtracts the arg to the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)