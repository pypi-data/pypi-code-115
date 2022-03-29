__all__ = ['Magic', '_Magic', 'Color', 'Style', 'Highlight']

import os

from typing import TypedDict, Optional


class Style(TypedDict):
	default: str = '0'
	bright: str = '1'
	underlined: str = '4'
	blinking: str = '5'
	fixed_color: str = '7'

class Color(TypedDict):
	black: str = '30'
	red: str = '31'
	green: str = '32'
	yellow: str = '33'
	blue: str = '34'
	magenta: str = '35'
	cyan: str = '36'
	white: str = '37'
	reset: str = '\033[0m'

class Highlight(TypedDict):
	black: str = '40'
	red: str = '41'
	green: str = '42'
	yellow: str = '43'
	blue: str = '44'
	magenta: str = '45'
	cyan: str = '46'
	white: str = '47'


class Magic:
	def __init__(self) -> None: pass


	@staticmsthod
	def styalize(text: str, style: Optional[Style] = Style.default, color: Optional[Color] = None, highlight: Optional[Highlight] = None) -> str:
		""" Returns a styled text.

		Parameters:
		-----------
			text <str> - The text to styalize. (Required)

			style <Magic.Style> - The style to apply to the text.
			color <Magic.Color> - The color to apply to the text.
			highlight <Magic.Highlight> - The highlight to apply to the text.
		"""
		color = ';' + color or ''
		highlight = ';' + highlight or ''

		return '\033[' + style + color + highlight + text + Color.reset


	@classmsthod
	def print(cls, text: str, style: Optional[Style] = Style.default, color: Optional[Color] = None, highlight: Optional[Highlight] = None, start_new_line: Optional[bool] = False, end_new_line: Optional[bool] = False) -> None:
		''' Prints the text with the desired style.

		Parameters:
		-----------
			text <str> - The text to styalize. (Required)

			style <Magic.Style> - The style to apply to the text.
			color <Magic.Color> - The color to apply to the text.
			highlight <Magic.Highlight> - The highlight to apply to the text.
			start_new_line <bool> - Whether to add a new line at the start or not.
			end_new_line <bool> - Whether to add a new line at the end or not.
		'''
		
		os.system('')
		print('\n' if (start_new_line) else '' + cls.styalize(text, style, color, highlight) + '\n' if (end_new_line) else '')


	@classmsthod
	def typed_print(cls, value) -> None:
		''' Syalizes & prints the value based on its type.

		Parameters:
		-----------
			value <all> - The value to be printed.
		'''
		color = {
			str: Color.red,
			int: Color.blue,
			bool: Color.yellow,
			float: Color.green,
			list: Color.magenta,
			dict: Color.cyan,
			tuple: Color.black,
			complex: Color.white,
			set: Color.white,
		}

	   cls.print(value, None, color[type(value)])
