# -*- coding: utf-8 -*-
# Copyright © 2014, 2015 Casey Dahlin, John H. Dulaney
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

# pylint: disable=protected-access

"""
A UI for PyM using Urwid
"""

import urwid
import importlib
import signal

from pym import pym_init
from pym.ui import UI
from pym.color import resolve_text_color

class UrwidUI(UI):
    """
    The Urwid UI class
    """
    def __init__(self):
        UI.__init__(self)
        self.loop = None
        self.bdisp = None

    def quit(self):
        raise urwid.ExitMainLoop()

    def notify(self, message, error=False):
        global status_msg
        global status_err
        status_msg = message
        status_err = error

    def redraw(self):
        self.bdisp._invalidate()
        self.loop.draw_screen()

    @property
    def buf(self):
        return buf

    @property
    def sline(self):
        return sline.buf

pym_init(UrwidUI())

from pym import pym

from .buf import Buffer

buf = Buffer()

from .mode import StatusLineBuf, normal

importlib.import_module(".commands", "pym")
importlib.import_module(".normal_mode", "pym")

def sigint(*_):
    """
    Handler for SIGINT. Passes Ctrl-c to the editor
    """
    do_input("ctrl c")
    pym.loop.draw_screen()

signal.signal(signal.SIGINT, sigint)

status_msg = None
status_err = False

urwid.set_encoding("UTF-8")

scrolloff = 5

class BufferDisplay(urwid.Widget):
    "Urwid widget for displaying a buffer's contents"
    _sizing = frozenset('box')

    def __init__(self, buff):
        urwid.Widget.__init__(self)
        self.buf = buff
        self.scroll = 0
        self.scroll_pos = "All"

    def get_cursor_coords(self, size):
        """
        Get the coordinates of the cursor
        """
        col = self.buf.col
        row = self.buf.row - self.scroll

        global status_msg
        old_scroll = self.scroll

        if row > size[1] - scrolloff:
            self.scroll += row - size[1] + scrolloff

        if self.scroll + size[1] > len(self.buf.lines):
            self.scroll = len(self.buf.lines) - size[1]

        if row < scrolloff:
            self.scroll -= scrolloff - row

        if self.scroll < 0:
            self.scroll = 0

        if self.scroll != old_scroll:
            self._invalidate()
            status_msg = None

        row = self.buf.row - self.scroll

        if size[1] >= len(self.buf.lines):
            self.scroll_pos = "All"
        else:
            max_scroll = len(self.buf.lines) - size[1]
            percent = self.scroll * 100 / max_scroll
            if percent == 0:
                self.scroll_pos = "Top"
            elif percent == 100:
                self.scroll_pos = "Bot"
            else:
                self.scroll_pos = "{}%".format(int(percent))

        # We do this late so the scroll calculations still happen
        if pym.mode.focus != "buffer":
            return None
        return (col, row)

    def render(self, size, **_):
        """
        Render this widget
        """
        encoded = [line_attrs(x + self.scroll, size[0]) for x in range(size[1])]
        encoded = [x for x in encoded if x != None]
        lines = [x[0] for x in encoded]
        attrs = [x[1] for x in encoded]
        if len(lines) < size[1]:
            attrs += [[('nonline', 1)]] * (size[1]-len(lines))
            lines += [b"~"] * (size[1]-len(lines))
        return urwid.TextCanvas(lines, attrs,
                                cursor=self.get_cursor_coords(size),
                                maxcol=size[0])

