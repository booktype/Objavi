# This file is part of Objavi.
# Copyright (c) 2012 Borko Jandras <borko.jandras@sourcefabric.org>
#
# Objavi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Objavi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Objavi.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^$',                "objavi.classic.views.default"),
    url(r'^css$',             "objavi.classic.views.fetch_css"),
    url(r'^booklist$',        "objavi.classic.views.fetch_booklist"),
    url(r'^fontlist$',        "objavi.classic.views.fetch_fontlist"),
    url(r'^espri$',           "objavi.classic.views.espri"),
)
