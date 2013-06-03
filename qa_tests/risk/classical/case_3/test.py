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
      <bin value="RC" absoluteLoss="2.1263e+07" fraction="0.00211"/>
      <bin value="W" absoluteLoss="7.6455e+08" fraction="0.07584"/>
      <bin value="UFB" absoluteLoss="1.8091e+09" fraction="0.17945"/>
      <bin value="DS" absoluteLoss="2.7800e+09" fraction="0.27576"/>
      <bin value="A" absoluteLoss="4.7064e+09" fraction="0.46684"/>
    </total>
    <map>
      <node lon="80.317596" lat="28.87">
        <bin value="RC" absoluteLoss="3.1936e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.1324e+07" fraction="0.07395"/>
        <bin value="UFB" absoluteLoss="2.7213e+07" fraction="0.17772"/>
        <bin value="DS" absoluteLoss="4.2585e+07" fraction="0.27811"/>
        <bin value="A" absoluteLoss="7.1682e+07" fraction="0.46813"/>
      </node>
      <node lon="80.484397" lat="29.2275">
        <bin value="RC" absoluteLoss="1.1353e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="4.0705e+06" fraction="0.07547"/>
        <bin value="UFB" absoluteLoss="9.6460e+06" fraction="0.17884"/>
        <bin value="DS" absoluteLoss="1.4874e+07" fraction="0.27576"/>
        <bin value="A" absoluteLoss="2.5233e+07" fraction="0.46783"/>
      </node>
      <node lon="80.562103" lat="29.5104">
        <bin value="RC" absoluteLoss="1.9048e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="6.8192e+06" fraction="0.07549"/>
        <bin value="UFB" absoluteLoss="1.6156e+07" fraction="0.17886"/>
        <bin value="DS" absoluteLoss="2.4905e+07" fraction="0.27572"/>
        <bin value="A" absoluteLoss="4.2257e+07" fraction="0.46782"/>
      </node>
      <node lon="80.782897" lat="29.890699">
        <bin value="RC" absoluteLoss="1.0795e+05" fraction="0.00212"/>
        <bin value="W" absoluteLoss="3.8772e+06" fraction="0.07605"/>
        <bin value="UFB" absoluteLoss="9.1404e+06" fraction="0.17929"/>
        <bin value="DS" absoluteLoss="1.4012e+07" fraction="0.27484"/>
        <bin value="A" absoluteLoss="2.3844e+07" fraction="0.46770"/>
      </node>
      <node lon="80.873497" lat="28.7436">
        <bin value="RC" absoluteLoss="5.8707e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="2.1021e+07" fraction="0.07513"/>
        <bin value="UFB" absoluteLoss="4.9962e+07" fraction="0.17856"/>
        <bin value="DS" absoluteLoss="7.7299e+07" fraction="0.27626"/>
        <bin value="A" absoluteLoss="1.3094e+08" fraction="0.46796"/>
      </node>
      <node lon="80.891998" lat="29.173">
        <bin value="RC" absoluteLoss="1.7504e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="6.2792e+06" fraction="0.07556"/>
        <bin value="UFB" absoluteLoss="1.4868e+07" fraction="0.17891"/>
        <bin value="DS" absoluteLoss="2.2903e+07" fraction="0.27561"/>
        <bin value="A" absoluteLoss="3.8875e+07" fraction="0.46781"/>
      </node>
      <node lon="81.1791" lat="29.7136">
        <bin value="RC" absoluteLoss="2.2028e+05" fraction="0.00220"/>
        <bin value="W" absoluteLoss="8.4100e+06" fraction="0.08414"/>
        <bin value="UFB" absoluteLoss="1.8605e+07" fraction="0.18614"/>
        <bin value="DS" absoluteLoss="2.6250e+07" fraction="0.26263"/>
        <bin value="A" absoluteLoss="4.6465e+07" fraction="0.46489"/>
      </node>
      <node lon="81.2985" lat="29.1098">
        <bin value="RC" absoluteLoss="2.0676e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="7.4559e+06" fraction="0.07583"/>
        <bin value="UFB" absoluteLoss="1.7613e+07" fraction="0.17913"/>
        <bin value="DS" absoluteLoss="2.7057e+07" fraction="0.27517"/>
        <bin value="A" absoluteLoss="4.5996e+07" fraction="0.46777"/>
      </node>
      <node lon="81.395103" lat="28.386699">
        <bin value="RC" absoluteLoss="3.4043e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.2154e+07" fraction="0.07496"/>
        <bin value="UFB" absoluteLoss="2.8930e+07" fraction="0.17844"/>
        <bin value="DS" absoluteLoss="4.4829e+07" fraction="0.27651"/>
        <bin value="A" absoluteLoss="7.5871e+07" fraction="0.46798"/>
      </node>
      <node lon="81.568496" lat="29.564199">
        <bin value="RC" absoluteLoss="1.6862e+05" fraction="0.00222"/>
        <bin value="W" absoluteLoss="6.4568e+06" fraction="0.08493"/>
        <bin value="UFB" absoluteLoss="1.4200e+07" fraction="0.18677"/>
        <bin value="DS" absoluteLoss="1.9889e+07" fraction="0.26160"/>
        <bin value="A" absoluteLoss="3.5315e+07" fraction="0.46449"/>
      </node>
      <node lon="81.586196" lat="28.638599">
        <bin value="RC" absoluteLoss="3.0546e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.0943e+07" fraction="0.07543"/>
        <bin value="UFB" absoluteLoss="2.5940e+07" fraction="0.17880"/>
        <bin value="DS" absoluteLoss="4.0018e+07" fraction="0.27584"/>
        <bin value="A" absoluteLoss="6.7871e+07" fraction="0.46783"/>
      </node>
      <node lon="81.687698" lat="28.877599">
        <bin value="RC" absoluteLoss="2.0788e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="7.4860e+06" fraction="0.07570"/>
        <bin value="UFB" absoluteLoss="1.7703e+07" fraction="0.17903"/>
        <bin value="DS" absoluteLoss="2.7231e+07" fraction="0.27538"/>
        <bin value="A" absoluteLoss="4.6258e+07" fraction="0.46779"/>
      </node>
      <node lon="81.755996" lat="29.1923">
        <bin value="RC" absoluteLoss="1.2242e+05" fraction="0.00215"/>
        <bin value="W" absoluteLoss="4.5558e+06" fraction="0.07995"/>
        <bin value="UFB" absoluteLoss="1.0406e+07" fraction="0.18263"/>
        <bin value="DS" absoluteLoss="1.5301e+07" fraction="0.26852"/>
        <bin value="A" absoluteLoss="2.6596e+07" fraction="0.46675"/>
      </node>
      <node lon="81.825302" lat="28.0893">
        <bin value="RC" absoluteLoss="3.7212e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.3211e+07" fraction="0.07414"/>
        <bin value="UFB" absoluteLoss="3.1692e+07" fraction="0.17786"/>
        <bin value="DS" absoluteLoss="4.9502e+07" fraction="0.27782"/>
        <bin value="A" absoluteLoss="8.3405e+07" fraction="0.46809"/>
      </node>
      <node lon="81.8899" lat="30.038799">
        <bin value="RC" absoluteLoss="2.4450e+04" fraction="0.00200"/>
        <bin value="W" absoluteLoss="8.2343e+05" fraction="0.06751"/>
        <bin value="UFB" absoluteLoss="2.1101e+06" fraction="0.17300"/>
        <bin value="DS" absoluteLoss="3.5278e+06" fraction="0.28924"/>
        <bin value="A" absoluteLoss="5.7109e+06" fraction="0.46823"/>
      </node>
      <node lon="82.141197" lat="28.3924">
        <bin value="RC" absoluteLoss="1.8906e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="6.7571e+06" fraction="0.07480"/>
        <bin value="UFB" absoluteLoss="1.6110e+07" fraction="0.17833"/>
        <bin value="DS" absoluteLoss="2.5004e+07" fraction="0.27679"/>
        <bin value="A" absoluteLoss="4.2278e+07" fraction="0.46800"/>
      </node>
      <node lon="82.170402" lat="28.863899">
        <bin value="RC" absoluteLoss="1.4226e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="5.1601e+06" fraction="0.07740"/>
        <bin value="UFB" absoluteLoss="1.2030e+07" fraction="0.18043"/>
        <bin value="DS" absoluteLoss="1.8174e+07" fraction="0.27260"/>
        <bin value="A" absoluteLoss="3.1165e+07" fraction="0.46744"/>
      </node>
      <node lon="82.222396" lat="29.2712">
        <bin value="RC" absoluteLoss="1.3301e+05" fraction="0.00223"/>
        <bin value="W" absoluteLoss="5.0958e+06" fraction="0.08530"/>
        <bin value="UFB" absoluteLoss="1.1177e+07" fraction="0.18710"/>
        <bin value="DS" absoluteLoss="1.5599e+07" fraction="0.26111"/>
        <bin value="A" absoluteLoss="2.7736e+07" fraction="0.46427"/>
      </node>
      <node lon="82.374801" lat="29.6196">
        <bin value="RC" absoluteLoss="4.1909e+04" fraction="0.00213"/>
        <bin value="W" absoluteLoss="1.4958e+06" fraction="0.07597"/>
        <bin value="UFB" absoluteLoss="3.5298e+06" fraction="0.17926"/>
        <bin value="DS" absoluteLoss="5.4124e+06" fraction="0.27487"/>
        <bin value="A" absoluteLoss="9.2109e+06" fraction="0.46778"/>
      </node>
      <node lon="82.419197" lat="27.956699">
        <bin value="RC" absoluteLoss="4.1572e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.4466e+07" fraction="0.07202"/>
        <bin value="UFB" absoluteLoss="3.5429e+07" fraction="0.17638"/>
        <bin value="DS" absoluteLoss="5.6466e+07" fraction="0.28111"/>
        <bin value="A" absoluteLoss="9.4094e+07" fraction="0.46843"/>
      </node>
      <node lon="82.623497" lat="28.335199">
        <bin value="RC" absoluteLoss="1.5399e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="5.3296e+06" fraction="0.07154"/>
        <bin value="UFB" absoluteLoss="1.3116e+07" fraction="0.17606"/>
        <bin value="DS" absoluteLoss="2.0994e+07" fraction="0.28182"/>
        <bin value="A" absoluteLoss="3.4901e+07" fraction="0.46850"/>
      </node>
      <node lon="82.663299" lat="28.6961">
        <bin value="RC" absoluteLoss="2.0021e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="7.3366e+06" fraction="0.07797"/>
        <bin value="UFB" absoluteLoss="1.7025e+07" fraction="0.18093"/>
        <bin value="DS" absoluteLoss="2.5561e+07" fraction="0.27164"/>
        <bin value="A" absoluteLoss="4.3975e+07" fraction="0.46733"/>
      </node>
      <node lon="82.866401" lat="28.106399">
        <bin value="RC" absoluteLoss="1.6969e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="5.9118e+06" fraction="0.07190"/>
        <bin value="UFB" absoluteLoss="1.4495e+07" fraction="0.17630"/>
        <bin value="DS" absoluteLoss="2.3127e+07" fraction="0.28129"/>
        <bin value="A" absoluteLoss="3.8514e+07" fraction="0.46844"/>
      </node>
      <node lon="82.991096" lat="27.6296">
        <bin value="RC" absoluteLoss="3.0103e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.0361e+07" fraction="0.07056"/>
        <bin value="UFB" absoluteLoss="2.5742e+07" fraction="0.17531"/>
        <bin value="DS" absoluteLoss="4.1639e+07" fraction="0.28357"/>
        <bin value="A" absoluteLoss="6.8793e+07" fraction="0.46851"/>
      </node>
      <node lon="83.055496" lat="29.165199">
        <bin value="RC" absoluteLoss="3.1638e+04" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.1603e+06" fraction="0.07595"/>
        <bin value="UFB" absoluteLoss="2.7377e+06" fraction="0.17919"/>
        <bin value="DS" absoluteLoss="4.2020e+06" fraction="0.27504"/>
        <bin value="A" absoluteLoss="7.1463e+06" fraction="0.46775"/>
      </node>
      <node lon="83.082298" lat="27.9006">
        <bin value="RC" absoluteLoss="1.6586e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="5.7741e+06" fraction="0.07185"/>
        <bin value="UFB" absoluteLoss="1.4166e+07" fraction="0.17627"/>
        <bin value="DS" absoluteLoss="2.2613e+07" fraction="0.28138"/>
        <bin value="A" absoluteLoss="3.7647e+07" fraction="0.46844"/>
      </node>
      <node lon="83.250999" lat="28.340499">
        <bin value="RC" absoluteLoss="2.4333e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="8.6393e+06" fraction="0.07412"/>
        <bin value="UFB" absoluteLoss="2.0725e+07" fraction="0.17782"/>
        <bin value="DS" absoluteLoss="3.2388e+07" fraction="0.27788"/>
        <bin value="A" absoluteLoss="5.4558e+07" fraction="0.46809"/>
      </node>
      <node lon="83.294197" lat="28.091299">
        <bin value="RC" absoluteLoss="2.3474e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="8.1764e+06" fraction="0.07220"/>
        <bin value="UFB" absoluteLoss="1.9987e+07" fraction="0.17649"/>
        <bin value="DS" absoluteLoss="3.1805e+07" fraction="0.28085"/>
        <bin value="A" absoluteLoss="5.3045e+07" fraction="0.46839"/>
      </node>
      <node lon="83.394302" lat="27.575799">
        <bin value="RC" absoluteLoss="5.5947e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="1.9306e+07" fraction="0.07102"/>
        <bin value="UFB" absoluteLoss="4.7774e+07" fraction="0.17575"/>
        <bin value="DS" absoluteLoss="7.6818e+07" fraction="0.28259"/>
        <bin value="A" absoluteLoss="1.2738e+08" fraction="0.46858"/>
      </node>
      <node lon="83.464302" lat="28.5414">
        <bin value="RC" absoluteLoss="1.5694e+05" fraction="0.00216"/>
        <bin value="W" absoluteLoss="5.9001e+06" fraction="0.08121"/>
        <bin value="UFB" absoluteLoss="1.3346e+07" fraction="0.18371"/>
        <bin value="DS" absoluteLoss="1.9371e+07" fraction="0.26664"/>
        <bin value="A" absoluteLoss="3.3875e+07" fraction="0.46628"/>
      </node>
      <node lon="83.633102" lat="27.8064">
        <bin value="RC" absoluteLoss="2.1222e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="7.3707e+06" fraction="0.07198"/>
        <bin value="UFB" absoluteLoss="1.8058e+07" fraction="0.17635"/>
        <bin value="DS" absoluteLoss="2.8792e+07" fraction="0.28117"/>
        <bin value="A" absoluteLoss="4.7969e+07" fraction="0.46843"/>
      </node>
      <node lon="83.686996" lat="28.200899">
        <bin value="RC" absoluteLoss="1.5271e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="5.5148e+06" fraction="0.07584"/>
        <bin value="UFB" absoluteLoss="1.3025e+07" fraction="0.17913"/>
        <bin value="DS" absoluteLoss="2.0008e+07" fraction="0.27516"/>
        <bin value="A" absoluteLoss="3.4013e+07" fraction="0.46777"/>
      </node>
      <node lon="83.819801" lat="28.020399">
        <bin value="RC" absoluteLoss="2.6044e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="9.1678e+06" fraction="0.07313"/>
        <bin value="UFB" absoluteLoss="2.2204e+07" fraction="0.17711"/>
        <bin value="DS" absoluteLoss="3.5034e+07" fraction="0.27946"/>
        <bin value="A" absoluteLoss="5.8699e+07" fraction="0.46822"/>
      </node>
      <node lon="83.837402" lat="28.968599">
        <bin value="RC" absoluteLoss="8.4211e+03" fraction="0.00195"/>
        <bin value="W" absoluteLoss="2.9181e+05" fraction="0.06747"/>
        <bin value="UFB" absoluteLoss="7.4817e+05" fraction="0.17299"/>
        <bin value="DS" absoluteLoss="1.2517e+06" fraction="0.28942"/>
        <bin value="A" absoluteLoss="2.0248e+06" fraction="0.46817"/>
      </node>
      <node lon="83.969902" lat="27.6322">
        <bin value="RC" absoluteLoss="4.5240e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="1.5684e+07" fraction="0.07159"/>
        <bin value="UFB" absoluteLoss="3.8580e+07" fraction="0.17610"/>
        <bin value="DS" absoluteLoss="6.1729e+07" fraction="0.28176"/>
        <bin value="A" absoluteLoss="1.0264e+08" fraction="0.46849"/>
      </node>
      <node lon="84.005996" lat="28.350099">
        <bin value="RC" absoluteLoss="7.2101e+05" fraction="0.00217"/>
        <bin value="W" absoluteLoss="2.7057e+07" fraction="0.08144"/>
        <bin value="UFB" absoluteLoss="6.1092e+07" fraction="0.18387"/>
        <bin value="DS" absoluteLoss="8.8481e+07" fraction="0.26631"/>
        <bin value="A" absoluteLoss="1.5490e+08" fraction="0.46621"/>
      </node>
      <node lon="84.229103" lat="28.669099">
        <bin value="RC" absoluteLoss="7.3420e+03" fraction="0.00213"/>
        <bin value="W" absoluteLoss="2.7251e+05" fraction="0.07909"/>
        <bin value="UFB" absoluteLoss="6.2551e+05" fraction="0.18153"/>
        <bin value="DS" absoluteLoss="9.3035e+05" fraction="0.27001"/>
        <bin value="A" absoluteLoss="1.6100e+06" fraction="0.46724"/>
      </node>
      <node lon="84.261001" lat="27.9458">
        <bin value="RC" absoluteLoss="3.2941e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.1826e+07" fraction="0.07544"/>
        <bin value="UFB" absoluteLoss="2.8030e+07" fraction="0.17881"/>
        <bin value="DS" absoluteLoss="4.3240e+07" fraction="0.27583"/>
        <bin value="A" absoluteLoss="7.3335e+07" fraction="0.46781"/>
      </node>
      <node lon="84.438796" lat="28.282499">
        <bin value="RC" absoluteLoss="2.7400e+05" fraction="0.00220"/>
        <bin value="W" absoluteLoss="1.0478e+07" fraction="0.08414"/>
        <bin value="UFB" absoluteLoss="2.3178e+07" fraction="0.18614"/>
        <bin value="DS" absoluteLoss="3.2702e+07" fraction="0.26262"/>
        <bin value="A" absoluteLoss="5.7891e+07" fraction="0.46490"/>
      </node>
      <node lon="84.449501" lat="27.581399">
        <bin value="RC" absoluteLoss="4.8717e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.7077e+07" fraction="0.07266"/>
        <bin value="UFB" absoluteLoss="4.1548e+07" fraction="0.17678"/>
        <bin value="DS" absoluteLoss="6.5846e+07" fraction="0.28016"/>
        <bin value="A" absoluteLoss="1.1007e+08" fraction="0.46833"/>
      </node>
      <node lon="84.785598" lat="27.2308">
        <bin value="RC" absoluteLoss="3.3466e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.1597e+07" fraction="0.07158"/>
        <bin value="UFB" absoluteLoss="2.8532e+07" fraction="0.17610"/>
        <bin value="DS" absoluteLoss="4.5649e+07" fraction="0.28176"/>
        <bin value="A" absoluteLoss="7.5903e+07" fraction="0.46849"/>
      </node>
      <node lon="84.801597" lat="28.312799">
        <bin value="RC" absoluteLoss="4.9747e+05" fraction="0.00224"/>
        <bin value="W" absoluteLoss="1.9469e+07" fraction="0.08762"/>
        <bin value="UFB" absoluteLoss="4.2008e+07" fraction="0.18905"/>
        <bin value="DS" absoluteLoss="5.7372e+07" fraction="0.25819"/>
        <bin value="A" absoluteLoss="1.0286e+08" fraction="0.46290"/>
      </node>
      <node lon="84.961799" lat="27.935199">
        <bin value="RC" absoluteLoss="5.3197e+05" fraction="0.00223"/>
        <bin value="W" absoluteLoss="2.0688e+07" fraction="0.08666"/>
        <bin value="UFB" absoluteLoss="4.4938e+07" fraction="0.18824"/>
        <bin value="DS" absoluteLoss="6.1926e+07" fraction="0.25940"/>
        <bin value="A" absoluteLoss="1.1065e+08" fraction="0.46348"/>
      </node>
      <node lon="85.066703" lat="27.1018">
        <bin value="RC" absoluteLoss="3.6621e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.2606e+07" fraction="0.07072"/>
        <bin value="UFB" absoluteLoss="3.1293e+07" fraction="0.17556"/>
        <bin value="DS" absoluteLoss="5.0448e+07" fraction="0.28303"/>
        <bin value="A" absoluteLoss="8.3532e+07" fraction="0.46864"/>
      </node>
      <node lon="85.092498" lat="27.455999">
        <bin value="RC" absoluteLoss="3.0829e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.0723e+07" fraction="0.07198"/>
        <bin value="UFB" absoluteLoss="2.6272e+07" fraction="0.17634"/>
        <bin value="DS" absoluteLoss="4.1891e+07" fraction="0.28118"/>
        <bin value="A" absoluteLoss="6.9787e+07" fraction="0.46843"/>
      </node>
      <node lon="85.242103" lat="27.902">
        <bin value="RC" absoluteLoss="4.6060e+05" fraction="0.00225"/>
        <bin value="W" absoluteLoss="1.8183e+07" fraction="0.08877"/>
        <bin value="UFB" absoluteLoss="3.8913e+07" fraction="0.18998"/>
        <bin value="DS" absoluteLoss="5.2598e+07" fraction="0.25680"/>
        <bin value="A" absoluteLoss="9.4669e+07" fraction="0.46220"/>
      </node>
      <node lon="85.303199" lat="26.9962">
        <bin value="RC" absoluteLoss="3.5023e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.2009e+07" fraction="0.07044"/>
        <bin value="UFB" absoluteLoss="2.9880e+07" fraction="0.17525"/>
        <bin value="DS" absoluteLoss="4.8368e+07" fraction="0.28368"/>
        <bin value="A" absoluteLoss="7.9892e+07" fraction="0.46858"/>
      </node>
      <node lon="85.347702" lat="27.523099">
        <bin value="RC" absoluteLoss="4.0387e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.4145e+07" fraction="0.07256"/>
        <bin value="UFB" absoluteLoss="3.4446e+07" fraction="0.17670"/>
        <bin value="DS" absoluteLoss="5.4644e+07" fraction="0.28032"/>
        <bin value="A" absoluteLoss="9.1297e+07" fraction="0.46834"/>
      </node>
      <node lon="85.3544" lat="27.712499">
        <bin value="RC" absoluteLoss="2.0971e+06" fraction="0.00213"/>
        <bin value="W" absoluteLoss="7.6652e+07" fraction="0.07794"/>
        <bin value="UFB" absoluteLoss="1.7789e+08" fraction="0.18088"/>
        <bin value="DS" absoluteLoss="2.6720e+08" fraction="0.27170"/>
        <bin value="A" absoluteLoss="4.5961e+08" fraction="0.46735"/>
      </node>
      <node lon="85.3908" lat="28.1667">
        <bin value="RC" absoluteLoss="8.0435e+04" fraction="0.00225"/>
        <bin value="W" absoluteLoss="3.2282e+06" fraction="0.09046"/>
        <bin value="UFB" absoluteLoss="6.8285e+06" fraction="0.19136"/>
        <bin value="DS" absoluteLoss="9.0941e+06" fraction="0.25484"/>
        <bin value="A" absoluteLoss="1.6454e+07" fraction="0.46109"/>
      </node>
      <node lon="85.438499" lat="27.6576">
        <bin value="RC" absoluteLoss="3.0271e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.0948e+07" fraction="0.07630"/>
        <bin value="UFB" absoluteLoss="2.5756e+07" fraction="0.17950"/>
        <bin value="DS" absoluteLoss="3.9367e+07" fraction="0.27436"/>
        <bin value="A" absoluteLoss="6.7112e+07" fraction="0.46772"/>
      </node>
      <node lon="85.583198" lat="26.981599">
        <bin value="RC" absoluteLoss="4.4290e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.5217e+07" fraction="0.07060"/>
        <bin value="UFB" absoluteLoss="3.7794e+07" fraction="0.17533"/>
        <bin value="DS" absoluteLoss="6.1100e+07" fraction="0.28345"/>
        <bin value="A" absoluteLoss="1.0101e+08" fraction="0.46858"/>
      </node>
      <node lon="85.627098" lat="27.5277">
        <bin value="RC" absoluteLoss="3.1198e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="1.1033e+07" fraction="0.07357"/>
        <bin value="UFB" absoluteLoss="2.6608e+07" fraction="0.17741"/>
        <bin value="DS" absoluteLoss="4.1811e+07" fraction="0.27879"/>
        <bin value="A" absoluteLoss="7.0211e+07" fraction="0.46815"/>
      </node>
      <node lon="85.747703" lat="27.9015">
        <bin value="RC" absoluteLoss="5.6788e+05" fraction="0.00228"/>
        <bin value="W" absoluteLoss="2.2695e+07" fraction="0.09119"/>
        <bin value="UFB" absoluteLoss="4.7772e+07" fraction="0.19196"/>
        <bin value="DS" absoluteLoss="6.3207e+07" fraction="0.25398"/>
        <bin value="A" absoluteLoss="1.1463e+08" fraction="0.46059"/>
      </node>
      <node lon="85.828697" lat="26.861799">
        <bin value="RC" absoluteLoss="3.6228e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.2435e+07" fraction="0.07032"/>
        <bin value="UFB" absoluteLoss="3.0977e+07" fraction="0.17517"/>
        <bin value="DS" absoluteLoss="5.0198e+07" fraction="0.28387"/>
        <bin value="A" absoluteLoss="8.2865e+07" fraction="0.46859"/>
      </node>
      <node lon="85.954299" lat="27.1849">
        <bin value="RC" absoluteLoss="2.0085e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="6.9430e+06" fraction="0.07138"/>
        <bin value="UFB" absoluteLoss="1.7115e+07" fraction="0.17597"/>
        <bin value="DS" absoluteLoss="2.7434e+07" fraction="0.28206"/>
        <bin value="A" absoluteLoss="4.5571e+07" fraction="0.46853"/>
      </node>
      <node lon="86.045402" lat="26.822999">
        <bin value="RC" absoluteLoss="4.5419e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.5594e+07" fraction="0.07046"/>
        <bin value="UFB" absoluteLoss="3.8786e+07" fraction="0.17527"/>
        <bin value="DS" absoluteLoss="6.2770e+07" fraction="0.28364"/>
        <bin value="A" absoluteLoss="1.0370e+08" fraction="0.46857"/>
      </node>
      <node lon="86.177299" lat="27.4869">
        <bin value="RC" absoluteLoss="1.8481e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="6.6398e+06" fraction="0.07539"/>
        <bin value="UFB" absoluteLoss="1.5743e+07" fraction="0.17876"/>
        <bin value="DS" absoluteLoss="2.4302e+07" fraction="0.27595"/>
        <bin value="A" absoluteLoss="4.1198e+07" fraction="0.46780"/>
      </node>
      <node lon="86.2117" lat="27.779499">
        <bin value="RC" absoluteLoss="3.8252e+05" fraction="0.00227"/>
        <bin value="W" absoluteLoss="1.5301e+07" fraction="0.09079"/>
        <bin value="UFB" absoluteLoss="3.2293e+07" fraction="0.19162"/>
        <bin value="DS" absoluteLoss="4.2878e+07" fraction="0.25443"/>
        <bin value="A" absoluteLoss="7.7671e+07" fraction="0.46089"/>
      </node>
      <node lon="86.352699" lat="26.743999">
        <bin value="RC" absoluteLoss="3.8482e+05" fraction="0.00205"/>
        <bin value="W" absoluteLoss="1.3199e+07" fraction="0.07035"/>
        <bin value="UFB" absoluteLoss="3.2868e+07" fraction="0.17519"/>
        <bin value="DS" absoluteLoss="5.3248e+07" fraction="0.28382"/>
        <bin value="A" absoluteLoss="8.7914e+07" fraction="0.46859"/>
      </node>
      <node lon="86.4346" lat="27.3117">
        <bin value="RC" absoluteLoss="1.2200e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="4.2626e+06" fraction="0.07285"/>
        <bin value="UFB" absoluteLoss="1.0349e+07" fraction="0.17685"/>
        <bin value="DS" absoluteLoss="1.6384e+07" fraction="0.28000"/>
        <bin value="A" absoluteLoss="2.7399e+07" fraction="0.46822"/>
      </node>
      <node lon="86.7108" lat="26.891399">
        <bin value="RC" absoluteLoss="2.2593e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="7.7899e+06" fraction="0.07086"/>
        <bin value="UFB" absoluteLoss="1.9310e+07" fraction="0.17564"/>
        <bin value="DS" absoluteLoss="3.1094e+07" fraction="0.28284"/>
        <bin value="A" absoluteLoss="5.1516e+07" fraction="0.46860"/>
      </node>
      <node lon="86.725898" lat="27.7005">
        <bin value="RC" absoluteLoss="2.0227e+05" fraction="0.00228"/>
        <bin value="W" absoluteLoss="8.0749e+06" fraction="0.09109"/>
        <bin value="UFB" absoluteLoss="1.7009e+07" fraction="0.19188"/>
        <bin value="DS" absoluteLoss="2.2524e+07" fraction="0.25410"/>
        <bin value="A" absoluteLoss="4.0834e+07" fraction="0.46065"/>
      </node>
      <node lon="86.727203" lat="26.6039">
        <bin value="RC" absoluteLoss="3.6260e+05" fraction="0.00204"/>
        <bin value="W" absoluteLoss="1.2243e+07" fraction="0.06882"/>
        <bin value="UFB" absoluteLoss="3.0992e+07" fraction="0.17421"/>
        <bin value="DS" absoluteLoss="5.0919e+07" fraction="0.28622"/>
        <bin value="A" absoluteLoss="8.3385e+07" fraction="0.46872"/>
      </node>
      <node lon="86.7966" lat="27.146799">
        <bin value="RC" absoluteLoss="1.5106e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="5.2466e+06" fraction="0.07171"/>
        <bin value="UFB" absoluteLoss="1.2889e+07" fraction="0.17617"/>
        <bin value="DS" absoluteLoss="2.0601e+07" fraction="0.28158"/>
        <bin value="A" absoluteLoss="3.4275e+07" fraction="0.46848"/>
      </node>
      <node lon="87.080902" lat="27.1648">
        <bin value="RC" absoluteLoss="1.4147e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="4.9254e+06" fraction="0.07199"/>
        <bin value="UFB" absoluteLoss="1.2065e+07" fraction="0.17634"/>
        <bin value="DS" absoluteLoss="1.9240e+07" fraction="0.28120"/>
        <bin value="A" absoluteLoss="3.2050e+07" fraction="0.46841"/>
      </node>
      <node lon="87.170898" lat="26.635099">
        <bin value="RC" absoluteLoss="4.1060e+05" fraction="0.00202"/>
        <bin value="W" absoluteLoss="1.3714e+07" fraction="0.06736"/>
        <bin value="UFB" absoluteLoss="3.5187e+07" fraction="0.17284"/>
        <bin value="DS" absoluteLoss="5.8948e+07" fraction="0.28955"/>
        <bin value="A" absoluteLoss="9.5327e+07" fraction="0.46824"/>
      </node>
      <node lon="87.290298" lat="27.574899">
        <bin value="RC" absoluteLoss="2.7944e+05" fraction="0.00227"/>
        <bin value="W" absoluteLoss="1.1048e+07" fraction="0.08965"/>
        <bin value="UFB" absoluteLoss="2.3502e+07" fraction="0.19071"/>
        <bin value="DS" absoluteLoss="3.1519e+07" fraction="0.25576"/>
        <bin value="A" absoluteLoss="5.6888e+07" fraction="0.46162"/>
      </node>
      <node lon="87.343803" lat="26.969999">
        <bin value="RC" absoluteLoss="1.2990e+05" fraction="0.00206"/>
        <bin value="W" absoluteLoss="4.4881e+06" fraction="0.07124"/>
        <bin value="UFB" absoluteLoss="1.1081e+07" fraction="0.17588"/>
        <bin value="DS" absoluteLoss="1.7783e+07" fraction="0.28226"/>
        <bin value="A" absoluteLoss="2.9521e+07" fraction="0.46856"/>
      </node>
      <node lon="87.481002" lat="26.6102">
        <bin value="RC" absoluteLoss="1.9811e+05" fraction="0.00188"/>
        <bin value="W" absoluteLoss="5.9190e+06" fraction="0.05618"/>
        <bin value="UFB" absoluteLoss="1.7542e+07" fraction="0.16649"/>
        <bin value="DS" absoluteLoss="3.3953e+07" fraction="0.32223"/>
        <bin value="A" absoluteLoss="4.7755e+07" fraction="0.45322"/>
      </node>
      <node lon="87.555702" lat="27.130899">
        <bin value="RC" absoluteLoss="7.2375e+04" fraction="0.00205"/>
        <bin value="W" absoluteLoss="2.4853e+06" fraction="0.07031"/>
        <bin value="UFB" absoluteLoss="6.1911e+06" fraction="0.17515"/>
        <bin value="DS" absoluteLoss="1.0037e+07" fraction="0.28395"/>
        <bin value="A" absoluteLoss="1.6562e+07" fraction="0.46854"/>
      </node>
      <node lon="87.769996" lat="27.085399">
        <bin value="RC" absoluteLoss="1.2945e+05" fraction="0.00204"/>
        <bin value="W" absoluteLoss="4.4095e+06" fraction="0.06960"/>
        <bin value="UFB" absoluteLoss="1.1067e+07" fraction="0.17468"/>
        <bin value="DS" absoluteLoss="1.8060e+07" fraction="0.28505"/>
        <bin value="A" absoluteLoss="2.9692e+07" fraction="0.46864"/>
      </node>
      <node lon="87.824996" lat="27.554599">
        <bin value="RC" absoluteLoss="9.9233e+04" fraction="0.00207"/>
        <bin value="W" absoluteLoss="3.4907e+06" fraction="0.07296"/>
        <bin value="UFB" absoluteLoss="8.4672e+06" fraction="0.17698"/>
        <bin value="DS" absoluteLoss="1.3385e+07" fraction="0.27977"/>
        <bin value="A" absoluteLoss="2.2401e+07" fraction="0.46821"/>
      </node>
      <node lon="87.911499" lat="26.571399">
        <bin value="RC" absoluteLoss="5.1877e+04" fraction="0.00179"/>
        <bin value="W" absoluteLoss="1.4832e+06" fraction="0.05106"/>
        <bin value="UFB" absoluteLoss="4.8059e+06" fraction="0.16546"/>
        <bin value="DS" absoluteLoss="1.0295e+07" fraction="0.35445"/>
        <bin value="A" absoluteLoss="1.2410e+07" fraction="0.42724"/>
      </node>
      <node lon="87.912498" lat="26.862899">
        <bin value="RC" absoluteLoss="1.5503e+05" fraction="0.00201"/>
        <bin value="W" absoluteLoss="5.1663e+06" fraction="0.06696"/>
        <bin value="UFB" absoluteLoss="1.3308e+07" fraction="0.17247"/>
        <bin value="DS" absoluteLoss="2.2420e+07" fraction="0.29057"/>
        <bin value="A" absoluteLoss="3.6110e+07" fraction="0.46799"/>
      </node>
    </map>
  </lossFraction>
</nrml>
"""

    @attr('qa', 'risk', 'classical', 'e2e')
    def test(self):
        self._run_test()

    def hazard_id(self):
        return models.Output.objects.latest('last_update').id

    def actual_xml_outputs(self, job):
        return models.Output.objects.filter(
            oq_job=job, output_type="loss_fraction").order_by('id')

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_FRACTION]
