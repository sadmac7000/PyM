import urwid
_mode = None

def mode():
    return _mode

class Mode():
    def __init__(self, abort_mode = mode, key_handler = None, label = "",
            focus="buffer", insert=False):
        self.label = label.encode()
        self.key_handler = key_handler
        self.abort_mode = abort_mode
        self.focus="buffer"
        self.insert = insert

    def handle_key(self, key, buf, sline):
        global _mode
        if key == 'esc':
            _mode = self.abort_mode
            buf.mode_changed()
        elif self.key_handler != None:
            self.key_handler(key, buf, sline)

def normal_mode_keys(key, buf, sline):
    global _mode
    if key == 'q':
        raise urwid.ExitMainLoop()

    if key == 'h':
        buf.move_left()

    if key == 'l':
        buf.move_right()

    if key == 'k':
        buf.move_up()

    if key == 'j':
        buf.move_down()

    if key == 'i':
        _mode=insert
        buf.mode_changed()

    if key == 'x':
        buf.delete()

    if key == 'a':
        _mode=insert
        buf.mode_changed()
        buf.move_right()

    if key == 'A':
        _mode=insert
        buf.mode_changed()
        buf.move_to(buf.row, len(buf.lines[buf.row]))

_mode = normal = Mode(None, normal_mode_keys)
normal.abort_mode = normal

def insert_mode_keys(key, buf, sline):
    if key == 'backspace':
        if not buf.move_left():
            return
        buf.delete()

    buf.insert(key)
    buf.move_right()

insert = Mode(normal, insert_mode_keys, "-- INSERT --", insert=True)
