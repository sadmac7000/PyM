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

from .mode import excommand
from .ui import ui

@excommand("quit")
def quitcmd(args):
    if args == None:
        ui().quit()
    ui().notify("Trailing characters", error=True)

@excommand("edit")
def editcmd(args):
    try:
        ui().buf.loadfile(args)
    except NoFileNameError:
        ui().notify("No File Name", error=True)
    except PermissionError:
        ui().notify("Permission denied", error=True)

@excommand("write")
def writecmd(args):
    try:
        ui().buf.writefile(args)
    except NoFileNameError:
        ui().notify("No File Name", error=True)
    except PermissionError:
        ui().notify("Permission denied", error=True)
    except FileNotFoundError:
        ui().notify("No Such File or Directory", error=True)
