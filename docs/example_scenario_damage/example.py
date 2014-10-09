import sys
import logging
from openquake.risklib import scientific
from openquake.commonlib.readini import parse_config
from openquake.commonlib.riskmodels import get_risk_model
from openquake.commonlib.calc import run_scenario

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with open(sys.argv[1]) as job_ini:
        oqparam = parse_config(job_ini, hazard_output_id=1)
        damage_states = get_risk_model(oqparam).damage_states
        aggfractions = run_scenario(oqparam)

        for taxonomy, fractions in aggfractions.iteritems():
            means, stds = scientific.mean_std(fractions)
            for damage_state, mean, std in zip(damage_states, means, stds):
                print taxonomy, damage_state, mean, std
