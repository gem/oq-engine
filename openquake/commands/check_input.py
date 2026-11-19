# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2026 GEM Foundation
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
"""
`oq check_input` checks the validity of job.ini files, job.zip files
and .xml files. With the --optimize flag it converts the MFD variants
of the source model logic trees into uncertainties, see
openquake.commonlib.optimize_smlt. Here is an example, from
qa_tests_data/event_based/case_7. The source model logic tree has two
branches, containing the same source "1" with the same geometry but
different truncated GR MFDs (aValue=5.0 in source_model1.xml and
aValue=4.0 in source_model2.xml)::

  <logicTreeBranchSet uncertaintyType="sourceModel" branchSetID="bs1">
    <logicTreeBranch branchID="b11">
      <uncertaintyModel>source_model1.xml</uncertaintyModel>
      <uncertaintyWeight>0.6</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b12">
      <uncertaintyModel>source_model2.xml</uncertaintyModel>
      <uncertaintyWeight>0.4</uncertaintyWeight>
    </logicTreeBranch>
  </logicTreeBranchSet>

so the contexts of the source are computed twice. Running
`oq check_input -o job.ini` collapses the two branches into a single
one, followed by a branchset changing the MFD of source "1"::

  <logicTreeBranchSet uncertaintyType="sourceModel" branchSetID="bs1">
    <logicTreeBranch branchID="b11_base">
      <uncertaintyModel>source_model1.xml</uncertaintyModel>
      <uncertaintyWeight>1.0</uncertaintyWeight>
    </logicTreeBranch>
  </logicTreeBranchSet>
  <logicTreeBranchSet uncertaintyType="abMaxMagAbsolute"
                      branchSetID="bs1_mfd" applyToBranches="b11_base"
                      applyToSources="1">
    <logicTreeBranch branchID="b11">
      <uncertaintyModel>5.0 1.0 6.5</uncertaintyModel>
      <uncertaintyWeight>0.6</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b12">
      <uncertaintyModel>4.0 1.0 6.5</uncertaintyModel>
      <uncertaintyWeight>0.4</uncertaintyWeight>
    </logicTreeBranch>
  </logicTreeBranchSet>

so that the contexts are computed once for both MFDs. Then the source
rates are compared realization by realization between the original
and the converted logic tree and, if they are the same, the converted
inputs are saved in a job.zip file next to the job.ini (here without
source_model2.xml, which is not needed anymore), otherwise they are
left in job_mfd.zip, to be inspected. The original files are never
modified.
"""
import os
import logging
from unittest import mock

from openquake.hazardlib import nrml
from openquake.commonlib import datastore, optimize_smlt
from openquake.calculators import views
from openquake.risklib import read_nrml  # noqa
from openquake.risklib.asset import Exposure
from openquake.engine import engine, workflow


def main(fnames, optimize=False):
    """
    Check the validity of job.ini files, job.zip files and .xml files.
    With --optimize, convert the MFD variants of the source model
    logic trees of the job.ini files into uncertainties and check the
    converted logic trees (see openquake.commonlib.optimize_smlt).
    """
    if optimize:
        bad = [fname for fname in fnames if fname.endswith('.ini')
               and not optimize_smlt.main(fname)]
        if bad:
            raise RuntimeError('The converted logic trees of %s are not '
                               'equivalent to the original ones' % bad)
        return
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    inis = []
    tomls = []
    for fname in fnames:
        if fname.endswith('.xml'):
            node = nrml.to_python(fname)
            if node.tag.endswith('exposureModel'):
                err = Exposure.check(fname)
                if err:
                    logging.warning(err)
            else:
                logging.info('Checked %s', fname)
        elif fname.endswith(('.ini', '.zip')):
            inis.append(fname)
        elif fname.endswith('.toml'):
            tomls.append(fname)
    with mock.patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
        if inis:
            jobctxs = engine.run_jobs(engine.create_jobs(inis))
            # print the uncertainty signatures of the sources, i.e. the
            # sets of realizations with the same uncertainties, stored in
            # the datastore by source_reader.build_groups
            for jobctx in jobctxs:
                with datastore.read(jobctx.calc_id) as ds:
                    if 'unc_signatures' in ds:
                        print('\nUncertainty signatures of calc_%s\n%s' % (
                            jobctx.calc_id,
                            views.view('usignatures', ds)))
        for toml in tomls:
            workflow.run_workflow(toml, {})

main.fnames = dict(help='File names to check', nargs='+')
main.optimize = 'convert the MFD variants of the source model logic tree'
