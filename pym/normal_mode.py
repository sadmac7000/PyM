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

from .mode import normal, insert, excmd, mode

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
def normal_begin_insert(md, buf, sline):
    """
    Key press handler for `i` in normal mode
    """
    arg, keys = normal_key_params(md)

    if keys == ['i']:
        mode(insert)
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
def normal_mode_insert_after(md, buf, sline):
    """
    Key press handler for `a` in normal mode
    """
    arg, keys = normal_key_params(md)

    if keys == ['a']:
        mode(insert)
        buf.mode_changed()
        buf.right_motion().execute()
        return "done"

@normal.register_handler
def normal_mode_insert_at_end(md, buf, sline):
    """
    Key press handler for `A` in normal mode
    """
    arg, keys = normal_key_params(md)

    if keys == ['A']:
        mode(insert)
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
    arg, keys = normal_key_params(mode)

    if (keys[0] == "``" or keys[0] == "'"):
        if len(keys) < 2:
            return "continue"
        buf.restore_mark(mode.key_tokens[1])

@normal.register_handler
def normal_mode_cmdmode(md, buf, sline):
    """
    Key press handler for `:` in normal mode
    """
    arg, keys = normal_key_params(md)

    if keys[0] == ':':
        sline.buf = ':'
        sline.pos = 1
        mode(excmd)
        buf.mode_changed()
        return "done"

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

    if key == 'h':
        return buf.left_motion(amt)

    if key == 'l':
        return buf.right_motion(amt)

    if key == 'k':
        return buf.up_motion(amt)

    if key == 'j' or key == 'enter':
        return buf.down_motion(amt)
