from mode import mode

class Buffer():
    def __init__(self, path = None):
        self.lines = [b""]
        self.path = None
        self.row = 0
        self.col = 0
        self.col_want = 0

        if path != None:
            self.loadfile(path)

    def loadfile(self, path):
        self.path = path
        self.lines = []
        with open(path, 'r') as f:
            for line in f.readlines():
                if line.endswith('\n'):
                    line = line[:-1]
                self.lines += [line.encode()]
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
        data = data.encode()
        if row == None:
            row = self.row
        if col == None:
            col = self.col

        line = self.lines[row]
        self.lines[row] = line[:col] + data + line[col:]
        self.lines[row:row+1] = self.lines[row].split(b'\n')

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
