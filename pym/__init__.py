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

"""
PyM is a VI-like editor written in Python
"""

pym = None

class PymInitError(Exception):
    """
    Exception raised when we try to set the UI twice
    """
    pass

def pym_init(uio):
    """
    Initialize the PyM library
    """
    global pym

    if pym != None:
        raise PymInitError("Attempt to initialize PyM twice")
    pym = uio

from pym import urwid_ui
from pym import buf
from pym import mode
