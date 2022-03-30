# Local imports
from qwilfish.constants import DEFAULT_START_SYMBOL
from qwilfish.grammar import opts
from qwilfish.session_builder import register_grammar

# Name of the plugin
PLUGIN_IDENTIFIER = "coap_grammar"

def initialize():
    '''Will be called by the plugin loader.'''
    register_grammar(PLUGIN_IDENTIFIER, create)

def create():
    return COAP_GRAMMAR.copy()

COAP_GRAMMAR = {
    DEFAULT_START_SYMBOL:
        ["I'm a CoAP message!"]
}
