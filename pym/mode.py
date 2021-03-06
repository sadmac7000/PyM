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

# pylint: disable=redefined-outer-name,too-few-public-methods

"""
Mode handling for PyM
"""

from pym import pym
from .key_parse import parse_key_expr
import re
import os

class StatusLineBuf(object):
    """
    A buffer for the contents of the status line, when the status line is
    showing primary content (i.e. in command-line mode)
    """
    def __init__(self):
        self.buf = ""
        self.pos = 0

class Mode(object):
    """
    The PyM mode determines everything about how the editor reacts to input
    from the user. The abstract mode can be defined to do almost anything, but
    ESC always exits the mode (restoring the mode specified by the abort mode)
    """
    def __init__(self, abort_mode, label="",
                 focus="buffer", insert=False):
        self.label = label
        self.key_exprs = []
        self.abort_mode = abort_mode
        self.focus = focus
        self.insert = insert

    def abort(self):
        """
        Exit this mode, return to its abort mode
        """
        self.reset()
        pym.mode = self.abort_mode

    def reset(self):
        """
        Reset parsing on all key expressions
        """
        for expr, _ in self.key_exprs:
            expr.reset()

        return False

    def handle_key(self, key):
        """
        Handle a keypress for this mode
        """
        if key == 'esc' and not self.reset():
            self.abort()

        try_again = False

        for expr, func in self.key_exprs:
            if not expr.ready:
                continue

            ret = expr.offer(key)
            try_again = expr.ready or try_again

            if not ret:
                continue

            if expr.complete:
                func(expr.get_parse())
                try_again = False
                break

        if not try_again:
            for expr, func in self.key_exprs:
                expr.reset()

    def handle(self, expr):
        """
        Set up a handler for a key sequence
        """
        expr = parse_key_expr(expr)
        def decor(func):
            """
            Decorator to capture the function that will handle this expression
            """
            self.key_exprs.append((expr, func))
            return func
        return decor

pym.mode = normal = Mode(None)
normal.abort_mode = normal
insert = Mode(normal, "-- INSERT --", insert=True)
excmd = Mode(normal, '', 'sline')
search = Mode(normal, '', 'sline')
backsearch = Mode(normal, '', 'sline')

@insert.handle("@|<backspace>|<delete>|<enter>|<left>|<right>|<up>|<down>")
def insert_mode_keys(key):
    """
    Handles keys in insert mode. For most renderable ASCII keys, this just
    inserts them in the buffer.
    """

    buf = pym.buf

    if key == 'backspace':
        buf.left_motion().delete()
    elif key == 'delete':
        buf.delete()
    elif key == 'enter':
        buf.insert('\n').execute()
    elif key == 'left':
        buf.left_motion().execute()
    elif key == 'right':
        buf.right_motion().execute()
    elif key == 'up':
        buf.up_motion().execute()
    elif key == 'down':
        buf.down_motion().execute()
    else:
        buf.insert(key).execute()

excmd_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*)')

@excmd.handle('<tab>')
def excmd_tab_complete(_):
    """
    Tab completion for command mode
    """
    sline = pym.sline
    data = sline.buf[1:sline.pos].lstrip()

    if len(data) == 0:
        return

    match = re.match(excmd_pattern, data)

    if match == None:
        return

    cmd, args = match.groups()

    if len(args) > 0:
        if cmd not in excmds:
            return
        new_args = excmds[cmd].tab_complete(args)

        if len(new_args) == 0:
            return

        new_args = os.path.commonprefix(new_args)[len(args):]
        sline.buf = sline.buf[:sline.pos] + new_args + sline.buf[sline.pos:]
        sline.pos += len(new_args)

@excmd.handle('<enter>')
def excmd_parse_exec(_):
    """
    Parse and execute an ex command in command mode
    """

    sline = pym.sline
    data = sline.buf[1:].strip()

    if len(data) == 0:
        sline.buf = ""
        pym.mode.abort()
        return

    match = re.match(excmd_pattern, data)

    if match != None:
        cmd, args = match.groups()
        if len(args) == 0:
            args = None
        if not do_excmd(cmd, args):
            pym.notify("Not an editor command: " + cmd, error=True)
    else:
        pym.notify("Malformed command: " + data, error=True)
    sline.buf = ""
    pym.mode.abort()
    return

@search.handle('<enter>')
def forward_search(_):
    """
    Handle a forward search request
    """
    pym.buf.search(pym.sline.buf[1:], False)
    pym.buf.mark()
    pym.buf.next_search().execute()
    pym.mode.abort()

@backsearch.handle('<enter>')
def backward_search(_):
    """
    Handle a backward search request
    """
    pym.buf.search(pym.sline.buf[1:], True)
    pym.buf.mark()
    pym.buf.next_search().execute()
    pym.mode.abort()

@excmd.handle('@|<delete>|<backspace>|<left>|<right>')
@search.handle('@|<delete>|<backspace>|<left>|<right>')
@backsearch.handle('@|<delete>|<backspace>|<left>|<right>')
def status_line_entry(key):
    """
    Command mode key handler. Mostly this just passes keys through to the
    status line buffer.
    """
    sline = pym.sline

    if key == 'backspace':
        sline.pos -= 1
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]

        if sline.pos == 0:
            sline.buf = ""
            pym.mode.abort()
    elif key == 'delete':
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]
    elif key == 'left':
        sline.pos -= 1
        if sline.pos < 1:
            sline.pos = 1
    elif key == 'right':
        sline.pos += 1
        if sline.pos > len(sline.buf):
            sline.pos = len(sline.buf)
    else:
        sline.buf = sline.buf[:sline.pos] + key + sline.buf[sline.pos:]
        sline.pos += 1

excmds = {}

class ExCommand(object):
    """
    An Ex Command
    """

    def __init__(self, name, run, tab_complete):
        self.tab_complete = tab_complete
        self.run = run
        self.name = name

        if name in excmds and excmds[name].name == name:
            excmds[name] = self
            return

        preflen = 1

        for k in excmds.keys():
            if name.startswith(k):
                del excmds[k]
                if len(k) >= preflen:
                    preflen = len(k) + 1

        while preflen <= len(name):
            excmds[name[:preflen]] = self
            preflen += 1

    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)

def null_tab_complete(_):
    """
    Tab completion method which offers no completions
    """
    return []

def excommand(name, tab_complete=null_tab_complete):
    """
    Decorator to create an Ex command
    """
    def func(target):
        """
        Function to actually perform decoration
        """
        ExCommand(name, target, tab_complete)
        return target
    return func

def do_excmd(cmd, args):
    """
    Process a command
    """

    if not cmd in excmds:
        return False

    excmds[cmd](args)
    return True
