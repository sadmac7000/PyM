# -*- coding: utf-8 -*-
# Copyright © 2014, 2015 Casey Dahlin, John H. Dulaney
#
# this file is part of PyM.
#
# PyM is free software: you can redistribute it and/or modify it under the
# terms of the gnu general public license as published by the free software
# foundation, either version 3 of the license, or (at your option) any later
# version.
#
# PyM is distributed in the hope that it will be useful, but without any
# warranty; without even the implied warranty of merchantability or fitness for
# a particular purpose.  see the gnu general public license for more details.
#
# you should have received a copy of the gnu general public license along with
# PyM. if not, see <http://www.gnu.org/licenses/>.

import urwid
from .ui_core import ui, UI
from .buf import Buffer
from .mode import mode, StatusLineBuf, normal
from .normal_mode import *

status_msg = None
status_err = False

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

ui(UrwidUI())

urwid.set_encoding("UTF-8")

scrolloff = 5

class BufferDisplay(urwid.Widget):
    "Urwid widget for displaying a buffer's contents"
    _sizing=frozenset('box')

    def __init__(self, buf):
        super(urwid.Widget, self).__init__()
        self.buf = buf
        self.scroll = 0
        self.scroll_pos = "All"

    def get_cursor_coords(self, size):
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
        if mode().focus != "buffer":
            return None
        return (col,row)

    def render(self, size, **kwargs):
        lines = [ x[:size[0]] for x in self.buf.encoded(self.scroll) ][:size[1]]
        attrs = [[]] * len(lines)
        if len(lines) < size[1]:
            attrs += [[('nonline', 1)]] * (size[1]-len(lines))
            lines += [b"~"] * (size[1]-len(lines))
        return urwid.TextCanvas(lines, attrs,
                cursor=self.get_cursor_coords(size), maxcol=size[0])

class Tabset(urwid.Widget):
    "Urwid widget for the tab bar at the top of the screen"
    _sizing=frozenset('flow')

    def rows(self, size, focus):
        return 1

    def render(self, size, **kwargs):
        global buf
        contents = (" " + buf.headline() + " ").encode()
        sz = len(contents)
        return urwid.TextCanvas([contents], [[('tab', sz), ('tabspace',
            size[0]-sz)]], maxcol=size[0])

class StatusLine(urwid.Widget):
    "Urwid widget for the status line"
    _sizing=frozenset('flow')

    def __init__(self):
        super(urwid.Widget, self).__init__()
        self.buf = StatusLineBuf()

    def rows(self, size, focus):
        return 1

    def get_cursor_coords(self,size):
        if mode().focus == 'sline':
            return (self.buf.pos, 0)
        return None

    def render(self, size, **kwargs):
        global status_msg
        global status_err

        if mode().focus == 'sline':
            content = self.buf.buf
            content += " " * (size[0] - len(content))
            content = content[:size[0]].encode()
            return urwid.TextCanvas([content], [[]], maxcol=size[0],
                    cursor=self.get_cursor_coords(size))
        content = " " * size[0]
        if mode() != normal:
            status_msg = None
        if status_msg != None:
            label = status_msg
        else:
            label = mode().label
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

buf=Buffer()
bdisp = BufferDisplay(buf)
sline = StatusLine()
tabset = Tabset()

layout = urwid.Pile([(1,tabset),bdisp,(1,sline)])

palette = [('tab', 'black,underline', 'light gray'),
        ('tabspace', 'black', 'light gray', '', 'h8', 'g74'),
        ('modelabel', 'white,bold', ''),
        ('errlabel', 'white,bold', 'dark red'),
        ('nonline', 'dark blue', '')]

def do_input(key):
    "Input line handling"
    mode().handle_key(key, buf, sline.buf)
    bdisp._invalidate()
    sline._invalidate()

def run():
    """
    Main looop for the Urwid UI
    """
    loop = urwid.MainLoop(layout, palette, unhandled_input=do_input)
    loop.screen.set_terminal_properties(colors=256)
    loop.run()
