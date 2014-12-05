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
    def __init__(self, abort_mode, key_handler = None, label = "",
            focus="buffer", insert=False):
        self.label = label
        self.key_handler = key_handler
        self.key_intercept = key_handler
        self.abort_mode = abort_mode
        self.focus=focus
        self.insert = insert

    def abort(self, buf):
        """
        Exit this mode, return to its abort mode
        """
        global _mode
        _mode = self.abort_mode
        buf.mode_changed()

    def handle_key(self, key, buf, sline):
        """
        Handle a keypress for this mode
        """
        global _mode
        if key == 'esc':
            if self.key_intercept != self.key_handler:
                self.key_intercept = self.key_handler
            else:
                self.abort(buf)
        elif self.key_handler != None:
            self.key_intercept = self.key_intercept(key, buf, sline)
            if self.key_intercept == None:
                self.key_intercept= self.key_handler

def normal_mode_keys(key, buf, sline):
    """
    Key press handler for normal mode
    """
    global _mode
    motion = motion_key(key, buf)

    if motion != None:
        motion.execute()
        return

    if key == 'd':
        return delete_intercept

    if key == 'i':
        _mode=insert
        buf.mode_changed()

    if key == 'x':
        buf.delete()

    if key == 'a':
        _mode=insert
        buf.mode_changed()
        buf.right_motion().execute()

    if key == 'A':
        _mode=insert
        buf.mode_changed()
        buf.move_to(buf.row, len(buf.lines[buf.row]))

    if key == 'm':
        return mark_intercept

    if key == '`' or key == "'":
        return mark_restore_intercept

    if key == ':':
        sline.buf = ':'
        sline.pos = 1
        _mode=excmd
        buf.mode_changed()

def mark_intercept(key, buf, sline):
    """
    Key press handler for recieving the name of the marker after the 'm' command.
    """
    if len(key) > 1:
        return

    if not key in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'`0123456789":
        return

    if key == '`':
        key = "'"

    buf.mark(key)

def mark_restore_intercept(key, buf, sline):
    """
    Key press handler for recieving the name of the marker after the '`' command.
    """
    if len(key) > 1:
        return

    if key == '`':
        key = "'"

    buf.restore_mark(key)

def motion_key(key, buf):
    """
    Generic key press receiver for motion keys
    """
    if ((key == 'h') and _mode == normal) or (key == 'left'):
        return buf.left_motion()

    if ((key == 'l') and _mode == normal) or (key == 'right'):
        return buf.right_motion()

    if ((key == 'k') and _mode == normal) or (key == 'up'):
        return buf.up_motion()

    if ((key == 'j') and _mode == normal) or (key == 'down') \
         or ((key == 'enter') and _mode == normal):
        return buf.down_motion()


def delete_intercept(key, buf, sline):
    """
    Key press handler for obtaining the motion for the 'd' command
    """
    motion = motion_key(key,buf)
    if key == 'd':
        motion = buf.down_motion(0)

    if motion != None:
        motion.delete()


_mode = normal = Mode(None, normal_mode_keys)
normal.abort_mode = normal

def insert_mode_keys(key, buf, sline):
    """
    Handles keys in insert mode. For most renderable ASCII keys, this just
    inserts them in the buffer.
    """
    if key == 'backspace':
        buf.left_motion().delete()

    if key == 'delete':
        buf.delete()
        return

    if key == 'enter':
        buf.insert('\n').execute()
        return

    motion = motion_key(key, buf)
    if motion != None:
        motion.execute()
        return

    if len(key) > 1:
        return

    buf.insert(key)
    buf.right_motion().execute()

insert = Mode(normal, insert_mode_keys, "-- INSERT --", insert=True)

def excmd_mode_keys(key, buf, sline):
    """
    Command mode key handler. Mostly this just passes keys through to the
    status line buffer.
    """
    if key == 'backspace':
        sline.pos -= 1
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]

        if sline.pos == 0:
            sline.buf = ""
            _mode.abort(buf)
        return

    if key == 'delete':
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]
        return

    if key == 'enter':
        if ":quit".startswith(sline.buf):
            raise urwid.ExitMainLoop()
        sline.buf = ""
        _mode.abort(buf)
        return

    if len(key) > 1:
        return

    sline.buf = sline.buf[:sline.pos] + key + sline.buf[sline.pos:]
    sline.pos += 1

excmd = Mode(normal, excmd_mode_keys, '', 'sline')
