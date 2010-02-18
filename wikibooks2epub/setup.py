#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# written by j@mailb.org 2009
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from distutils.core import setup
import os.path
import sys

setup(name="wikibooks2epub",
        version="0.1",
        description="wikibooks2epub - convert wikibooks to epub",
        long_description="wikibooks2epub - convert wikibooks to epub",
        author="j",
        author_email="j@oil21.org",
        url="http://oil21.org/~j/wikibooks2epub",
        platforms="linux",
        license="GPL",
        classifiers=[
            "License :: OSI Approved :: GPL",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python",
        ],
        py_modules = [],
        packages = ['wikibooks', ],
        scripts=['bin/wikibooks2epub'],
        data_files=[
          ]
        )

