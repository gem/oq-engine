# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import os
import random
import StringIO

from django.db import transaction
from nrml import parsers as nrml_parsers

from openquake import engine2
from openquake import writer
from openquake.calculators import base
from openquake.calculators.hazard import general
from openquake.db import models
from openquake.input import logictree
from openquake.input import source
from openquake.job.validation import MIN_SINT_32
from openquake.job.validation import MAX_SINT_32


class ClassicalHazardCalculator(base.CalculatorNext):

    def __init__(self, job):
        self.site_data = None  # assigned a value only if there is a site model
        super(ClassicalHazardCalculator, self).__init__(job)

    def initialize_site_model(self):
        hc_id = self.job.hazard_calculation.id

        site_model_inp = general.get_site_model(hc_id)
        if site_model_inp is not None:
            # Explicit cast to `str` here because the XML parser doesn't like
            # unicode. (More specifically, lxml doesn't like unicode.)
            site_model_content = str(site_model_inp.model_content.raw_content)

            # Store `site_model` records:
            general.store_site_model(
                site_model_inp, StringIO.StringIO(site_model_content))

            mesh = self.job.hazard_calculation.points_to_compute()

            # Get the site model records we stored:
            site_model_data = models.SiteModel.objects.filter(
                input=site_model_inp)

            general.validate_site_model(site_model_data, mesh)

            self.site_data = general.store_site_data(
                hc_id, site_model_inp, mesh)

    def initialize_sources(self):
        """
        Parse and validation logic trees (source and gsim). Then get all
        sources referenced in the the source model logic tree, create
        :class:`~openquake.db.models.Input` records for all of them, parse
        then, and save the parsed sources to the `parsed_source` table
        (see :class:`openquake.db.models.ParsedSource`).
        """
        hc = self.job.hazard_calculation

        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')
        [gsimlt] = models.inputs4hcalc(hc.id, input_type='lt_gsim')
        source_paths = logictree.read_logic_trees(
            hc.base_path, smlt.path, gsimlt.path)

        src_inputs = []
        for src_path in source_paths:
            full_path = os.path.join(hc.base_path, src_path)

            # Get or reuse the 'source' Input:
            inp = engine2.get_input(
                full_path, 'source', hc.owner, hc.force_inputs)
            src_inputs.append(inp)

            # Associate the source input to the calculation:
            models.Input2hcalc.objects.get_or_create(
                input=inp, hazard_calculation=hc)

            # Associate the source input to the source model logic tree input:
            models.Src2ltsrc.objects.get_or_create(
                hzrd_src=inp, lt_src=smlt, filename=src_path)

        # Now parse the source models and store `pared_source` records:
        for src_inp in src_inputs:
            src_content = StringIO.StringIO(src_inp.model_content.raw_content)
            sm_parser = nrml_parsers.SourceModelParser(src_content)
            src_db_writer = source.SourceDBWriter(
                src_inp, sm_parser.parse(), hc.rupture_mesh_spacing,
                hc.width_of_mfd_bin, hc.area_source_discretization)
            src_db_writer.serialize()

    @transaction.commit_on_success(using='reslt_writer')
    def initialize_realizations(self):
        hc = self.job.hazard_calculation

        # Each realization will have two seeds:
        # One for source model logic tree, one for GSIM logic tree.
        rnd = random.Random()
        seed = hc.random_seed
        rnd.seed(seed)

        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')

        ltp = logictree.LogicTreeProcessor(hc.id)

        # The first realization gets the seed we specified in the config file.
        for i in xrange(hc.number_of_logic_tree_samples):
            lt_rlz = models.LtRealization(hazard_calculation=hc)
            lt_rlz.ordinal = i
            lt_rlz.seed = seed

            # Sample source model logic tree branch paths:
            sm_name, _, sm_lt_branch_ids = ltp.sample_source_model_logictree(
                rnd.randint(MIN_SINT_32, MAX_SINT_32))
            lt_rlz.sm_lt_path = sm_lt_branch_ids

            # Sample GSIM logic tree branch paths:
            _, gsim_branch_ids = ltp.sample_gmpe_logictree(
                rnd.randint(MIN_SINT_32, MAX_SINT_32))
            lt_rlz.gsim_lt_path = gsim_branch_ids

            # Get the source model for this sample:
            hzrd_src = models.Src2ltsrc.objects.get(
                lt_src=smlt.id, filename=sm_name).hzrd_src
            parsed_sources = models.ParsedSource.objects.filter(input=hzrd_src)

            lt_rlz.total_sources = len(parsed_sources)
            lt_rlz.save()

            # Create source_progress for this realization
            # A bulk insert is more efficient because there could be lots of
            # of individual sources.
            sp_inserter = writer.BulkInserter(models.SourceProgress)
            for ps in parsed_sources:
                sp_inserter.add_entry(
                    lt_realization_id=lt_rlz.id, parsed_source_id=ps.id)
            sp_inserter.flush()

            # update the seed for the next realization
            seed = rnd.randint(MIN_SINT_32, MAX_SINT_32)

    def pre_execute(self):

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # (if a site model was specified, that is).
        self.initialize_site_model()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        self.initialize_realizations()