def line_attrs(num, truncate):
    """
    Given a line number, truncate it to fit the screen, encode it, and return
    the tuple of its encoded text and its attrs
    """

    if num >= len(pym.buf.lines):
        return None

    line = pym.buf.lines[num][:truncate]
    regions = pym.buf.regions_for_line(num)

    attr_endpoints = []
    for reg in regions:
        if reg.start[0] < num:
            start = 0
        else:
            start = reg.start[1]

        if reg.end[0] > num:
            end = len(line)
        else:
            end = reg.end[1]

        attr_endpoints.append([start, end, start, end, reg.tag])

    offset = 0
    encoded_line = "".encode()
    attr_ep_pos = 0
    for pos, char in enumerate(line):
        encoded_char = char.encode()
        encoded_line += encoded_char
        offset += len(encoded_char) - 1

        if attr_ep_pos >= len(attr_endpoints):
            continue

        for ep in attr_endpoints:
            if ep[0] > pos:
                ep[2] = ep[0] + offset
            if ep[1] > pos:
                ep[3] = ep[1] + offset

    for ep in attr_endpoints:
        ep.pop(0)
        ep.pop(0)

    pos = 0

    attrs = []
    for ep in attr_endpoints:
        if ep[0] > pos:
            attrs.append((None, ep[0] - pos))
        pos = ep[1]
        if ep[1] != ep[0]:
            attr_name = urwid_text_color(ep[2])
            attrs.append((attr_name, ep[1] - ep[0]))

    return (encoded_line, attrs)

class Tabset(urwid.Widget):
    "Urwid widget for the tab bar at the top of the screen"
    _sizing = frozenset('flow')

    def rows(self, dummy1, dummy2):
        """
        Number of rows taken up by the tabset
        """
        return 1

    def render(self, size, **_):
        """
        Render the tabset
        """
        contents = (" " + buf.headline() + " ").encode()
        sz = len(contents)
        return urwid.TextCanvas([contents],
                                [[('tab', sz), ('tabspace', size[0]-sz)]],
                                maxcol=size[0])

class StatusLine(urwid.Widget):
    "Urwid widget for the status line"
    _sizing = frozenset('flow')

    def __init__(self):
        urwid.Widget.__init__(self)
        self.buf = StatusLineBuf()

    def rows(self, dummy1, dummy2):
        """
        Number of rows used by the status line
        """
        return 1

    def get_cursor_coords(self, _):
        """
        Coordinates of the cursor
        """
        if pym.mode.focus == 'sline':
            return (self.buf.pos, 0)
        return None

    def render(self, size, **_):
        """
        Render the status line
        """
        global status_msg

        if pym.mode.focus == 'sline':
            content = self.buf.buf
            content += " " * (size[0] - len(content))
            content = content[:size[0]].encode()
            return urwid.TextCanvas([content], [[]], maxcol=size[0],
                                    cursor=self.get_cursor_coords(size))
        content = " " * size[0]
        if pym.mode != normal:
            status_msg = None
        if status_msg != None:
            label = status_msg
        else:
            label = pym.mode.label
        content = label + content[len(label):]
        content = content[:-4] + bdisp.scroll_pos + " "
        content = content.encode()
        if len(label):
            if status_msg == None:
                attr = [[('modelabel', len(label))]]
            elif status_err:
                attr = [[('errlabel', len(label))]]
            else:
                attr = [[]]
        else:
            attr = [[]]
        canv = urwid.TextCanvas([content], attr, maxcol=size[0])
        return canv

bdisp = BufferDisplay(buf)
sline = StatusLine()
tabset = Tabset()

layout = urwid.Pile([(1, tabset), bdisp, (1, sline)])

palette = [('tab', 'black,underline', 'light gray'),
           ('tabspace', 'black', 'light gray', '', 'h8', 'g74'),
           ('modelabel', 'white,bold', ''),
           ('errlabel', 'white,bold', 'dark red'),
           ('nonline', 'dark blue', '')]

def urwid_text_color(pym_color):
    "Get an urwid palette entry for a PyM color"
    return pym_color
    pym_color = resolve_text_color(pym_color)

def do_input(key):
    "Input line handling"
    pym.mode.handle_key(key)
    bdisp._invalidate()
    sline._invalidate()
    tabset._invalidate()

pym.loop = urwid.MainLoop(layout, palette, unhandled_input=do_input)
pym.bdisp = bdisp

C16_MAP = {
        (0x0,0x0,0x0): "black",
        (0xb,0x0,0x0): "dark red",
        (0x0,0xb,0x0): "dark green",
        (0xb,0xb,0x0): "brown",
        (0x0,0x0,0xb): "dark blue",
        (0xb,0x0,0xb): "dark magenta",
        (0x0,0xb,0xb): "dark cyan",
        (0xd,0xd,0xd): "light gray",
        (0xb,0xb,0xb): "dark gray",
        (0xf,0x0,0x0): "light red",
        (0x0,0xf,0x0): "light green",
        (0xf,0xf,0x0): "yellow",
        (0x0,0x0,0xf): "light blue",
        (0xf,0x0,0xf): "light magenta",
        (0x0,0xf,0xf): "light cyan",
        (0xf,0xf,0xf): "white",
        }

