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

class UrwidUI(UI):
    """
    The Urwid UI class
    """

    def quit(self):
        raise urwid.ExitMainLoop()

    def notify(self, message, error=False):
        global status_msg
        global status_err
        status_msg = message
        status_err = error

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
    loop.draw_screen()

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

    attrs = []
    line = pym.buf.lines[num][:truncate]
    regions = pym.buf.regions_for_line(num)
    end = 0
    start = len(line)

    for reg in regions:
        if reg.start[0] < num:
            start = 0
        elif reg.start[1] < start:
            start = reg.start[1]

        if reg.end[0] > num:
            end = len(line)
        elif reg.end[1] > end:
            end = reg.end[1]

    real_end = end
    real_start = start
    encoded_line = "".encode()

    for pos, char in enumerate(line):
        encoded_char = char.encode()

        if pos < start:
            real_start += len(encoded_char) - 1
        if pos < end:
            real_end += len(encoded_char) - 1
        encoded_line += encoded_char

    if end > start:
        if real_start > 0:
            attrs.append((None, real_start))
        attrs.append(('hilight', real_end - real_start))

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
           ('hilight', 'black', 'yellow', '', 'black', 'h11'),
           ('modelabel', 'white,bold', ''),
           ('errlabel', 'white,bold', 'dark red'),
           ('nonline', 'dark blue', '')]

def do_input(key):
    "Input line handling"
    pym.mode.handle_key(key)
    bdisp._invalidate()
    sline._invalidate()
    tabset._invalidate()

loop = urwid.MainLoop(layout, palette, unhandled_input=do_input)

def run():
    """
    Main looop for the Urwid UI
    """
    loop.screen.set_terminal_properties(colors=256)
    loop.run()
