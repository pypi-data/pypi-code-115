"""IPython terminal interface using prompt_toolkit"""

import asyncio
import os
import sys
from warnings import warn

from IPython.core.async_helpers import get_asyncio_loop
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.utils.py3compat import input
from IPython.utils.terminal import toggle_set_term_title, set_term_title, restore_term_title
from IPython.utils.process import abbrev_cwd
from traitlets import (
    Bool,
    Unicode,
    Dict,
    Integer,
    observe,
    Instance,
    Type,
    default,
    Enum,
    Union,
    Any,
    validate,
    Float,
)

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import (HasFocus, Condition, IsDone)
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.history import History
from prompt_toolkit.layout.processors import ConditionalProcessor, HighlightMatchingBracketProcessor
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle, print_formatted_text
from prompt_toolkit.styles import DynamicStyle, merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls, style_from_pygments_dict
from prompt_toolkit import __version__ as ptk_version

from pygments.styles import get_style_by_name
from pygments.style import Style
from pygments.token import Token

from .debugger import TerminalPdb, Pdb
from .magics import TerminalMagics
from .pt_inputhooks import get_inputhook_name_and_func
from .prompts import Prompts, ClassicPrompts, RichPromptDisplayHook
from .ptutils import IPythonPTCompleter, IPythonPTLexer
from .shortcuts import create_ipython_shortcuts

PTK3 = ptk_version.startswith('3.')


class _NoStyle(Style): pass



_style_overrides_light_bg = {
            Token.Prompt: '#ansibrightblue',
            Token.PromptNum: '#ansiblue bold',
            Token.OutPrompt: '#ansibrightred',
            Token.OutPromptNum: '#ansired bold',
}

_style_overrides_linux = {
            Token.Prompt: '#ansibrightgreen',
            Token.PromptNum: '#ansigreen bold',
            Token.OutPrompt: '#ansibrightred',
            Token.OutPromptNum: '#ansired bold',
}

def get_default_editor():
    try:
        return os.environ['EDITOR']
    except KeyError:
        pass
    except UnicodeError:
        warn("$EDITOR environment variable is not pure ASCII. Using platform "
             "default editor.")

    if os.name == 'posix':
        return 'vi'  # the only one guaranteed to be there!
    else:
        return 'notepad' # same in Windows!

# conservatively check for tty
# overridden streams can result in things like:
# - sys.stdin = None
# - no isatty method
for _name in ('stdin', 'stdout', 'stderr'):
    _stream = getattr(sys, _name)
    if not _stream or not hasattr(_stream, 'isatty') or not _stream.isatty():
        _is_tty = False
        break
else:
    _is_tty = True


_use_simple_prompt = ('IPY_TEST_SIMPLE_PROMPT' in os.environ) or (not _is_tty)

def black_reformat_handler(text_before_cursor):
    """
    We do not need to protect against error,
    this is taken care at a higher level where any reformat error is ignored.
    Indeed we may call reformatting on incomplete code.
    """
    import black

    formatted_text = black.format_str(text_before_cursor, mode=black.FileMode())
    if not text_before_cursor.endswith("\n") and formatted_text.endswith("\n"):
        formatted_text = formatted_text[:-1]
    return formatted_text


def yapf_reformat_handler(text_before_cursor):
    from yapf.yapflib import file_resources
    from yapf.yapflib import yapf_api

    style_config = file_resources.GetDefaultStyleForDir(os.getcwd())
    formatted_text, was_formatted = yapf_api.FormatCode(
        text_before_cursor, style_config=style_config
    )
    if was_formatted:
        if not text_before_cursor.endswith("\n") and formatted_text.endswith("\n"):
            formatted_text = formatted_text[:-1]
        return formatted_text
    else:
        return text_before_cursor