C16B_MAP = {
        (0x0,0x0,0x0): "black",
        (0xb,0x0,0x0): "dark red",
        (0x0,0xb,0x0): "dark green",
        (0xb,0xb,0x0): "brown",
        (0x0,0x0,0xb): "dark blue",
        (0xb,0x0,0xb): "dark magenta",
        (0x0,0xb,0xb): "dark cyan",
        (0xd,0xd,0xd): "light gray",
        }

def nearest_88(color):
    "Convert a color value to 88-color"

    nearest = 0x0

    for i in [0x8, 0xc, 0xf]:
        if abs(color - i) < abs(color - nearest):
            nearest = i

    return nearest

def nearest_256(color):
    "Convert a color value to 256-color"

    nearest = 0x0

    for i in [0x6, 0x8, 0xa, 0xd, 0xf]:
        if abs(color - i) < abs(color - nearest):
            nearest = i

    return nearest

def nearest_list(r, g, b, items):
    "Nearest RGB value in a list"

    distance = None
    rvalue = None

    for colors in items:
        r_b, g_b, b_b = colors
        value = items[colors]

        r_b -= r
        g_b -= g
        b_b -= b

        r_b = r_b ** 2
        g_b = g_b ** 2
        b_b = b_b ** 2

        new_distance = r_b + g_b + b_b

        if distance == None or new_distance < distance:
            distance = new_distance
            rvalue = value

    return rvalue

def hex_color(r, g, b):
    r = hex(r)[2:]
    g = hex(g)[2:]
    b = hex(b)[2:]

    return '#' + r + g + b

NEW_ENTRIES = 0

def urwid_text_color(pym_color):
    "Get an urwid palette entry for a PyM color"

    global NEW_ENTRIES
    foreground = 'default'
    background = 'default'
    foreground_88 = 'default'
    background_88 = 'default'
    foreground_256 = 'default'
    background_256 = 'default'

    pym_color = resolve_text_color(pym_color)

    if pym_color == "#x|x":
        return None

    pym_color = pym_color[1:]

    fg_start = None
    bg_start = None

    if pym_color[0] != 'x':
        r = int(pym_color[0], 16)
        g = int(pym_color[1], 16)
        b = int(pym_color[2], 16)

        fg_start = (r, g, b)
        pym_color = pym_color[4:]
    else:
        pym_color = pym_color[2:]

    if len(pym_color) and pym_color[0] != 'x':
        r = int(pym_color[0], 16)
        g = int(pym_color[1], 16)
        b = int(pym_color[2], 16)

        bg_start = (r, g, b)

    if fg_start != None:
        r, g, b = fg_start
        r88 = nearest_88(r)
        g88 = nearest_88(g)
        b88 = nearest_88(b)
        r256 = nearest_256(r)
        g256 = nearest_256(g)
        b256 = nearest_256(b)

        foreground_88 = hex_color(r88,g88,b88)
        foreground_256 = hex_color(r256,g256,b256)
        foreground = nearest_list(r, g, b, C16_MAP)

    if bg_start != None:
        r, g, b = bg_start
        r88 = nearest_88(r)
        g88 = nearest_88(g)
        b88 = nearest_88(b)
        r256 = nearest_256(r)
        g256 = nearest_256(g)
        b256 = nearest_256(b)

        background_88 = hex_color(r88,g88,b88)
        background_256 = hex_color(r256,g256,b256)
        background = nearest_list(r, g, b, C16B_MAP)

    entry_name = 'p' + str(NEW_ENTRIES)
    NEW_ENTRIES += 1

    pym.loop.screen.register_palette_entry(entry_name, foreground, background,
            None, foreground_256, background_256)
    return entry_name

def run():
    """
    Main looop for the Urwid UI
    """
    pym.loop.screen.set_terminal_properties(colors=256)
    pym.loop.run()
