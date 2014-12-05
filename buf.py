from mode import mode

class Motion():
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def exec(self, buf):
        buf.move_to(self.end)

    def ordered_coords(self):
        start = self.start
        end = self.end

        if start[0] > end[0] || (start[0] == end[0] && start[1] > end[1]):
            tmp = start
            start = end
            end = start

        return start, end

    def delete(self, buf):
        start, end = self.ordered_coords()

        row = start[0]
        col = start[1]
        prepend = ""

        if row != end[0]:
            prepend = buf.lines[row][:col]
            del buf.lines[row:end[0]]
            col = 0

        line = buf.lines[row]
        buf.lines[row] = prepend + line[0:col] + line[end[1]:]

    def get_text(self, buf):
        start, end = self.ordered_coords()

        row = start[0]
        col = start[1]

        ret = ""

        while row < end[0]:
            ret += buf.lines[row][col:] + "\n"
            row += 1
            col = 0

        return ret + buf.lines[row][col:end[1]]

class Buffer():
    def __init__(self, path = None):
        self.lines = [""]
        self.path = None
        self.row = 0
        self.col = 0
        self.col_want = 0

        if path != None:
            self.loadfile(path)

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
            self.lines = [b'']

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

        if col > len(self.lines[row]):
            col = len(self.lines[row]) - 1

        if (not mode().insert) and col == len(self.lines[row]):
            col = len(self.lines[row]) - 1

        self.row = row
        self.col = col

    def move_down(self):
        if self.row >= len(self.lines) - 1:
            return False
        self.move_to(self.row + 1, self.col_want)
        return True

    def move_up(self):
        if self.row == 0:
            return False
        self.move_to(self.row - 1, self.col_want)
        return True

    def move_left(self):
        if self.col == 0:
            return False
        self.move_to(self.row, self.col - 1)
        self.col_want = self.col
        return True

    def move_right(self):
        if not mode().insert and self.col >= len(self.lines[self.row]) - 1:
            return False
        if self.col >= len(self.lines[self.row]):
            return False
        self.move_to(self.row, self.col + 1)
        self.col_want = self.col
        return True

    def insert(self, data, row=None, col=None):
        print(data)
        if row == None:
            row = self.row
        if col == None:
            col = self.col

        line = self.lines[row]
        self.lines[row] = line[:col] + data + line[col:]
        self.lines[row:row+1] = self.lines[row].split('\n')

    def delete(self, start = None, end = None):
        if start == None:
            start = (self.row, self.col)
        if end == None:
            end = (self.row, self.col + 1)

        row = start[0]
        col = start[1]
        prepend = ""

        if row != end[0]:
            prepend = self.lines[row][:col]
            del self.lines[row:end[0]]
            col = 0

        line = self.lines[row]
        self.lines[row] = prepend + line[0:col] + line[end[1]:]