class PtkHistoryAdapter(History):
    """
    Prompt toolkit has it's own way of handling history, Where it assumes it can
    Push/pull from history.

    """

    def __init__(self, shell):
        super().__init__()
        self.shell = shell
        self._refresh()

    def append_string(self, string):
        # we rely on sql for that.
        self._loaded = False
        self._refresh()

    def _refresh(self):
        if not self._loaded:
            self._loaded_strings = list(self.load_history_strings())

    def load_history_strings(self):
        last_cell = ""
        res = []
        for __, ___, cell in self.shell.history_manager.get_tail(
            self.shell.history_load_length, include_latest=True
        ):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                res.append(cell)
                last_cell = cell
        yield from res[::-1]

    def store_string(self, string: str) -> None:
        pass

class TerminalInteractiveShell(InteractiveShell):
    mime_renderers = Dict().tag(config=True)

    space_for_menu = Integer(6, help='Number of line at the bottom of the screen '
                                     'to reserve for the tab completion menu, '
                                     'search history, ...etc, the height of '
                                     'these menus will at most this value. '
                                     'Increase it is you prefer long and skinny '
                                     'menus, decrease for short and wide.'
                            ).tag(config=True)

    pt_app = None
    debugger_history = None

    debugger_history_file = Unicode(
        "~/.pdbhistory", help="File in which to store and read history"
    ).tag(config=True)

    simple_prompt = Bool(_use_simple_prompt,
        help="""Use `raw_input` for the REPL, without completion and prompt colors.

            Useful when controlling IPython as a subprocess, and piping STDIN/OUT/ERR. Known usage are:
            IPython own testing machinery, and emacs inferior-shell integration through elpy.

            This mode default to `True` if the `IPY_TEST_SIMPLE_PROMPT`
            environment variable is set, or the current terminal is not a tty."""
            ).tag(config=True)

    @property
    def debugger_cls(self):
        return Pdb if self.simple_prompt else TerminalPdb

    confirm_exit = Bool(True,
        help="""
        Set to confirm when you try to exit IPython with an EOF (Control-D
        in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
        you can force a direct exit without any confirmation.""",
    ).tag(config=True)

    editing_mode = Unicode('emacs',
        help="Shortcut style to use at the prompt. 'vi' or 'emacs'.",
    ).tag(config=True)

    emacs_bindings_in_vi_insert_mode = Bool(
        True,
        help="Add shortcuts from 'emacs' insert mode to 'vi' insert mode.",
    ).tag(config=True)

    modal_cursor = Bool(
        True,
        help="""
       Cursor shape changes depending on vi mode: beam in vi insert mode,
       block in nav mode, underscore in replace mode.""",
    ).tag(config=True)

    ttimeoutlen = Float(
        0.01,
        help="""The time in milliseconds that is waited for a key code
       to complete.""",
    ).tag(config=True)

    timeoutlen = Float(
        0.5,
        help="""The time in milliseconds that is waited for a mapped key
       sequence to complete.""",
    ).tag(config=True)

    autoformatter = Unicode(
        None,
        help="Autoformatter to reformat Terminal code. Can be `'black'`, `'yapf'` or `None`",
        allow_none=True
    ).tag(config=True)

    auto_match = Bool(
        False,
        help="""
        Automatically add/delete closing bracket or quote when opening bracket or quote is entered/deleted.
        Brackets: (), [], {}
        Quotes: '', \"\"
        """,
    ).tag(config=True)

    mouse_support = Bool(False,
        help="Enable mouse support in the prompt\n(Note: prevents selecting text with the mouse)"
    ).tag(config=True)

    # We don't load the list of styles for the help string, because loading
    # Pygments plugins takes time and can cause unexpected errors.
    highlighting_style = Union([Unicode('legacy'), Type(klass=Style)],
        help="""The name or class of a Pygments style to use for syntax
        highlighting. To see available styles, run `pygmentize -L styles`."""
    ).tag(config=True)

    @validate('editing_mode')
    def _validate_editing_mode(self, proposal):
        if proposal['value'].lower() == 'vim':
            proposal['value']= 'vi'
        elif proposal['value'].lower() == 'default':
            proposal['value']= 'emacs'

        if hasattr(EditingMode, proposal['value'].upper()):
            return proposal['value'].lower()

        return self.editing_mode


    @observe('editing_mode')
    def _editing_mode(self, change):
        if self.pt_app:
            self.pt_app.editing_mode = getattr(EditingMode, change.new.upper())

    def _set_formatter(self, formatter):
        if formatter is None:
            self.reformat_handler = lambda x:x
        elif formatter == 'black':
            self.reformat_handler = black_reformat_handler
        elif formatter == "yapf":
            self.reformat_handler = yapf_reformat_handler
        else:
            raise ValueError

    @observe("autoformatter")
    def _autoformatter_changed(self, change):
        formatter = change.new
        self._set_formatter(formatter)

    @observe('highlighting_style')
    @observe('colors')
    def _highlighting_style_changed(self, change):
        self.refresh_style()

    def refresh_style(self):
        self._style = self._make_style_from_name_or_cls(self.highlighting_style)


    highlighting_style_overrides = Dict(
        help="Override highlighting format for specific tokens"
    ).tag(config=True)

    true_color = Bool(False,
        help="""Use 24bit colors instead of 256 colors in prompt highlighting.
        If your terminal supports true color, the following command should
        print ``TRUECOLOR`` in orange::

            printf \"\\x1b[38;2;255;100;0mTRUECOLOR\\x1b[0m\\n\"
        """,
    ).tag(config=True)

    editor = Unicode(get_default_editor(),
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad)."
    ).tag(config=True)

    prompts_class = Type(Prompts, help='Class used to generate Prompt token for prompt_toolkit').tag(config=True)

    prompts = Instance(Prompts)

    @default('prompts')
    def _prompts_default(self):
        return self.prompts_class(self)

