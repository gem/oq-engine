# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
import pytest
from openquake.commonlib import better_smlt
from openquake.qa_tests_data.event_based import case_7

CASE7 = os.path.dirname(case_7.__file__)


def _source_models(path, kind):
    # exercise correlated changes and an identity source found in one file
    if kind == 'multi':
        fixture = (Path(__file__).parents[2] / 'hazardlib/tests/source_model/'
                   'multi-point-source.xml')
    else:
        fixture = Path(CASE7) / 'source_model1.xml'
    root = ET.parse(fixture).getroot()
    container = root.find('.//{*}sourceGroup') if kind == 'multi' else \
        root.find('{*}sourceModel')
    source = container[0]
    container[:] = [source, copy.deepcopy(source)]
    container[1].set('id', 'other')
    if kind == 'gr':
        container.append(copy.deepcopy(source))
        container[2].find('{*}ruptAspectRatio').text = '2'
    for i, fname in enumerate(('base.xml', 'variant.xml', 'identity.xml')):
        model = copy.deepcopy(root)
        group = model.find('.//{*}sourceGroup') if kind == 'multi' else \
            model.find('{*}sourceModel')
        if i == 2:
            group[:] = [group[0]]
            group[0].set('id', 'identity')
        for src in group:
            mfd = src.find('{*}multiMFD' if kind == 'multi' else
                           '{*}truncGutenbergRichterMFD')
            if kind == 'multi':
                mfd.find('{*}occurRates').text = ' '.join(
                    str(float(r) * (i + 1)) for r in
                    mfd.find('{*}occurRates').text.split())
            elif kind == 'incremental':
                new = ET.Element(mfd.tag.replace(
                    'truncGutenbergRichterMFD', 'incrementalMFD'),
                    minMag='5', binWidth='0.1')
                rates = ET.SubElement(new, mfd.tag.replace(
                    'truncGutenbergRichterMFD', 'occurRates'))
                rates.text = str(i + 1)
                src[list(src).index(mfd)] = new
            else:
                mfd.set('aValue', str(3 + i))
                mfd.set('minMag', str(4.5 + i * 0.5))
        ET.ElementTree(model).write(path / fname, encoding='utf-8')


@pytest.mark.parametrize('version', ['0.4', '0.5'])
@pytest.mark.parametrize('kind', ['gr', 'incremental', 'multi'])
def test_conversion_paths(tmp_path, version, kind):
    _source_models(tmp_path, kind)
    shutil.copy(Path(CASE7) / 'job.ini', tmp_path)
    shutil.copy(Path(CASE7) / 'gmpe_logic_tree.xml', tmp_path)
    level = '<n:logicTreeBranchingLevel branchingLevelID="bl1">'
    tree = f'''<n:nrml xmlns:n="http://openquake.org/xmlns/nrml/{version}">
    <n:logicTree logicTreeID="lt1">
    {level if version == '0.4' else ''}
    <n:logicTreeBranchSet branchSetID="bs1" uncertaintyType="sourceModel">
    <!-- preserve the model comment -->
    <n:logicTreeBranch branchID="b1">
      <n:uncertaintyModel><!-- keep file list -->base.xml</n:uncertaintyModel>
      <n:uncertaintyWeight>0.3</n:uncertaintyWeight></n:logicTreeBranch>
    <n:logicTreeBranch branchID="b 2">
      <n:uncertaintyModel>variant.xml</n:uncertaintyModel>
      <n:uncertaintyWeight>0.3</n:uncertaintyWeight></n:logicTreeBranch>
    <n:logicTreeBranch branchID="b1_mfd1">
      <n:uncertaintyModel>identity.xml</n:uncertaintyModel>
      <n:uncertaintyWeight>0.4</n:uncertaintyWeight></n:logicTreeBranch>
    </n:logicTreeBranchSet>
    {'</n:logicTreeBranchingLevel>' if version == '0.4' else ''}
    </n:logicTree></n:nrml>'''
    if kind == 'gr':
        later = '''<n:logicTreeBranchSet branchSetID="later"
        uncertaintyType="maxMagGRRelative" applyToBranches="b1">
        <n:logicTreeBranch branchID="later1">
        <n:uncertaintyModel>0.2</n:uncertaintyModel>
        <n:uncertaintyWeight>1</n:uncertaintyWeight></n:logicTreeBranch>
        </n:logicTreeBranchSet>'''
        if version == '0.4':
            later = ('<n:logicTreeBranchingLevel branchingLevelID="bl2">' +
                     later + '</n:logicTreeBranchingLevel>')
        tree = tree.replace('</n:logicTree>', later + '</n:logicTree>')
    (tmp_path / 'source_model_logic_tree.xml').write_text(tree)
    originals = {f.name: f.read_bytes() for f in tmp_path.iterdir()}
    assert better_smlt.main(tmp_path / 'job.ini')
    with zipfile.ZipFile(tmp_path / 'job.zip') as archive:
        text = archive.read('source_model_logic_tree.xml').decode()
    assert '<correlated ' in text
    assert 'preserve the model comment' in text
    root = ET.fromstring(text)
    assert {el.tag.split('}')[0] for el in root.iter()} == {
        root.tag.split('}')[0]}
    branches = root.findall('.//{*}logicTreeBranch')
    ids = [br.get('branchID') for br in branches]
    assert len(ids) == len(set(ids))
    assert 'b_2' in ids
    assert 'b1_mfd1_' in ids
    assert '_fixed/' not in text
    if kind == 'gr':
        later = root.find('.//{*}logicTreeBranchSet[@branchSetID="later"]')
        assert later.get('applyToBranches') in ids
        assert later.get('applyToBranches') != 'b1'
        selected = {el.get('src') for el in root.findall('.//{*}correlated')}
        assert {'1_1', '1_2'} <= selected
    for fname, content in originals.items():
        assert (tmp_path / fname).read_bytes() == content


