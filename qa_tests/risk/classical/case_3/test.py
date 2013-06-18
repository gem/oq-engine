# Copyright (c) 2013, GEM Foundation.
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
from nose.plugins.attrib import attr

from qa_tests import risk

from openquake.engine.db import models


class ClassicalRiskCase3TestCase(risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

    EXPECTED_LOSS_FRACTION = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossFraction investigationTime="50.00" poE="0.1000" sourceModelTreePath="b1" gsimTreePath="b1" lossCategory="buildings" unit="USD" variable="taxonomy">
    <total>
      <bin value="RC" absoluteLoss="2.1260e+07" fraction="0.00211"/>
      <bin value="W" absoluteLoss="7.6442e+08" fraction="0.07584"/>
      <bin value="UFB" absoluteLoss="1.8089e+09" fraction="0.17945"/>
      <bin value="DS" absoluteLoss="2.7797e+09" fraction="0.27576"/>
      <bin value="A" absoluteLoss="4.7058e+09" fraction="0.46684"/>
    </total>
    <map>
      <node lon="80.317596" lat="28.87">
        <bin value="RC" absoluteLoss="3.1933e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.1323e+07" fraction="0.07395"/>
        <bin value="UFB" absoluteLoss="2.7211e+07" fraction="0.17772"/>
        <bin value="DS" absoluteLoss="4.2582e+07" fraction="0.27811"/>
        <bin value="A" absoluteLoss="7.1676e+07" fraction="0.46813"/>
      </node>
      <node lon="80.484397" lat="29.2275">
        <bin value="RC" absoluteLoss="1.1353e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="4.0707e+06" fraction="0.07547"/>
        <bin value="UFB" absoluteLoss="9.6465e+06" fraction="0.17884"/>
        <bin value="DS" absoluteLoss="1.4874e+07" fraction="0.27576"/>
        <bin value="A" absoluteLoss="2.5234e+07" fraction="0.46782"/>
      </node>
      <node lon="80.562103" lat="29.5104">
        <bin value="RC" absoluteLoss="1.9053e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="6.8209e+06" fraction="0.07550"/>
        <bin value="UFB" absoluteLoss="1.6160e+07" fraction="0.17886"/>
        <bin value="DS" absoluteLoss="2.4909e+07" fraction="0.27571"/>
        <bin value="A" absoluteLoss="4.2265e+07" fraction="0.46782"/>
      </node>
      <node lon="80.782897" lat="29.890699">
        <bin value="RC" absoluteLoss="1.0798e+05" fraction="0.00212"/>
        <bin value="W" absoluteLoss="3.8783e+06" fraction="0.07606"/>
        <bin value="UFB" absoluteLoss="9.1427e+06" fraction="0.17929"/>
        <bin value="DS" absoluteLoss="1.4014e+07" fraction="0.27483"/>
        <bin value="A" absoluteLoss="2.3849e+07" fraction="0.46770"/>
      </node>
      <node lon="80.873497" lat="28.7436">
        <bin value="RC" absoluteLoss="5.8706e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="2.1020e+07" fraction="0.07513"/>
        <bin value="UFB" absoluteLoss="4.9962e+07" fraction="0.17856"/>
        <bin value="DS" absoluteLoss="7.7298e+07" fraction="0.27626"/>
        <bin value="A" absoluteLoss="1.3094e+08" fraction="0.46796"/>
      </node>
      <node lon="80.891998" lat="29.173">
        <bin value="RC" absoluteLoss="1.7506e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="6.2802e+06" fraction="0.07556"/>
        <bin value="UFB" absoluteLoss="1.4870e+07" fraction="0.17891"/>
        <bin value="DS" absoluteLoss="2.2905e+07" fraction="0.27560"/>
        <bin value="A" absoluteLoss="3.8880e+07" fraction="0.46781"/>
      </node>
      <node lon="81.1791" lat="29.7136">
        <bin value="RC" absoluteLoss="2.2031e+05" fraction="0.00220"/>
        <bin value="W" absoluteLoss="8.4112e+06" fraction="0.08414"/>
        <bin value="UFB" absoluteLoss="1.8607e+07" fraction="0.18614"/>
        <bin value="DS" absoluteLoss="2.6252e+07" fraction="0.26262"/>
        <bin value="A" absoluteLoss="4.6470e+07" fraction="0.46488"/>
      </node>
      <node lon="81.2985" lat="29.1098">
        <bin value="RC" absoluteLoss="2.0680e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="7.4578e+06" fraction="0.07583"/>
        <bin value="UFB" absoluteLoss="1.7617e+07" fraction="0.17913"/>
        <bin value="DS" absoluteLoss="2.7062e+07" fraction="0.27516"/>
        <bin value="A" absoluteLoss="4.6005e+07" fraction="0.46777"/>
      </node>
      <node lon="81.395103" lat="28.386699">
        <bin value="RC" absoluteLoss="3.4042e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.2153e+07" fraction="0.07496"/>
        <bin value="UFB" absoluteLoss="2.8929e+07" fraction="0.17844"/>
        <bin value="DS" absoluteLoss="4.4828e+07" fraction="0.27651"/>
        <bin value="A" absoluteLoss="7.5869e+07" fraction="0.46798"/>
      </node>
      <node lon="81.568496" lat="29.564199">
        <bin value="RC" absoluteLoss="1.6863e+05" fraction="0.00222"/>
        <bin value="W" absoluteLoss="6.4573e+06" fraction="0.08493"/>
        <bin value="UFB" absoluteLoss="1.4201e+07" fraction="0.18677"/>
        <bin value="DS" absoluteLoss="1.9890e+07" fraction="0.26160"/>
        <bin value="A" absoluteLoss="3.5317e+07" fraction="0.46449"/>
      </node>
      <node lon="81.586196" lat="28.638599">
        <bin value="RC" absoluteLoss="3.0548e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.0944e+07" fraction="0.07543"/>
        <bin value="UFB" absoluteLoss="2.5942e+07" fraction="0.17880"/>
        <bin value="DS" absoluteLoss="4.0020e+07" fraction="0.27584"/>
        <bin value="A" absoluteLoss="6.7876e+07" fraction="0.46783"/>
      </node>
      <node lon="81.687698" lat="28.877599">
        <bin value="RC" absoluteLoss="2.0793e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="7.4880e+06" fraction="0.07571"/>
        <bin value="UFB" absoluteLoss="1.7707e+07" fraction="0.17903"/>
        <bin value="DS" absoluteLoss="2.7236e+07" fraction="0.27537"/>
        <bin value="A" absoluteLoss="4.6268e+07" fraction="0.46779"/>
      </node>
      <node lon="81.755996" lat="29.1923">
        <bin value="RC" absoluteLoss="1.2244e+05" fraction="0.00215"/>
        <bin value="W" absoluteLoss="4.5570e+06" fraction="0.07996"/>
        <bin value="UFB" absoluteLoss="1.0409e+07" fraction="0.18263"/>
        <bin value="DS" absoluteLoss="1.5303e+07" fraction="0.26851"/>
        <bin value="A" absoluteLoss="2.6602e+07" fraction="0.46675"/>
      </node>
      <node lon="81.825302" lat="28.0893">
        <bin value="RC" absoluteLoss="3.7214e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.3212e+07" fraction="0.07415"/>
        <bin value="UFB" absoluteLoss="3.1693e+07" fraction="0.17786"/>
        <bin value="DS" absoluteLoss="4.9504e+07" fraction="0.27781"/>
        <bin value="A" absoluteLoss="8.3408e+07" fraction="0.46809"/>
      </node>
      <node lon="81.8899" lat="30.038799">
        <bin value="RC" absoluteLoss="2.4450e+04" fraction="0.00200"/>
        <bin value="W" absoluteLoss="8.2342e+05" fraction="0.06751"/>
        <bin value="UFB" absoluteLoss="2.1101e+06" fraction="0.17300"/>
        <bin value="DS" absoluteLoss="3.5278e+06" fraction="0.28924"/>
        <bin value="A" absoluteLoss="5.7108e+06" fraction="0.46823"/>
      </node>
      <node lon="82.141197" lat="28.3924">
        <bin value="RC" absoluteLoss="1.8910e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="6.7590e+06" fraction="0.07480"/>
        <bin value="UFB" absoluteLoss="1.6113e+07" fraction="0.17833"/>
        <bin value="DS" absoluteLoss="2.5009e+07" fraction="0.27678"/>
        <bin value="A" absoluteLoss="4.2287e+07" fraction="0.46800"/>
      </node>
      <node lon="82.170402" lat="28.863899">
        <bin value="RC" absoluteLoss="1.4231e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="5.1620e+06" fraction="0.07740"/>
        <bin value="UFB" absoluteLoss="1.2033e+07" fraction="0.18044"/>
        <bin value="DS" absoluteLoss="1.8179e+07" fraction="0.27259"/>
        <bin value="A" absoluteLoss="3.1174e+07" fraction="0.46744"/>
      </node>
      <node lon="82.222396" lat="29.2712">
        <bin value="RC" absoluteLoss="1.3302e+05" fraction="0.00223"/>
        <bin value="W" absoluteLoss="5.0960e+06" fraction="0.08530"/>
        <bin value="UFB" absoluteLoss="1.1177e+07" fraction="0.18710"/>
        <bin value="DS" absoluteLoss="1.5599e+07" fraction="0.26110"/>
        <bin value="A" absoluteLoss="2.7736e+07" fraction="0.46427"/>
      </node>
      <node lon="82.374801" lat="29.6196">
        <bin value="RC" absoluteLoss="4.1908e+04" fraction="0.00213"/>
        <bin value="W" absoluteLoss="1.4958e+06" fraction="0.07597"/>
        <bin value="UFB" absoluteLoss="3.5297e+06" fraction="0.17926"/>
        <bin value="DS" absoluteLoss="5.4123e+06" fraction="0.27487"/>
        <bin value="A" absoluteLoss="9.2107e+06" fraction="0.46778"/>
      </node>
      <node lon="82.419197" lat="27.956699">
        <bin value="RC" absoluteLoss="4.1583e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.4471e+07" fraction="0.07202"/>
        <bin value="UFB" absoluteLoss="3.5438e+07" fraction="0.17638"/>
        <bin value="DS" absoluteLoss="5.6477e+07" fraction="0.28110"/>
        <bin value="A" absoluteLoss="9.4115e+07" fraction="0.46843"/>
      </node>
      <node lon="82.623497" lat="28.335199">
        <bin value="RC" absoluteLoss="1.5409e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="5.3339e+06" fraction="0.07156"/>
        <bin value="UFB" absoluteLoss="1.3124e+07" fraction="0.17607"/>
        <bin value="DS" absoluteLoss="2.1005e+07" fraction="0.28180"/>
        <bin value="A" absoluteLoss="3.4921e+07" fraction="0.46850"/>
      </node>
      <node lon="82.663299" lat="28.6961">
        <bin value="RC" absoluteLoss="2.0027e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="7.3391e+06" fraction="0.07797"/>
        <bin value="UFB" absoluteLoss="1.7030e+07" fraction="0.18093"/>
        <bin value="DS" absoluteLoss="2.5567e+07" fraction="0.27163"/>
        <bin value="A" absoluteLoss="4.3987e+07" fraction="0.46733"/>
      </node>
      <node lon="82.866401" lat="28.106399">
        <bin value="RC" absoluteLoss="1.6977e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="5.9151e+06" fraction="0.07191"/>
        <bin value="UFB" absoluteLoss="1.4501e+07" fraction="0.17631"/>
        <bin value="DS" absoluteLoss="2.3135e+07" fraction="0.28127"/>
        <bin value="A" absoluteLoss="3.8530e+07" fraction="0.46844"/>
      </node>
      <node lon="82.991096" lat="27.6296">
        <bin value="RC" absoluteLoss="3.0092e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.0356e+07" fraction="0.07055"/>
        <bin value="UFB" absoluteLoss="2.5733e+07" fraction="0.17531"/>
        <bin value="DS" absoluteLoss="4.1624e+07" fraction="0.28357"/>
        <bin value="A" absoluteLoss="6.8770e+07" fraction="0.46851"/>
      </node>
      <node lon="83.055496" lat="29.165199">
        <bin value="RC" absoluteLoss="3.1637e+04" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.1603e+06" fraction="0.07595"/>
        <bin value="UFB" absoluteLoss="2.7376e+06" fraction="0.17919"/>
        <bin value="DS" absoluteLoss="4.2019e+06" fraction="0.27504"/>
        <bin value="A" absoluteLoss="7.1461e+06" fraction="0.46775"/>
      </node>
      <node lon="83.082298" lat="27.9006">
        <bin value="RC" absoluteLoss="1.6588e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="5.7750e+06" fraction="0.07185"/>
        <bin value="UFB" absoluteLoss="1.4168e+07" fraction="0.17627"/>
        <bin value="DS" absoluteLoss="2.2616e+07" fraction="0.28137"/>
        <bin value="A" absoluteLoss="3.7651e+07" fraction="0.46844"/>
      </node>
      <node lon="83.250999" lat="28.340499">
        <bin value="RC" absoluteLoss="2.4345e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="8.6445e+06" fraction="0.07413"/>
        <bin value="UFB" absoluteLoss="2.0735e+07" fraction="0.17782"/>
        <bin value="DS" absoluteLoss="3.2401e+07" fraction="0.27786"/>
        <bin value="A" absoluteLoss="5.4582e+07" fraction="0.46809"/>
      </node>
      <node lon="83.294197" lat="28.091299">
        <bin value="RC" absoluteLoss="2.3480e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="8.1790e+06" fraction="0.07221"/>
        <bin value="UFB" absoluteLoss="1.9992e+07" fraction="0.17649"/>
        <bin value="DS" absoluteLoss="3.1812e+07" fraction="0.28084"/>
        <bin value="A" absoluteLoss="5.3057e+07" fraction="0.46839"/>
      </node>
      <node lon="83.394302" lat="27.575799">
        <bin value="RC" absoluteLoss="5.5924e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="1.9297e+07" fraction="0.07101"/>
        <bin value="UFB" absoluteLoss="4.7755e+07" fraction="0.17574"/>
        <bin value="DS" absoluteLoss="7.6795e+07" fraction="0.28261"/>
        <bin value="A" absoluteLoss="1.2733e+08" fraction="0.46858"/>
      </node>
      <node lon="83.464302" lat="28.5414">
        <bin value="RC" absoluteLoss="1.5701e+05" fraction="0.00216"/>
        <bin value="W" absoluteLoss="5.9031e+06" fraction="0.08122"/>
        <bin value="UFB" absoluteLoss="1.3352e+07" fraction="0.18371"/>
        <bin value="DS" absoluteLoss="1.9378e+07" fraction="0.26663"/>
        <bin value="A" absoluteLoss="3.3888e+07" fraction="0.46627"/>
      </node>
      <node lon="83.633102" lat="27.8064">
        <bin value="RC" absoluteLoss="2.1223e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="7.3711e+06" fraction="0.07198"/>
        <bin value="UFB" absoluteLoss="1.8059e+07" fraction="0.17635"/>
        <bin value="DS" absoluteLoss="2.8793e+07" fraction="0.28117"/>
        <bin value="A" absoluteLoss="4.7971e+07" fraction="0.46843"/>
      </node>
      <node lon="83.686996" lat="28.200899">
        <bin value="RC" absoluteLoss="1.5277e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="5.5172e+06" fraction="0.07585"/>
        <bin value="UFB" absoluteLoss="1.3030e+07" fraction="0.17914"/>
        <bin value="DS" absoluteLoss="2.0014e+07" fraction="0.27515"/>
        <bin value="A" absoluteLoss="3.4025e+07" fraction="0.46776"/>
      </node>
      <node lon="83.819801" lat="28.020399">
        <bin value="RC" absoluteLoss="2.6052e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="9.1710e+06" fraction="0.07314"/>
        <bin value="UFB" absoluteLoss="2.2210e+07" fraction="0.17712"/>
        <bin value="DS" absoluteLoss="3.5041e+07" fraction="0.27944"/>
        <bin value="A" absoluteLoss="5.8714e+07" fraction="0.46822"/>
      </node>
      <node lon="83.837402" lat="28.968599">
        <bin value="RC" absoluteLoss="8.4220e+03" fraction="0.00195"/>
        <bin value="W" absoluteLoss="2.9185e+05" fraction="0.06747"/>
        <bin value="UFB" absoluteLoss="7.4825e+05" fraction="0.17299"/>
        <bin value="DS" absoluteLoss="1.2518e+06" fraction="0.28941"/>
        <bin value="A" absoluteLoss="2.0250e+06" fraction="0.46817"/>
      </node>
      <node lon="83.969902" lat="27.6322">
        <bin value="RC" absoluteLoss="4.5247e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.5687e+07" fraction="0.07159"/>
        <bin value="UFB" absoluteLoss="3.8586e+07" fraction="0.17610"/>
        <bin value="DS" absoluteLoss="6.1736e+07" fraction="0.28175"/>
        <bin value="A" absoluteLoss="1.0265e+08" fraction="0.46849"/>
      </node>
      <node lon="84.005996" lat="28.350099">
        <bin value="RC" absoluteLoss="7.2134e+05" fraction="0.00217"/>
        <bin value="W" absoluteLoss="2.7071e+07" fraction="0.08145"/>
        <bin value="UFB" absoluteLoss="6.1119e+07" fraction="0.18388"/>
        <bin value="DS" absoluteLoss="8.8512e+07" fraction="0.26630"/>
        <bin value="A" absoluteLoss="1.5496e+08" fraction="0.46620"/>
      </node>
      <node lon="84.229103" lat="28.669099">
        <bin value="RC" absoluteLoss="7.3431e+03" fraction="0.00213"/>
        <bin value="W" absoluteLoss="2.7255e+05" fraction="0.07909"/>
        <bin value="UFB" absoluteLoss="6.2561e+05" fraction="0.18154"/>
        <bin value="DS" absoluteLoss="9.3047e+05" fraction="0.27000"/>
        <bin value="A" absoluteLoss="1.6102e+06" fraction="0.46724"/>
      </node>
      <node lon="84.261001" lat="27.9458">
        <bin value="RC" absoluteLoss="3.2956e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.1832e+07" fraction="0.07545"/>
        <bin value="UFB" absoluteLoss="2.8043e+07" fraction="0.17882"/>
        <bin value="DS" absoluteLoss="4.3255e+07" fraction="0.27582"/>
        <bin value="A" absoluteLoss="7.3364e+07" fraction="0.46781"/>
      </node>
      <node lon="84.438796" lat="28.282499">
        <bin value="RC" absoluteLoss="2.7412e+05" fraction="0.00220"/>
        <bin value="W" absoluteLoss="1.0483e+07" fraction="0.08415"/>
        <bin value="UFB" absoluteLoss="2.3189e+07" fraction="0.18615"/>
        <bin value="DS" absoluteLoss="3.2713e+07" fraction="0.26260"/>
        <bin value="A" absoluteLoss="5.7913e+07" fraction="0.46490"/>
      </node>
      <node lon="84.449501" lat="27.581399">
        <bin value="RC" absoluteLoss="4.8751e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.7091e+07" fraction="0.07267"/>
        <bin value="UFB" absoluteLoss="4.1576e+07" fraction="0.17679"/>
        <bin value="DS" absoluteLoss="6.5882e+07" fraction="0.28014"/>
        <bin value="A" absoluteLoss="1.1014e+08" fraction="0.46833"/>
      </node>
      <node lon="84.785598" lat="27.2308">
        <bin value="RC" absoluteLoss="3.3473e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.1600e+07" fraction="0.07158"/>
        <bin value="UFB" absoluteLoss="2.8537e+07" fraction="0.17611"/>
        <bin value="DS" absoluteLoss="4.5656e+07" fraction="0.28175"/>
        <bin value="A" absoluteLoss="7.5918e+07" fraction="0.46849"/>
      </node>
      <node lon="84.801597" lat="28.312799">
        <bin value="RC" absoluteLoss="4.9774e+05" fraction="0.00224"/>
        <bin value="W" absoluteLoss="1.9482e+07" fraction="0.08763"/>
        <bin value="UFB" absoluteLoss="4.2030e+07" fraction="0.18906"/>
        <bin value="DS" absoluteLoss="5.7395e+07" fraction="0.25818"/>
        <bin value="A" absoluteLoss="1.0291e+08" fraction="0.46289"/>
      </node>
      <node lon="84.961799" lat="27.935199">
        <bin value="RC" absoluteLoss="5.3189e+05" fraction="0.00223"/>
        <bin value="W" absoluteLoss="2.0684e+07" fraction="0.08665"/>
        <bin value="UFB" absoluteLoss="4.4931e+07" fraction="0.18823"/>
        <bin value="DS" absoluteLoss="6.1919e+07" fraction="0.25940"/>
        <bin value="A" absoluteLoss="1.1063e+08" fraction="0.46348"/>
      </node>
      <node lon="85.066703" lat="27.1018">
        <bin value="RC" absoluteLoss="3.6620e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.2606e+07" fraction="0.07072"/>
        <bin value="UFB" absoluteLoss="3.1293e+07" fraction="0.17556"/>
        <bin value="DS" absoluteLoss="5.0448e+07" fraction="0.28303"/>
        <bin value="A" absoluteLoss="8.3532e+07" fraction="0.46864"/>
      </node>
      <node lon="85.092498" lat="27.455999">
        <bin value="RC" absoluteLoss="3.0830e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.0724e+07" fraction="0.07198"/>
        <bin value="UFB" absoluteLoss="2.6273e+07" fraction="0.17634"/>
        <bin value="DS" absoluteLoss="4.1892e+07" fraction="0.28118"/>
        <bin value="A" absoluteLoss="6.9790e+07" fraction="0.46843"/>
      </node>
      <node lon="85.242103" lat="27.902">
        <bin value="RC" absoluteLoss="4.6034e+05" fraction="0.00225"/>
        <bin value="W" absoluteLoss="1.8171e+07" fraction="0.08876"/>
        <bin value="UFB" absoluteLoss="3.8892e+07" fraction="0.18997"/>
        <bin value="DS" absoluteLoss="5.2577e+07" fraction="0.25682"/>
        <bin value="A" absoluteLoss="9.4625e+07" fraction="0.46221"/>
      </node>
      <node lon="85.303199" lat="26.9962">
        <bin value="RC" absoluteLoss="3.5023e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.2009e+07" fraction="0.07044"/>
        <bin value="UFB" absoluteLoss="2.9879e+07" fraction="0.17525"/>
        <bin value="DS" absoluteLoss="4.8367e+07" fraction="0.28368"/>
        <bin value="A" absoluteLoss="7.9891e+07" fraction="0.46858"/>
      </node>
      <node lon="85.347702" lat="27.523099">
        <bin value="RC" absoluteLoss="4.0376e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.4141e+07" fraction="0.07256"/>
        <bin value="UFB" absoluteLoss="3.4437e+07" fraction="0.17670"/>
        <bin value="DS" absoluteLoss="5.4633e+07" fraction="0.28033"/>
        <bin value="A" absoluteLoss="9.1275e+07" fraction="0.46834"/>
      </node>
      <node lon="85.3544" lat="27.712499">
        <bin value="RC" absoluteLoss="2.0956e+06" fraction="0.00213"/>
        <bin value="W" absoluteLoss="7.6587e+07" fraction="0.07793"/>
        <bin value="UFB" absoluteLoss="1.7776e+08" fraction="0.18087"/>
        <bin value="DS" absoluteLoss="2.6705e+08" fraction="0.27172"/>
        <bin value="A" absoluteLoss="4.5931e+08" fraction="0.46735"/>
      </node>
      <node lon="85.3908" lat="28.1667">
        <bin value="RC" absoluteLoss="8.0456e+04" fraction="0.00225"/>
        <bin value="W" absoluteLoss="3.2292e+06" fraction="0.09047"/>
        <bin value="UFB" absoluteLoss="6.8304e+06" fraction="0.19136"/>
        <bin value="DS" absoluteLoss="9.0958e+06" fraction="0.25483"/>
        <bin value="A" absoluteLoss="1.6457e+07" fraction="0.46108"/>
      </node>
      <node lon="85.438499" lat="27.6576">
        <bin value="RC" absoluteLoss="3.0250e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.0939e+07" fraction="0.07629"/>
        <bin value="UFB" absoluteLoss="2.5738e+07" fraction="0.17949"/>
        <bin value="DS" absoluteLoss="3.9346e+07" fraction="0.27439"/>
        <bin value="A" absoluteLoss="6.7070e+07" fraction="0.46772"/>
      </node>
      <node lon="85.583198" lat="26.981599">
        <bin value="RC" absoluteLoss="4.4290e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.5217e+07" fraction="0.07060"/>
        <bin value="UFB" absoluteLoss="3.7793e+07" fraction="0.17533"/>
        <bin value="DS" absoluteLoss="6.1099e+07" fraction="0.28345"/>
        <bin value="A" absoluteLoss="1.0101e+08" fraction="0.46858"/>
      </node>
      <node lon="85.627098" lat="27.5277">
        <bin value="RC" absoluteLoss="3.1179e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="1.1025e+07" fraction="0.07355"/>
        <bin value="UFB" absoluteLoss="2.6592e+07" fraction="0.17740"/>
        <bin value="DS" absoluteLoss="4.1792e+07" fraction="0.27881"/>
        <bin value="A" absoluteLoss="7.0174e+07" fraction="0.46815"/>
      </node>
      <node lon="85.747703" lat="27.9015">
        <bin value="RC" absoluteLoss="5.6760e+05" fraction="0.00228"/>
        <bin value="W" absoluteLoss="2.2681e+07" fraction="0.09118"/>
        <bin value="UFB" absoluteLoss="4.7748e+07" fraction="0.19194"/>
        <bin value="DS" absoluteLoss="6.3184e+07" fraction="0.25400"/>
        <bin value="A" absoluteLoss="1.1458e+08" fraction="0.46060"/>
      </node>
      <node lon="85.828697" lat="26.861799">
        <bin value="RC" absoluteLoss="3.6228e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.2435e+07" fraction="0.07032"/>
        <bin value="UFB" absoluteLoss="3.0977e+07" fraction="0.17517"/>
        <bin value="DS" absoluteLoss="5.0198e+07" fraction="0.28387"/>
        <bin value="A" absoluteLoss="8.2865e+07" fraction="0.46859"/>
      </node>
      <node lon="85.954299" lat="27.1849">
        <bin value="RC" absoluteLoss="2.0082e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="6.9418e+06" fraction="0.07138"/>
        <bin value="UFB" absoluteLoss="1.7113e+07" fraction="0.17596"/>
        <bin value="DS" absoluteLoss="2.7431e+07" fraction="0.28206"/>
        <bin value="A" absoluteLoss="4.5565e+07" fraction="0.46853"/>
      </node>
      <node lon="86.045402" lat="26.822999">
        <bin value="RC" absoluteLoss="4.5419e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.5593e+07" fraction="0.07046"/>
        <bin value="UFB" absoluteLoss="3.8786e+07" fraction="0.17527"/>
        <bin value="DS" absoluteLoss="6.2769e+07" fraction="0.28364"/>
        <bin value="A" absoluteLoss="1.0369e+08" fraction="0.46857"/>
      </node>
      <node lon="86.177299" lat="27.4869">
        <bin value="RC" absoluteLoss="1.8462e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="6.6320e+06" fraction="0.07537"/>
        <bin value="UFB" absoluteLoss="1.5727e+07" fraction="0.17874"/>
        <bin value="DS" absoluteLoss="2.4283e+07" fraction="0.27598"/>
        <bin value="A" absoluteLoss="4.1161e+07" fraction="0.46781"/>
      </node>
      <node lon="86.2117" lat="27.779499">
        <bin value="RC" absoluteLoss="3.8227e+05" fraction="0.00227"/>
        <bin value="W" absoluteLoss="1.5290e+07" fraction="0.09078"/>
        <bin value="UFB" absoluteLoss="3.2272e+07" fraction="0.19159"/>
        <bin value="DS" absoluteLoss="4.2860e+07" fraction="0.25446"/>
        <bin value="A" absoluteLoss="7.7634e+07" fraction="0.46090"/>
      </node>
      <node lon="86.352699" lat="26.743999">
        <bin value="RC" absoluteLoss="3.8478e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.3198e+07" fraction="0.07035"/>
        <bin value="UFB" absoluteLoss="3.2864e+07" fraction="0.17519"/>
        <bin value="DS" absoluteLoss="5.3243e+07" fraction="0.28382"/>
        <bin value="A" absoluteLoss="8.7905e+07" fraction="0.46859"/>
      </node>
      <node lon="86.4346" lat="27.3117">
        <bin value="RC" absoluteLoss="1.2193e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="4.2597e+06" fraction="0.07284"/>
        <bin value="UFB" absoluteLoss="1.0342e+07" fraction="0.17685"/>
        <bin value="DS" absoluteLoss="1.6376e+07" fraction="0.28002"/>
        <bin value="A" absoluteLoss="2.7382e+07" fraction="0.46821"/>
      </node>
      <node lon="86.7108" lat="26.891399">
        <bin value="RC" absoluteLoss="2.2585e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="7.7865e+06" fraction="0.07085"/>
        <bin value="UFB" absoluteLoss="1.9303e+07" fraction="0.17564"/>
        <bin value="DS" absoluteLoss="3.1086e+07" fraction="0.28285"/>
        <bin value="A" absoluteLoss="5.1500e+07" fraction="0.46860"/>
      </node>
      <node lon="86.725898" lat="27.7005">
        <bin value="RC" absoluteLoss="2.0217e+05" fraction="0.00228"/>
        <bin value="W" absoluteLoss="8.0705e+06" fraction="0.09108"/>
        <bin value="UFB" absoluteLoss="1.7001e+07" fraction="0.19187"/>
        <bin value="DS" absoluteLoss="2.2517e+07" fraction="0.25411"/>
        <bin value="A" absoluteLoss="4.0819e+07" fraction="0.46066"/>
      </node>
      <node lon="86.727203" lat="26.6039">
        <bin value="RC" absoluteLoss="3.6239e+05" fraction="0.00204"/>
        <bin value="W" absoluteLoss="1.2235e+07" fraction="0.06881"/>
        <bin value="UFB" absoluteLoss="3.0974e+07" fraction="0.17420"/>
        <bin value="DS" absoluteLoss="5.0895e+07" fraction="0.28624"/>
        <bin value="A" absoluteLoss="8.3342e+07" fraction="0.46872"/>
      </node>
      <node lon="86.7966" lat="27.146799">
        <bin value="RC" absoluteLoss="1.5097e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="5.2428e+06" fraction="0.07170"/>
        <bin value="UFB" absoluteLoss="1.2881e+07" fraction="0.17616"/>
        <bin value="DS" absoluteLoss="2.0591e+07" fraction="0.28160"/>
        <bin value="A" absoluteLoss="3.4257e+07" fraction="0.46848"/>
      </node>
      <node lon="87.080902" lat="27.1648">
        <bin value="RC" absoluteLoss="1.4134e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="4.9196e+06" fraction="0.07196"/>
        <bin value="UFB" absoluteLoss="1.2054e+07" fraction="0.17632"/>
        <bin value="DS" absoluteLoss="1.9226e+07" fraction="0.28123"/>
        <bin value="A" absoluteLoss="3.2022e+07" fraction="0.46841"/>
      </node>
      <node lon="87.170898" lat="26.635099">
        <bin value="RC" absoluteLoss="4.1003e+05" fraction="0.00202"/>
        <bin value="W" absoluteLoss="1.3694e+07" fraction="0.06735"/>
        <bin value="UFB" absoluteLoss="3.5139e+07" fraction="0.17282"/>
        <bin value="DS" absoluteLoss="5.8878e+07" fraction="0.28958"/>
        <bin value="A" absoluteLoss="9.5203e+07" fraction="0.46823"/>
      </node>
      <node lon="87.290298" lat="27.574899">
        <bin value="RC" absoluteLoss="2.7930e+05" fraction="0.00227"/>
        <bin value="W" absoluteLoss="1.1041e+07" fraction="0.08963"/>
        <bin value="UFB" absoluteLoss="2.3490e+07" fraction="0.19069"/>
        <bin value="DS" absoluteLoss="3.1507e+07" fraction="0.25578"/>
        <bin value="A" absoluteLoss="5.6864e+07" fraction="0.46163"/>
      </node>
      <node lon="87.343803" lat="26.969999">
        <bin value="RC" absoluteLoss="1.2974e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="4.4816e+06" fraction="0.07121"/>
        <bin value="UFB" absoluteLoss="1.1068e+07" fraction="0.17586"/>
        <bin value="DS" absoluteLoss="1.7767e+07" fraction="0.28230"/>
        <bin value="A" absoluteLoss="2.9490e+07" fraction="0.46857"/>
      </node>
      <node lon="87.481002" lat="26.6102">
        <bin value="RC" absoluteLoss="1.9795e+05" fraction="0.00188"/>
        <bin value="W" absoluteLoss="5.9141e+06" fraction="0.05618"/>
        <bin value="UFB" absoluteLoss="1.7528e+07" fraction="0.16649"/>
        <bin value="DS" absoluteLoss="3.3924e+07" fraction="0.32223"/>
        <bin value="A" absoluteLoss="4.7715e+07" fraction="0.45322"/>
      </node>
      <node lon="87.555702" lat="27.130899">
        <bin value="RC" absoluteLoss="7.2289e+04" fraction="0.00205"/>
        <bin value="W" absoluteLoss="2.4819e+06" fraction="0.07029"/>
        <bin value="UFB" absoluteLoss="6.1839e+06" fraction="0.17513"/>
        <bin value="DS" absoluteLoss="1.0027e+07" fraction="0.28399"/>
        <bin value="A" absoluteLoss="1.6544e+07" fraction="0.46854"/>
      </node>
      <node lon="87.769996" lat="27.085399">
        <bin value="RC" absoluteLoss="1.2932e+05" fraction="0.00204"/>
        <bin value="W" absoluteLoss="4.4045e+06" fraction="0.06958"/>
        <bin value="UFB" absoluteLoss="1.1057e+07" fraction="0.17466"/>
        <bin value="DS" absoluteLoss="1.8046e+07" fraction="0.28507"/>
        <bin value="A" absoluteLoss="2.9666e+07" fraction="0.46864"/>
      </node>
      <node lon="87.824996" lat="27.554599">
        <bin value="RC" absoluteLoss="9.9161e+04" fraction="0.00207"/>
        <bin value="W" absoluteLoss="3.4881e+06" fraction="0.07295"/>
        <bin value="UFB" absoluteLoss="8.4612e+06" fraction="0.17697"/>
        <bin value="DS" absoluteLoss="1.3378e+07" fraction="0.27980"/>
        <bin value="A" absoluteLoss="2.2386e+07" fraction="0.46821"/>
      </node>
      <node lon="87.911499" lat="26.571399">
        <bin value="RC" absoluteLoss="5.1859e+04" fraction="0.00179"/>
        <bin value="W" absoluteLoss="1.4826e+06" fraction="0.05106"/>
        <bin value="UFB" absoluteLoss="4.8042e+06" fraction="0.16546"/>
        <bin value="DS" absoluteLoss="1.0292e+07" fraction="0.35446"/>
        <bin value="A" absoluteLoss="1.2405e+07" fraction="0.42723"/>
      </node>
      <node lon="87.912498" lat="26.862899">
        <bin value="RC" absoluteLoss="1.5493e+05" fraction="0.00201"/>
        <bin value="W" absoluteLoss="5.1627e+06" fraction="0.06695"/>
        <bin value="UFB" absoluteLoss="1.3299e+07" fraction="0.17247"/>
        <bin value="DS" absoluteLoss="2.2407e+07" fraction="0.29058"/>
        <bin value="A" absoluteLoss="3.6086e+07" fraction="0.46799"/>
      </node>
    </map>
  </lossFraction>
</nrml>
"""

    @attr('qa', 'risk', 'classical', 'e2e')
    def test(self):
        self._run_test()

    def actual_xml_outputs(self, job):
        return models.Output.objects.filter(
            oq_job=job, output_type="loss_fraction").order_by('id')

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_FRACTION]
