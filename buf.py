from mode import mode

class Motion():
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
    def __init__(self, buf, start, end):
        if end >= start:
            super(LineMotion, self).__init__(buf, (start,0),(end + 1, 0))
        else:
            super(LineMotion, self).__init__(buf, (start+1,0),(end, 0))

        self.target = end

    def execute(self):
        self.buf.move_to(self.target, self.buf.col_want)

class Buffer():
    def __init__(self, path = None):
        self.lines = [""]
        self.path = None
        self.row = 0
        self.col = 0
        self.col_want = 0

        if path != None:
            self.loadfile(path)

        self.markers = {}

    def mark(self, char):
        self.markers[char] = (self.row, self.col)

    def restore_mark(self, char):
        if char in self.markers:
            self.move_to(*self.markers[char])
            return True
        return False

    def encoded(self, start = 0, end = None):
        if end == None:
            end = len(self.lines)
        return [ x.encode() for x in self.lines[start:end] ]

    def loadfile(self, path):
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
        if mode().insert:
            return

        if self.col < len(self.lines[self.row]):
            return

        if self.col == 0:
            return
        self.col -= 1

    def move_to(self, row, col):
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
        return LineMotion(self, self.row, self.row + count)

    def up_motion(self, count = 1):
        return LineMotion(self, self.row, self.row - count)

    def left_motion(self, count = 1):
        return Motion(self, (self.row, self.col), (self.row,self.col - count))

    def right_motion(self, count = 1):
        return Motion(self, (self.row, self.col), (self.row,self.col + count))

    def insert(self, data, row=None, col=None):
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
