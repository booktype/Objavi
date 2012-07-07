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

from django import forms

import config
import form_config


def get_size_list():
    def calc_size(name, pointsize, klass):
        if pointsize:
            mmx = pointsize[0] * config.POINT_2_MM
            mmy = pointsize[1] * config.POINT_2_MM
            return (mmx * mmy, name, klass, '%s (%dmm x %dmm)' % (name, mmx, mmy))
        else:
            return (0, name, klass, name)
    # (name, pointsize, class) entries
    entries = [(k, v.get("pointsize"), v.get("class", "")) for (k,v) in config.PAGE_SIZE_DATA.items() if v.get("display")]
    # names sorted by size
    return [x[1] for x in sorted(calc_size(*entry) for entry in entries)]


def get_server_choices():
    return sorted((k,k) for (k,v) in config.SERVER_DEFAULTS.items() if v['display'])

def get_mode_choices():
    return sorted((k,k) for (k,v) in form_config.CGI_MODES.items() if v[0])

def get_booksize_choices():
    return [(x,x) for x in get_size_list()]

def get_license_choices():
    return [(k,k) for (k,v) in config.LICENSES.items()]

def get_page_number_choices():
    return [(k,k) for k in config.PAGE_NUMBER_OPTIONS]


class ObjaviForm(forms.Form):
    server              = forms.ChoiceField(choices = get_server_choices(), initial = config.DEFAULT_SERVER)
    book                = forms.ChoiceField()
    title               = forms.CharField()
    mode                = forms.ChoiceField(choices = get_mode_choices(), initial = form_config.DEFAULT_PDF_TYPE)
    booksize            = forms.ChoiceField(choices = get_booksize_choices())
    page_width          = forms.FloatField()
    page_height         = forms.FloatField()
    cover_url           = forms.URLField()
    output_profile      = forms.CharField()
    output_format       = forms.CharField()

    # lulucom
    #
    to_lulu             = forms.BooleanField()
    lulu_api_key        = forms.CharField()
    lulu_user           = forms.CharField()
    lulu_password       = forms.CharField()
    lulu_project        = forms.CharField()
    copyright_year      = forms.CharField()
    copyright_citation  = forms.CharField()
    lulu_license        = forms.CharField()
    lulu_access         = forms.CharField()
    lulu_allow_ratings  = forms.BooleanField()
    lulu_color          = forms.BooleanField()
    lulu_drm            = forms.BooleanField()
    lulu_paper_type     = forms.CharField()
    lulu_binding_type   = forms.CharField()
    lulu_language       = forms.CharField()
    lulu_keywords       = forms.CharField()
    lulu_currency_code  = forms.CharField()
    lulu_download_price = forms.CharField()
    lulu_print_price    = forms.CharField()
    description         = forms.CharField()
    authors             = forms.CharField()

    # advanced
    #
    license             = forms.ChoiceField(choices = get_license_choices(), initial = config.DEFAULT_LICENSE)
    toc_header          = forms.CharField()
    isbn                = forms.CharField()
    top_margin          = forms.CharField()
    side_margin         = forms.CharField()
    bottom_margin       = forms.CharField()
    gutter              = forms.CharField()
    columns             = forms.CharField()
    column_margin       = forms.CharField()
    grey_scale          = forms.BooleanField()
    #css_url             = forms.CharField() # css-url
    #font_list           = forms.CharField() # list
    #font_links          = forms.CharField() # list
    #css                 = forms.CharField(widget = forms.Textarea)
    rotate              = forms.BooleanField()
    html_template       = forms.CharField(widget = forms.Textarea)
    max_age             = forms.CharField() # max-age
    booki_group         = forms.CharField() # booki-group
    booki_user          = forms.CharField() # booki-user
    page_numbers        = forms.ChoiceField(choices = get_page_number_choices(), initial = config.DEFAULT_PAGE_NUMBER_OPTION)
    embed_fonts         = forms.BooleanField() # embed-fonts
    allow_breaks        = forms.BooleanField() # allow-breaks


__all__ = [ ObjaviForm ]
