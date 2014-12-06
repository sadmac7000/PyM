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

from .mode import mode

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
        self.buf.move_to(*self.end)
        self.buf.col_want = self.end[1]

    def ordered_coords(self):
        start = self.start
        end = self.end

        if start[0] > end[0] or (start[0] == end[0] and start[1] > end[1]):
            tmp = start
            start = end
            end = tmp

        return start, end

    def delete(self):
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

        line = self.buf.lines[row]
        self.buf.lines[row] = prepend + line[0:col] + line[end[1]:]
        col = self.buf.col
        if start != self.start:
            self.execute()
        self.buf.col_want = col

    def get_text(self):
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

        if path != None:
            self.loadfile(path)

        self.markers = {}

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

    def loadfile(self, path):
        """
        Replace the contents of this buffer with the contents of the file at
        the given path.
        """
        self.path = path
        self.lines = []
        with open(path, 'r') as f:
            for line in f.readlines():
                if line.endswith('\n'):
                    line = line[:-1]
                self.lines += [line]
        if len(self.lines) == 0:
            self.lines = ['']

    def mode_changed(self):
        """
        Notify this buffer of a mode change. Some of its state (i.e. the cursor
        position) may have a different set of legal values depending on mode,
        so this is the buffer's opportunity to correct.
        """
        if mode().insert:
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

        if mode().insert and col > len(self.lines[row]) or (
            not mode().insert and col >= len(self.lines[row])
                ):
            self.col_want = col
            col = len(self.lines[row])
            if not mode().insert:
                col -= 1

        if (not mode().insert) and col == len(self.lines[row]):
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

        return Motion(self, (row,col), (end_row,end_col))
