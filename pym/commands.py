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
Definitions of base Ex Commands
"""

from pym import pym
from .mode import excommand
from .buf import NoFileNameError
from glob import glob
import os

def file_tab_complete(string):
    """
    Tab completion for commands that take a file name
    """
    def slashed_path(path):
        """
        Filter to append slashes to folders and spaces to complete files
        """
        if os.path.isdir(path):
            return path + '/'
        else:
            return path + ' '
    return [slashed_path(x) for x in glob(string + '*')]

@excommand("quit")
def quitcmd(args):
    """
    :quit
    """
    if args == None:
        pym.quit()
    pym.notify("Trailing characters", error=True)

@excommand("edit", file_tab_complete)
def editcmd(args):
    """
    :edit
    """
    try:
        pym.buf.loadfile(args)
    except NoFileNameError:
        pym.notify("No File Name", error=True)
    except PermissionError:
        pym.notify("Permission denied", error=True)

@excommand("write", file_tab_complete)
def writecmd(args):
    """
    :write
    """
    try:
        pym.buf.writefile(args)
    except NoFileNameError:
        pym.notify("No File Name", error=True)
    except PermissionError:
        pym.notify("Permission denied", error=True)
    except FileNotFoundError:
        pym.notify("No Such File or Directory", error=True)
