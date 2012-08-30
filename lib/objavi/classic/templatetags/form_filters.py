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

from django import template
from django.conf import settings


register = template.Library()


@register.filter
def get_widget(value, arg):
    arg = str(arg).replace("-", "_")
    try:
        return value[arg]
    except KeyError:
        return settings.TEMPLATE_STRING_IF_INVALID
