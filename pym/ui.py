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

class UI(object):
    """
    A representation of the UI to UI-agnostic portions of the code
    """
    def quit(self):
        """
        Exit the program
        """
        raise NotImplementedError("UI does not implement quit()")

    def notify(self, message, error=False):
        """
        Display a notification to the user
        """
        raise NotImplementedError("UI does not implement notify()")

    def buf(self):
        """
        Get the active buffer
        """
        raise NotImplementedError("UI does not implement buf()")

    def sline(self):
        """
        Get the status line buffer
        """
        raise NotImplementedError("UI does not implement buf()")

_ui = None

class UIOverrideError(Exception):
    """
    Exception raised when we try to set the UI twice
    """
    pass

def ui(newUI = None):
    global _ui
    if newUI != None:
        if _ui != None:
            raise UIOverrideError("UI can only be set once")
        _ui = newUI
    return _ui
