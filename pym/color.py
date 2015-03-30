# -*- coding: utf-8 -*-
# Copyright © 2015 Casey Dahlin, John H. Dulaney
#
# This file is part of PyM.
#
# PyM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# PyM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# PyM.  If not, see <http://www.gnu.org/licenses/>.

import re

COLOR_MAP = {}

COLOR_FMT = re.compile(r'^#([a-fA-F0-9]{3}|[xX])(\|([a-fA-F0-9]{3}|[xX]))?$')

def resolve_text_color(text_color):
    """
    Canonicalize a text color string, or resolve a color name into a text color
    string if appropriate.
    
    Text color strings are of the form '#hhh' or '#hhh|hhh' where 'h' is a hex
    digit. You get one hex digit per red/green/blue value. In the second form,
    the second cluster of hex digits refers to the background color for the text.

    To specify text should use the default color, you may replace either
    cluster of hex digits with 'x'.
    """
    if text_color[0] != '#':
        if text_color in COLOR_MAP:
            return COLOR_MAP[text_color]
    elif COLOR_FMT.match(text_color):
        text_color = text_color.lower()
        if not '|' in text_color:
            text_color += '|x'
        return text_color

    return '#x|x'

def color_alias(name, color):
    """
    Create a color alias.
    """

    color = resolve_text_color(color)

    if color == '#x|x':
        if name in COLOR_MAP:
            del COLOR_MAP[name]
        return

    if name[0] == '#':
        return

    COLOR_MAP[name] = color

COLOR_MAP['keyword'] = '#b0b'
COLOR_MAP['hilight'] = '#000|ff0'
