# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
from os.path import basename
import re
import csv
import random
import string
import json
import zipfile
import tempfile
import shutil
import requests
import django
import xml.etree.ElementTree as etree
import operator

try:
    from email.utils import formatdate
except ImportError:  # Python 2
    from email.Utils import formatdate
from requests import HTTPError
from django.shortcuts import render
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         )
from django.conf import settings
from django import forms

from django.template.loader import get_template

from openquakeplatform import __version__ as oqp_version
from openquakeplatform.settings import WEBUIURL, TIME_INVARIANT_OUTPUTS
try:
    from openquakeplatform.settings import GEM_IPT_CLEAN_ALL
except Exception:
    GEM_IPT_CLEAN_ALL = True

from openquakeplatform.python3compat import unicode, encode, decode
from openquakeplatform.utils import oq_is_qgis_browser
from openquake.ipt.build_rupture_plane import get_rupture_surface_round
from packaging.version import Version

from openquake.ipt.multienv_common import VolConst
from openquake.ipt.common import (
    get_full_path, zwrite_or_collect, zwrite_or_collect_str, bool2s)


from openquake.ipt.converters import (
    gem_input_converter, gem_shapefile_get_fields)

# from pyproj import Proj, transform

django_version = django.get_version()

if Version(django_version) < Version('1.8'):
    from django.template import Context

ALLOWED_DIR = {
    'rupture_file': ('xml',),
    'list_of_sites': ('csv',),
    'gmf_file': ('xml', 'csv'),
    'exposure_csv': ('csv',),
    'exposure_model': ('xml', 'zip'),
    'site_conditions': ('csv', 'xml',),
    'imt': ('xml',),
    'fragility_model': ('xml',),
    'fragility_cons': ('xml',),
    'vulnerability_model': ('xml',),
    'gsim_logic_tree_file': ('xml',),
    'source_model_logic_tree_file': ('xml',),
    'source_model_file': ('xml',),
    'taxonomy_mapping': ('csv',),

    'ashfall_file': {
        VolConst.ty_text: ('asc', 'txt'),
        VolConst.ty_open: ('csv',),
        VolConst.ty_shap: ('zip',)
    },
    'lavaflow_file': {
        VolConst.ty_twkt: ('asc',),
        VolConst.ty_open: ('csv',),
        VolConst.ty_swkt: ('zip',)
    },
    'lahar_file': {
        VolConst.ty_twkt: ('asc', 'txt'),
        VolConst.ty_open: ('csv',),
        VolConst.ty_swkt: ('zip',)
    },
    'pyroclasticflow_file': {
        VolConst.ty_twkt: ('-00001',),
        VolConst.ty_open: ('csv',),
        VolConst.ty_swkt: ('zip',)
    },
}

DEFAULT_SUBTYPE = {'ashfall_file': VolConst.ty_text,
                   'lavaflow_file': VolConst.ty_twkt,
                   'lahar_file': VolConst.ty_twkt,
                   'pyroclasticflow_file': VolConst.ty_twkt,
                   }


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def _get_error_line(exc_msg):
    # check if the exc_msg contains a line number indication
    search_match = re.search(r'line \d+', exc_msg)
    if search_match:
        error_line = int(search_match.group(0).split()[1])
    else:
        error_line = None
    return error_line


JSON = 'application/json'


def _make_response(error_msg, error_line, valid):
    response_data = dict(error_msg=error_msg,
                         error_line=error_line,
                         valid=valid)
    return HttpResponse(
        content=json.dumps(response_data), content_type=JSON)


def site_conditions_check(full_path):
    '''
    check site condition file and return a tuple (Bool, String_descr)
    '''
    with enc_open(full_path, encoding='utf-8-sig') as csv_fp:
        reader = csv.DictReader(csv_fp)
        for field in ['lon', 'lat']:
            if field not in reader.fieldnames:
                return (False, "'%s' field not found" % field)

        lonlat = set()
        for i, row in enumerate(reader, start=1):
            lon = round(float(row['lon']), 5)
            lat = round(float(row['lat']), 5)
            lonlat.add((lon, lat))
            if len(lonlat) < i:
                return (False, "%f, %f rounded coords at line"
                        " %d already found" % (lon, lat, i))

            if lon > 180. or lon < -180.:
                return (False, "lon %f out of range ±180° at line %d" %
                        lon, i)
            if lat > 90. or lat < -90.:
                return (False, "lat %f out of range ±90° at line %d" %
                        lat, i)
        return (True, '')


def taxonomy_mapping_check(full_path):
    '''
    check taxonomy mapping file and return a tuple (Bool, String_descr)
    '''
    with enc_open(full_path, encoding='utf-8-sig') as csv_fp:
        reader = csv.DictReader(csv_fp)
        for field in ['taxonomy', 'conversion', 'weight']:
            if field not in reader.fieldnames:
                return (False, "'%s' field not found" % field)

        grp = {}

        for row in reader:
            key = row['taxonomy']
            if key not in grp:
                grp[key] = 0.0
            grp[key] += float(row['weight'])

        for key, taxonomy_sum in grp.items():
            if abs(taxonomy_sum - 1.0) > 1e-12:
                return (False,
                        ("abs(1.0 - (sum of weights)) exceed 1e-12"
                         " (%1.2e) for taxonomy '%s'") % (
                            abs(1.0 - taxonomy_sum), key))

        csv_fp.seek(0)
        reader = csv.DictReader(csv_fp)
        maps = set()
        maps_n = 0
        for i, row in enumerate(reader, start=1):
            maps.add((row['taxonomy'], row['conversion']))
            maps_n += 1
            if len(maps) < i:
                return (False, "pair (%s, %s) at line %d already found" % (
                    row['taxonomy'], row['conversion'], i))
        return (True, '')


def _do_validate_nrml(xml_text):
    data = dict(xml_text=xml_text)
    ret = requests.post('%sv1/valid/' % WEBUIURL, data)

    if ret.status_code != 200:
        raise HTTPError({'message': "URL '%s' unreachable", 'lineno': -1})

    ret_dict = json.loads(decode(ret.content))

    if not ret_dict['valid']:
        raise ValueError({'message': ret_dict.get('error_msg', ''),
                          'lineno': ret_dict.get('error_line', -1)})


def validate_nrml(request):
    """
    Leverage oq-risklib to check if a given XML text is a valid NRML

    :param request:
        a `django.http.HttpRequest` object containing the mandatory
        parameter 'xml_text': the text of the XML to be validated as NRML

    :returns: a JSON object, containing:
        * 'valid': a boolean indicating if the provided text is a valid NRML
        * 'error_msg': the error message, if any error was found
                       (None otherwise)
        * 'error_line': line of the given XML where the error was found
                        (None if no error was found or if it was not a
                        validation error)
    """
    xml_text = request.POST.get('xml_text')
    if not xml_text:
        return HttpResponseBadRequest(
            'Please provide the "xml_text" parameter')
    try:
        xml_text = xml_text.replace('\r\n', '\n').replace('\r', '\n')
        _do_validate_nrml(xml_text)
    except (HTTPError, ValueError) as e:
        exc = e.args[0]
        return _make_response(error_msg=exc['message'],
                              error_line=exc['lineno'],
                              valid=False)
    except Exception as exc:
        # get the exception message
        exc_msg = exc.args[0]
        if isinstance(exc_msg, bytes):
            exc_msg = decode(exc_msg)   # make it a unicode object
        elif isinstance(exc_msg, unicode):
            pass
        else:
            # if it is another kind of object, it is not obvious a priori how
            # to extract the error line from it
            # but we can attempt anyway to extract it
            error_line = _get_error_line(unicode(exc_msg))
            return _make_response(
                error_msg=unicode(exc_msg), error_line=error_line,
                valid=False)
        error_msg = exc_msg
        error_line = _get_error_line(exc_msg)
        return _make_response(
            error_msg=error_msg, error_line=error_line, valid=False)
    else:
        return _make_response(error_msg=None, error_line=None, valid=True)


