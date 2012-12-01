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

from objavi import config
from objavi import form_config
from objavi import book_utils


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


class ServerChoiceField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        super(ServerChoiceField, self).__init__(
            required = True,
            choices = get_server_choices(),
            initial = config.DEFAULT_SERVER, *args, **kwargs)

    def valid_value(self, value):
        if super(ServerChoiceField, self).valid_value(value):
            return True
        elif book_utils.get_server_defaults(value):
            return True
        else:
            return False


class ObjaviForm(forms.Form):
    server              = ServerChoiceField()
    book                = forms.CharField(widget = forms.Select())
    title               = forms.CharField(required = False)
    mode                = forms.ChoiceField(choices = get_mode_choices(), initial = form_config.DEFAULT_PDF_TYPE)
    booksize            = forms.ChoiceField(choices = get_booksize_choices(), initial = config.DEFAULT_SIZE)
    page_width          = forms.FloatField(required = False)
    page_height         = forms.FloatField(required = False)
    cover_url           = forms.URLField(required = False)
    output_profile      = forms.CharField(required = False)
    output_format       = forms.CharField(required = False)

    # lulucom
    #
    to_lulu             = forms.BooleanField(required = False)
    lulu_api_key        = forms.CharField(required = False)
    lulu_user           = forms.CharField(required = False)
    lulu_password       = forms.CharField(required = False)
    lulu_project        = forms.CharField(required = False)
    copyright_year      = forms.CharField(required = False)
    copyright_citation  = forms.CharField(required = False)
    lulu_license        = forms.CharField(required = False)
    lulu_access         = forms.CharField(required = False)
    lulu_allow_ratings  = forms.BooleanField(required = False)
    lulu_color          = forms.BooleanField(required = False)
    lulu_drm            = forms.BooleanField(required = False)
    lulu_paper_type     = forms.CharField(required = False)
    lulu_binding_type   = forms.CharField(required = False)
    lulu_language       = forms.CharField(required = False)
    lulu_keywords       = forms.CharField(required = False)
    lulu_currency_code  = forms.CharField(required = False)
    lulu_download_price = forms.CharField(required = False)
    lulu_print_price    = forms.CharField(required = False)
    description         = forms.CharField(required = False)
    authors             = forms.CharField(required = False)

    # advanced
    #
    license             = forms.ChoiceField(choices = get_license_choices(), initial = config.DEFAULT_LICENSE)
    toc_header          = forms.CharField(required = False)
    isbn                = forms.CharField(required = False)
    top_margin          = forms.CharField(required = False)
    side_margin         = forms.CharField(required = False)
    bottom_margin       = forms.CharField(required = False)
    gutter              = forms.CharField(required = False)
    columns             = forms.CharField(required = False)
    column_margin       = forms.CharField(required = False)
    grey_scale          = forms.BooleanField(required = False)
    css_url             = forms.CharField(required = False)
    css                 = forms.CharField(widget = forms.Textarea, required = False)
    rotate              = forms.BooleanField(required = False)
    html_template       = forms.CharField(widget = forms.Textarea, required = False)
    max_age             = forms.FloatField(required = False)
    booki_group         = forms.CharField(required = False)
    booki_user          = forms.CharField(required = False)
    page_numbers        = forms.ChoiceField(choices = get_page_number_choices(), initial = config.DEFAULT_PAGE_NUMBER_OPTION)
    embed_fonts         = forms.BooleanField(required = False)
    allow_breaks        = forms.BooleanField(required = False)

    def clean(self):
        cleaned_data = self.cleaned_data

        booksize    = cleaned_data["booksize"]
        page_width  = cleaned_data["page_width"]
        page_height = cleaned_data["page_height"]

        if booksize == "custom":
            msg = u"custom book size requires this parameter"

            if not page_width:
                self._errors["page_width"] = self.error_class([msg])
                del self.cleaned_data["page_width"]

            if not page_height:
                self._errors["page_height"] = self.error_class([msg])
                del self.cleaned_data["page_height"]

        return cleaned_data


ESPRI_SOURCES = (
    ("url", "URI (of an epub"),
    ("archive.org", "Internet Archive ID"),
)

class EspriForm(forms.Form):
    book   = forms.CharField(required = True)
    source = forms.ChoiceField(choices = ESPRI_SOURCES, initial = ESPRI_SOURCES[0][0], widget = forms.RadioSelect)


__all__ = [ObjaviForm, EspriForm]
