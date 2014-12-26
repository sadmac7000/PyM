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
import re

_mode = None

class StatusLineBuf:
    """
    A buffer for the contents of the status line, when the status line is
    showing primary content (i.e. in command-line mode)
    """
    def __init__(self):
        self.buf = ""
        self.pos = 0

def mode():
    """
    Get the current PyM mode
    """
    return _mode

class Mode():
    """
    The PyM mode determines everything about how the editor reacts to input
    from the user. The abstract mode can be defined to do almost anything, but
    ESC always exits the mode (restoring the mode specified by the abort mode)
    """
    def __init__(self, abort_mode, label = "",
            focus="buffer", insert=False, tokenize_ints=False):
        self.label = label
        self.key_handlers = []
        self.abort_mode = abort_mode
        self.focus=focus
        self.insert = insert
        self.key_tokens = []
        self.tokenize_ints = tokenize_ints

    def abort(self, buf):
        """
        Exit this mode, return to its abort mode
        """
        global _mode
        self.reset()
        _mode = self.abort_mode
        buf.mode_changed()

    def reset(self):
        """
        Reset the key token buffer
        """

        if len(self.key_tokens):
            self.key_tokens = []
            return True
        return False

    def handle_key(self, key, buf, sline):
        """
        Handle a keypress for this mode
        """
        global _mode
        if key == 'esc':
            if not self.reset():
                self.abort(buf)
        elif self.tokenize_ints and re.match(r'[1-9]', key):
            if len(self.key_tokens) > 0 and type(self.key_tokens[-1]) == int:
                self.key_tokens[-1] *= 10
                self.key_tokens[-1] += int(key)
            else:
                self.key_tokens += [int(key)]
        elif self.tokenize_ints and key == '0' and \
                type(self.key_tokens[-1]) == int:
            self.key_tokens[-1] *= 10
        else:
            self.key_tokens += [key]
            cont = False
            for handler in self.key_handlers:
                got = handler(self, buf, sline)
                if got == "done":
                    self.reset()
                    return
                elif got == "continue":
                    cont = True
            if not cont:
                self.reset()

    def register_handler(self, handler):
        """
        Register a new key handler with this mode
        """
        self.key_handlers += [handler]
        return handler

_mode = normal = Mode(None, tokenize_ints=True)
normal.abort_mode = normal

def normal_key_params(mode):
    """
    Break down the key token buffer into an integer argument and a series of
    keys.
    """
    if isinstance(mode.key_tokens[0], int):
        arg = mode.key_tokens[0]
        keys = mode.key_tokens[1:]
    else:
        arg = None
        keys = mode.key_tokens
    return arg, keys

@normal.register_handler
def normal_delete_key(mode, buf, sline):
    """
    Key press handler for `d` in normal mode
    """
    arg, keys = normal_key_params(mode)

    if keys[0] != 'd':
        return

    if len(keys) < 2:
        return "continue"

    if arg and not isinstance(keys[1], int):
        prepend = [arg]
        count = arg - 1
    else:
        prepend = []
        count = 0
    motion = motion_key(prepend + keys[1:], buf)
    if keys[1] == 'd':
        motion = buf.down_motion(count)
    if motion != None:
        motion.delete()
    return "done"

@normal.register_handler
def normal_begin_insert(mode, buf, sline):
    """
    Key press handler for `i` in normal mode
    """
    global _mode

    arg, keys = normal_key_params(mode)

    if keys == ['i']:
        _mode=insert
        buf.mode_changed()
        return "done"

@normal.register_handler
def normal_mode_motion(mode, buf, sline):
    """
    Key press handler for motions in normal mode
    """
    motion = motion_key(mode.key_tokens, buf)

    if motion != None:
        motion.execute()
        return "done"

@normal.register_handler
def normal_delchar_key(mode, buf, sline):
    """
    Key press handler for `x` in normal mode
    """
    arg, keys = normal_key_params(mode)

    if keys == ['x']:
        print("hi")
        if arg:
            count = arg
        else:
            count = 1
        buf.right_motion(count).delete()
        return "done"