def sendback_nrml(request):
    """
    Leverage oq-risklib to check if a given XML text is a valid NRML. If it is,
    save it as a XML file.

    :param request:
        a `django.http.HttpRequest` object containing the mandatory
        parameter 'xml_text': the text of the XML to be validated as NRML
        and the optional parameter 'func_type': the function type (known types
        are ['exposure', 'fragility', 'vulnerability', 'site'])

    :returns: an XML file, containing the given NRML text
    """
    file_list = []
    content = 'content not yet set'
    xml_text = request.POST.get('xml_text')
    func_type = request.POST.get('func_type')
    if not xml_text:
        return HttpResponseBadRequest(
            'Please provide the "xml_text" parameter')
    known_func_types = [
        'exposure', 'fragility', 'consequence', 'vulnerability', 'site',
        'earthquake_rupture']
    try:
        xml_text = xml_text.replace('\r\n', '\n').replace('\r', '\n')
        _do_validate_nrml(xml_text)
        if func_type == u'exposure':
            ns = {'oq': 'http://openquake.org/xmlns/nrml/0.4'}

            root = etree.fromstring(encode(xml_text))
            assets = root.findall('.//oq:assets/oq:asset', ns)

            if not assets:
                assets = root.findall('.//oq:assets', ns)
                file_list = assets[0].text.strip().split()
                file_list = [os.path.join('exposure_csv', f) for f
                             in file_list]
    except Exception:
        return HttpResponseBadRequest(
            'Invalid NRML')

    if file_list:
        if getattr(settings, 'AUTH_ONLY', False):
            userid = str(request.user.id)
        else:
            userid = ''
        namespace = request.resolver_match.namespace

        ext = 'zip'
        (fd, fname) = tempfile.mkstemp(
            suffix='.zip', prefix='ipt_', dir=tempfile.gettempdir())
        os.close(fd)
        file_collect = None
        z = zipfile.ZipFile(fname, 'w', zipfile.ZIP_DEFLATED,
                            allowZip64=True)
        for csv_fname in file_list:
            # print(csv_fname)
            zwrite_or_collect(z, userid, namespace,
                              csv_fname, file_collect)

        zwrite_or_collect_str(z, 'exposure.xml', xml_text, file_collect)
        z.close()
        to_delete = False
        with open(fname, 'rb') as content_file:
            content = content_file.read()
            to_delete = True
        if to_delete and GEM_IPT_CLEAN_ALL:
            os.unlink(fname)
    else:
        content = xml_text
        ext = 'xml'

    if func_type in known_func_types:
        filename = func_type + '_model.%s' % ext
    else:
        filename = 'unknown_model.%s' % ext

    resp = HttpResponse(content=content,
                        content_type='application/%s' % ext)
    resp['Content-Description'] = 'File Transfer'
    resp['Content-Length'] = len(content)
    resp['Content-Disposition'] = (
        'attachment; filename="' + filename + '"')
    return resp


def sendback_er_rupture_surface(request):
    mag = request.POST.get('mag')
    hypo_lat = request.POST.get('hypo_lat')
    hypo_lon = request.POST.get('hypo_lon')
    hypo_depth = request.POST.get('hypo_depth')
    strike = request.POST.get('strike')
    dip = request.POST.get('dip')
    rake = request.POST.get('rake')

    if (mag is None or hypo_lat is None or hypo_lon is None or
            hypo_depth is None or strike is None or dip is None or
            rake is None):
        ret = {'ret': 1, 'ret_s': 'incomplete arguments'}
    else:
        try:
            mag = float(mag)
            hypo_lat = float(hypo_lat)
            hypo_lon = float(hypo_lon)
            hypo_depth = float(hypo_depth)
            strike = float(strike)
            dip = float(dip)
            rake = float(rake)

            ret = get_rupture_surface_round(mag, {"lon": hypo_lon,
                                                  "lat": hypo_lat,
                                                  "depth": hypo_depth},
                                            strike, dip, rake)
            ret['ret'] = 0
            ret['ret_s'] = 'success'
        except Exception as exc:
            ret = {'ret': 2, 'ret_s': 'exception raised: %s' % exc}

    return HttpResponse(json.dumps(ret), content_type="application/json")


class ButtonWidget(forms.widgets.TextInput):
    template_name = 'widgets/button_widget.html'

    def __init__(self, is_bridged=False, name=None, *args, **kwargs):
        super(ButtonWidget, self).__init__(*args, **kwargs)
        self.gem_is_bridged = is_bridged
        self.gem_name = name

    if Version(django_version) > Version('2.0'):
        def get_context(self, name, value, attrs):
            context = super().get_context(name, value, attrs)
            context['widget']['gem_name'] = self.gem_name
            context['widget']['gem_is_bridged'] = self.gem_is_bridged
            return context

    else:
        def render(self, name, value, attrs=None):
            t = get_template(self.template_name)
            if Version(django_version) >= Version('1.8'):
                html = t.render(
                    {'widget': {'gem_name': self.gem_name,
                                'gem_is_bridged': self.gem_is_bridged}})
            else:
                html = t.render(Context(
                    {'widget': {
                        'gem_name': self.gem_name,
                        'gem_is_bridged': self.gem_is_bridged}}))
            return html


class ButtonField(forms.Field):
    def __init__(self, is_bridged=False, name=None, *args, **kwargs):
        super(ButtonField, self).__init__(*args, **kwargs)
        self.widget = ButtonWidget(is_bridged, name)


class FileUpload(forms.Form):
    def __init__(self, *args, **kwargs):
        self.accept = kwargs.pop('accept')
        self.with_subtype = kwargs.pop('with_subtype', False)
        super(FileUpload, self).__init__(*args, **kwargs)
        self.fields['file_upload'].widget = forms.ClearableFileInput(
            attrs={'class': 'hide_file_upload',
                   'data-gem-with-subtype': (
                       'true' if self.with_subtype else 'false'),
                   'accept': self.accept})

    file_upload = forms.FileField(allow_empty_file=True)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class FileUploadMulti(forms.Form):
    def __init__(self, *args, **kwargs):
        self.accept = kwargs.pop('accept')
        self.with_subtype = kwargs.pop('with_subtype', False)
        super(FileUploadMulti, self).__init__(*args, **kwargs)
        self.fields['file_upload'].widget = MultipleFileInput(
            attrs={'class': 'hide_file_upload', 'multiple': True,
                   'data-gem-with-subtype': (
                       'true' if self.with_subtype else 'false'),
                   'accept': self.accept})

    file_upload = forms.FileField(allow_empty_file=True)


