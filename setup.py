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

from setuptools import setup, find_packages
setup(
    name = "PyM",
    version = "0.0.1",
    packages = find_packages(),

    install_requires = ['urwid>=1.2.0'],

    # metadata for upload to PyPI
    description = "A Vi-like editor written in python",
    license = "GPLv3+",
    keywords = "pym vim vi text editor",
    #url = "http://example.com/HelloWorld/",
    entry_points={
        "console_scripts": [
            "pym = pym.urwid_ui:run"
        ]
    },
)
