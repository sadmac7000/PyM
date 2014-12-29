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

from .mode import ExCommand
from .ui_core import ui

def quitcmd(args, sline, buf):
    if args == None:
        ui().quit()
    ui().notify("Trailing characters", error=True)

ExCommand("quit", quitcmd)

def editcmd(args, sline, buf):
    buf.loadfile(args)

ExCommand("edit", editcmd)

def writecmd(args, sline, buf):
    buf.writefile(args)

ExCommand("write", writecmd)