class FilePathFieldByUser(forms.ChoiceField):
    def __init__(self, is_bridged, userid, subdir, namespace, match=None,
                 recursive=False, allow_files=True,
                 allow_folders=False, required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        self.is_bridged = is_bridged
        self.match = match
        self.recursive = recursive
        self.subdir = subdir
        self.userid = str(userid)
        self.namespace = namespace
        self.allow_files, self.allow_folders = allow_files, allow_folders
        super(FilePathFieldByUser, self).__init__(
            choices=(), required=required, widget=widget, label=label,
            initial=initial, help_text=help_text, *args, **kwargs)

        if self.required:
            self.choices = []
        else:
            self.choices = [("", "---------")]

        if self.is_bridged is True:
            self.widget.choices = self.choices
            self.widget.attrs['data-gem-subdir'] = self.subdir
            return

        if self.match is not None:
            self.match_re = re.compile(self.match)

        normalized_path = get_full_path(self.userid, self.namespace,
                                        self.subdir)
        user_allowed_path = get_full_path(self.userid, self.namespace)
        if not normalized_path.startswith(user_allowed_path):
            raise LookupError('Unauthorized path: "%s"' % normalized_path)

        if recursive:
            for root, dirs, files in sorted(os.walk(normalized_path)):
                if self.allow_files:
                    for f in files:
                        if self.match is None or self.match_re.search(f):
                            filename = os.path.basename(f)
                            subdir_and_name = os.path.join(subdir, filename)
                            self.choices.append((subdir_and_name, filename))
                if self.allow_folders:
                    for f in dirs:
                        if f == '__pycache__':
                            continue
                        if self.match is None or self.match_re.search(f):
                            f = os.path.join(root, f)
                            filename = os.path.basename(f)
                            subdir_and_name = os.path.join(subdir, filename)
                            self.choices.append((subdir_and_name, filename))
        else:
            try:
                for f in sorted(os.listdir(normalized_path)):
                    if f == '__pycache__':
                        continue
                    full_file = os.path.normpath(
                        os.path.join(normalized_path, f))
                    if (((self.allow_files and os.path.isfile(full_file)) or
                            (self.allow_folders and os.path.isdir(
                                full_file))) and (self.match is None or
                                                  self.match_re.search(f))):
                        self.choices.append((f, f))
            except OSError:
                pass

        self.choices.sort(key=operator.itemgetter(1))

        self.widget.choices = self.choices


def filehtml_create(is_bridged, suffix, userid, namespace,
                    is_multiple=False, name=None):
    if (suffix not in ALLOWED_DIR):
        raise KeyError("suffix (%s) not in allowed list" % suffix)

    if name is None:
        name = suffix
    name = name.replace('_', '-')

    if not is_bridged:
        normalized_path = get_full_path(userid, namespace, suffix)
        user_allowed_path = get_full_path(userid, namespace)
        if not normalized_path.startswith(user_allowed_path):
            raise LookupError('Unauthorized path: "%s"' % normalized_path)
        if not os.path.isdir(normalized_path):
            try:
                os.makedirs(normalized_path)
            except OSError:
                fullpa = normalized_path
                print("makedirs failed, full path: [%s]" % fullpa)
                while fullpa != "/":
                    os.system("ls -ld '%s' 1>&2" % fullpa)
                    fullpa = os.path.dirname(fullpa)
                raise

    if isinstance(ALLOWED_DIR[suffix], dict):
        ext_list = ALLOWED_DIR[suffix][DEFAULT_SUBTYPE[suffix]]
        with_subtype = True
    else:
        ext_list = ALLOWED_DIR[suffix]
        with_subtype = False

    match = "|".join(
        [".*\\.%s$" % ext for ext in ext_list])

    class FileHtml(forms.Form):
        def __init__(self, *args, **kwargs):
            super(FileHtml, self).__init__(*args, **kwargs)
            self.gem_ext_list = list(ext_list)

        def gem_accepted(self):
            return ', '.join(['.' + x for x in self.gem_ext_list])

        def gem_fileupload(self):
            if is_multiple:
                return FileUploadMulti(
                    accept=self.gem_accepted(), with_subtype=with_subtype)
            else:
                return FileUpload(
                    accept=self.gem_accepted(), with_subtype=with_subtype)

        file_html = FilePathFieldByUser(
            is_bridged=is_bridged,
            userid=userid,
            subdir=suffix,
            namespace=namespace,
            match=match,
            recursive=True,
            required=is_multiple,
            widget=(forms.fields.SelectMultiple if is_multiple else None))
        new_btn = ButtonField(is_bridged=is_bridged, name=name)
    fh = FileHtml()

    return fh, fh.gem_fileupload()


def _get_available_gsims():

    ret = requests.get('%sv1/available_gsims' % WEBUIURL)

    if ret.status_code != 200:
        raise HTTPError({'message': "URL '%s' unreachable" % WEBUIURL})

    ret_list = json.loads(decode(ret.content))

    return [gsim for gsim in ret_list]


def view(request, **kwargs):
    is_qgis_browser = oq_is_qgis_browser(request)

    if getattr(settings, 'AUTH_ONLY', False):
        userid = str(request.user.id)
    else:
        userid = ''
    namespace = request.resolver_match.namespace
    gmpe = _get_available_gsims()

    rupture_file_html, rupture_file_upload = filehtml_create(
        is_qgis_browser, 'rupture_file', userid, namespace)

    list_of_sites_html, list_of_sites_upload = filehtml_create(
        is_qgis_browser, 'list_of_sites', userid, namespace)

    gmf_file_html, gmf_file_upload = filehtml_create(
        is_qgis_browser, 'gmf_file', userid, namespace)

    exposure_model_html, exposure_model_upload = filehtml_create(
        is_qgis_browser, 'exposure_model', userid, namespace)

    taxonomy_mapping_html, taxonomy_mapping_upload = filehtml_create(
        is_qgis_browser, 'taxonomy_mapping', userid, namespace)

    exposure_csv_html, exposure_csv_upload = filehtml_create(
        is_qgis_browser, 'exposure_csv', userid, namespace,
        is_multiple=True)

    fm_structural_html, fm_structural_upload = filehtml_create(
        is_qgis_browser, 'fragility_model', userid, namespace,
        name='fm_structural')
    fm_nonstructural_html, fm_nonstructural_upload = filehtml_create(
        is_qgis_browser, 'fragility_model', userid, namespace,
        name='fm_nonstructural')
    fm_contents_html, fm_contents_upload = filehtml_create(
        is_qgis_browser, 'fragility_model', userid, namespace,
        name='fm_contents')
    fm_businter_html, fm_businter_upload = filehtml_create(
        is_qgis_browser, 'fragility_model', userid, namespace,
        name='fm_businter')
    fm_ashfall_file_html, fm_ashfall_file_upload = filehtml_create(
        is_qgis_browser, 'fragility_model', userid, namespace,
        name='fm_ashfall_file')

    fm_structural_cons_html, fm_structural_cons_upload = filehtml_create(
        is_qgis_browser, 'fragility_cons', userid, namespace,
        name='fm_structural_cons')
    fm_nonstructural_cons_html, fm_nonstructural_cons_upload = filehtml_create(
        is_qgis_browser, 'fragility_cons', userid, namespace,
        name='fm_nonstructural_cons')
    fm_contents_cons_html, fm_contents_cons_upload = filehtml_create(
        is_qgis_browser, 'fragility_cons', userid, namespace,
        name='fm_contents_cons')
    fm_businter_cons_html, fm_businter_cons_upload = filehtml_create(
        is_qgis_browser, 'fragility_cons', userid, namespace,
        name='fm_businter_cons')
    fm_ashfall_cons_html, fm_ashfall_cons_upload = filehtml_create(
        is_qgis_browser, 'fragility_cons', userid, namespace,
        name='fm_ashfall_cons')

    vm_structural_html, vm_structural_upload = filehtml_create(
        is_qgis_browser, 'vulnerability_model', userid, namespace,
        name='vm_structural')
    vm_nonstructural_html, vm_nonstructural_upload = filehtml_create(
        is_qgis_browser, 'vulnerability_model', userid, namespace,
        name='vm_nonstructural')
    vm_contents_html, vm_contents_upload = filehtml_create(
        is_qgis_browser, 'vulnerability_model', userid, namespace,
        name='vm_contents')
    vm_businter_html, vm_businter_upload = filehtml_create(
        is_qgis_browser, 'vulnerability_model', userid, namespace,
        name='vm_businter')
    vm_occupants_html, vm_occupants_upload = filehtml_create(
        is_qgis_browser, 'vulnerability_model', userid, namespace,
        name='vm_occupants')

    site_conditions_html, site_conditions_upload = filehtml_create(
        is_qgis_browser, 'site_conditions', userid, namespace)

    gsim_logic_tree_file_html, gsim_logic_tree_file_upload = filehtml_create(
        is_qgis_browser, 'gsim_logic_tree_file', userid, namespace)

    (source_model_logic_tree_file_html,
     source_model_logic_tree_file_upload) = filehtml_create(
        is_qgis_browser, 'source_model_logic_tree_file', userid, namespace)

    source_model_file_html, source_model_file_upload = filehtml_create(
        is_qgis_browser, 'source_model_file', userid, namespace,
        is_multiple=True)

    ashfall_file_html, ashfall_file_upload = filehtml_create(
        is_qgis_browser, 'ashfall_file', userid, namespace)

    lavaflow_file_html, lavaflow_file_upload = filehtml_create(
        is_qgis_browser, 'lavaflow_file', userid, namespace)

    lahar_file_html, lahar_file_upload = filehtml_create(
        is_qgis_browser, 'lahar_file', userid, namespace)

    pyroclasticflow_file_html, pyroclasticflow_file_upload = filehtml_create(
        is_qgis_browser, 'pyroclasticflow_file', userid, namespace)

    multi_accept = {}
    for dkey in ALLOWED_DIR:
        dval = ALLOWED_DIR[dkey]
        if isinstance(dval, dict):
            multi_accept[dkey] = dval

    render_dict = dict(
        gem_path_sep=os.path.sep,
        oqp_version_maj=oqp_version.split('.')[0],
        g_gmpe=json.dumps(gmpe),
        rupture_file_html=rupture_file_html,
        rupture_file_upload=rupture_file_upload,
        list_of_sites_html=list_of_sites_html,
        list_of_sites_upload=list_of_sites_upload,
        gmf_file_html=gmf_file_html,
        gmf_file_upload=gmf_file_upload,
        exposure_model_html=exposure_model_html,
        exposure_model_upload=exposure_model_upload,
        taxonomy_mapping_upload=taxonomy_mapping_upload,
        taxonomy_mapping_html=taxonomy_mapping_html,
        exposure_csv_html=exposure_csv_html,
        exposure_csv_upload=exposure_csv_upload,
        fm_structural_html=fm_structural_html,
        fm_structural_upload=fm_structural_upload,
        fm_nonstructural_html=fm_nonstructural_html,
        fm_nonstructural_upload=fm_nonstructural_upload,
        fm_contents_html=fm_contents_html,
        fm_contents_upload=fm_contents_upload,
        fm_businter_html=fm_businter_html,
        fm_businter_upload=fm_businter_upload,

        fm_structural_cons_html=fm_structural_cons_html,
        fm_structural_cons_upload=fm_structural_cons_upload,
        fm_nonstructural_cons_html=fm_nonstructural_cons_html,
        fm_nonstructural_cons_upload=fm_nonstructural_cons_upload,
        fm_contents_cons_html=fm_contents_cons_html,
        fm_contents_cons_upload=fm_contents_cons_upload,
        fm_businter_cons_html=fm_businter_cons_html,
        fm_businter_cons_upload=fm_businter_cons_upload,

        vm_structural_html=vm_structural_html,
        vm_structural_upload=vm_structural_upload,
        vm_nonstructural_html=vm_nonstructural_html,
        vm_nonstructural_upload=vm_nonstructural_upload,
        vm_contents_html=vm_contents_html,
        vm_contents_upload=vm_contents_upload,
        vm_businter_html=vm_businter_html,
        vm_businter_upload=vm_businter_upload,
        vm_occupants_html=vm_occupants_html,
        vm_occupants_upload=vm_occupants_upload,

        site_conditions_html=site_conditions_html,
        site_conditions_upload=site_conditions_upload,
        gsim_logic_tree_file_html=gsim_logic_tree_file_html,
        gsim_logic_tree_file_upload=gsim_logic_tree_file_upload,

        source_model_logic_tree_file_html=(
            source_model_logic_tree_file_html),
        source_model_logic_tree_file_upload=(
            source_model_logic_tree_file_upload),

        source_model_file_html=source_model_file_html,
        source_model_file_upload=source_model_file_upload,

        ashfall_file_html=ashfall_file_html,
        ashfall_file_upload=ashfall_file_upload,

        lavaflow_file_html=lavaflow_file_html,
        lavaflow_file_upload=lavaflow_file_upload,

        lahar_file_html=lahar_file_html,
        lahar_file_upload=lahar_file_upload,

        pyroclasticflow_file_html=pyroclasticflow_file_html,
        pyroclasticflow_file_upload=pyroclasticflow_file_upload,

        fm_ashfall_file_html=fm_ashfall_file_html,
        fm_ashfall_file_upload=fm_ashfall_file_upload,

        fm_ashfall_cons_html=fm_ashfall_cons_html,
        fm_ashfall_cons_upload=fm_ashfall_cons_upload,
        multi_accept=json.dumps(multi_accept),
    )

    if is_qgis_browser:
        render_dict.update({'allowed_dir': ALLOWED_DIR.keys()})

    return render(request, "ipt/ipt.html", render_dict)


def upload(request, **kwargs):
    ret = {}

    if 'target' not in kwargs:
        ret['ret'] = 3
        ret['ret_msg'] = 'Malformed request.'
        return HttpResponse(json.dumps(ret), content_type="application/json")

    target = kwargs['target']
    if target not in ALLOWED_DIR:
        ret['ret'] = 4
        ret['ret_msg'] = 'Unknown target "' + target + '".'
        return HttpResponse(json.dumps(ret), content_type="application/json")

    if is_ajax(request):
        if request.method == 'POST':
            class FileUpload(forms.Form):
                file_upload = forms.FileField(allow_empty_file=True)
            form = FileUpload(request.POST, request.FILES)

            if isinstance(ALLOWED_DIR[target], dict):
                if 'gem-subtype' not in request.POST:
                    ret['ret'] = 5
                    ret['ret_msg'] = 'Target ' + target + ' requires subtype.'
                    return HttpResponse(json.dumps(ret),
                                        content_type="application/json")

                subtype = request.POST['gem-subtype']
                ext_list = ALLOWED_DIR[target][subtype]
            else:
                ext_list = ALLOWED_DIR[target]

            if not form.is_valid():
                if getattr(settings, 'AUTH_ONLY', False):
                    userid = str(request.user.id)
                else:
                    userid = ''
                namespace = request.resolver_match.namespace

                suffix = target
                match = "|".join(
                    [".*\\.%s$" % ext for ext in ext_list])

                class FileHtml(forms.Form):
                    file_html = FilePathFieldByUser(
                        is_bridged=False,
                        userid=userid,
                        subdir=suffix,
                        namespace=namespace,
                        match=match,
                        recursive=True)

                fileslist = FileHtml()

                ret['ret'] = 0
                ret['items'] = fileslist.fields['file_html'].choices
                ret['ret_msg'] = 'List updated'

                # Redirect to the document list after POST
                return HttpResponse(json.dumps(ret),
                                    content_type="application/json")

            for fi_up in request.FILES.getlist('file_upload'):
                if (not fi_up.name.endswith(
                        tuple('.%s' % _ext for _ext in ext_list))):
                    ret['ret'] = 1
                    if len(ext_list) == 1:
                        ret['ret_msg'] = (
                            'File uploaded %s isn\'t an .%s file.' %
                            (fi_up.name, ext_list[0].upper()))
                    else:
                        ls = ', '.join(['.%s' % ext.upper()
                                        for ext in ext_list])
                        ret['ret_msg'] = ('Type of uploaded file not in the '
                                          'recognized list [%s].' % ls)

                    # Redirect to the document list after POST
                    return HttpResponse(json.dumps(ret),
                                        content_type="application/json")

            if getattr(settings, 'AUTH_ONLY', False):
                userid = str(request.user.id)
            else:
                userid = ''
            namespace = request.resolver_match.namespace
            user_dir = get_full_path(userid, namespace)
            bname = os.path.join(user_dir, target)
            # check if the directory exists (or create it)
            if not os.path.exists(bname):
                os.makedirs(bname)

            files_list = []
            for fi_up in request.FILES.getlist('file_upload'):
                full_path = os.path.join(
                    bname, fi_up.name)
                overwrite_existing_files = request.POST.get(
                    'overwrite_existing_files', True)
                if not overwrite_existing_files:
                    modified_path = full_path
                    n = 0
                    while os.path.isfile(modified_path):
                        n += 1
                        f_name, f_ext = os.path.splitext(full_path)
                        modified_path = '%s_%s%s' % (f_name, n, f_ext)
                    full_path = modified_path
                if not os.path.normpath(full_path).startswith(user_dir):
                    ret['ret'] = 5
                    ret['ret_msg'] = 'Not authorized to write the file.'
                    return HttpResponse(json.dumps(ret),
                                        content_type="application/json")
                with open(full_path, "wb") as f:
                    f.write(encode(fi_up.read()))
                files_list.append((os.path.basename(fi_up.name),
                                   os.path.basename(full_path)))
                if (os.path.basename(os.path.dirname(full_path)) ==
                        u'site_conditions' and full_path.endswith('.csv')):
                    check_ret, check_desc = site_conditions_check(full_path)
                    if not check_ret:
                        ret['ret'] = 6
                        ret['ret_msg'] = (
                            'Error in "%s" file: %s.' % (
                                os.path.basename(full_path), check_desc))

                        return HttpResponse(json.dumps(ret),
                                            content_type="application/json")
                elif (os.path.basename(os.path.dirname(full_path)) ==
                        u'taxonomy_mapping' and full_path.endswith('.csv')):
                    check_ret, check_desc = taxonomy_mapping_check(full_path)
                    if not check_ret:
                        ret['ret'] = 6
                        ret['ret_msg'] = (
                            'Error in "%s" file: %s.' % (
                                os.path.basename(full_path), check_desc))

                        return HttpResponse(json.dumps(ret),
                                            content_type="application/json")

            suffix = target
            match = "|".join(
                [".*\\.%s$" % ext for ext in ext_list])

            class FileHtml(forms.Form):
                file_html = FilePathFieldByUser(
                    is_bridged=False,
                    userid=userid,
                    subdir=suffix,
                    namespace=namespace,
                    match=match,
                    recursive=True)

            fileslist = FileHtml()

            ret['ret'] = 0
            ret['items'] = fileslist.fields['file_html'].choices
            changed_msg = ''
            ret['selected'] = []
            glue = ''
            ret['ret_msg'] = ''
            for file_name in files_list:
                ret['selected'].append(os.path.join(target, file_name[1]))

                if file_name[0] != file_name[1]:
                    changed_msg = ' (Renamed into %s)' % file_name[1]
                ret['ret_msg'] += ('%sFile %s uploaded successfully.%s' %
                                   (glue, file_name[0], changed_msg))
                glue = '<br/>'

            # Redirect to the document list after POST
            return HttpResponse(json.dumps(ret),
                                content_type="application/json")
    ret['ret'] = 2
    ret['ret_msg'] = 'Please provide e file.'

    return HttpResponse(json.dumps(ret), content_type="application/json")


def exposure_model_prep_sect(data, z, is_regcons, userid, namespace,
                             file_collect, save_files=True,
                             spec_ass_haz_dists=()):
    jobini = "\n[Exposure model]\n"
    #           ################

    exp_head, exp_sep, exp_tail = data['exposure_model'].rpartition('.')
    exposure_model = data['exposure_model']

    jobini += "exposure_file = %s\n" % basename(exposure_model)
    if save_files is True:
        zwrite_or_collect(z, userid, namespace, data['exposure_model'],
                          file_collect)
    if is_regcons:
        if data['asset_hazard_distance_enabled'] is True:
            jobini += "asset_hazard_distance = {"
            for spec in spec_ass_haz_dists:
                jobini += "'%s': %s, " % (spec[0], spec[1])
            jobini += "'default': %s}\n" % data['asset_hazard_distance']
        elif spec_ass_haz_dists:
            jobini += "asset_hazard_distance = {"
            for spec in spec_ass_haz_dists:
                jobini += "'%s': %s, " % (spec[0], spec[1])
            jobini += "}\n"

    if data['taxonomy_mapping_choice'] is True:
        tam_head, tam_sep, tam_tail = data['taxonomy_mapping'].rpartition('.')
        taxonomy_mapping = data['taxonomy_mapping']

        jobini += "taxonomy_mapping_csv = %s\n" % basename(taxonomy_mapping)
        if save_files is True:
            zwrite_or_collect(z, userid, namespace, data['taxonomy_mapping'],
                              file_collect)

    return jobini


def vulnerability_model_prep_sect(data, z, userid, namespace, file_collect,
                                  save_files=True):
    jobini = "\n[Vulnerability model]\n"
    #            #####################
    descr = {'structural': 'structural', 'nonstructural': 'nonstructural',
             'contents': 'contents', 'businter': 'business_interruption',
             'occupants': 'occupants'}
    for losslist in ['structural', 'nonstructural', 'contents', 'businter',
                     'occupants']:
        if data['vm_loss_%s_choice' % losslist] is True:
            jobini += "%s_vulnerability_file = %s\n" % (
                descr[losslist], basename(data['vm_loss_' + losslist]))
            if save_files is True:
                zwrite_or_collect(z, userid, namespace,
                                  data['vm_loss_%s' % losslist],
                                  file_collect)

    return jobini


def site_conditions_prep_sect(data, z, userid, namespace, file_collect):
    jobini = "\n[Site conditions]\n"
    #           #################

    if data['site_conditions_choice'] == 'from-file':
        jobini += ("site_model_file = %s\n" %
                   basename(data['site_model_file']))
        zwrite_or_collect(z, userid, namespace, data['site_model_file'],
                          file_collect)
    elif data['site_conditions_choice'] == 'uniform-param':
        jobini += "reference_vs30_value = %s\n" % data['reference_vs30_value']
        jobini += "reference_vs30_type = %s\n" % data['reference_vs30_type']
        jobini += ("reference_depth_to_2pt5km_per_sec = %s\n" %
                   data['reference_depth_to_2pt5km_per_sec'])
        jobini += ("reference_depth_to_1pt0km_per_sec = %s\n" %
                   data['reference_depth_to_1pt0km_per_sec'])
    return jobini


def scenario_prepare(request, **kwargs):
    ret = {}

    if request.POST.get('data', '') == '':
        ret['ret'] = 1
        ret['msg'] = 'Malformed request.'
        return HttpResponse(json.dumps(ret), content_type="application/json")

    if getattr(settings, 'AUTH_ONLY', False):
        userid = str(request.user.id)
    else:
        userid = ''

    is_qgis_browser = oq_is_qgis_browser(request)

    namespace = request.resolver_match.namespace

    data = json.loads(request.POST.get('data'))

    if not is_qgis_browser:
        (fd, fname) = tempfile.mkstemp(
            suffix='.zip', prefix='ipt_', dir=tempfile.gettempdir())
        os.close(fd)
        z = zipfile.ZipFile(fname, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        file_collect = None
    else:
        z = None
        file_collect = []
        fname = 'ipt_' + ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(8)) + '.zip'

    jobini = "# Generated automatically with IPT at %s\n" % (
        "TESTING TIME" if TIME_INVARIANT_OUTPUTS else formatdate())
    jobini += "[general]\n"
    jobini += "description = %s\n" % data['description']

    if data['risk'] == 'damage':
        jobini += "calculation_mode = scenario_damage\n"
    elif data['risk'] == 'losses':
        jobini += "calculation_mode = scenario_risk\n"
    elif data['hazard'] == 'hazard':
        jobini += "calculation_mode = scenario\n"
    else:
        ret['ret'] = 2
        ret['msg'] = 'Neither hazard nor risk selected.'
        return HttpResponse(json.dumps(ret), content_type="application/json")

    jobini += "random_seed = 113\n"

    if (data['hazard'] is None and data['risk'] is not None and
            data['gmf_file'] is not None):
        jobini += "\n[hazard]\n"
        jobini += ("gmfs_file = %s\n" % basename(data['gmf_file']))
        zwrite_or_collect(z, userid, namespace, data['gmf_file'], file_collect)

    if data['hazard'] == 'hazard':
        jobini += "\n[Rupture information]\n"
        #            #####################

        jobini += ("rupture_model_file = %s\n" %
                   basename(data['rupture_model_file']))
        zwrite_or_collect(z, userid, namespace, data['rupture_model_file'],
                          file_collect)

        jobini += "rupture_mesh_spacing = %s\n" % data['rupture_mesh_spacing']

    if data['hazard'] == 'hazard':
        jobini += "\n[Hazard sites]\n"
        #            ##############

        if data['hazard_sites_choice'] == 'region-grid':
            jobini += "region_grid_spacing = %s\n" % data['grid_spacing']
            if data['region_grid_choice'] == 'region-coordinates':
                is_first = True
                jobini += "region = "
                for el in data['reggrid_coords_data']:
                    if is_first:
                        is_first = False
                    else:
                        jobini += ", "
                    jobini += "%s %s" % (el[0], el[1])
                jobini += "\n"
        elif data['hazard_sites_choice'] == 'list-of-sites':
            jobini += "sites_csv = %s\n" % basename(data['list_of_sites'])
            zwrite_or_collect(z, userid, namespace, data['list_of_sites'],
                              file_collect)

        elif data['hazard_sites_choice'] == 'exposure-model':
            pass
        elif data['hazard_sites_choice'] == 'site-cond-model':
            if data['site_conditions_choice'] != 'from-file':
                ret['ret'] = 4
                ret['msg'] = ('Input hazard sites choices mismatch method to '
                              'specify site conditions.')
                return HttpResponse(json.dumps(ret),
                                    content_type="application/json")
        else:
            ret['ret'] = 4
            ret['msg'] = 'Unknown hazard_sites_choice.'
            return HttpResponse(json.dumps(ret),
                                content_type="application/json")

    if ((data['hazard'] == 'hazard' and
         (data['hazard_sites_choice'] == 'exposure-model' or
          data['region_grid_choice'] == 'infer-from-exposure')) or
            data['risk'] is not None):
        jobini += exposure_model_prep_sect(data, z, (data['risk'] is not None),
                                           userid, namespace, file_collect)

    if data['risk'] == 'damage':
        jobini += "\n[Fragility model]\n"
        #            #################
        descr = {'structural': 'structural', 'nonstructural': 'nonstructural',
                 'contents': 'contents', 'businter': 'business_interruption'}
        with_cons = data['fm_loss_show_cons_choice']
        for losslist in ['structural', 'nonstructural',
                         'contents', 'businter']:
            if data['fm_loss_%s_choice' % losslist] is True:
                jobini += "%s_fragility_file = %s\n" % (
                    descr[losslist],
                    basename(data['fm_loss_' + losslist]))
                zwrite_or_collect(z, userid, namespace,
                                  data['fm_loss_' + losslist], file_collect)
                if with_cons is True:
                    jobini += "%s_consequence_file = %s\n" % (
                        descr[losslist],
                        basename(data['fm_loss_%s_cons' % losslist]))
                    zwrite_or_collect(z, userid, namespace,
                                      data['fm_loss_%s_cons' % losslist],
                                      file_collect)
    elif data['risk'] == 'losses':
        jobini += vulnerability_model_prep_sect(data, z, userid, namespace,
                                                file_collect, save_files=True)

    if data['hazard'] == 'hazard':
        jobini += site_conditions_prep_sect(data, z, userid, namespace,
                                            file_collect)

    if data['hazard'] == 'hazard':
        jobini += "\n[Calculation parameters]\n"
        #            ########################

        gsim_n = len(data['gsim'])
        gsim_w = [0] * gsim_n
        for i in range(0, (gsim_n - 1)):
            gsim_w[i] = "%1.3f" % (1.0 / float(gsim_n))

        gsim_w[gsim_n - 1] = "%1.3f" % (1.0 - (float(
            gsim_w[0]) * (gsim_n - 1)))

        jobini += "gsim_logic_tree_file = gmpe.xml\n"

        gmpe = "<?xml version='1.0' encoding='utf-8'?>\n\
<nrml xmlns:gml='http://www.opengis.net/gml'\n\
      xmlns='http://openquake.org/xmlns/nrml/0.5'>\n\
\n\
<logicTree logicTreeID='lt1'>\n\
  <logicTreeBranchingLevel branchingLevelID='bl1'>\n\
    <logicTreeBranchSet uncertaintyType='gmpeModel'\n\
                        branchSetID='bs1' \n\
                        applyToTectonicRegionType='Active Shallow Crust'>\n"

        for i in range(0, gsim_n):
            gmpe += "      <logicTreeBranch branchID='b%d'>\n\
        <uncertaintyModel>%s</uncertaintyModel>\n\
        <uncertaintyWeight>%s</uncertaintyWeight>\n\
      </logicTreeBranch>\n" % (i, data['gsim'][i], gsim_w[i])

        gmpe += "    </logicTreeBranchSet>\n\
  </logicTreeBranchingLevel>\n\
</logicTree>\n\
</nrml>\n"

        zwrite_or_collect_str(z, 'gmpe.xml', gmpe, file_collect)

        if data['risk'] is None:
            jobini += "intensity_measure_types = "
            is_first = True
            for imt in data['intensity_measure_types']:
                if is_first:
                    is_first = False
                else:
                    jobini += ", "
                jobini += imt
            if data['custom_imt'] != '':
                if not is_first:
                    jobini += ", "
                jobini += data['custom_imt']
            jobini += "\n"

        jobini += ("ground_motion_correlation_model = %s\n" %
                   data['ground_motion_correlation_model'])
        if data['ground_motion_correlation_model'] == 'JB2009':
            jobini += ("ground_motion_correlation_params = "
                       "{\"vs30_clustering\": False}\n")

        jobini += "truncation_level = %s\n" % data['truncation_level']
        jobini += "maximum_distance = %s\n" % data['maximum_distance']
        jobini += ("number_of_ground_motion_fields = %s\n" %
                   data['number_of_ground_motion_fields'])

    #  print(encode(jobini))

    zwrite_or_collect_str(z, 'job.ini', jobini, file_collect)

    if is_qgis_browser:
        ret['ret'] = 0
        ret['msg'] = 'Success, scenario prepared correctly.'
        ret['content'] = file_collect
    else:
        z.close()
        ret['ret'] = 0
        ret['msg'] = 'Success, download it.'

    ret['zipname'] = os.path.basename(fname)

    return HttpResponse(json.dumps(ret),
                        content_type="application/json")


def event_based_prepare(request, **kwargs):
    ret = {}
    vuln_file_saved = False
    expo_file_saved = False

    if request.POST.get('data', '') == '':
        ret['ret'] = 1
        ret['msg'] = 'Malformed request.'
        return HttpResponse(json.dumps(ret), content_type="application/json")

    if getattr(settings, 'AUTH_ONLY', False):
        userid = str(request.user.id)
    else:
        userid = ''

    is_qgis_browser = oq_is_qgis_browser(request)

    namespace = request.resolver_match.namespace

    data = json.loads(request.POST.get('data'))

    if not is_qgis_browser:
        (fd, fname) = tempfile.mkstemp(
            suffix='.zip', prefix='ipt_', dir=tempfile.gettempdir())
        os.close(fd)
        z = zipfile.ZipFile(fname, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        file_collect = None
    else:
        z = None
        fname = 'ipt_' + ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(8)) + '.zip'
        file_collect = []

    jobhaz = ""
    outhaz = ""
    jobris = ""
    outris = ""
    is_full = False
    if data['hazard'] == 'hazard' and data['risk'] == 'risk':
        jobini = ""
        is_full = True

    job_sect = ""
    job_sect += "# Generated automatically with IPT at %s\n" % (
        "TESTING TIME" if TIME_INVARIANT_OUTPUTS else formatdate())
    job_sect += "[general]\n"
    job_sect += "description = %s\n" % data['description']

    if is_full:
        jobini += job_sect
        jobini += "calculation_mode = event_based_risk\n"
    else:
        if data['hazard'] == 'hazard':
            jobhaz += job_sect
            jobhaz += "calculation_mode = event_based\n"
        if data['risk'] == 'risk':
            jobris += job_sect
            jobris += "calculation_mode = event_based_risk\n"

    job_sect = ""
    if data['hazard'] == 'hazard':
        job_sect += "\n[Hazard sites]\n"
        #              ##############

        if data['hazard_sites_choice'] == 'region-grid':
            job_sect += "region_grid_spacing = %s\n" % data['grid_spacing']
            if data['region_grid_choice'] == 'region-coordinates':
                is_first = True
                job_sect += "region = "
                for el in data['reggrid_coords_data']:
                    if is_first:
                        is_first = False
                    else:
                        job_sect += ", "
                    job_sect += "%s %s" % (el[0], el[1])
                job_sect += "\n"
        elif data['hazard_sites_choice'] == 'list-of-sites':
            job_sect += "sites_csv = %s\n" % basename(data['list_of_sites'])
            zwrite_or_collect(z, userid, namespace, data['list_of_sites'],
                              file_collect)
        elif data['hazard_sites_choice'] == 'exposure-model':
            pass
        else:
            ret['ret'] = 4
            ret['msg'] = 'Unknown hazard_sites_choice.'
            return HttpResponse(json.dumps(ret),
                                content_type="application/json")

        # Site conditions
        job_sect += site_conditions_prep_sect(data, z, userid, namespace,
                                              file_collect)

        # Hazard model
        job_sect += "source_model_logic_tree_file = %s\n" % basename(
            data['source_model_logic_tree_file'])
        zwrite_or_collect(z, userid, namespace,
                          data['source_model_logic_tree_file'],
                          file_collect)

        for source_model_name in data['source_model_file']:
            zwrite_or_collect(z, userid, namespace, source_model_name,
                              file_collect)

        job_sect += "gsim_logic_tree_file = %s\n" % basename(
            data['gsim_logic_tree_file'])
        zwrite_or_collect(z, userid, namespace, data['gsim_logic_tree_file'],
                          file_collect)

        job_sect += "\n[Hazard model]\n"
        #              ##############
        job_sect += "width_of_mfd_bin = %s\n" % data['width_of_mfd_bin']

        job_sect += ("rupture_mesh_spacing = %s\n" %
                     data['rupture_mesh_spacing'])

        job_sect += ("area_source_discretization = %s\n" %
                     data['area_source_discretization'])

        if data['complex_fault_mesh_choice'] is True:
            job_sect += ("complex_fault_mesh_spacing = %s\n" %
                         data['complex_fault_mesh'])

        if (not is_full and data['use_imt_from_vulnerability_choice'] is True):
            job_sect += vulnerability_model_prep_sect(
                data, z, userid, namespace, file_collect,
                save_files=(not vuln_file_saved))
            vuln_file_saved = True

        job_sect += "\n[Hazard calculation]\n"
        #              ####################

        if not is_full and data['use_imt_from_vulnerability_choice'] is False:
            job_sect += ("intensity_measure_types_and_levels = %s\n" %
                         json.dumps(data['imt_and_levels']))

        job_sect += ("ground_motion_correlation_model = %s\n" %
                     data['ground_motion_correlation_model'])
        if data['ground_motion_correlation_model'] == 'JB2009':
            job_sect += ("ground_motion_correlation_params = "
                         "{\"vs30_clustering\": True}\n")
        job_sect += "maximum_distance = %s\n" % data['maximum_distance']
        job_sect += "truncation_level = %s\n" % data['truncation_level']
        job_sect += "investigation_time = %s\n" % data['investigation_time']
        job_sect += ("ses_per_logic_tree_path = %s\n" %
                     data['ses_per_logic_tree_path'])
        job_sect += ("number_of_logic_tree_samples = %s\n" %
                     data['number_of_logic_tree_samples'])

        outhaz += ("ground_motion_fields = %s\n" %
                   bool2s(data['ground_motion_fields']))
        outhaz += ("hazard_curves_from_gmfs = %s\n" %
                   bool2s(data['hazard_curves_from_gmfs']))
        if data['hazard_curves_from_gmfs']:
            outhaz += "hazard_maps = %s\n" % bool2s(data['hazard_maps'])
            if data['hazard_maps']:
                outhaz += "poes = %s\n" % data['poes']
                outhaz += ("uniform_hazard_spectra = %s\n" %
                           bool2s(data['uniform_hazard_spectra']))

        outhaz += ("individual_curves = %s\n" % (
            "True" if data['individual_curves'] else "False"))

        if data['quantiles']:
            outhaz += "quantiles = " + ", ".join(data['quantiles'])
            outhaz += "\n"

        if is_full:
            jobini += job_sect
        else:
            jobhaz += job_sect
            if outhaz:
                jobhaz += "\n[Outputs]\n"
                #            #########
                jobhaz += outhaz

    job_sect = ""
    # Exposure model
    if data['risk'] == 'risk':
        job_sect += exposure_model_prep_sect(
            data, z, True, userid, namespace,
            file_collect, save_files=(not expo_file_saved))
        expo_file_saved = True
        if is_full:
            jobini += job_sect
        else:
            jobris += job_sect

    if (not is_full and data['hazard'] == 'hazard' and
        (data['hazard_sites_choice'] == 'exposure-model' or
         data['region_grid_choice'] == 'infer-from-exposure')):
        jobhaz += exposure_model_prep_sect(
            data, z, False, userid, namespace, file_collect,
            save_files=(not expo_file_saved))
        expo_file_saved = True

    job_sect = ""
    if data['risk'] == 'risk':
        # Vulnerability model
        job_sect += vulnerability_model_prep_sect(
            data, z, userid, namespace, file_collect,
            save_files=(not vuln_file_saved))
        vuln_file_saved = True

        job_sect += "\n[Risk calculation]\n"
        #              ##################
        job_sect += ("risk_investigation_time = %s\n" %
                     data['risk_investigation_time'])
        if data['ret_periods_for_aggr'] is not None:
            job_sect += ("return_periods = [%s]\n" %
                         data['ret_periods_for_aggr'])

        if data['conditional_loss_poes_choice']:
            outris += ("conditional_loss_poes = %s\n" %
                       data['conditional_loss_poes'])

        if is_full:
            jobini += job_sect
        else:
            if outris:
                job_sect += "\n[Outputs]\n"
                #              #########
                job_sect += outris

            jobris += job_sect

    if is_full:
        if outhaz + outris:
            jobini += "\n[Outputs]\n"
            #            #########
            jobini += outhaz + outris

        zwrite_or_collect_str(z, 'job.ini', jobini, file_collect)
    else:
        if data['hazard'] == 'hazard':
            zwrite_or_collect_str(z, 'job_hazard.ini', jobhaz, file_collect)

        if data['risk'] == 'risk':
            zwrite_or_collect_str(z, 'job_risk.ini', jobris, file_collect)

    if is_qgis_browser:
        ret['ret'] = 0
        ret['msg'] = 'Success, event based prepared correctly.'
        ret['content'] = file_collect
    else:
        z.close()
        ret['ret'] = 0
        ret['msg'] = 'Success, download it.'

    ret['zipname'] = os.path.basename(fname)

    return HttpResponse(json.dumps(ret), content_type="application/json")


def volcano_prepare(request, **kwargs):
    ret = {}

    if request.POST.get('data', '') == '':
        ret['ret'] = 1
        ret['msg'] = 'Malformed request.'
        return HttpResponse(json.dumps(ret), content_type="application/json")

    if getattr(settings, 'AUTH_ONLY', False):
        userid = str(request.user.id)
    else:
        userid = ''

    is_qgis_browser = oq_is_qgis_browser(request)

    namespace = request.resolver_match.namespace

    data = json.loads(request.POST.get('data'))

    if not is_qgis_browser:
        (fd, fname) = tempfile.mkstemp(
            suffix='.zip', prefix='ipt_', dir=tempfile.gettempdir())
        os.close(fd)
        z = zipfile.ZipFile(fname, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        file_collect = None
    else:
        z = None
        fname = 'ipt_' + ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(8)) + '.zip'
        file_collect = []

    jobris = ""

    jobris += "# Generated automatically with IPT at %s\n" % (
        "TESTING TIME" if TIME_INVARIANT_OUTPUTS else formatdate())
    jobris += "[general]\n"
    jobris += "description = %s\n" % data['description']

    jobris += "calculation_mode = multi_risk\n"

    jobris += "\n[Volcano information]\n"

    phenoms = {
        VolConst.ph_ashf: {
            'name': 'ashfall',
            'f': data['ashfall_file'] if data['ashfall_choice'] else None
        },
        VolConst.ph_lava: {
            'name': 'lavaflow',
            'f': data['lavaflow_file'] if data['lavaflow_choice'] else None
        },
        VolConst.ph_laha: {
            'name': 'lahar',
            'f': data['lahar_file'] if data['lahar_choice'] else None
        },
        VolConst.ph_pyro: {
            'name': 'pyroclasticflow',
            'f': (data['pyroclasticflow_file'] if
                  data['pyroclasticflow_choice'] else None)
        }
    }

    try:
        phenom_arr = []
        spec_ass_haz_dists = []
        for key in sorted(phenoms):
            if phenoms[key]['f'] is None:
                continue

            in_type = data[phenoms[key]['name'] + '_in_type']
            if in_type != 'shape-to-wkt' and in_type != 'text-to-wkt':
                spec_ass_haz_dist = data[phenoms[key]['name'] +
                                         '_ass_haz_dist']
                spec_ass_haz_dist = spec_ass_haz_dist.strip()
            else:
                spec_ass_haz_dist = ''

            if spec_ass_haz_dist != '':
                spec_ass_haz_dists.append([key, spec_ass_haz_dist])

            if in_type == VolConst.ty_text and key == VolConst.ph_ashf:
                # 'text' case for textual external software case
                # FIXME
                if data[phenoms[key]['name'] + '_epsg'] == '':
                    raise ValueError("Not valid EPSG value for '%s' "
                                     "input file" % (
                                         phenoms[key]['name'],))

                density = data[phenoms[key]['name'] + '_density']

                phenom_inputfile = gem_input_converter(
                    z, key, VolConst.ty_text, userid, namespace,
                    phenoms[key]['f'], file_collect,
                    data[phenoms[key]['name'] + '_epsg'],
                    density)
                phenom_arr.append("'%s': '%s'" % (key, phenom_inputfile))
            elif in_type == VolConst.ty_twkt:
                if data[phenoms[key]['name'] + '_epsg'] == '':
                    raise ValueError("Not valid EPSG value for '%s' "
                                     "input file" % (
                                         phenoms[key]['name'],))
                # and not key == VolConst.ph_ashf (already excluded above)
                density = None
                if key == VolConst.ph_laha:
                    nodata_extra = ["1"]
                else:
                    nodata_extra = None
                phenom_inputfile = gem_input_converter(
                    z, key, VolConst.ty_twkt, userid, namespace,
                    phenoms[key]['f'], file_collect,
                    data[phenoms[key]['name'] + '_epsg'],
                    density, nodata_extra)
                phenom_arr.append("'%s': '%s'" % (key, phenom_inputfile))
            elif in_type == VolConst.ty_shap or in_type == VolConst.ty_swkt:
                # 'shape'-file case
                if in_type == VolConst.ty_shap:
                    if data[phenoms[key]['name'] + '_discr_dist'] == '':
                        raise ValueError("Discretization distance is missing "
                                         "for '%s' input file" % (
                                             phenoms[key]['name'],))
                    if data[phenoms[key]['name'] + '_haz_field'] == '':
                        raise ValueError("Hazard field name is missing "
                                         "for '%s' input file" % (
                                             phenoms[key]['name'],))
                if key == VolConst.ph_ashf:
                    if data[phenoms[key]['name'] + '_density'] == '':
                        raise ValueError("Ashfall density is missing "
                                         "for '%s' input file" % (
                                             phenoms[key]['name'],))

                    density = data[phenoms[key]['name'] + '_density']
                else:
                    density = None

                if in_type == VolConst.ty_shap:
                    phenom_inputfile = gem_input_converter(
                        z, key, VolConst.ty_shap, userid, namespace,
                        phenoms[key]['f'], file_collect,
                        data[phenoms[key]['name'] + '_discr_dist'],
                        data[phenoms[key]['name'] + '_haz_field'],
                        density)
                else:
                    phenom_inputfile = gem_input_converter(
                        z, key, VolConst.ty_swkt, userid, namespace,
                        phenoms[key]['f'], file_collect)

                phenom_arr.append("'%s': '%s'" % (key, phenom_inputfile))
            else:
                # 'openquake' case
                zwrite_or_collect(z, userid, namespace, phenoms[key]['f'],
                                  file_collect)

                phenom_arr.append("'%s': '%s'" % (key, basename(
                    phenoms[key]['f'])))
        jobris += 'multi_peril_csv = {' + ', '.join(phenom_arr) + '}\n'

        if data['ashfall_choice']:
            jobris += 'ash_wet_amplification_factor = %f\n' % float(
                data['ashfall_wet_ampl'])

        jobris += exposure_model_prep_sect(
            data, z, True, userid, namespace, file_collect,
            spec_ass_haz_dists=spec_ass_haz_dists)

        if data['ashfall_choice']:
            jobris += "\n[Fragility model]\n"

            zwrite_or_collect(z, userid, namespace, data['fm_ashfall_file'],
                              file_collect)
            jobris += ("structural_fragility_file = %s\n" %
                       basename(data['fm_ashfall_file']))

            if data['ashfall_cons_models_choice']:
                zwrite_or_collect(
                    z, userid, namespace, data['ashfall_cons_models_file'],
                    file_collect)
                jobris += ("structural_consequence_file = %s\n" %
                           basename(data['ashfall_cons_models_file']))

        # FIXME modal_damage_state
        # jobris += "modal_damage_state = " + (
        #    "true" if data['is_modal_damage_state'] is True else "false")
        #
        zwrite_or_collect_str(z, 'job.ini', jobris, file_collect)
    except NameError as err:
        ret['ret'] = 2
        ret['msg'] = ' exception raised: %s' % err
        return HttpResponse(json.dumps(ret), content_type="application/json")

    if is_qgis_browser:
        ret['ret'] = 0
        ret['msg'] = 'Success, event based prepared correctly.'
        ret['content'] = file_collect
    else:
        z.close()
        ret['ret'] = 0
        ret['msg'] = 'Success, download it.'

    ret['zipname'] = os.path.basename(fname)

    return HttpResponse(json.dumps(ret), content_type="application/json")


def download(request):
    if request.method == 'POST':
        zipname = request.POST.get('zipname', '')
        dest_name = request.POST.get('dest_name', 'Unknown')
        if zipname == '':
            return HttpResponseBadRequest('No zipname provided.')
        absfile = os.path.join(tempfile.gettempdir(), zipname)
        if not os.path.isfile(absfile):
            return HttpResponseBadRequest('Zipfile not found.')

        to_delete = False
        with open(absfile, 'rb') as content_file:
            content = content_file.read()
            to_delete = True
        if to_delete and GEM_IPT_CLEAN_ALL:
            os.unlink(absfile)

        resp = HttpResponse(content=content,
                            content_type='application/zip')
        resp['Content-Description'] = 'File Transfer'
        resp['Content-Disposition'] = (
            'attachment; filename="' + dest_name + '.zip"')
        resp['Content-Length'] = len(content)
        return resp


def clean_all(request):
    if request.method == 'POST':
        if getattr(settings, 'AUTH_ONLY', False):
            userid = str(request.user.id)
        else:
            userid = ''
        namespace = request.resolver_match.namespace
        user_allowed_path = get_full_path(userid, namespace)
        for ipt_dir in ALLOWED_DIR:
            normalized_path = get_full_path(userid, namespace, ipt_dir)
            if not normalized_path.startswith(user_allowed_path):
                raise LookupError('Unauthorized path: "%s"' % normalized_path)
            if not os.path.isdir(normalized_path):
                continue
            shutil.rmtree(normalized_path)
            os.makedirs(normalized_path)

        ret = {}
        ret['ret'] = 0
        ret['msg'] = 'Success, reload it.'
        return HttpResponse(json.dumps(ret), content_type="application/json")


def shapefile_get_fields(request):
    if request.method == 'POST':
        if getattr(settings, 'AUTH_ONLY', False):
            userid = str(request.user.id)
        else:
            userid = ''
        namespace = request.resolver_match.namespace
        data = json.loads(request.POST.get('data'))

        fname = data['filepath']
        fields_list = gem_shapefile_get_fields(userid, namespace, fname)

        return HttpResponse(json.dumps(
            {'ret': 0, 'ret_s': 'Success', 'items': fields_list}),
            content_type="application/json")


def enc_open(*args, **kwargs):
    if sys.version_info[0] < 3:
        try:
            codecs
        except NameError:
            import codecs

        return codecs.open(*args, **kwargs)
    else:
        return open(*args, **kwargs)


def ex_csv_check(request):
    if request.method == 'POST':
        if getattr(settings, 'AUTH_ONLY', False):
            userid = str(request.user.id)
        else:
            userid = ''
        namespace = request.resolver_match.namespace
        data = json.loads(request.POST.get('data'))

        field_names = data['field_names']
        csv_files = data['csv_files']

        for csv_file in csv_files:
            fpath, fname = os.path.split(csv_file)

            if fpath not in ALLOWED_DIR:
                return HttpResponse(
                    json.dumps(
                        {'ret': 1, 'ret_s': 'Failed: "%s" '
                         'not in a autorized path.' % fpath}),
                    content_type="application/json")

            input_filepath = get_full_path(userid, namespace, csv_file)

            with enc_open(input_filepath, encoding='utf-8-sig') as csv_fp:
                csv_dr = csv.reader(csv_fp)
                csv_field_names = next(csv_dr)
                csv_field_names_n = len(csv_field_names)
                for field_name in field_names:
                    if field_name not in csv_field_names:
                        return HttpResponse(
                            json.dumps(
                                {'ret': 2, 'ret_s': (
                                    "Failed: missing column '%s'"
                                    " in csv file '%s'" %
                                    (field_name, fname))}),
                            content_type="application/json")

                for row_id, row in enumerate(csv_dr):
                    if len(row) != csv_field_names_n:
                        return HttpResponse(json.dumps(
                            {'ret': 3, 'ret_s': (
                                "Failed: at row %d of csv file '%s'"
                                " columns number is %d instead of %d" %
                                (row_id+1, fname,
                                 len(row), csv_field_names_n))}),
                            content_type="application/json")

        return HttpResponse(json.dumps(
            {'ret': 0, 'ret_s': 'Success'}),
            content_type="application/json")
