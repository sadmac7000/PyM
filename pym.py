import urwid
from buf import Buffer
from mode import mode

urwid.set_encoding("UTF-8")

scrolloff = 5

class BufferDisplay(urwid.Widget):
    _sizing=frozenset('box')

    def __init__(self, buf):
        super(urwid.Widget, self).__init__()
        self.buf = buf
        self.scroll = 0

    def get_cursor_coords(self, size):
        col = self.buf.col
        row = self.buf.row - self.scroll

        if row > size[1] - scrolloff:
            self.scroll += row - size[1] + scrolloff

        if self.scroll + size[1] > len(self.buf.lines):
            self.scroll = len(self.buf.lines) - size[1]

        if row < scrolloff:
            self.scroll -= scrolloff - row

        if self.scroll < 0:
            self.scroll = 0

        row = self.buf.row - self.scroll
        return (col,row)

    def render(self, size, **kwargs):
        lines = [ x[:size[0]] for x in self.buf.encoded(self.scroll) ][:size[1]]
        attrs = [[]] * len(lines)
        if len(lines) < size[1]:
            attrs += [[('nonline', 1)]] * (size[1]-len(lines))
            lines += [b"~"] * (size[1]-len(lines))
        return urwid.TextCanvas(lines, attrs,
                cursor=self.get_cursor_coords(size), maxcol=size[0])

class Tabset(urwid.Widget):
    _sizing=frozenset('flow')

    def rows(self, size, focus):
        return 1

    def render(self, size, **kwargs):
        return urwid.TextCanvas([b"Unnamed"], [[('tab', 7), ('tabspace',
            size[0]-7)]], maxcol=size[0])

class StatusLine(urwid.Widget):
    _sizing=frozenset('flow')

    def rows(self, size, focus):
        return 1

    def render(self, size, **kwargs):
        label = mode().label
        attr = ('modelabel', len(label))
        return urwid.TextCanvas([label], [[attr]], maxcol=size[0])

buf=Buffer('pym.py')
bdisp = BufferDisplay(buf)
sline = StatusLine()
tabset = Tabset()

layout = urwid.Pile([(1,tabset),bdisp,(1,sline)])

palette = [('tab', 'black,underline', 'light gray'),
        ('tabspace', 'black', 'light gray', '', 'h8', 'g74'),
        ('modelabel', 'white,bold', ''),
        ('nonline', 'dark blue', '')]

def do_input(key):
    mode().handle_key(key, buf, sline)
    bdisp._invalidate()
    sline._invalidate()

loop = urwid.MainLoop(layout, palette, unhandled_input=do_input)
loop.screen.set_terminal_properties(colors=256)
loop.run()
