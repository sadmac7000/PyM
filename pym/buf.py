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

import os
from pym import pym

class NoFileNameError(Exception):
    """
    Exception raised when we try to use the recorded file name of a buffer that
    doesn't have one.
    """
    pass

class Motion():
    """
    A motion describes a movement of the cursor over a region of text, but it
    is much more than that. It is used to store regions of text for
    manipulation.
    """
    def __init__(self, buf, start, end):
        self.start = start
        self.end = end
        self.buf = buf

    def execute(self):
        """
        Move the cursor to the end of this motion.
        """
        self.buf.move_to(*self.end)
        self.buf.col_want = self.end[1]

    def ordered_coords(self):
        """
        Return the coordinates in order of increasing text position.
        """
        start = self.start
        end = self.end

        if start[0] > end[0] or (start[0] == end[0] and start[1] > end[1]):
            tmp = start
            start = end
            end = tmp

        return start, end

    def delete(self):
        """
        Delete the text passed over by this motion
        """
        start, end = self.ordered_coords()

        row = start[0]
        col = start[1]
        if col < 0:
            col = 0
        if row < 0:
            row = 0
        prepend = ""

        if row < end[0]:
            prepend = self.buf.lines[row][:col]
            del self.buf.lines[row:end[0]]
            col = 0
        if len(self.buf.lines) == 0:
            self.buf.lines = ['']

        if row >= len(self.buf.lines):
            row = len(self.buf.lines) - 1
        line = self.buf.lines[row]
        self.buf.lines[row] = prepend + line[0:col] + line[end[1]:]
        col = self.buf.col
        if start != self.start:
            self.execute()
        else:
            self.buf.move_to(*start)
        self.buf.col_want = col
        self.buf.dirty = True

    def get_text(self):
        """
        Retrieve the text passed over by this motion
        """
        start, end = self.ordered_coords()

        row = start[0]
        col = start[1]

        ret = ""

        while row < end[0]:
            ret += self.buf.lines[row][col:] + "\n"
            row += 1
            col = 0

        return ret + self.buf.lines[row][col:end[1]]

class LineMotion(Motion):
    """
    A LineMotion is a Motion that moves from one line to another, and is more
    or less agnostic of column
    """
    def __init__(self, buf, start, end):
        if end >= start:
            super(LineMotion, self).__init__(buf, (start,0),(end + 1, 0))
        else:
            super(LineMotion, self).__init__(buf, (start+1,0),(end, 0))

        self.target = end

    def execute(self):
        self.buf.move_to(self.target, self.buf.col_want)

class Buffer():
    """
    A buffer stores a filesworth of text as a list of lines. It can generate
    motion objects over that text and maintains a cursor position.
    """
    def __init__(self, path = None):
        self.lines = [""]
        self.path = None
        self.row = 0
        self.col = 0
        self.col_want = 0
        self.dirty = False

        if path != None:
            self.loadfile(path)

        self.markers = {}

    def headline(self):
        if self.dirty:
            dirty_marker = "+ "
        else:
            dirty_marker = ""

        if self.path == None:
            return dirty_marker + "[No Name]"

        return dirty_marker + os.path.relpath(self.path)

    def mark(self, char= "'"):
        """
        Store a mark position which can be returned to. We use the current
        cursor position and pass a name, which is usually a single character.
        """
        self.markers[char] = (self.row, self.col)

    def restore_mark(self, char):
        """
        Restore the cursor to a position previously marked with the mark
        method.
        """
        if char in self.markers:
            self.move_to(*self.markers[char])
            return True
        return False

    def encoded(self, start = 0, end = None):
        """
        Get the contents of this buffer as a list of lines which have been
        encoded as UTF-8 bytes objects.
        """
        if end == None:
            end = len(self.lines)
        return [ x.encode() for x in self.lines[start:end] ]

    def loadfile(self, path = None):
        """
        Replace the contents of this buffer with the contents of the file at
        the given path.
        """
        if path != None:
            self.path = os.path.abspath(path)
        elif self.path == None:
            raise NoFileNameError()

        try:
            os.stat(self.path)
        except FileNotFoundError:
            self.dirty = False
            #TODO: Notify if the directory isn't there either
            self.lines = ['']
            return

        new_lines = []

        with open(self.path, 'r') as f:
            for line in f.readlines():
                if line.endswith('\n'):
                    line = line[:-1]
                new_lines += [line]

        if len(new_lines) == 0:
            self.lines = ['']
        else:
            self.lines = new_lines

    def writefile(self, path = None):
        if path == None:
            path = self.path

        if path == None:
            raise NoFileNameError()

        if self.path == None:
            self.path = path

        with open(path, "wb") as f:
            f.write(("\n".join(self.lines)+"\n").encode())

        if os.path.samefile(path, self.path):
            self.dirty = False

    def mode_changed(self):
        """
        Notify this buffer of a mode change. Some of its state (i.e. the cursor
        position) may have a different set of legal values depending on mode,
        so this is the buffer's opportunity to correct.
        """
        if pym.mode.insert:
            return

        if self.col < len(self.lines[self.row]):
            return

        if self.col == 0:
            return
        self.col -= 1

    def move_to(self, row, col):
        """
        Move the cursor to the given row and column.
        """
        if row < 0:
            row = 0
        if col < 0:
            col = 0
        if row >= len(self.lines):
            row = len(self.lines) - 1

        if pym.mode.insert and col > len(self.lines[row]) or (
            not pym.mode.insert and col >= len(self.lines[row])
                ):
            self.col_want = col
            col = len(self.lines[row])
            if not pym.mode.insert:
                col -= 1

        if (not pym.mode.insert) and col == len(self.lines[row]):
            col = len(self.lines[row]) - 1

        self.row = row
        self.col = col

    def down_motion(self, count = 1):
        """
        Get a motion that moves the cursor down by the given number of lines.
        """
        return LineMotion(self, self.row, self.row + count)

    def up_motion(self, count = 1):
        """
        Get a motion that moves the cursor up by the given number of lines.
        """
        return LineMotion(self, self.row, self.row - count)

    def left_motion(self, count = 1):
        """
        Get a motion that moves the cursor left by the given number of columns.
        """
        return Motion(self, (self.row, self.col), (self.row,self.col - count))

    def right_motion(self, count = 1):
        """
        Get a motion that moves the cursor right by the given number of columns.
        """
        return Motion(self, (self.row, self.col), (self.row,self.col + count))

    def insert(self, data, row=None, col=None):
        """
        Insert new text at the given row and column. If the position is not
        given, it defaults to the cursor position.
        """
        if row == None:
            row = self.row
        if col == None:
            col = self.col

        data = data.split('\n')
        postfix = self.lines[row][col:]
        self.lines[row] = self.lines[row][:col] + data.pop(0)
        end_row = row

        if len(data) > 0:
            self.lines = self.lines[:row + 1] + data + self.lines[row + 1:]
            end_row += len(data)

        end_col = len(self.lines[end_row])
        self.lines[end_row] += postfix
        self.dirty = True

        return Motion(self, (row,col), (end_row,end_col))
