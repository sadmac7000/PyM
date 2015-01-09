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

# pylint: disable=too-few-public-methods

"""
Handling for text buffers. This is the core of the editor.
"""

import os
import re
import magic
from operator import attrgetter
from .filetypes import plain_text, file_type_for_mime

from pym import pym

class NoFileNameError(Exception):
    """
    Exception raised when we try to use the recorded file name of a buffer that
    doesn't have one.
    """
    pass

class Motion(object):
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
        pym.redraw()

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
        self.buf.collapse_regions((row, col), end)
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
            super(LineMotion, self).__init__(buf, (start, 0), (end + 1, 0))
        else:
            super(LineMotion, self).__init__(buf, (start + 1, 0), (end, 0))

        self.target = end

    def execute(self):
        self.buf.move_to(self.target, self.buf.col_want)
        pym.redraw()

"A motion that goes nowhere"
class NullMotion(Motion):
    def __init__(self):
        pass

    def execute(self):
        pass

    def delete(self):
        pass

    def get_text(self):
        return ""

NULL_MOTION = NullMotion()

class Region(object):
    """
    A static region in a buffer. Usually used for things like hilighting or
    folding.
    """

    def __init__(self, owner, tag, start, end):
        self.owner = owner
        self.tag = tag
        self.start = start
        self.end = end

