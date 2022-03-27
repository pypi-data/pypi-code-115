"""This module is for the translation mapping data of the
following document:

Document file: timer_reset.md
Language: jp
"""

from typing import Dict

MAPPING: Dict[str, str] = {

    '# Timer class reset interface':
    '',

    'This page explains the `Timer` class `reset` method interface.':
    '',

    '## What interface is this?':
    '',

    'The `reset` method interface resets a timer count and stops it.':
    '',

    '## Basic usage':
    '',

    'The `reset` method has no arguments.\n\nThe following example rotates the rectangle 90 degrees (`repeat_count=90`) by the first-timer and then reset and start the second one. The second-timer resets and restart the first-timer after 1 second.':  # noqa
    '',

    '```py\n# runnable\nfrom typing_extensions import TypedDict\n\nimport apysc as ap\n\nap.Stage(\n    stage_width=150, stage_height=150, background_color=\'#333\',\n    stage_elem_id=\'stage\')\nsprite: ap.Sprite = ap.Sprite()\nsprite.graphics.begin_fill(color=\'#0af\')\nrectangle: ap.Rectangle = sprite.graphics.draw_rect(\n    x=50, y=50, width=50, height=50)\n\n\nclass _RectOptions(TypedDict):\n    rectangle: ap.Rectangle\n\n\nclass _TimerOptions(TypedDict):\n    timer: ap.Timer\n\n\ndef on_first_timer(e: ap.TimerEvent, options: _RectOptions) -> None:\n    """\n    The handler that the first-timer calls.\n\n    Parameters\n    ----------\n    e : ap.TimerEvent\n        Event instance.\n    options : dict\n        Optional arguments dictionary.\n    """\n    rectangle: ap.Rectangle = options[\'rectangle\']\n    rectangle.rotation_around_center += 1\n\n\ndef on_first_timer_complete(\n        e: ap.TimerEvent, options: _TimerOptions) -> None:\n    """\n    The handler that the first-timer calls when completed.\n\n    Parameters\n    ----------\n    e : ap.TimerEvent\n        Event instance.\n    options : dict\n        Optional arguments dictionary.\n    """\n    timer_2: ap.Timer = options[\'timer\']\n    timer_2.reset()\n    timer_2.start()\n\n\ndef on_second_timer(e: ap.TimerEvent, options: _TimerOptions) -> None:\n    """\n    The handler that the second timer calls.\n\n    Parameters\n    ----------\n    e : ap.TimerEvent\n        Event instance.\n    options : dict\n        Optional arguments dictionary.\n    """\n    timer_1: ap.Timer = options[\'timer\']\n    timer_1.reset()\n    timer_1.start()\n\n\noptions_1: _RectOptions = {\'rectangle\': rectangle}\ntimer_1: ap.Timer = ap.Timer(\n    handler=on_first_timer, delay=ap.FPS.FPS_60, repeat_count=90,\n    options=options_1)\n\noptions_2: _TimerOptions = {\'timer\': timer_1}\ntimer_2: ap.Timer = ap.Timer(\n    handler=on_second_timer, delay=1000, repeat_count=1,\n    options=options_2)\noptions_2 = {\'timer\': timer_2}\ntimer_1.timer_complete(\n    on_first_timer_complete, options=options_2)\ntimer_1.start()\n\nap.save_overall_html(\n    dest_dir_path=\'timer_reset_basic_usage/\')\n```':  # noqa
    '',

    '<iframe src="static/timer_reset_basic_usage/index.html" width="150" height="150"></iframe>':  # noqa
    '',

    '## reset API':
    '',

    '<!-- Docstring: apysc._time.timer.Timer.reset -->\n\n<span class="inconspicuous-txt">Note: the document build script generates and updates this API document section automatically. Maybe this section is duplicated compared with previous sections.</span>\n\n**[Interface signature]** `reset(self) -> None`<hr>\n\n**[Interface summary]** Reset the timer count and stop this timer.<hr>\n\n**[Examples]**':  # noqa
    '',

    '```py\n>>> from typing_extensions import TypedDict\n>>> import apysc as ap\n>>> class RectOptions(TypedDict):\n...     rectangle: ap.Rectangle\n>>> def on_timer(e: ap.TimerEvent, options: RectOptions) -> None:\n...     rectangle: ap.Rectangle = options[\'rectangle\']\n...     rectangle.x += 1\n...     with ap.If(rectangle.x > 100):\n...         timer: ap.Timer = e.this\n...         timer.reset()\n>>> stage: ap.Stage = ap.Stage()\n>>> sprite: ap.Sprite = ap.Sprite()\n>>> sprite.graphics.begin_fill(color=\'#0af\')\n>>> rectangle: ap.Rectangle = sprite.graphics.draw_rect(\n...     x=50, y=50, width=50, height=50)\n>>> options: RectOptions = {\'rectangle\': rectangle}\n>>> _ = ap.Timer(\n...     on_timer, delay=33.3, options=options).start()\n```':  # noqa
    '',

}
