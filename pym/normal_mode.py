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

"""
Standard bindings for normal mode
"""

from pym import pym
from .mode import normal, insert, excmd, search, backsearch
from .key_parse import KeyGroup

motionGroup = KeyGroup('motion')

@motionGroup.add("#?(h|j|k|l|<enter>| |<backspace>)")
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

    if key == ' ':
        return pym.buf.forward_motion(amt)

    if key == 'backspace':
        return pym.buf.backward_motion(amt)

@motionGroup.add('#?(n|N)')
def search_motion(keys):
    """
    Move to next search item
    """
    times = keys[0]
    backward = keys[1] == 'N'

    if times == None:
        times = 1

    for _ in range(times):
        if backward:
            return pym.buf.prev_search()
        else:
            return pym.buf.next_search()

@normal.handle('#?d(d|`motion`)')
def normal_delete(keys):
    """
    Key press handler for `d` in normal mode
    """
    count, _, mot = keys

    if count == None:
        count = 1

    if mot == 'd':
        mot = pym.buf.down_motion(count - 1)

    mot.delete()

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
def normal_mode_motion(mot):
    """
    Key press handler for motions in normal mode
    """
    mot.execute()

@normal.handle('#?x')
def normal_delchar_key(key):
    """
    Key press handler for `x` in normal mode
    """
    count, key = key

    if count == None:
        count = 1
    pym.buf.right_motion(count).delete()

@normal.handle('/')
def normal_mode_to_search_mode(_):
    """
    Key press handler for `:` in normal mode
    """
    sline = pym.sline
    sline.buf = '/'
    sline.pos = 1
    pym.mode = search

@normal.handle('<?>')
def normal_mode_to_back_search_mode(_):
    """
    Key press handler for `?` in normal mode
    """
    sline = pym.sline
    sline.buf = '?'
    sline.pos = 1
    pym.mode = backsearch

@normal.handle(':')
def normal_mode_to_command_mode(_):
    """
    Key press handler for `:` in normal mode
    """
    sline = pym.sline
    sline.buf = ':'
    sline.pos = 1
    pym.mode = excmd

@normal.handle('i|a|A')
def normal_mode_to_insert_mode(key):
    """
    Key press handler for `i`, `a`, and `A` in normal mode
    """
    pym.mode = insert
    buf = pym.buf
    if key == 'A':
        buf.move_to(buf.row, len(buf.lines[buf.row]))
    elif key == 'a':
        buf.right_motion().execute()