#    @observe('prompts')
#    def _(self, change):
#        self._update_layout()

    @default('displayhook_class')
    def _displayhook_class_default(self):
        return RichPromptDisplayHook

    term_title = Bool(True,
        help="Automatically set the terminal title"
    ).tag(config=True)

    term_title_format = Unicode("IPython: {cwd}",
        help="Customize the terminal title format.  This is a python format string. " +
             "Available substitutions are: {cwd}."
    ).tag(config=True)

    display_completions = Enum(('column', 'multicolumn','readlinelike'),
        help= ( "Options for displaying tab completions, 'column', 'multicolumn', and "
                "'readlinelike'. These options are for `prompt_toolkit`, see "
                "`prompt_toolkit` documentation for more information."
                ),
        default_value='multicolumn').tag(config=True)

    highlight_matching_brackets = Bool(True,
        help="Highlight matching brackets.",
    ).tag(config=True)

    extra_open_editor_shortcuts = Bool(False,
        help="Enable vi (v) or Emacs (C-X C-E) shortcuts to open an external editor. "
             "This is in addition to the F2 binding, which is always enabled."
    ).tag(config=True)

    handle_return = Any(None,
        help="Provide an alternative handler to be called when the user presses "
             "Return. This is an advanced option intended for debugging, which "
             "may be changed or removed in later releases."
    ).tag(config=True)

    enable_history_search = Bool(True,
        help="Allows to enable/disable the prompt toolkit history search"
    ).tag(config=True)

    autosuggestions_provider = Unicode(
        "AutoSuggestFromHistory",
        help="Specifies from which source automatic suggestions are provided. "
        "Can be set to `'AutoSuggestFromHistory`' or `None` to disable"
        "automatic suggestions. Default is `'AutoSuggestFromHistory`'.",
        allow_none=True,
    ).tag(config=True)

    def _set_autosuggestions(self, provider):
        if provider is None:
            self.auto_suggest = None
        elif provider == "AutoSuggestFromHistory":
            self.auto_suggest = AutoSuggestFromHistory()
        else:
            raise ValueError("No valid provider.")
        if self.pt_app:
            self.pt_app.auto_suggest = self.auto_suggest

    @observe("autosuggestions_provider")
    def _autosuggestions_provider_changed(self, change):
        provider = change.new
        self._set_autosuggestions(provider)

    prompt_includes_vi_mode = Bool(True,
        help="Display the current vi mode (when using vi editing mode)."
    ).tag(config=True)

    @observe('term_title')
    def init_term_title(self, change=None):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title(self.term_title_format.format(cwd=abbrev_cwd()))
        else:
            toggle_set_term_title(False)

    def restore_term_title(self):
        if self.term_title:
            restore_term_title()

    def init_display_formatter(self):
        super(TerminalInteractiveShell, self).init_display_formatter()
        # terminal only supports plain text
        self.display_formatter.active_types = ["text/plain"]

    def init_prompt_toolkit_cli(self):
        if self.simple_prompt:
            # Fall back to plain non-interactive output for tests.
            # This is very limited.
            def prompt():
                prompt_text = "".join(x[1] for x in self.prompts.in_prompt_tokens())
                lines = [input(prompt_text)]
                prompt_continuation = "".join(x[1] for x in self.prompts.continuation_prompt_tokens())
                while self.check_complete('\n'.join(lines))[0] == 'incomplete':
                    lines.append( input(prompt_continuation) )
                return '\n'.join(lines)
            self.prompt_for_code = prompt
            return

        # Set up keyboard shortcuts
        key_bindings = create_ipython_shortcuts(self)


        # Pre-populate history from IPython's history database
        history = PtkHistoryAdapter(self)

        self._style = self._make_style_from_name_or_cls(self.highlighting_style)
        self.style = DynamicStyle(lambda: self._style)

        editing_mode = getattr(EditingMode, self.editing_mode.upper())

        self.pt_loop = asyncio.new_event_loop()
        self.pt_app = PromptSession(
            auto_suggest=self.auto_suggest,
            editing_mode=editing_mode,
            key_bindings=key_bindings,
            history=history,
            completer=IPythonPTCompleter(shell=self),
            enable_history_search=self.enable_history_search,
            style=self.style,
            include_default_pygments_style=False,
            mouse_support=self.mouse_support,
            enable_open_in_editor=self.extra_open_editor_shortcuts,
            color_depth=self.color_depth,
            tempfile_suffix=".py",
            **self._extra_prompt_options()
        )

    def _make_style_from_name_or_cls(self, name_or_cls):
        """
        Small wrapper that make an IPython compatible style from a style name

        We need that to add style for prompt ... etc.
        """
        style_overrides = {}
        if name_or_cls == 'legacy':
            legacy = self.colors.lower()
            if legacy == 'linux':
                style_cls = get_style_by_name('monokai')
                style_overrides = _style_overrides_linux
            elif legacy == 'lightbg':
                style_overrides = _style_overrides_light_bg
                style_cls = get_style_by_name('pastie')
            elif legacy == 'neutral':
                # The default theme needs to be visible on both a dark background
                # and a light background, because we can't tell what the terminal
                # looks like. These tweaks to the default theme help with that.
                style_cls = get_style_by_name('default')
                style_overrides.update({
                    Token.Number: '#ansigreen',
                    Token.Operator: 'noinherit',
                    Token.String: '#ansiyellow',
                    Token.Name.Function: '#ansiblue',
                    Token.Name.Class: 'bold #ansiblue',
                    Token.Name.Namespace: 'bold #ansiblue',
                    Token.Name.Variable.Magic: '#ansiblue',
                    Token.Prompt: '#ansigreen',
                    Token.PromptNum: '#ansibrightgreen bold',
                    Token.OutPrompt: '#ansired',
                    Token.OutPromptNum: '#ansibrightred bold',
                })

                # Hack: Due to limited color support on the Windows console
                # the prompt colors will be wrong without this
                if os.name == 'nt':
                    style_overrides.update({
                        Token.Prompt: '#ansidarkgreen',
                        Token.PromptNum: '#ansigreen bold',
                        Token.OutPrompt: '#ansidarkred',
                        Token.OutPromptNum: '#ansired bold',
                    })
            elif legacy =='nocolor':
                style_cls=_NoStyle
                style_overrides = {}
            else :
                raise ValueError('Got unknown colors: ', legacy)
        else :
            if isinstance(name_or_cls, str):
                style_cls = get_style_by_name(name_or_cls)
            else:
                style_cls = name_or_cls
            style_overrides = {
                Token.Prompt: '#ansigreen',
                Token.PromptNum: '#ansibrightgreen bold',
                Token.OutPrompt: '#ansired',
                Token.OutPromptNum: '#ansibrightred bold',
            }
        style_overrides.update(self.highlighting_style_overrides)
        style = merge_styles([
            style_from_pygments_cls(style_cls),
            style_from_pygments_dict(style_overrides),
        ])

        return style

    @property
    def pt_complete_style(self):
        return {
            'multicolumn': CompleteStyle.MULTI_COLUMN,
            'column': CompleteStyle.COLUMN,
            'readlinelike': CompleteStyle.READLINE_LIKE,
        }[self.display_completions]

    @property
    def color_depth(self):
        return (ColorDepth.TRUE_COLOR if self.true_color else None)

    def _extra_prompt_options(self):
        """
        Return the current layout option for the current Terminal InteractiveShell
        """
        def get_message():
            return PygmentsTokens(self.prompts.in_prompt_tokens())

        if self.editing_mode == 'emacs':
            # with emacs mode the prompt is (usually) static, so we call only
            # the function once. With VI mode it can toggle between [ins] and
            # [nor] so we can't precompute.
            # here I'm going to favor the default keybinding which almost
            # everybody uses to decrease CPU usage.
            # if we have issues with users with custom Prompts we can see how to
            # work around this.
            get_message = get_message()

        options = {
                'complete_in_thread': False,
                'lexer':IPythonPTLexer(),
                'reserve_space_for_menu':self.space_for_menu,
                'message': get_message,
                'prompt_continuation': (
                    lambda width, lineno, is_soft_wrap:
                        PygmentsTokens(self.prompts.continuation_prompt_tokens(width))),
                'multiline': True,
                'complete_style': self.pt_complete_style,

                # Highlight matching brackets, but only when this setting is
                # enabled, and only when the DEFAULT_BUFFER has the focus.
                'input_processors': [ConditionalProcessor(
                        processor=HighlightMatchingBracketProcessor(chars='[](){}'),
                        filter=HasFocus(DEFAULT_BUFFER) & ~IsDone() &
                            Condition(lambda: self.highlight_matching_brackets))],
                }
        if not PTK3:
            options['inputhook'] = self.inputhook

        return options

    def prompt_for_code(self):
        if self.rl_next_input:
            default = self.rl_next_input
            self.rl_next_input = None
        else:
            default = ''

        # In order to make sure that asyncio code written in the
        # interactive shell doesn't interfere with the prompt, we run the
        # prompt in a different event loop.
        # If we don't do this, people could spawn coroutine with a
        # while/true inside which will freeze the prompt.

        policy = asyncio.get_event_loop_policy()
        old_loop = get_asyncio_loop()

        # FIXME: prompt_toolkit is using the deprecated `asyncio.get_event_loop`
        # to get the current event loop.
        # This will probably be replaced by an attribute or input argument,
        # at which point we can stop calling the soon-to-be-deprecated `set_event_loop` here.
        if old_loop is not self.pt_loop:
            policy.set_event_loop(self.pt_loop)
        try:
            with patch_stdout(raw=True):
                text = self.pt_app.prompt(
                    default=default,
                    **self._extra_prompt_options())
        finally:
            # Restore the original event loop.
            if old_loop is not None and old_loop is not self.pt_loop:
                policy.set_event_loop(old_loop)

        return text

    def enable_win_unicode_console(self):
        # Since IPython 7.10 doesn't support python < 3.6 and PEP 528, Python uses the unicode APIs for the Windows
        # console by default, so WUC shouldn't be needed.
        warn("`enable_win_unicode_console` is deprecated since IPython 7.10, does not do anything and will be removed in the future",
             DeprecationWarning,
             stacklevel=2)

    def init_io(self):
        if sys.platform not in {'win32', 'cli'}:
            return

        import colorama
        colorama.init()

    def init_magics(self):
        super(TerminalInteractiveShell, self).init_magics()
        self.register_magics(TerminalMagics)

    def init_alias(self):
        # The parent class defines aliases that can be safely used with any
        # frontend.
        super(TerminalInteractiveShell, self).init_alias()

        # Now define aliases that only make sense on the terminal, because they
        # need direct access to the console in a way that we can't emulate in
        # GUI or web frontend
        if os.name == 'posix':
            for cmd in ('clear', 'more', 'less', 'man'):
                self.alias_manager.soft_define_alias(cmd, cmd)


    def __init__(self, *args, **kwargs):
        super(TerminalInteractiveShell, self).__init__(*args, **kwargs)
        self._set_autosuggestions(self.autosuggestions_provider)
        self.init_prompt_toolkit_cli()
        self.init_term_title()
        self.keep_running = True
        self._set_formatter(self.autoformatter)


    def ask_exit(self):
        self.keep_running = False

    rl_next_input = None

    def interact(self):
        self.keep_running = True
        while self.keep_running:
            print(self.separate_in, end='')

            try:
                code = self.prompt_for_code()
            except EOFError:
                if (not self.confirm_exit) \
                        or self.ask_yes_no('Do you really want to exit ([y]/n)?','y','n'):
                    self.ask_exit()

            else:
                if code:
                    self.run_cell(code, store_history=True)

    def mainloop(self):
        # An extra layer of protection in case someone mashing Ctrl-C breaks
        # out of our internal code.
        while True:
            try:
                self.interact()
                break
            except KeyboardInterrupt as e:
                print("\n%s escaped interact()\n" % type(e).__name__)
            finally:
                # An interrupt during the eventloop will mess up the
                # internal state of the prompt_toolkit library.
                # Stopping the eventloop fixes this, see
                # https://github.com/ipython/ipython/pull/9867
                if hasattr(self, '_eventloop'):
                    self._eventloop.stop()

                self.restore_term_title()

        # try to call some at-exit operation optimistically as some things can't
        # be done during interpreter shutdown. this is technically inaccurate as
        # this make mainlool not re-callable, but that should be a rare if not
        # in existent use case.

        self._atexit_once()


    _inputhook = None
    def inputhook(self, context):
        if self._inputhook is not None:
            self._inputhook(context)

    active_eventloop = None
    def enable_gui(self, gui=None):
        if gui and (gui != 'inline') :
            self.active_eventloop, self._inputhook =\
                get_inputhook_name_and_func(gui)
        else:
            self.active_eventloop = self._inputhook = None

        # For prompt_toolkit 3.0. We have to create an asyncio event loop with
        # this inputhook.
        if PTK3:
            import asyncio
            from prompt_toolkit.eventloop import new_eventloop_with_inputhook

            if gui == 'asyncio':
                # When we integrate the asyncio event loop, run the UI in the
                # same event loop as the rest of the code. don't use an actual
                # input hook. (Asyncio is not made for nesting event loops.)
                self.pt_loop = get_asyncio_loop()

            elif self._inputhook:
                # If an inputhook was set, create a new asyncio event loop with
                # this inputhook for the prompt.
                self.pt_loop = new_eventloop_with_inputhook(self._inputhook)
            else:
                # When there's no inputhook, run the prompt in a separate
                # asyncio event loop.
                self.pt_loop = asyncio.new_event_loop()

    # Run !system commands directly, not through pipes, so terminal programs
    # work correctly.
    system = InteractiveShell.system_raw

    def auto_rewrite_input(self, cmd):
        """Overridden from the parent class to use fancy rewriting prompt"""
        if not self.show_rewritten_input:
            return

        tokens = self.prompts.rewrite_prompt_tokens()
        if self.pt_app:
            print_formatted_text(PygmentsTokens(tokens), end='',
                                 style=self.pt_app.app.style)
            print(cmd)
        else:
            prompt = ''.join(s for t, s in tokens)
            print(prompt, cmd, sep='')

    _prompts_before = None
    def switch_doctest_mode(self, mode):
        """Switch prompts to classic for %doctest_mode"""
        if mode:
            self._prompts_before = self.prompts
            self.prompts = ClassicPrompts(self)
        elif self._prompts_before:
            self.prompts = self._prompts_before
            self._prompts_before = None
#        self._update_layout()


InteractiveShellABC.register(TerminalInteractiveShell)

if __name__ == '__main__':
    TerminalInteractiveShell.instance().interact()
