#!/usr/bin/python
#
# Part of the Objavi2 package.  This script is for testing callbacks
#
# Copyright (C) 2009 Douglas Bagnall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os, sys
os.chdir('..')
sys.path.insert(0, os.path.abspath('.'))

import cgi

from objavi.book_utils import log

def log_args():
    log("callback-test.cgi called the following arguments:")
    form = cgi.FieldStorage()
    for k in form:
        log("%s: %s" % (k, form.getlist(k)))


log_args()
print "Content-type: text/plain"
print
print "hello"