@normal.register_handler
def normal_mode_insert_after(mode, buf, sline):
    """
    Key press handler for `a` in normal mode
    """
    global _mode
    arg, keys = normal_key_params(mode)

    if keys == ['a']:
        _mode=insert
        buf.mode_changed()
        buf.right_motion().execute()
        return "done"

@normal.register_handler
def normal_mode_insert_at_end(mode, buf, sline):
    """
    Key press handler for `A` in normal mode
    """
    global _mode
    arg, keys = normal_key_params(mode)

    if keys == ['A']:
        _mode=insert
        buf.mode_changed()
        buf.move_to(buf.row, len(buf.lines[buf.row]))
        return "done"

@normal.register_handler
def normal_mode_mark(mode, buf, sline):
    """
    Key press handler for `m` in normal mode
    """
    arg, keys = normal_key_params(mode)

    if keys[0] == 'm':
        if len(keys) < 2:
            return "continue"
        key = keys[1]
        if not key in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'`0123456789":
            return "done"

        if key == '`':
            key = "'"

        buf.mark(key)

        return "done"

@normal.register_handler
def normal_mode_goto(mode, buf, sline):
    """
    Key press handler for '`' in normal mode
    """
    global _mode
    arg, keys = normal_key_params(mode)

    if (keys[0] == "``" or keys[0] == "'"):
        if len(keys) < 2:
            return "continue"
        buf.restore_mark(mode.key_tokens[1])

@normal.register_handler
def normal_mode_cmdmode(mode, buf, sline):
    """
    Key press handler for `:` in normal mode
    """
    global _mode
    arg, keys = normal_key_params(mode)

    if keys[0] == ':':
        sline.buf = ':'
        sline.pos = 1
        _mode=excmd
        buf.mode_changed()
        return "done"

    return

def motion_key(keys, buf):
    """
    Generic key press receiver for motion keys
    """

    if len(keys) > 2:
        return

    if isinstance(keys[0], int):
        if len(keys) < 2:
            return
        key = keys[1]
        amt = keys[0]
    else:
        key = keys[0]
        amt = 1

    if ((key == 'h') and _mode == normal) or (key == 'left'):
        return buf.left_motion(amt)

    if ((key == 'l') and _mode == normal) or (key == 'right'):
        return buf.right_motion(amt)

    if ((key == 'k') and _mode == normal) or (key == 'up'):
        return buf.up_motion(amt)

    if ((key == 'j') and _mode == normal) or (key == 'down') \
         or ((key == 'enter') and _mode == normal):
        return buf.down_motion(amt)

insert = Mode(normal, "-- INSERT --", insert=True)

@insert.register_handler
def insert_mode_keys(mode, buf, sline):
    """
    Handles keys in insert mode. For most renderable ASCII keys, this just
    inserts them in the buffer.
    """
    key = mode.key_tokens[0]

    if key == 'backspace':
        buf.left_motion().delete()
        return "done"

    if key == 'delete':
        buf.delete()
        return "done"

    if key == 'enter':
        buf.insert('\n').execute()
        return "done"

    motion = motion_key(key, buf)
    if motion != None:
        motion.execute()
        return "done"

    if len(key) > 1:
        return "done"

    buf.insert(key)
    buf.right_motion().execute()
    return "done"

excmd = Mode(normal, '', 'sline')

@excmd.register_handler
def excmd_mode_keys(mode, buf, sline):
    """
    Command mode key handler. Mostly this just passes keys through to the
    status line buffer.
    """
    key = mode.key_tokens[0]

    if key == 'backspace':
        sline.pos -= 1
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]

        if sline.pos == 0:
            sline.buf = ""
            _mode.abort(buf)
        return "done"

    if key == 'delete':
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]
        return "done"

    if key == 'enter':
        if ":quit".startswith(sline.buf):
            raise urwid.ExitMainLoop()
        sline.buf = ""
        _mode.abort(buf)
        return "done"

    if len(key) > 1:
        return "done"

    sline.buf = sline.buf[:sline.pos] + key + sline.buf[sline.pos:]
    sline.pos += 1
    return "done"
