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
from pygments.lexers import PythonLexer
from pygments import token

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
        tokens = PythonLexer().get_tokens_unprocessed(buf.dump_text())

        for t in tokens:
            pos = buf.index_to_line_col(t[0])
            end_line = pos[0]
            end_col = pos[1]
            i = 0

            while i < len(t[2]):
                if t[2][i] == '\n':
                    end_line += 1
                    end_col = 0
                else:
                    end_col += 1
                i += 1

            end = (end_line, end_col)

            if t[1] in token.Comment:
                buf.add_region(Region(None, 'comment', pos, end))
            elif t[1] in token.String.Escape:
                buf.add_region(Region(None, 'string_literal_esc', pos, end))
            elif t[1] in token.String:
                buf.add_region(Region(None, 'string_literal', pos, end))
            elif t[1] in token.Literal:
                buf.add_region(Region(None, 'literal', pos, end))
            elif t[1] in token.Keyword:
                buf.add_region(Region(None, 'keyword', pos, end))
            elif t[1] in token.Name.Decorator:
                buf.add_region(Region(None, 'function_name', pos, end))
            elif t[1] in token.Name.Class:
                buf.add_region(Region(None, 'class_name', pos, end))
            elif t[1] in token.Name.Function:
                buf.add_region(Region(None, 'function_name', pos, end))

MIME_DICT['text/x-python'] = PythonFileType()

def file_type_for_mime(mime):
    """
    Get the file type object for a given mime type
    """
    if mime in MIME_DICT:
        return MIME_DICT[mime]

    return plain_text
