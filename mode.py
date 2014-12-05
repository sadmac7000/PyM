import urwid
_mode = None

def mode():
    return _mode

class Mode():
    def __init__(self, abort_mode = mode, key_handler = None, label = "",
            focus="buffer", insert=False):
        self.label = label.encode()
        self.key_handler = key_handler
        self.key_intercept = key_handler
        self.abort_mode = abort_mode
        self.focus="buffer"
        self.insert = insert

    def handle_key(self, key, buf, sline):
        global _mode
        if key == 'esc':
            if self.key_intercept != self.key_handler:
                self.key_intercept = self.key_handler
            else:
                _mode = self.abort_mode
                buf.mode_changed()
        elif self.key_handler != None:
            self.key_intercept = self.key_intercept(key, buf, sline)
            if self.key_intercept == None:
                self.key_intercept= self.key_handler

def normal_mode_keys(key, buf, sline):
    global _mode
    motion = motion_key(key, buf)

    if motion != None:
        motion.execute()
        return

    if key == 'q':
        raise urwid.ExitMainLoop()

    if key == 'd':
        return delete_intercept

    if key == 'i':
        _mode=insert
        buf.mode_changed()

    if key == 'x':
        buf.delete()

    if key == 'a':
        _mode=insert
        buf.mode_changed()
        buf.right_motion().execute()

    if key == 'A':
        _mode=insert
        buf.mode_changed()
        buf.move_to(buf.row, len(buf.lines[buf.row]))

    if key == 'enter':
        return buf.down_motion().execute()

def motion_key(key, buf):
    if key == 'h':
        return buf.left_motion()

    if key == 'l':
        return buf.right_motion()

    if key == 'k':
        return buf.up_motion()

    if key == 'j':
        return buf.down_motion()


def delete_intercept(key, buf, sline):
    motion = motion_key(key,buf)
    if key == 'd':
        motion = buf.down_motion(0)

    if motion != None:
        motion.delete()


_mode = normal = Mode(None, normal_mode_keys)
normal.abort_mode = normal

def insert_mode_keys(key, buf, sline):
    if key == 'backspace':
        buf.left_motion().delete()

    if key == 'delete':
        buf.delete()
        return

    if len(key) > 1:
        return

    buf.insert(key)
    buf.right_motion().execute()

insert = Mode(normal, insert_mode_keys, "-- INSERT --", insert=True)