class BetterSmltTestCase(unittest.TestCase):
    # the two source models of event_based/case_7 contain the same sources
    # with different MFDs: the variants are moved into the logic tree and
    # the converted logic tree is checked against the original one
    def test_case_7(self):
        with tempfile.TemporaryDirectory() as tmp:
            dname = shutil.copytree(CASE7, os.path.join(tmp, 'case_7'))
            # an existing job.zip is overwritten
            with open(os.path.join(dname, 'job.zip'), 'w') as f:
                f.write('old')
            self.assertTrue(better_smlt.main(os.path.join(dname, 'job.ini')))
            # job.zip contains a job with the converted logic tree, saved
            # with the name of the original one, and the rewritten sources
            with zipfile.ZipFile(os.path.join(dname, 'job.zip')) as z:
                names = z.namelist()
                ini = z.read('job.ini').decode()
                new = z.read('source_model_logic_tree.xml').decode()
            self.assertIn('source_model_logic_tree.xml', ini)
            # a single source: no correlated element is needed
            self.assertIn('applyToSources="1"', new)
            self.assertNotIn('correlated', new)
            self.assertIn('source_model2.xml', names)
            # nothing else is written in the folder of the job
            self.assertEqual(sorted(os.listdir(dname)),
                             sorted(set(os.listdir(CASE7)) | {'job.zip'}))


class MultiWriterTestCase(unittest.TestCase):
    # the multiMFD elements are written with one array per line, wrapped
    # to avoid extra-long lines in the XML
    def test_wrap(self):
        values = ' '.join('%.7E' % (i / 7) for i in range(893))
        arrays = (('a_val', values), ('b_val', values), ('min_mag', '4.5'))
        root = ET.Element('multiMFD', kind='truncGutenbergRichterMFD',
                          size='893')
        for tag, values in arrays:
            ET.SubElement(root, tag).text = values
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'multi.xml'
            better_smlt._write_xml(root, path)
            text = path.read_text()
        lengths = list(map(len, text.splitlines()))
        self.assertLessEqual(max(lengths), better_smlt.LINE_WIDTH)
        self.assertGreater(len(text.splitlines()), 20)
        # the element is parsed back to the same arrays
        root = ET.fromstring(text)
        self.assertEqual(root.attrib, {'kind': 'truncGutenbergRichterMFD',
                                       'size': '893'})
        got = tuple((c.tag, ' '.join(c.text.split())) for c in root)
        self.assertEqual(got, arrays)


class SourceWriterTestCase(unittest.TestCase):
    def test_combined_edits(self):
        # ID-only, MFD-only and combined edits preserve the other XML,
        # including comments, source order and namespace URIs.
        mfds = [
            '<{p}truncGutenbergRichterMFD aValue="{a}" bValue="1" '
            'minMag="4" maxMag="7"/>',
            '<{p}incrementalMFD minMag="4" binWidth="0.1">'
            '<{p}occurRates>{a}</{p}occurRates></{p}incrementalMFD>',
            '<{p}multiMFD kind="incrementalMFD" size="1">'
            '<{p}min_mag>4</{p}min_mag><{p}bin_width>0.1</{p}bin_width>'
            '<{p}occurRates>{a}</{p}occurRates>'
            '<{p}lengths>1</{p}lengths></{p}multiMFD>']
        for prefix in ('', 'n:'):
            for mfd in mfds:
                with self.subTest(prefix=prefix, mfd=mfd):
                    base_mfd = mfd.format(p=prefix, a='2')
                    other_mfd = mfd.format(p=prefix, a='3')
                    source = (f'<{prefix}pointSource id="{{id}}">'
                              '<!-- keep -->{mfd}'
                              f'</{prefix}pointSource>')
                    sources = [source.format(id=i, mfd=other_mfd)
                               for i in range(4)]
                    namespace = 'xmlns:n' if prefix else 'xmlns'
                    text = (f'<{prefix}sourceModel {namespace}="urn:test">' +
                            '\n'.join(sources) + f'</{prefix}sourceModel>')
                    base_el = ET.fromstring(text.replace(
                        other_mfd, base_mfd))[0]
                    base = better_smlt.Copy('base.xml', 0, base_el, {})
                    original = [better_smlt.Copy('sources.xml', i, el, {})
                                for i, el in enumerate(ET.fromstring(text))]
                    original[0].id = 'renamed'
                    original[2].id = 'combined'
                    with tempfile.TemporaryDirectory() as tmp:
                        path = Path(tmp)
                        (path / 'sources.xml').write_text(text)
                        nfiles = better_smlt._write_files(
                            path, path / 'out', original,
                            {'renamed': '0', 'combined': '2'},
                            [[base, original[1]], [base, original[2]]],
                            {'sources.xml'})
                        self.assertEqual(nfiles, 1)
                        result = (path / 'out/sources.xml').read_text()
                    root = ET.fromstring(result)
                    self.assertEqual([el.attrib['id'] for el in root],
                                     ['renamed', '1', 'combined', '3'])
                    copies = [better_smlt.Copy('out.xml', i, el, {})
                              for i, el in enumerate(root)]
                    self.assertEqual(copies[1].params, base.params)
                    self.assertEqual(copies[2].params, base.params)
                    self.assertEqual(copies[0].params, original[0].params)
                    self.assertEqual(copies[3].params, original[3].params)
                    self.assertEqual(root.tag, '{urn:test}sourceModel')
                    self.assertEqual(result.count('<!-- keep -->'), 4)
