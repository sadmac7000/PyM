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
