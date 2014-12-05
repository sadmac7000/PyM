import urwid
_mode = None

class StatusLineBuf:
    def __init__(self):
        self.buf = ""
        self.pos = 0

def mode():
    return _mode

class Mode():
    def __init__(self, abort_mode = mode, key_handler = None, label = "",
            focus="buffer", insert=False):
        self.label = label
        self.key_handler = key_handler
        self.key_intercept = key_handler
        self.abort_mode = abort_mode
        self.focus=focus
        self.insert = insert

    def abort(self, buf):
        global _mode
        _mode = self.abort_mode
        buf.mode_changed()

    def handle_key(self, key, buf, sline):
        global _mode
        if key == 'esc':
            if self.key_intercept != self.key_handler:
                self.key_intercept = self.key_handler
            else:
                self.abort(buf)
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

    if key == 'm':
        return mark_intercept

    if key == '`' or key == "'":
        return mark_restore_intercept

    if key == ':':
        sline.buf = ':'
        sline.pos = 1
        _mode=excmd
        buf.mode_changed()

def mark_intercept(key, buf, sline):
    if len(key) > 1:
        return

    if not key in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'`0123456789":
        return

    if key == '`':
        key = "'"

    buf.mark(key)

def mark_restore_intercept(key, buf, sline):
    if len(key) > 1:
        return

    if key == '`':
        key = "'"

    buf.restore_mark(key)

def motion_key(key, buf):
    if ((key == 'h') and _mode == normal) or (key == 'left'):
        return buf.left_motion()

    if ((key == 'l') and _mode == normal) or (key == 'right'):
        return buf.right_motion()

    if ((key == 'k') and _mode == normal) or (key == 'up'):
        return buf.up_motion()

    if ((key == 'j') and _mode == normal) or (key == 'down') \
         or ((key == 'enter') and _mode == normal):
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

    if key == 'enter':
        buf.insert('\n').execute()
        return

    motion = motion_key(key, buf)
    if motion != None:
        motion.execute()
        return

    if len(key) > 1:
        return

    buf.insert(key)
    buf.right_motion().execute()

insert = Mode(normal, insert_mode_keys, "-- INSERT --", insert=True)

def excmd_mode_keys(key, buf, sline):
    if key == 'backspace':
        sline.pos -= 1
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]

        if sline.pos == 0:
            sline.buf = ""
            _mode.abort(buf)
        return

    if key == 'delete':
        sline.buf = sline.buf[:sline.pos] + sline.buf[sline.pos+1:]
        return

    if key == 'enter':
        if ":quit".startswith(sline.buf):
            raise urwid.ExitMainLoop()
        sline.buf = ""
        _mode.abort(buf)
        return

    if len(key) > 1:
        return

    sline.buf = sline.buf[:sline.pos] + key + sline.buf[sline.pos:]
    sline.pos += 1

excmd = Mode(normal, excmd_mode_keys, '', 'sline')
