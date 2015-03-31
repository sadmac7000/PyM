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

# pylint: disable=too-few-public-methods

"""
File type support
"""

import ast
from pym.buf import Region

class FileType(object):
    """
    A file type
    """
    def load(self, buf):
        """
        Action to perform when we load a file of this type
        """
        pass

MIME_DICT = {}

plain_text = FileType()

class PythonFileType(FileType):
    """
    File type for python sources
    """

    def load(self, buf):
        """
        Build an AST and set up syntax hilighting
        """
        self.ast = ast.parse(buf.dump_text())
        for node in ast.walk(self.ast):
            if isinstance(node, ast.FunctionDef):
                buf.add_region(Region(None, 'keyword',
                    (node.lineno - 1, node.col_offset),
                    (node.lineno, node.col_offset)))

MIME_DICT['text/x-python'] = PythonFileType()

def file_type_for_mime(mime):
    """
    Get the file type object for a given mime type
    """
    if mime in MIME_DICT:
        return MIME_DICT[mime]

    return plain_text
