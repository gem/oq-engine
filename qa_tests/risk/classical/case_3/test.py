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

    EXPECTED_LOSS_FRACTION = """
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossFraction investigationTime="50.00" poE="0.1000" sourceModelTreePath="b1" gsimTreePath="b1" lossCategory="buildings" unit="USD" variable="taxonomy">
    <total>
      <bin value="RC" absoluteLoss="2.4509e+07" fraction="0.00214"/>
      <bin value="W" absoluteLoss="9.0106e+08" fraction="0.07865"/>
      <bin value="UFB" absoluteLoss="2.0807e+09" fraction="0.18162"/>
      <bin value="DS" absoluteLoss="3.1100e+09" fraction="0.27147"/>
      <bin value="A" absoluteLoss="5.3401e+09" fraction="0.46613"/>
    </total>
    <map>
      <node lon="80.317596" lat="28.87">
        <bin value="RC" absoluteLoss="3.6983e+05" fraction="0.00212"/>
        <bin value="W" absoluteLoss="1.3432e+07" fraction="0.07693"/>
        <bin value="UFB" absoluteLoss="3.1436e+07" fraction="0.18005"/>
        <bin value="DS" absoluteLoss="4.7710e+07" fraction="0.27325"/>
        <bin value="A" absoluteLoss="8.1652e+07" fraction="0.46765"/>
      </node>
      <node lon="80.484397" lat="29.2275">
        <bin value="RC" absoluteLoss="1.3105e+05" fraction="0.00214"/>
        <bin value="W" absoluteLoss="4.7981e+06" fraction="0.07822"/>
        <bin value="UFB" absoluteLoss="1.1112e+07" fraction="0.18115"/>
        <bin value="DS" absoluteLoss="1.6634e+07" fraction="0.27119"/>
        <bin value="A" absoluteLoss="2.8663e+07" fraction="0.46730"/>
      </node>
      <node lon="80.562103" lat="29.5104">
        <bin value="RC" absoluteLoss="2.1982e+05" fraction="0.00214"/>
        <bin value="W" absoluteLoss="8.0353e+06" fraction="0.07824"/>
        <bin value="UFB" absoluteLoss="1.8606e+07" fraction="0.18117"/>
        <bin value="DS" absoluteLoss="2.7848e+07" fraction="0.27116"/>
        <bin value="A" absoluteLoss="4.7990e+07" fraction="0.46729"/>
      </node>
      <node lon="80.782897" lat="29.890699">
        <bin value="RC" absoluteLoss="1.2404e+05" fraction="0.00215"/>
        <bin value="W" absoluteLoss="4.5435e+06" fraction="0.07867"/>
        <bin value="UFB" absoluteLoss="1.0483e+07" fraction="0.18150"/>
        <bin value="DS" absoluteLoss="1.5624e+07" fraction="0.27051"/>
        <bin value="A" absoluteLoss="2.6981e+07" fraction="0.46717"/>
      </node>
      <node lon="80.873497" lat="28.7436">
        <bin value="RC" absoluteLoss="6.7845e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="2.4831e+07" fraction="0.07798"/>
        <bin value="UFB" absoluteLoss="5.7617e+07" fraction="0.18094"/>
        <bin value="DS" absoluteLoss="8.6484e+07" fraction="0.27160"/>
        <bin value="A" absoluteLoss="1.4881e+08" fraction="0.46735"/>
      </node>
      <node lon="80.891998" lat="29.173">
        <bin value="RC" absoluteLoss="2.0190e+05" fraction="0.00214"/>
        <bin value="W" absoluteLoss="7.3948e+06" fraction="0.07830"/>
        <bin value="UFB" absoluteLoss="1.7115e+07" fraction="0.18121"/>
        <bin value="DS" absoluteLoss="2.5602e+07" fraction="0.27107"/>
        <bin value="A" absoluteLoss="4.4133e+07" fraction="0.46728"/>
      </node>
      <node lon="81.1791" lat="29.7136">
        <bin value="RC" absoluteLoss="2.4842e+05" fraction="0.00224"/>
        <bin value="W" absoluteLoss="9.6749e+06" fraction="0.08709"/>
        <bin value="UFB" absoluteLoss="2.0948e+07" fraction="0.18858"/>
        <bin value="DS" absoluteLoss="2.8756e+07" fraction="0.25886"/>
        <bin value="A" absoluteLoss="5.1459e+07" fraction="0.46323"/>
      </node>
      <node lon="81.2985" lat="29.1098">
        <bin value="RC" absoluteLoss="2.3805e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="8.7594e+06" fraction="0.07850"/>
        <bin value="UFB" absoluteLoss="2.0239e+07" fraction="0.18139"/>
        <bin value="DS" absoluteLoss="3.0210e+07" fraction="0.27074"/>
        <bin value="A" absoluteLoss="5.2136e+07" fraction="0.46724"/>
      </node>
      <node lon="81.395103" lat="28.386699">
        <bin value="RC" absoluteLoss="3.9346e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="1.4363e+07" fraction="0.07785"/>
        <bin value="UFB" absoluteLoss="3.3364e+07" fraction="0.18083"/>
        <bin value="DS" absoluteLoss="5.0151e+07" fraction="0.27181"/>
        <bin value="A" absoluteLoss="8.6233e+07" fraction="0.46738"/>
      </node>
      <node lon="81.568496" lat="29.564199">
        <bin value="RC" absoluteLoss="1.8997e+05" fraction="0.00225"/>
        <bin value="W" absoluteLoss="7.4201e+06" fraction="0.08794"/>
        <bin value="UFB" absoluteLoss="1.5971e+07" fraction="0.18929"/>
        <bin value="DS" absoluteLoss="2.1753e+07" fraction="0.25781"/>
        <bin value="A" absoluteLoss="3.9041e+07" fraction="0.46270"/>
      </node>
      <node lon="81.586196" lat="28.638599">
        <bin value="RC" absoluteLoss="3.5267e+05" fraction="0.00214"/>
        <bin value="W" absoluteLoss="1.2902e+07" fraction="0.07819"/>
        <bin value="UFB" absoluteLoss="2.9887e+07" fraction="0.18112"/>
        <bin value="DS" absoluteLoss="4.4761e+07" fraction="0.27125"/>
        <bin value="A" absoluteLoss="7.7111e+07" fraction="0.46730"/>
      </node>
      <node lon="81.687698" lat="28.877599">
        <bin value="RC" absoluteLoss="2.3954e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="8.8042e+06" fraction="0.07841"/>
        <bin value="UFB" absoluteLoss="2.0359e+07" fraction="0.18130"/>
        <bin value="DS" absoluteLoss="3.0420e+07" fraction="0.27090"/>
        <bin value="A" absoluteLoss="5.2469e+07" fraction="0.46726"/>
      </node>
      <node lon="81.755996" lat="29.1923">
        <bin value="RC" absoluteLoss="1.3894e+05" fraction="0.00218"/>
        <bin value="W" absoluteLoss="5.2656e+06" fraction="0.08249"/>
        <bin value="UFB" absoluteLoss="1.1795e+07" fraction="0.18478"/>
        <bin value="DS" absoluteLoss="1.6906e+07" fraction="0.26485"/>
        <bin value="A" absoluteLoss="2.9727e+07" fraction="0.46570"/>
      </node>
      <node lon="81.825302" lat="28.0893">
        <bin value="RC" absoluteLoss="4.3049e+05" fraction="0.00212"/>
        <bin value="W" absoluteLoss="1.5648e+07" fraction="0.07708"/>
        <bin value="UFB" absoluteLoss="3.6574e+07" fraction="0.18016"/>
        <bin value="DS" absoluteLoss="5.5425e+07" fraction="0.27302"/>
        <bin value="A" absoluteLoss="9.4928e+07" fraction="0.46761"/>
      </node>
      <node lon="81.8899" lat="30.038799">
        <bin value="RC" absoluteLoss="2.8282e+04" fraction="0.00202"/>
        <bin value="W" absoluteLoss="9.6147e+05" fraction="0.06870"/>
        <bin value="UFB" absoluteLoss="2.4374e+06" fraction="0.17416"/>
        <bin value="DS" absoluteLoss="4.0088e+06" fraction="0.28644"/>
        <bin value="A" absoluteLoss="6.5594e+06" fraction="0.46868"/>
      </node>
      <node lon="82.141197" lat="28.3924">
        <bin value="RC" absoluteLoss="2.1853e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="7.9893e+06" fraction="0.07770"/>
        <bin value="UFB" absoluteLoss="1.8580e+07" fraction="0.18071"/>
        <bin value="DS" absoluteLoss="2.7974e+07" fraction="0.27207"/>
        <bin value="A" absoluteLoss="4.8057e+07" fraction="0.46740"/>
      </node>
      <node lon="82.170402" lat="28.863899">
        <bin value="RC" absoluteLoss="1.6296e+05" fraction="0.00216"/>
        <bin value="W" absoluteLoss="6.0206e+06" fraction="0.07991"/>
        <bin value="UFB" absoluteLoss="1.3757e+07" fraction="0.18259"/>
        <bin value="DS" absoluteLoss="2.0235e+07" fraction="0.26856"/>
        <bin value="A" absoluteLoss="3.5170e+07" fraction="0.46679"/>
      </node>
      <node lon="82.222396" lat="29.2712">
        <bin value="RC" absoluteLoss="1.4988e+05" fraction="0.00226"/>
        <bin value="W" absoluteLoss="5.8591e+06" fraction="0.08839"/>
        <bin value="UFB" absoluteLoss="1.2573e+07" fraction="0.18968"/>
        <bin value="DS" absoluteLoss="1.7053e+07" fraction="0.25726"/>
        <bin value="A" absoluteLoss="3.0651e+07" fraction="0.46241"/>
      </node>
      <node lon="82.374801" lat="29.6196">
        <bin value="RC" absoluteLoss="4.8223e+04" fraction="0.00216"/>
        <bin value="W" absoluteLoss="1.7558e+06" fraction="0.07862"/>
        <bin value="UFB" absoluteLoss="4.0537e+06" fraction="0.18150"/>
        <bin value="DS" absoluteLoss="6.0412e+06" fraction="0.27049"/>
        <bin value="A" absoluteLoss="1.0435e+07" fraction="0.46724"/>
      </node>
      <node lon="82.419197" lat="27.956699">
        <bin value="RC" absoluteLoss="4.8273e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.7279e+07" fraction="0.07526"/>
        <bin value="UFB" absoluteLoss="4.1022e+07" fraction="0.17866"/>
        <bin value="DS" absoluteLoss="6.3384e+07" fraction="0.27605"/>
        <bin value="A" absoluteLoss="1.0744e+08" fraction="0.46794"/>
      </node>
      <node lon="82.623497" lat="28.335199">
        <bin value="RC" absoluteLoss="1.7900e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="6.3788e+06" fraction="0.07484"/>
        <bin value="UFB" absoluteLoss="1.5201e+07" fraction="0.17834"/>
        <bin value="DS" absoluteLoss="2.3586e+07" fraction="0.27672"/>
        <bin value="A" absoluteLoss="3.9890e+07" fraction="0.46800"/>
      </node>
      <node lon="82.663299" lat="28.6961">
        <bin value="RC" absoluteLoss="2.2852e+05" fraction="0.00216"/>
        <bin value="W" absoluteLoss="8.5263e+06" fraction="0.08043"/>
        <bin value="UFB" absoluteLoss="1.9403e+07" fraction="0.18304"/>
        <bin value="DS" absoluteLoss="2.8384e+07" fraction="0.26776"/>
        <bin value="A" absoluteLoss="4.9464e+07" fraction="0.46662"/>
      </node>
      <node lon="82.866401" lat="28.106399">
        <bin value="RC" absoluteLoss="1.9706e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="7.0634e+06" fraction="0.07515"/>
        <bin value="UFB" absoluteLoss="1.6785e+07" fraction="0.17857"/>
        <bin value="DS" absoluteLoss="2.5964e+07" fraction="0.27623"/>
        <bin value="A" absoluteLoss="4.3984e+07" fraction="0.46795"/>
      </node>
      <node lon="82.991096" lat="27.6296">
        <bin value="RC" absoluteLoss="3.5111e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="1.2435e+07" fraction="0.07376"/>
        <bin value="UFB" absoluteLoss="2.9938e+07" fraction="0.17758"/>
        <bin value="DS" absoluteLoss="4.6942e+07" fraction="0.27843"/>
        <bin value="A" absoluteLoss="7.8925e+07" fraction="0.46815"/>
      </node>
      <node lon="83.055496" lat="29.165199">
        <bin value="RC" absoluteLoss="3.6415e+04" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.3626e+06" fraction="0.07861"/>
        <bin value="UFB" absoluteLoss="3.1449e+06" fraction="0.18145"/>
        <bin value="DS" absoluteLoss="4.6908e+06" fraction="0.27063"/>
        <bin value="A" absoluteLoss="8.0979e+06" fraction="0.46721"/>
      </node>
      <node lon="83.082298" lat="27.9006">
        <bin value="RC" absoluteLoss="1.9270e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="6.9033e+06" fraction="0.07511"/>
        <bin value="UFB" absoluteLoss="1.6411e+07" fraction="0.17855"/>
        <bin value="DS" absoluteLoss="2.5394e+07" fraction="0.27630"/>
        <bin value="A" absoluteLoss="4.3009e+07" fraction="0.46795"/>
      </node>
      <node lon="83.250999" lat="28.340499">
        <bin value="RC" absoluteLoss="2.8136e+05" fraction="0.00212"/>
        <bin value="W" absoluteLoss="1.0233e+07" fraction="0.07709"/>
        <bin value="UFB" absoluteLoss="2.3907e+07" fraction="0.18011"/>
        <bin value="DS" absoluteLoss="3.6249e+07" fraction="0.27309"/>
        <bin value="A" absoluteLoss="6.2065e+07" fraction="0.46758"/>
      </node>
      <node lon="83.294197" lat="28.091299">
        <bin value="RC" absoluteLoss="2.7266e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="9.7669e+06" fraction="0.07544"/>
        <bin value="UFB" absoluteLoss="2.3151e+07" fraction="0.17881"/>
        <bin value="DS" absoluteLoss="3.5710e+07" fraction="0.27582"/>
        <bin value="A" absoluteLoss="6.0568e+07" fraction="0.46782"/>
      </node>
      <node lon="83.394302" lat="27.575799">
        <bin value="RC" absoluteLoss="6.5180e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="2.3192e+07" fraction="0.07443"/>
        <bin value="UFB" absoluteLoss="5.5487e+07" fraction="0.17806"/>
        <bin value="DS" absoluteLoss="8.6432e+07" fraction="0.27736"/>
        <bin value="A" absoluteLoss="1.4586e+08" fraction="0.46806"/>
      </node>
      <node lon="83.464302" lat="28.5414">
        <bin value="RC" absoluteLoss="1.7761e+05" fraction="0.00219"/>
        <bin value="W" absoluteLoss="6.8046e+06" fraction="0.08386"/>
        <bin value="UFB" absoluteLoss="1.5083e+07" fraction="0.18589"/>
        <bin value="DS" absoluteLoss="2.1340e+07" fraction="0.26300"/>
        <bin value="A" absoluteLoss="3.7734e+07" fraction="0.46505"/>
      </node>
      <node lon="83.633102" lat="27.8064">
        <bin value="RC" absoluteLoss="2.4643e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="8.8049e+06" fraction="0.07522"/>
        <bin value="UFB" absoluteLoss="2.0909e+07" fraction="0.17862"/>
        <bin value="DS" absoluteLoss="3.2321e+07" fraction="0.27611"/>
        <bin value="A" absoluteLoss="5.4776e+07" fraction="0.46794"/>
      </node>
      <node lon="83.686996" lat="28.200899">
        <bin value="RC" absoluteLoss="1.7581e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="6.4783e+06" fraction="0.07851"/>
        <bin value="UFB" absoluteLoss="1.4966e+07" fraction="0.18139"/>
        <bin value="DS" absoluteLoss="2.2339e+07" fraction="0.27074"/>
        <bin value="A" absoluteLoss="3.8551e+07" fraction="0.46723"/>
      </node>
      <node lon="83.819801" lat="28.020399">
        <bin value="RC" absoluteLoss="3.0264e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.0937e+07" fraction="0.07630"/>
        <bin value="UFB" absoluteLoss="2.5731e+07" fraction="0.17951"/>
        <bin value="DS" absoluteLoss="3.9325e+07" fraction="0.27435"/>
        <bin value="A" absoluteLoss="6.7042e+07" fraction="0.46772"/>
      </node>
      <node lon="83.837402" lat="28.968599">
        <bin value="RC" absoluteLoss="9.7396e+03" fraction="0.00196"/>
        <bin value="W" absoluteLoss="3.4068e+05" fraction="0.06866"/>
        <bin value="UFB" absoluteLoss="8.6410e+05" fraction="0.17414"/>
        <bin value="DS" absoluteLoss="1.4223e+06" fraction="0.28662"/>
        <bin value="A" absoluteLoss="2.3254e+06" fraction="0.46862"/>
      </node>
      <node lon="83.969902" lat="27.6322">
        <bin value="RC" absoluteLoss="5.2599e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.8775e+07" fraction="0.07489"/>
        <bin value="UFB" absoluteLoss="4.4723e+07" fraction="0.17839"/>
        <bin value="DS" absoluteLoss="6.9358e+07" fraction="0.27664"/>
        <bin value="A" absoluteLoss="1.1733e+08" fraction="0.46798"/>
      </node>
      <node lon="84.005996" lat="28.350099">
        <bin value="RC" absoluteLoss="8.1575e+05" fraction="0.00220"/>
        <bin value="W" absoluteLoss="3.1189e+07" fraction="0.08409"/>
        <bin value="UFB" absoluteLoss="6.9022e+07" fraction="0.18610"/>
        <bin value="DS" absoluteLoss="9.7424e+07" fraction="0.26268"/>
        <bin value="A" absoluteLoss="1.7243e+08" fraction="0.46492"/>
      </node>
      <node lon="84.229103" lat="28.669099">
        <bin value="RC" absoluteLoss="8.3736e+03" fraction="0.00216"/>
        <bin value="W" absoluteLoss="3.1669e+05" fraction="0.08169"/>
        <bin value="UFB" absoluteLoss="7.1235e+05" fraction="0.18375"/>
        <bin value="DS" absoluteLoss="1.0317e+06" fraction="0.26612"/>
        <bin value="A" absoluteLoss="1.8077e+06" fraction="0.46628"/>
      </node>
      <node lon="84.261001" lat="27.9458">
        <bin value="RC" absoluteLoss="3.8014e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="1.3936e+07" fraction="0.07819"/>
        <bin value="UFB" absoluteLoss="3.2280e+07" fraction="0.18111"/>
        <bin value="DS" absoluteLoss="4.8349e+07" fraction="0.27127"/>
        <bin value="A" absoluteLoss="8.3287e+07" fraction="0.46729"/>
      </node>
      <node lon="84.438796" lat="28.282499">
        <bin value="RC" absoluteLoss="3.0898e+05" fraction="0.00223"/>
        <bin value="W" absoluteLoss="1.2053e+07" fraction="0.08709"/>
        <bin value="UFB" absoluteLoss="2.6097e+07" fraction="0.18857"/>
        <bin value="DS" absoluteLoss="3.5824e+07" fraction="0.25885"/>
        <bin value="A" absoluteLoss="6.4111e+07" fraction="0.46325"/>
      </node>
      <node lon="84.449501" lat="27.581399">
        <bin value="RC" absoluteLoss="5.6642e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="2.0397e+07" fraction="0.07585"/>
        <bin value="UFB" absoluteLoss="4.8176e+07" fraction="0.17915"/>
        <bin value="DS" absoluteLoss="7.3983e+07" fraction="0.27512"/>
        <bin value="A" absoluteLoss="1.2579e+08" fraction="0.46778"/>
      </node>
      <node lon="84.785598" lat="27.2308">
        <bin value="RC" absoluteLoss="3.8913e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.3885e+07" fraction="0.07488"/>
        <bin value="UFB" absoluteLoss="3.3078e+07" fraction="0.17840"/>
        <bin value="DS" absoluteLoss="5.1293e+07" fraction="0.27663"/>
        <bin value="A" absoluteLoss="8.6773e+07" fraction="0.46799"/>
      </node>
      <node lon="84.801597" lat="28.312799">
        <bin value="RC" absoluteLoss="5.5870e+05" fraction="0.00228"/>
        <bin value="W" absoluteLoss="2.2323e+07" fraction="0.09090"/>
        <bin value="UFB" absoluteLoss="4.7088e+07" fraction="0.19174"/>
        <bin value="DS" absoluteLoss="6.2446e+07" fraction="0.25428"/>
        <bin value="A" absoluteLoss="1.1316e+08" fraction="0.46080"/>
      </node>
      <node lon="84.961799" lat="27.935199">
        <bin value="RC" absoluteLoss="5.9794e+05" fraction="0.00226"/>
        <bin value="W" absoluteLoss="2.3728e+07" fraction="0.08982"/>
        <bin value="UFB" absoluteLoss="5.0421e+07" fraction="0.19087"/>
        <bin value="DS" absoluteLoss="6.7503e+07" fraction="0.25554"/>
        <bin value="A" absoluteLoss="1.2191e+08" fraction="0.46150"/>
      </node>
      <node lon="85.066703" lat="27.1018">
        <bin value="RC" absoluteLoss="4.2699e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.5167e+07" fraction="0.07417"/>
        <bin value="UFB" absoluteLoss="3.6373e+07" fraction="0.17788"/>
        <bin value="DS" absoluteLoss="5.6796e+07" fraction="0.27776"/>
        <bin value="A" absoluteLoss="9.5717e+07" fraction="0.46810"/>
      </node>
      <node lon="85.092498" lat="27.455999">
        <bin value="RC" absoluteLoss="3.5786e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="1.2806e+07" fraction="0.07522"/>
        <bin value="UFB" absoluteLoss="3.0409e+07" fraction="0.17860"/>
        <bin value="DS" absoluteLoss="4.7015e+07" fraction="0.27614"/>
        <bin value="A" absoluteLoss="7.9669e+07" fraction="0.46794"/>
      </node>
      <node lon="85.242103" lat="27.902">
        <bin value="RC" absoluteLoss="5.1690e+05" fraction="0.00229"/>
        <bin value="W" absoluteLoss="2.0844e+07" fraction="0.09219"/>
        <bin value="UFB" absoluteLoss="4.3581e+07" fraction="0.19276"/>
        <bin value="DS" absoluteLoss="5.7159e+07" fraction="0.25282"/>
        <bin value="A" absoluteLoss="1.0399e+08" fraction="0.45994"/>
      </node>
      <node lon="85.303199" lat="26.9962">
        <bin value="RC" absoluteLoss="4.0801e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.4389e+07" fraction="0.07356"/>
        <bin value="UFB" absoluteLoss="3.4710e+07" fraction="0.17744"/>
        <bin value="DS" absoluteLoss="5.4527e+07" fraction="0.27874"/>
        <bin value="A" absoluteLoss="9.1585e+07" fraction="0.46818"/>
      </node>
      <node lon="85.347702" lat="27.523099">
        <bin value="RC" absoluteLoss="4.6956e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.6897e+07" fraction="0.07575"/>
        <bin value="UFB" absoluteLoss="3.9940e+07" fraction="0.17906"/>
        <bin value="DS" absoluteLoss="6.1408e+07" fraction="0.27530"/>
        <bin value="A" absoluteLoss="1.0434e+08" fraction="0.46779"/>
      </node>
      <node lon="85.3544" lat="27.712499">
        <bin value="RC" absoluteLoss="2.3933e+06" fraction="0.00216"/>
        <bin value="W" absoluteLoss="8.9061e+07" fraction="0.08039"/>
        <bin value="UFB" absoluteLoss="2.0270e+08" fraction="0.18298"/>
        <bin value="DS" absoluteLoss="2.9670e+08" fraction="0.26783"/>
        <bin value="A" absoluteLoss="5.1694e+08" fraction="0.46664"/>
      </node>
      <node lon="85.3908" lat="28.1667">
        <bin value="RC" absoluteLoss="9.0126e+04" fraction="0.00229"/>
        <bin value="W" absoluteLoss="3.6969e+06" fraction="0.09404"/>
        <bin value="UFB" absoluteLoss="7.6344e+06" fraction="0.19420"/>
        <bin value="DS" absoluteLoss="9.8602e+06" fraction="0.25082"/>
        <bin value="A" absoluteLoss="1.8030e+07" fraction="0.45865"/>
      </node>
      <node lon="85.438499" lat="27.6576">
        <bin value="RC" absoluteLoss="3.4762e+05" fraction="0.00214"/>
        <bin value="W" absoluteLoss="1.2820e+07" fraction="0.07892"/>
        <bin value="UFB" absoluteLoss="2.9524e+07" fraction="0.18175"/>
        <bin value="DS" absoluteLoss="4.3876e+07" fraction="0.27009"/>
        <bin value="A" absoluteLoss="7.5879e+07" fraction="0.46710"/>
      </node>
      <node lon="85.583198" lat="26.981599">
        <bin value="RC" absoluteLoss="5.1692e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="1.8290e+07" fraction="0.07391"/>
        <bin value="UFB" absoluteLoss="4.3970e+07" fraction="0.17769"/>
        <bin value="DS" absoluteLoss="6.8835e+07" fraction="0.27818"/>
        <bin value="A" absoluteLoss="1.1583e+08" fraction="0.46812"/>
      </node>
      <node lon="85.627098" lat="27.5277">
        <bin value="RC" absoluteLoss="3.6159e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="1.3110e+07" fraction="0.07661"/>
        <bin value="UFB" absoluteLoss="3.0758e+07" fraction="0.17975"/>
        <bin value="DS" absoluteLoss="4.6862e+07" fraction="0.27385"/>
        <bin value="A" absoluteLoss="8.0029e+07" fraction="0.46768"/>
      </node>
      <node lon="85.747703" lat="27.9015">
        <bin value="RC" absoluteLoss="6.3584e+05" fraction="0.00232"/>
        <bin value="W" absoluteLoss="2.5983e+07" fraction="0.09487"/>
        <bin value="UFB" absoluteLoss="5.3364e+07" fraction="0.19485"/>
        <bin value="DS" absoluteLoss="6.8446e+07" fraction="0.24991"/>
        <bin value="A" absoluteLoss="1.2545e+08" fraction="0.45805"/>
      </node>
      <node lon="85.828697" lat="26.861799">
        <bin value="RC" absoluteLoss="4.2157e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="1.4878e+07" fraction="0.07339"/>
        <bin value="UFB" absoluteLoss="3.5947e+07" fraction="0.17731"/>
        <bin value="DS" absoluteLoss="5.6563e+07" fraction="0.27901"/>
        <bin value="A" absoluteLoss="9.4919e+07" fraction="0.46821"/>
      </node>
      <node lon="85.954299" lat="27.1849">
        <bin value="RC" absoluteLoss="2.3361e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="8.3182e+06" fraction="0.07471"/>
        <bin value="UFB" absoluteLoss="1.9847e+07" fraction="0.17825"/>
        <bin value="DS" absoluteLoss="3.0834e+07" fraction="0.27693"/>
        <bin value="A" absoluteLoss="5.2111e+07" fraction="0.46802"/>
      </node>
      <node lon="86.045402" lat="26.822999">
        <bin value="RC" absoluteLoss="5.2925e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="1.8690e+07" fraction="0.07360"/>
        <bin value="UFB" absoluteLoss="4.5067e+07" fraction="0.17747"/>
        <bin value="DS" absoluteLoss="7.0769e+07" fraction="0.27868"/>
        <bin value="A" absoluteLoss="1.1889e+08" fraction="0.46817"/>
      </node>
      <node lon="86.177299" lat="27.4869">
        <bin value="RC" absoluteLoss="2.1330e+05" fraction="0.00213"/>
        <bin value="W" absoluteLoss="7.8257e+06" fraction="0.07815"/>
        <bin value="UFB" absoluteLoss="1.8132e+07" fraction="0.18106"/>
        <bin value="DS" absoluteLoss="2.7176e+07" fraction="0.27137"/>
        <bin value="A" absoluteLoss="4.6796e+07" fraction="0.46729"/>
      </node>
      <node lon="86.2117" lat="27.779499">
        <bin value="RC" absoluteLoss="4.2844e+05" fraction="0.00231"/>
        <bin value="W" absoluteLoss="1.7520e+07" fraction="0.09443"/>
        <bin value="UFB" absoluteLoss="3.6086e+07" fraction="0.19449"/>
        <bin value="DS" absoluteLoss="4.6458e+07" fraction="0.25039"/>
        <bin value="A" absoluteLoss="8.5049e+07" fraction="0.45839"/>
      </node>
      <node lon="86.352699" lat="26.743999">
        <bin value="RC" absoluteLoss="4.4793e+05" fraction="0.00208"/>
        <bin value="W" absoluteLoss="1.5798e+07" fraction="0.07344"/>
        <bin value="UFB" absoluteLoss="3.8151e+07" fraction="0.17734"/>
        <bin value="DS" absoluteLoss="6.0005e+07" fraction="0.27893"/>
        <bin value="A" absoluteLoss="1.0072e+08" fraction="0.46820"/>
      </node>
      <node lon="86.4346" lat="27.3117">
        <bin value="RC" absoluteLoss="1.4197e+05" fraction="0.00212"/>
        <bin value="W" absoluteLoss="5.0926e+06" fraction="0.07603"/>
        <bin value="UFB" absoluteLoss="1.2010e+07" fraction="0.17930"/>
        <bin value="DS" absoluteLoss="1.8407e+07" fraction="0.27480"/>
        <bin value="A" absoluteLoss="3.1331e+07" fraction="0.46775"/>
      </node>
      <node lon="86.7108" lat="26.891399">
        <bin value="RC" absoluteLoss="2.6328e+05" fraction="0.00209"/>
        <bin value="W" absoluteLoss="9.3631e+06" fraction="0.07428"/>
        <bin value="UFB" absoluteLoss="2.2432e+07" fraction="0.17796"/>
        <bin value="DS" absoluteLoss="3.4994e+07" fraction="0.27761"/>
        <bin value="A" absoluteLoss="5.9003e+07" fraction="0.46807"/>
      </node>
      <node lon="86.725898" lat="27.7005">
        <bin value="RC" absoluteLoss="2.2648e+05" fraction="0.00232"/>
        <bin value="W" absoluteLoss="9.2451e+06" fraction="0.09477"/>
        <bin value="UFB" absoluteLoss="1.9000e+07" fraction="0.19476"/>
        <bin value="DS" absoluteLoss="2.4393e+07" fraction="0.25004"/>
        <bin value="A" absoluteLoss="4.4692e+07" fraction="0.45811"/>
      </node>
      <node lon="86.727203" lat="26.6039">
        <bin value="RC" absoluteLoss="4.2150e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="1.4602e+07" fraction="0.07157"/>
        <bin value="UFB" absoluteLoss="3.5931e+07" fraction="0.17611"/>
        <bin value="DS" absoluteLoss="5.7483e+07" fraction="0.28174"/>
        <bin value="A" absoluteLoss="9.5588e+07" fraction="0.46851"/>
      </node>
      <node lon="86.7966" lat="27.146799">
        <bin value="RC" absoluteLoss="1.7548e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="6.2725e+06" fraction="0.07498"/>
        <bin value="UFB" absoluteLoss="1.4928e+07" fraction="0.17843"/>
        <bin value="DS" absoluteLoss="2.3133e+07" fraction="0.27651"/>
        <bin value="A" absoluteLoss="3.9152e+07" fraction="0.46799"/>
      </node>
      <node lon="87.080902" lat="27.1648">
        <bin value="RC" absoluteLoss="1.6424e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="5.8825e+06" fraction="0.07523"/>
        <bin value="UFB" absoluteLoss="1.3968e+07" fraction="0.17864"/>
        <bin value="DS" absoluteLoss="2.1596e+07" fraction="0.27620"/>
        <bin value="A" absoluteLoss="3.6580e+07" fraction="0.46783"/>
      </node>
      <node lon="87.170898" lat="26.635099">
        <bin value="RC" absoluteLoss="4.7473e+05" fraction="0.00203"/>
        <bin value="W" absoluteLoss="1.6011e+07" fraction="0.06853"/>
        <bin value="UFB" absoluteLoss="4.0631e+07" fraction="0.17391"/>
        <bin value="DS" absoluteLoss="6.7016e+07" fraction="0.28684"/>
        <bin value="A" absoluteLoss="1.0950e+08" fraction="0.46869"/>
      </node>
      <node lon="87.290298" lat="27.574899">
        <bin value="RC" absoluteLoss="3.1333e+05" fraction="0.00231"/>
        <bin value="W" absoluteLoss="1.2659e+07" fraction="0.09317"/>
        <bin value="UFB" absoluteLoss="2.6296e+07" fraction="0.19353"/>
        <bin value="DS" absoluteLoss="3.4207e+07" fraction="0.25175"/>
        <bin value="A" absoluteLoss="6.2402e+07" fraction="0.45925"/>
      </node>
      <node lon="87.343803" lat="26.969999">
        <bin value="RC" absoluteLoss="1.5121e+05" fraction="0.00210"/>
        <bin value="W" absoluteLoss="5.3837e+06" fraction="0.07460"/>
        <bin value="UFB" absoluteLoss="1.2860e+07" fraction="0.17818"/>
        <bin value="DS" absoluteLoss="1.9997e+07" fraction="0.27708"/>
        <bin value="A" absoluteLoss="3.3780e+07" fraction="0.46804"/>
      </node>
      <node lon="87.481002" lat="26.6102">
        <bin value="RC" absoluteLoss="2.2713e+05" fraction="0.00189"/>
        <bin value="W" absoluteLoss="6.8572e+06" fraction="0.05711"/>
        <bin value="UFB" absoluteLoss="2.0051e+07" fraction="0.16698"/>
        <bin value="DS" absoluteLoss="3.8360e+07" fraction="0.31946"/>
        <bin value="A" absoluteLoss="5.4582e+07" fraction="0.45456"/>
      </node>
      <node lon="87.555702" lat="27.130899">
        <bin value="RC" absoluteLoss="8.4329e+04" fraction="0.00208"/>
        <bin value="W" absoluteLoss="2.9773e+06" fraction="0.07338"/>
        <bin value="UFB" absoluteLoss="7.1935e+06" fraction="0.17730"/>
        <bin value="DS" absoluteLoss="1.1323e+07" fraction="0.27908"/>
        <bin value="A" absoluteLoss="1.8995e+07" fraction="0.46816"/>
      </node>
      <node lon="87.769996" lat="27.085399">
        <bin value="RC" absoluteLoss="1.5039e+05" fraction="0.00207"/>
        <bin value="W" absoluteLoss="5.2623e+06" fraction="0.07250"/>
        <bin value="UFB" absoluteLoss="1.2823e+07" fraction="0.17667"/>
        <bin value="DS" absoluteLoss="2.0350e+07" fraction="0.28039"/>
        <bin value="A" absoluteLoss="3.3994e+07" fraction="0.46837"/>
      </node>
      <node lon="87.824996" lat="27.554599">
        <bin value="RC" absoluteLoss="1.1547e+05" fraction="0.00211"/>
        <bin value="W" absoluteLoss="4.1712e+06" fraction="0.07617"/>
        <bin value="UFB" absoluteLoss="9.8252e+06" fraction="0.17942"/>
        <bin value="DS" absoluteLoss="1.5037e+07" fraction="0.27459"/>
        <bin value="A" absoluteLoss="2.5613e+07" fraction="0.46772"/>
      </node>
      <node lon="87.911499" lat="26.571399">
        <bin value="RC" absoluteLoss="1.1903e+05" fraction="0.00187"/>
        <bin value="W" absoluteLoss="3.5544e+06" fraction="0.05595"/>
        <bin value="UFB" absoluteLoss="1.0572e+07" fraction="0.16642"/>
        <bin value="DS" absoluteLoss="2.0558e+07" fraction="0.32362"/>
        <bin value="A" absoluteLoss="2.8721e+07" fraction="0.45213"/>
      </node>
      <node lon="87.912498" lat="26.862899">
        <bin value="RC" absoluteLoss="1.8014e+05" fraction="0.00203"/>
        <bin value="W" absoluteLoss="6.0691e+06" fraction="0.06824"/>
        <bin value="UFB" absoluteLoss="1.5439e+07" fraction="0.17359"/>
        <bin value="DS" absoluteLoss="2.5585e+07" fraction="0.28766"/>
        <bin value="A" absoluteLoss="4.1668e+07" fraction="0.46849"/>
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
