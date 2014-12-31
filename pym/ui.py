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

# pylint: disable=attribute-defined-outside-init

"""
The interface by which the PyM UI identifies itself to the core code
"""

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

    @property
    def buf(self):
        """
        Get the active buffer
        """
        raise NotImplementedError("UI does not implement buf")

    @property
    def sline(self):
        """
        Get the status line buffer
        """
        raise NotImplementedError("UI does not implement sline")

    def get_mode(self):
        """
        Get the mode
        """
        return self._mode

    def set_mode(self, mode):
        """
        Set the mode
        """
        self._mode = mode
        self.buf.mode_changed()

    mode = property(get_mode, set_mode, "The current editor mode")
