from openquake.calculators import base
from openquake.commonlib import readinput
from openquake.hazardlib.calc.gmf import ground_motion_fields
from openquake.commonlib.export import export


@base.calculators.add('my_scenario')
class MyScenarioCalculator(base.BaseCalculator):
    def pre_execute(self):
        self.sitecol = readinput.get_site_collection(self.oqparam)
        [self.gsim] = readinput.get_gsims(self.oqparam)
        self.imts = readinput.get_imts(self.oqparam)
        self.rupture = readinput.get_rupture(self.oqparam)
        self.rupture_tags = [  # used in the export phase
            'tag%d' % i
            for i in range(self.oqparam.number_of_ground_motion_fields)]

    def execute(self):
        gmfs_by_imt = ground_motion_fields(
            self.rupture, self.sitecol, self.imts, self.gsim,
            self.oqparam.truncation_level,
            self.oqparam.number_of_ground_motion_fields,
            correlation_model=readinput.get_correl_model(self.oqparam),
            seed=self.oqparam.random_seed)
        return gmfs_by_imt

    def post_execute(self, result):
        result = {str(imt): gmvs for imt, gmvs in result.items()}
        out = export('gmf_xml', self.oqparam.export_dir, self.sitecol,
                     self.rupture_tags, result)
        return out