class Buffer(object):
    """
    A buffer stores a filesworth of text as a list of lines. It can generate
    motion objects over that text and maintains a cursor position.
    """
    def __init__(self, path=None):
        self.lines = [""]
        self.path = None
        self.row = 0
        self.col = 0
        self.col_want = 0
        self.dirty = False
        self.regions = []
        self.search_expr = None
        self.search_backward = False
        self.file_type = plain_text

        if path != None:
            self.load_file(path)

        self.markers = {}

    def add_region(self, reg):
        """
        Add a region to the buffer
        """
        inserted = False

        for i, other in enumerate(self.regions):
            if other.start >= reg.start:
                self.regions.insert(i, reg)
                inserted = True
                break

        if not inserted:
            self.regions.append(reg)

    def headline(self):
        """
        Get a text headline for this buffer for the UI
        """
        if self.dirty:
            dirty_marker = "+ "
        else:
            dirty_marker = ""

        if self.path == None:
            return dirty_marker + "[No Name]"

        return dirty_marker + os.path.relpath(self.path)

    def regions_for_line(self, line):
        """
        Get the regions affecting a line
        """
        regions = [x for x in self.regions if x.start[0] <= line and x.end[0] >= line]

        if self.search_expr == None:
            return regions

        for k in self.search_expr.finditer(self.lines[line]):
            regions.append(Region(None, 'search', (line, k.start()), (line,
                k.end())))

        regions.sort(key=attrgetter('start'))

        return regions

    def mark(self, char="'"):
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
            tgt = self.markers[char]
            self.mark()
            self.move_to(*tgt)
            return True
        return False

    def load_file(self, path=None):
        """
        Replace the contents of this buffer with the contents of the file at
        the given path.
        """
        if path != None:
            self.path = os.path.abspath(path)
        elif self.path == None:
            raise NoFileNameError()

        new_lines = []

        try:
            with open(self.path, 'r') as f:
                for line in f.readlines():
                    if line.endswith('\n'):
                        line = line[:-1]
                    new_lines += [line]

                mimetype = magic.from_file(self.path, mime=True)
        except FileNotFoundError:
            #TODO: Notify if the directory isn't there either
            pass

        self.file_type = file_type_for_mime(mimetype)

        if len(new_lines) == 0:
            self.lines = ['']
        else:
            self.lines = new_lines

        self.regions = []
        self.dirty = False

    def write_file(self, path=None):
        """
        Write the contents of this buffer to a file. If no path is given, use
        the last known location.
        """
        do_mime = False

        if path == None:
            path = self.path

        if path == None:
            raise NoFileNameError()

        if self.path == None:
            do_mime = True
            self.path = path

        with open(path, "wb") as f:
            f.write(("\n".join(self.lines)+"\n").encode())

        if os.path.samefile(path, self.path):
            self.dirty = False


    def mode_changed(self, old_mode):
        """
        Notify this buffer of a mode change. Some of its state (i.e. the cursor
        position) may have a different set of legal values depending on mode,
        so this is the buffer's opportunity to correct.
        """
        if pym.mode.insert:
            return

        if self.col < len(self.lines[self.row]) and \
                (old_mode == None or not old_mode.insert):
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
                not pym.mode.insert and col >= len(self.lines[row])):
            self.col_want = col
            col = len(self.lines[row])
            if not pym.mode.insert:
                col -= 1

        if (not pym.mode.insert) and col == len(self.lines[row]):
            col = len(self.lines[row]) - 1

        self.row = row
        self.col = col

    def down_motion(self, count=1):
        """
        Get a motion that moves the cursor down by the given number of lines.
        """
        return LineMotion(self, self.row, self.row + count)

    def up_motion(self, count=1):
        """
        Get a motion that moves the cursor up by the given number of lines.
        """
        return LineMotion(self, self.row, self.row - count)

    def left_motion(self, count=1):
        """
        Get a motion that moves the cursor left by the given number of columns.
        """
        return Motion(self, (self.row, self.col), (self.row, self.col - count))

    def right_motion(self, count=1):
        """
        Get a motion that moves the cursor right by the given number of columns.
        """
        return Motion(self, (self.row, self.col), (self.row, self.col + count))

    def forward_motion(self, count=1):
        """
        Get a motion that moves the cursor right by the given number of
        columns. If we reach the end of the line, we count skipping to the next
        line as one column.
        """

        line = self.row
        col = self.col

        while (len(self.lines[line]) - col) < count and \
                line < (len(self.lines) - 1):
            count -= len(self.lines)
            count -= 1
            col = 0
            line += 1

        if line == len(self.lines):
            col = len(self.lines[line]) - 1
        elif (len(self.lines[line]) - col) == count:
            col = 0
            line += 1
        else:
            col += count

        return Motion(self, (self.row, self.col), (line, col))

    def backward_motion(self, count=1):
        """
        Get a motion that moves the cursor left by the given number of
        columns. If we reach the end of the line, we count skipping to the
        previous line as one column.
        """

        col = self.col
        line = self.row

        while line > 0 and col < count:
            count -= col
            count -= 1
            line -= 1
            col = len(self.lines[line]) - 1

        if col < count:
            col = 0
        else:
            col -= count

        return Motion(self, (self.row, self.col), (line, col))

    def expand_regions(self, start, end):
        """
        Expand regions to cover newly-inserted text
        """
        lines_added = end[0] - start[0]
        cols_added = end[1] - start[1]

        for reg in self.regions:
            newcol = reg.end[1]
            if reg.end > start:
                if reg.end[0] == start[0]:
                    newcol += cols_added
                reg.end = (reg.end[0] + lines_added, newcol)

            if reg.start > start:
                newcol = reg.start[1]
                if reg.start[0] == start[0]:
                    newcol += cols_added
                reg.start = (reg.start[0] + lines_added, newcol)

    def forward_search(self, start_pos=None):
        """
        Get the linearly next matching search position
        """
        if start_pos == None:
            start_pos = (self.row, self.col)

        row, col = start_pos

        if self.search_expr == None:
            return NULL_MOTION

        match = self.search_expr.search(self.lines[row], col + 1)

        if match != None:
            return Motion(self, (self.row, self.col), (row, match.start()))

        stop_row = row
        row = row + 1
        if row >= len(self.lines):
            row = 0

        while row != stop_row:
            if row >= len(self.lines):
                row = 0

            match = self.search_expr.search(self.lines[row])

            if match == None:
                row += 1
                continue

            start, end = match.span()

            if start == end:
                row += 1
                continue
            return Motion(self, (self.row, self.col), (row, start))

        return NULL_MOTION

    def backward_search(self, start_pos=None):
        """
        Get the linearly next matching search position
        """
        if start_pos == None:
            start_pos = (self.row, self.col)

        row, col = start_pos

        if self.search_expr == None:
            return NULL_MOTION

        match = None

        for m in self.search_expr.finditer(self.lines[row]):
            if m.start() < col and m.start() != m.end():
                match = m
            elif m.start() >= col:
                break

        if match != None:
            return Motion(self, (self.row, self.col), (row, match.start()))

        stop_row = row
        row = row - 1

        if row < 0:
            row = len(self.lines) - 1

        while row != stop_row:
            if row < 0:
                row = len(self.lines) - 1

            match = None

            for match in self.search_expr.finditer(self.lines[row]):
                pass

            if match == None:
                row -= 1
                continue

            start, end = match.span()

            if start != end:
                return Motion(self, (self.row, self.col), (row, start))

            row -= 1

        return NULL_MOTION

    def next_search(self, pos=None):
        """
        Get the next match by the direction specified for the search
        """
        if self.search_backward:
            return self.backward_search(pos)
        else:
            return self.forward_search(pos)

    def prev_search(self, pos=None):
        """
        Get the previos match by the direction specified for the search
        """
        if self.search_backward:
            return self.forward_search(pos)
        else:
            return self.backward_search(pos)

    def search(self, expr, backward):
        """
        Set the search variable
        """
        self.search_expr= re.compile(expr)
        self.search_backward = backward

    def collapse_regions(self, start, end):
        """
        Collapse regions that were surrounding deleted text
        """
        for reg in self.regions:
            if reg.start >= end:
                newcol = reg.start[1]
                if reg.start[0] == end[0]:
                    newcol -= end[1]
                    if start[0] == end[0]:
                        newcol += start[1]
                reg.start = (reg.start[0] - end[0] + start[0], newcol)
            elif reg.start >= start:
                reg.start = start

            if reg.end >= end:
                newcol = reg.end[1]
                if reg.end[0] == end[0]:
                    newcol -= end[1]
                    if start[0] == end[0]:
                        newcol += start[1]
                reg.end = (reg.end[0] - end[0] + start[0], newcol)
            elif reg.end >= start:
                reg.end = start

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
        self.expand_regions((row, col), (end_row, end_col))

        return Motion(self, (row, col), (end_row, end_col))
