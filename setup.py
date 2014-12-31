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
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Text Editors",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
)
