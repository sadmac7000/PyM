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
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# PyM.  If not, see <http://www.gnu.org/licenses/>.

from pym import pym
from .mode import normal, insert, excmd, mode
from .key_parse import key_macro

@key_macro("#?(h|j|k|l|<enter>)")
def motion(key):
    """
    Generic key press receiver for motion keys
    """
    amt, key = key

    if amt == None:
        amt = 1

    if key == 'h':
        return pym.buf.left_motion(amt)

    if key == 'l':
        return pym.buf.right_motion(amt)

    if key == 'k':
        return pym.buf.up_motion(amt)

    if key == 'j' or key == 'enter':
        return pym.buf.down_motion(amt)

@normal.handle('#?d(d|`motion`)')
def normal_delete(keys):
    """
    Key press handler for `d` in normal mode
    """
    count, key, motion = keys

    if count == None:
        count = 1

    if motion == 'd':
        motion = pym.buf.down_motion(count - 1)

    motion.delete()

@normal.handle('m@')
def normal_mode_mark(keys):
    """
    Key press handler for `m` in normal mode
    """
    key = keys[1]

    if key == '`':
        key = "'"

    pym.buf.mark(key)

@normal.handle("('|<`>)@")
def normal_mode_goto(keys):
    """
    Key press handler for '`' in normal mode
    """
    key = keys[1]

    if key == '`':
        key = "'"

    pym.buf.restore_mark(key)

@normal.handle("`motion`")
def normal_mode_motion(motion):
    """
    Key press handler for motions in normal mode
    """
    motion.execute()

@normal.handle('#?x')
def normal_delchar_key(key):
    """
    Key press handler for `x` in normal mode
    """
    count, key = key

    if count == None:
        count = 1
    pym.buf.right_motion(count).delete()

@normal.handle(':')
def normal_mode_to_command_mode(key):
    """
    Key press handler for `:` in normal mode
    """
    sline = pym.sline
    sline.buf = ':'
    sline.pos = 1
    mode(excmd)

@normal.handle('i|a|A')
def normal_mode_to_insert_mode(key):
    """
    Key press handler for `i`, `a`, and `A` in normal mode
    """
    mode(insert)
    buf = pym.buf
    if key == 'A':
        buf.move_to(buf.row, len(buf.lines[buf.row]))
    elif key == 'a':
        buf.right_motion().execute()
