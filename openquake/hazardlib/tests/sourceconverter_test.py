# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2020 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import io
import unittest.mock
import numpy
from openquake.baselib import hdf5
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import update_source_model, \
    SourceConverter

testdir = os.path.join(os.path.dirname(__file__), 'source_model')

expected = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <sourceGroup
    name="group 1"
    tectonicRegion="Active Shallow Crust"
    >
        <multiPointSource
        id="mps-0"
        name="multiPointSource-0"
        >
            <multiPointGeometry>
                <gml:posList>
                    -7.0899780E+01 -1.8157140E+01 -7.1899780E+01 -1.8157140E+01
                </gml:posList>
                <upperSeismoDepth>
                    0.0000000E+00
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    3.8000000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                WC1994
            </magScaleRel>
            <ruptAspectRatio>
                1.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="truncGutenbergRichterMFD"
            size="2"
            >
                <min_mag>
                    4.5000000E+00
                </min_mag>
                <max_mag>
                    8.2000000E+00
                </max_mag>
                <a_val>
                    1.9473715E+00
                </a_val>
                <b_val>
                    1.0153966E+00
                </b_val>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="9.0000000E+01" probability="5.0000000E-01" rake="-9.0000000E+01" strike="1.3500000E+02"/>
                <nodalPlane dip="6.0000000E+01" probability="5.0000000E-01" rake="9.0000000E+01" strike="1.3500000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="5.5000000E+00" probability="2.3200000E-01"/>
                <hypoDepth depth="1.6500000E+01" probability="9.8000000E-02"/>
                <hypoDepth depth="2.7500000E+01" probability="6.7000000E-01"/>
            </hypoDepthDist>
        </multiPointSource>
    </sourceGroup>
</nrml>
'''

multipoint = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <sourceGroup
    rup_interdep="indep"
    src_interdep="indep"
    tectonicRegion="Active Shallow Crust"
    >
        <multiPointSource
        id="mps-0"
        name="multiPointSource-0"
        >
            <multiPointGeometry>
                <gml:posList>
                    1.6837127E+02 -2.9331920E+01 1.6720091E+02 -2.8522530E+01 1.7500779E+02 -2.6903750E+01 1.7283889E+02 -2.7623210E+01 1.7354940E+02 -2.7623210E+01 1.7494762E+02 -2.7083620E+01 1.7842808E+02 -3.4547990E+01 1.6475001E+02 -2.6364160E+01 1.7985907E+02 -2.6184290E+01 1.7318125E+02 -2.6364160E+01 1.7700355E+02 -2.5105110E+01 1.7711453E+02 -3.3199000E+01 1.7742031E+02 -2.3396400E+01 1.7149714E+02 -2.4295720E+01 1.7485195E+02 -2.4295720E+01 1.7914280E+02 -3.2839270E+01 1.6568785E+02 -1.6111890E+01 1.7806967E+02 -3.4458050E+01 1.6540162E+02 -1.3503860E+01 1.6517621E+02 -1.2874330E+01 1.6544726E+02 -1.2784400E+01 1.6488306E+02 -1.2604540E+01 1.6293384E+02 -1.2334740E+01 1.7796971E+02 -2.3216530E+01 1.6716627E+02 -1.9709180E+01 1.6709062E+02 -1.9889040E+01 1.6298593E+02 -1.9978980E+01 1.6346438E+02 -1.9978980E+01 1.6749370E+02 -2.0068910E+01 1.7723915E+02 -3.2569480E+01 1.7916000E+02 -3.2569480E+01 1.7710212E+02 -3.0321170E+01 1.7999942E+02 -3.0590970E+01 1.6784666E+02 -3.0411110E+01 1.7956252E+02 -2.9152060E+01 1.7987145E+02 -2.9152060E+01 1.7289682E+02 -2.7893010E+01 1.7319953E+02 -2.8342670E+01
                </gml:posList>
                <upperSeismoDepth>
                    0.0000000E+00
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    6.0000000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                WC1994
            </magScaleRel>
            <ruptAspectRatio>
                2.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="incrementalMFD"
            size="38"
            >
                <min_mag>
                    5.0500000E+00
                </min_mag>
                <bin_width>
                    1.0000000E-01
                </bin_width>
                <occurRates>
                    5.2726318E-05 3.9992604E-05 3.0334156E-05 2.3008280E-05 1.7451646E-05 1.3236971E-05 1.0040165E-05 7.6154064E-06 5.7762412E-06 4.3812452E-06 3.3231488E-06 2.5205889E-06 1.9118520E-06 1.4501285E-06 1.0999140E-06 8.3427833E-07 6.3279523E-07 4.7997148E-07 3.6405556E-07 2.7613401E-07 2.0944603E-07 1.5886359E-07 1.2049710E-07 9.1396348E-08 6.9323595E-08 1.9170866E-05 1.4540989E-05 1.1029255E-05 8.3656257E-06 6.3452781E-06 4.8128563E-06 3.6505234E-06 2.7689006E-06 2.1001949E-06 1.5929856E-06 1.2082702E-06 9.1646589E-07 6.9513402E-07 5.2725508E-07 3.9991990E-07 3.0333690E-07 2.3007926E-07 1.7451378E-07 1.3236768E-07 1.0040011E-07 7.6152895E-08 5.7761525E-08 4.3811779E-08 3.3230978E-08 2.5205502E-08 7.8854269E-05 5.9810502E-05 4.5365916E-05 3.4409781E-05 2.6099618E-05 1.9796407E-05 1.5015459E-05 1.1389138E-05 8.6385945E-06 6.5523234E-06 4.9698989E-06 3.7696393E-06 2.8592493E-06 2.1687239E-06 1.6449644E-06 1.2476958E-06 9.4637000E-07 7.1781611E-07 5.4445932E-07 4.1296921E-07 3.1323473E-07 2.3758671E-07 1.8020813E-07 1.3668681E-07 1.0367615E-07 1.3074758E-05 9.9171271E-06 7.5220828E-06 5.7054558E-06 4.3275548E-06 3.2824250E-06 2.4897002E-06 1.8884230E-06 1.4323578E-06 1.0864350E-06 8.2405460E-07 6.2504059E-07 4.7408963E-07 3.5959421E-07 2.7275011E-07 2.0687936E-07 1.5691678E-07 1.1902046E-07 9.0276324E-08 6.8474063E-08 5.1937176E-08 3.9394044E-08 2.9880152E-08 2.2663921E-08 1.7190451E-08 2.1006658E-05 1.5933427E-05 1.2085411E-05 9.1667136E-06 6.9528986E-06 5.2737329E-06 4.0000956E-06 3.0340491E-06 2.3013085E-06 1.7455290E-06 1.3239735E-06 1.0042262E-06 7.6169968E-07 5.7774475E-07 4.3821601E-07 3.3238428E-07 2.5211153E-07 1.9122512E-07 1.4504314E-07 1.1001437E-07 8.3445256E-08 6.3292738E-08 4.8007172E-08 3.6413159E-08 2.7619168E-08 2.3935232E-04 1.8154733E-04 1.3770259E-04 1.0444661E-04 7.9222142E-05 6.0089531E-05 4.5577558E-05 3.4570311E-05 2.6221378E-05 1.9888762E-05 1.5085510E-05 1.1442271E-05 8.6788954E-06 6.5828914E-06 4.9930846E-06 3.7872255E-06 2.8725883E-06 2.1788415E-06 1.6526385E-06 1.2535166E-06 9.5078502E-07 7.2116488E-07 5.4699934E-07 4.1489580E-07 3.1469604E-07 5.5494679E-05 4.2092389E-05 3.1926831E-05 2.4216314E-05 1.8367933E-05 1.3931969E-05 1.0567317E-05 8.0152483E-06 6.0795190E-06 4.6112795E-06 3.4976286E-06 2.6529308E-06 2.0122325E-06 1.5262666E-06 1.1576643E-06 8.7808156E-07 6.6601973E-07 5.0517207E-07 3.8317006E-07 2.9063225E-07 2.2044286E-07 1.6720462E-07 1.2682372E-07 9.6195052E-08 7.2963384E-08 6.8898323E-05 5.2258975E-05 3.9638127E-05 3.0065287E-05 2.2804344E-05 1.7296962E-05 1.3119644E-05 9.9511734E-06 7.5479068E-06 5.7250431E-06 4.3424117E-06 3.2936939E-06 2.4982475E-06 1.8949061E-06 1.4372752E-06 1.0901648E-06 8.2688365E-07 6.2718641E-07 4.7571722E-07 3.6082873E-07 2.7368648E-07 2.0758959E-07 1.5745549E-07 1.1942907E-07 9.0586250E-08 9.7342763E-06 7.3833916E-06 5.6002593E-06 4.2477639E-06 3.2219041E-06 2.4437954E-06 1.8536045E-06 1.4059482E-06 1.0664035E-06 8.0886078E-07 6.1351617E-07 4.6534842E-07 3.5296406E-07 2.6772117E-07 2.0306494E-07 1.5402357E-07 1.1682598E-07 8.8611820E-08 6.7211547E-08 5.0979565E-08 3.8667702E-08 2.9329225E-08 2.2246046E-08 1.6873496E-08 1.2798448E-08 1.9106429E-05 1.4492115E-05 1.0992184E-05 8.3375074E-06 6.3239506E-06 4.7966795E-06 3.6382533E-06 2.7595939E-06 2.0931358E-06 1.5876313E-06 1.2042090E-06 9.1338549E-07 6.9279755E-07 5.2548289E-07 3.9857570E-07 3.0231733E-07 2.2930593E-07 1.7392720E-07 1.3192277E-07 1.0006265E-07 7.5896932E-08 5.7567379E-08 4.3664520E-08 3.3119283E-08 2.5120782E-08 1.3663516E-04 1.0363697E-04 7.8608034E-05 5.9623734E-05 4.5224253E-05 3.4302331E-05 2.6018118E-05 1.9734590E-05 1.4968571E-05 1.1353574E-05 8.6116191E-06 6.5318627E-06 4.9543796E-06 3.7578679E-06 2.8503208E-06 2.1619517E-06 1.6398277E-06 1.2437997E-06 9.4341481E-07 7.1557461E-07 5.4275915E-07 4.1167964E-07 3.1225660E-07 2.3684480E-07 1.7964540E-07 7.2440623E-06 5.4945789E-06 4.1676059E-06 3.1611047E-06 2.3976794E-06 1.8186258E-06 1.3794170E-06 1.0462797E-06 7.9359707E-07 6.0193873E-07 4.5656700E-07 3.4630340E-07 2.6266910E-07 1.9923298E-07 1.5111705E-07 1.1462140E-07 8.6939659E-08 6.5943222E-08 5.0017548E-08 3.7938018E-08 2.8775764E-08 2.1826249E-08 1.6555082E-08 1.2556933E-08 9.5243601E-09 5.0974773E-05 3.8664067E-05 2.9326469E-05 2.2243955E-05 1.6871910E-05 1.2797245E-05 9.7066352E-06 7.3624260E-06 5.5843571E-06 4.2357022E-06 3.2127553E-06 2.4368561E-06 1.8483411E-06 1.4019559E-06 1.0633753E-06 8.0656398E-07 6.1177406E-07 4.6402704E-07 3.5196180E-07 2.6696096E-07 2.0248833E-07 1.5358621E-07 1.1649424E-07 8.8360202E-08 6.7020696E-08 2.2814893E-05 1.7304963E-05 1.3125713E-05 9.9557764E-06 7.5513981E-06 5.7276913E-06 4.3444203E-06 3.2952174E-06 2.4994031E-06 1.8957826E-06 1.4379400E-06 1.0906691E-06 8.2726613E-07 6.2747652E-07 4.7593727E-07 3.6099563E-07 2.7381308E-07 2.0768562E-07 1.5752832E-07 1.1948431E-07 9.0628151E-08 6.8740922E-08 5.2139587E-08 3.9547572E-08 2.9996602E-08 1.8444564E-05 1.3990094E-05 1.0611404E-05 8.0486881E-06 6.1048829E-06 4.6305179E-06 3.5122207E-06 2.6639989E-06 2.0206276E-06 1.5326342E-06 1.1624941E-06 8.8174494E-07 6.6879838E-07 5.0727966E-07 3.8476865E-07 2.9184477E-07 2.2136255E-07 1.6790220E-07 1.2735284E-07 9.6596380E-08 7.3267789E-08 5.5573189E-08 4.2151939E-08 3.1971999E-08 2.4250574E-08 1.2578650E-04 9.5408325E-05 7.2366656E-05 5.4889685E-05 4.1633505E-05 3.1578770E-05 2.3952312E-05 1.8167689E-05 1.3780086E-05 1.0452114E-05 7.9278675E-06 6.0132411E-06 4.5610082E-06 3.4594980E-06 2.6240090E-06 1.9902955E-06 1.5096275E-06 1.1450436E-06 8.6850887E-07 6.5875890E-07 4.9966477E-07 3.7899280E-07 2.8746382E-07 2.1803963E-07 1.6538178E-07 1.0108558E-05 7.6672818E-06 5.8155883E-06 4.4110897E-06 3.3457857E-06 2.5377589E-06 1.9248753E-06 1.4600066E-06 1.1074065E-06 8.3996134E-07 6.3710576E-07 4.8324099E-07 3.6653547E-07 2.7801501E-07 2.1087276E-07 1.5994575E-07 1.2131792E-07 9.2018929E-08 6.9795819E-08 5.2939721E-08 4.0154468E-08 3.0456929E-08 2.3101403E-08 1.7522279E-08 1.3290546E-08 1.1918413E-05 9.0400465E-06 6.8568223E-06 5.2008596E-06 3.9448216E-06 2.9921241E-06 2.2695086E-06 1.7214090E-06 1.3056787E-06 9.9034962E-07 7.5117439E-07 5.6976138E-07 4.3216067E-07 3.2779134E-07 2.4862781E-07 1.8858274E-07 1.4303891E-07 1.0849417E-07 8.2292196E-08 6.2418149E-08 4.7343801E-08 3.5909996E-08 2.7237522E-08 2.0659501E-08 1.5670110E-08 1.5365138E-04 1.1654367E-04 8.8397692E-05 6.7049132E-05 5.0856374E-05 3.8574262E-05 2.9258352E-05 2.2192289E-05 1.6832721E-05 1.2767521E-05 9.6840897E-06 7.3453254E-06 5.5713863E-06 4.2258639E-06 3.2052931E-06 2.4311960E-06 1.8440480E-06 1.3986996E-06 1.0609055E-06 8.0469058E-07 6.1035309E-07 4.6294925E-07 3.5114430E-07 2.6634089E-07 2.0201801E-07 2.2148063E-05 1.6799176E-05 1.2742077E-05 9.6647907E-06 7.3306872E-06 5.5602833E-06 4.2174424E-06 3.1989054E-06 2.4263510E-06 1.8403730E-06 1.3959122E-06 1.0587912E-06 8.0308694E-07 6.0913675E-07 4.6202666E-07 3.5044452E-07 2.6581011E-07 2.0161542E-07 1.5292411E-07 1.1599205E-07 8.7979288E-08 6.6731775E-08 5.0615661E-08 3.8391682E-08 2.9119867E-08 2.6631990E-04 2.0200209E-04 1.5321740E-04 1.1621450E-04 8.8148021E-05 6.6859758E-05 5.0712735E-05 3.8465313E-05 2.9175715E-05 2.2129609E-05 1.6785179E-05 1.2731460E-05 9.6567379E-06 7.3245792E-06 5.5556504E-06 4.2139283E-06 3.1962400E-06 2.4243293E-06 1.8388396E-06 1.3947491E-06 1.0579090E-06 8.0241780E-07 6.0862920E-07 4.6164169E-07 3.5015252E-07 9.8357079E-05 7.4603269E-05 5.6586143E-05 4.2920258E-05 3.2554765E-05 2.4692599E-05 1.8729192E-05 1.4205982E-05 1.0775154E-05 8.1728915E-06 6.1990904E-06 4.7019738E-06 3.5664196E-06 2.7051084E-06 2.0518089E-06 1.5562850E-06 1.1804331E-06 8.9535159E-07 6.7911894E-07 5.1510775E-07 3.9070621E-07 2.9634837E-07 2.2477851E-07 1.7049318E-07 1.2931808E-07 2.3605152E-05 1.7904370E-05 1.3580360E-05 1.0300623E-05 7.8129626E-06 5.9260864E-06 4.4949019E-06 3.4093568E-06 2.5859772E-06 1.9614485E-06 1.4877472E-06 1.1284476E-06 8.5592088E-07 6.4921098E-07 4.9242273E-07 3.7349976E-07 2.8329738E-07 2.1487941E-07 1.6298477E-07 1.2362300E-07 9.3767319E-08 7.1121963E-08 5.3945593E-08 4.0917416E-08 3.1035621E-08 8.4721329E-06 6.4260632E-06 4.8741313E-06 3.6970001E-06 2.8041529E-06 2.1269336E-06 1.6132667E-06 1.2236533E-06 9.2813390E-07 7.0398413E-07 5.3396784E-07 4.0501148E-07 3.0719884E-07 2.3300852E-07 1.7673560E-07 1.3405292E-07 1.0167836E-07 7.7122437E-08 5.8496917E-08 4.4369570E-08 3.3654059E-08 2.5526407E-08 1.9361630E-08 1.4685683E-08 1.1139005E-08 2.6038077E-05 1.9749729E-05 1.4980054E-05 1.1362283E-05 8.6182253E-06 6.5368734E-06 4.9581802E-06 3.7607507E-06 2.8525074E-06 2.1636102E-06 1.6410857E-06 1.2447539E-06 9.4413852E-07 7.1612354E-07 5.4317552E-07 4.1199545E-07 3.1249614E-07 2.3702649E-07 1.7978321E-07 1.3636451E-07 1.0343168E-07 7.8452327E-08 5.9505631E-08 4.5134673E-08 3.4234385E-08 1.0992024E-05 8.3373857E-06 6.3238583E-06 4.7966095E-06 3.6382002E-06 2.7595536E-06 2.0931053E-06 1.5876081E-06 1.2041914E-06 9.1337216E-07 6.9278744E-07 5.2547522E-07 3.9856988E-07 3.0231292E-07 2.2930258E-07 1.7392467E-07 1.3192084E-07 1.0006119E-07 7.5895824E-08 5.7566539E-08 4.3663883E-08 3.3118800E-08 2.5120416E-08 1.9053688E-08 1.4452111E-08 3.1166993E-05 2.3639982E-05 1.7930788E-05 1.3600398E-05 1.0315822E-05 7.8244907E-06 5.9348304E-06 4.5015341E-06 3.4143873E-06 2.5897928E-06 1.9643427E-06 1.4899424E-06 1.1301126E-06 8.5718380E-07 6.5016890E-07 4.9314930E-07 3.7405086E-07 2.8371539E-07 2.1519646E-07 1.6322526E-07 1.2380540E-07 9.3905674E-08 7.1226904E-08 5.4025190E-08 4.0977790E-08 2.1633018E-04 1.6408518E-04 1.2445765E-04 9.4400397E-05 7.1602149E-05 5.4309811E-05 4.1193674E-05 3.1245160E-05 2.3699271E-05 1.7975759E-05 1.3634508E-05 1.0341694E-05 7.8441146E-06 5.9497151E-06 4.5128241E-06 3.4229506E-06 2.5962880E-06 1.9692693E-06 1.4936792E-06 1.1329469E-06 8.5933363E-07 6.5179953E-07 4.9438613E-07 3.7498899E-07 2.8442695E-07 3.4705930E-04 2.6324245E-04 1.9966786E-04 1.5144690E-04 1.1487159E-04 8.7129428E-05 6.6087162E-05 5.0126725E-05 3.8020828E-05 2.8838575E-05 2.1873891E-05 1.6591218E-05 1.2584342E-05 9.5451496E-06 7.2399401E-06 5.4914522E-06 4.1652344E-06 3.1593059E-06 2.3963150E-06 1.8175909E-06 1.3786321E-06 1.0456844E-06 7.9314548E-07 6.0159620E-07 4.5630720E-07 2.2204507E-05 1.6841988E-05 1.2774550E-05 9.6894212E-06 7.3493693E-06 5.5744536E-06 4.2281904E-06 3.2070577E-06 2.4325345E-06 1.8450632E-06 1.3994696E-06 1.0614895E-06 8.0513359E-07 6.1068912E-07 4.6320412E-07 3.5133761E-07 2.6648752E-07 2.0212923E-07 1.5331384E-07 1.1628765E-07 8.8203501E-08 6.6901839E-08 5.0744653E-08 3.8489523E-08 2.9194078E-08 7.5076083E-05 5.6944770E-05 4.3192275E-05 3.2761087E-05 2.4849093E-05 1.8847892E-05 1.4296016E-05 1.0843444E-05 8.2246890E-06 6.2383784E-06 4.7317735E-06 3.5890225E-06 2.7222526E-06 2.0648127E-06 1.5661483E-06 1.1879143E-06 9.0102607E-07 6.8342301E-07 5.1837235E-07 3.9318239E-07 2.9822655E-07 2.2620309E-07 1.7157372E-07 1.3013766E-07 9.8708655E-08 1.0285083E-05 7.8011756E-06 5.9171460E-06 4.4881206E-06 3.4042132E-06 2.5820758E-06 1.9584894E-06 1.4855027E-06 1.1267451E-06 8.5462960E-07 6.4823155E-07 4.9167984E-07 3.7293628E-07 2.8286998E-07 2.1455523E-07 1.6273889E-07 1.2343649E-07 9.3625857E-08 7.1014665E-08 5.3864207E-08 4.0855686E-08 3.0988799E-08 2.3504823E-08 1.7828270E-08 1.3522639E-08 7.1611734E-05 5.4317081E-05 4.1199188E-05 3.1249343E-05 2.3702444E-05 1.7978165E-05 1.3636333E-05 1.0343079E-05 7.8451647E-06 5.9505115E-06 4.5134282E-06 3.4234089E-06 2.5966356E-06 1.9695329E-06 1.4938792E-06 1.1330986E-06 8.5944867E-07 6.5188679E-07 4.9445231E-07 3.7503919E-07 2.8446503E-07 2.1576506E-07 1.6365653E-07 1.2413252E-07 9.4153793E-08 2.7702799E-05 2.1012411E-05 1.5937790E-05 1.2088721E-05 9.1692240E-06 6.9548027E-06 5.2751772E-06 4.0011910E-06 3.0348800E-06 2.3019387E-06 1.7460070E-06 1.3243361E-06 1.0045012E-06 7.6190828E-07 5.7790297E-07 4.3833602E-07 3.3247531E-07 2.5218058E-07 1.9127749E-07 1.4508286E-07 1.1004450E-07 8.3468108E-08 6.3310072E-08 4.8020319E-08 3.6423131E-08 6.5174061E-05 4.9434144E-05 3.7495509E-05 2.8440124E-05 2.1571668E-05 1.6361984E-05 1.2410469E-05 9.4132681E-06 7.1399087E-06 5.4155790E-06 4.1076850E-06 3.1156550E-06 2.3632061E-06 1.7924780E-06 1.3595841E-06 1.0312366E-06 7.8218690E-07 5.9328419E-07 4.5000258E-07 3.4132433E-07 2.5889250E-07 1.9636845E-07 1.4894432E-07 1.1297339E-07 8.5689659E-08 2.8906642E-05 2.1925519E-05 1.6630378E-05 1.2614044E-05 9.5676787E-06 7.2570283E-06 5.5044135E-06 4.1750654E-06 3.1667627E-06 2.4019710E-06 1.8218809E-06 1.3818860E-06 1.0481525E-06 7.9501751E-07 6.0301613E-07 4.5738420E-07 3.4692324E-07 2.6313925E-07 1.9958958E-07 1.5138753E-07 1.1482655E-07 8.7095270E-08 6.6061252E-08 5.0107073E-08 3.8005922E-08 7.5914333E-05 5.7580577E-05 4.3674531E-05 3.3126876E-05 2.5126542E-05 1.9058335E-05 1.4455635E-05 1.0964515E-05 8.3165204E-06 6.3080320E-06 4.7846054E-06 3.6290952E-06 2.7526475E-06 2.0878670E-06 1.5836349E-06 1.2011778E-06 9.1108633E-07 6.9105365E-07 5.2416015E-07 3.9757241E-07 3.0155634E-07 2.2872872E-07 1.7348940E-07 1.3159069E-07 9.9810771E-08 1.2708337E-05 9.6391989E-06 7.3112760E-06 5.5455600E-06 4.2062748E-06 3.1904349E-06 2.4199262E-06 1.8354998E-06 1.3922159E-06 1.0559876E-06 8.0096042E-07 6.0752379E-07 4.6080324E-07 3.4951656E-07 2.6510627E-07 2.0108155E-07 1.5251918E-07 1.1568491E-07 8.7746324E-08 6.6555073E-08 5.0481634E-08 3.8290024E-08 2.9042759E-08 2.2028763E-08 1.6708688E-08
                </occurRates>
                <lengths>
                    25
                </lengths>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="9.0000000E+01" probability="1.0000000E+00" rake="0.0000000E+00" strike="2.7000000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="5.0000000E+00" probability="7.0000000E-02"/>
                <hypoDepth depth="1.5000000E+01" probability="2.4000000E-01"/>
                <hypoDepth depth="2.5000000E+01" probability="1.2000000E-01"/>
                <hypoDepth depth="3.5000000E+01" probability="5.7000000E-01"/>
            </hypoDepthDist>
        </multiPointSource>
    </sourceGroup>
</nrml>
'''


class PointToMultiPointTestCase(unittest.TestCase):
    def test_simple(self):
        testfile = os.path.join(testdir, 'two-point-sources.xml')
        sm = nrml.read(testfile).sourceModel
        update_source_model(sm, testfile)
        with io.BytesIO() as f:
            nrml.write(sm, f)
            got = f.getvalue().decode('utf-8')
            self.assertEqual(got, expected)

    def test_complex(self):
        testfile = os.path.normpath(os.path.join(
            testdir, '../../../qa_tests_data/classical/case_30/ssm/shallow/'
            'gridded_seismicity_source_4.xml'))
        sm = nrml.read(testfile).sourceModel
        update_source_model(sm, testfile)
        with io.BytesIO() as f:
            nrml.write(sm, f)
            got = f.getvalue().decode('utf-8')
            self.assertEqual(got, multipoint)


class SourceConverterTestCase(unittest.TestCase):

    def test_wrong_trt(self):
        """ Test consistency between group and sources TRTs """
        testfile = os.path.join(testdir, 'wrong-trt.xml')
        with self.assertRaises(ValueError) as ctx:
            nrml.to_python(testfile)
        self.assertIn('node pointSource: Found Cratonic, expected '
                      'Active Shallow Crust, line 67', str(ctx.exception))

    def test_tom_poisson_not_defined(self):
        """ Read area source without tom """
        testfile = os.path.join(testdir, 'area-source.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        src = sg[0].sources[0]
        self.assertEqual(src.temporal_occurrence_model.time_span, 50,
                         "Wrong time span in the temporal occurrence model")

    def test_tom_poisson_no_rate(self):
        testfile = os.path.join(testdir, 'tom_poisson_no_rate.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        src = sg[0].sources[0]
        msg = "Wrong time span in the temporal occurrence model"
        self.assertEqual(src.temporal_occurrence_model.time_span, 50, msg)

    def test_wrong_source_type(self):
        """ Test that only nonparametric sources are used with mutex ruptures
        """
        testfile = os.path.join(testdir, 'rupture_mutex_wrong.xml')
        with self.assertRaises(ValueError):
            nrml.to_python(testfile)

    def test_non_parametric_mutex(self):
        """ Test non-parametric source with mutex ruptures """
        fname = 'nonparametric-source-mutex-ruptures.xml'
        testfile = os.path.join(testdir, fname)
        grp = nrml.to_python(testfile)[0]
        src = grp[0]
        expected = numpy.array([0.2, 0.8])
        computed = numpy.array([src.data[0][0].weight, src.data[1][0].weight])
        numpy.testing.assert_equal(computed, expected)

    def test_tom_poisson_with_rate(self):
        testfile = os.path.join(testdir, 'tom_poisson_with_rate.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        src = sg[0].sources[0]
        msg = "Wrong time span in the temporal occurrence model"
        self.assertEqual(src.temporal_occurrence_model.time_span, 50, msg)
        msg = "Wrong occurrence rate in the temporal occurrence model"
        self.assertEqual(src.temporal_occurrence_model.occurrence_rate,
                         0.01, msg)

    def test_source_group_with_tom(self):
        testfile = os.path.join(testdir, 'source_group_with_tom.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        msg = "Wrong occurrence rate in the temporal occurrence model"
        expected = sg[0].temporal_occurrence_model.occurrence_rate
        self.assertEqual(expected, 0.01, msg)
        msg = "Wrong cluster definition"
        self.assertEqual(sg[0].cluster, False, msg)

    def test_source_group_cluster(self):
        testfile = os.path.join(testdir, 'source_group_cluster.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        msg = "Wrong cluster definition"
        self.assertEqual(sg[0].cluster, True, msg)

    def test_dupl_values_npdist(self):
        testfile = os.path.join(testdir, 'wrong-npdist.xml')
        with unittest.mock.patch('logging.warning') as w:
            nrml.to_python(testfile)
        self.assertEqual(
            'There were repeated values %s in %s:%s', w.call_args[0][0])

    def test_dupl_values_hddist(self):
        testfile = os.path.join(testdir, 'wrong-hddist.xml')
        with unittest.mock.patch('logging.warning') as w:
            nrml.to_python(testfile)
        self.assertEqual(
            'There were repeated values %s in %s:%s', w.call_args[0][0])

    def test_mfd_with_slip_rate(self):
        testfile = os.path.join(testdir, 'source_with_slip_rate.xml')
        src = nrml.to_python(testfile).src_groups[0][0]
        self.assertAlmostEqual(src.mfd.a_val, 3.97184573434)


class SourceGroupHDF5TestCase(unittest.TestCase):
    def test_serialization(self):
        testfile = os.path.join(
            testdir, 'nonparametric-source-mutex-ruptures.xml')
        [grp] = nrml.to_python(testfile)
        for i, src in enumerate(grp, 1):
            src.id = i
        with hdf5.File.temporary() as f:
            f['grp'] = grp
        with hdf5.File(f.path, 'r') as f:
            print(f['grp'])
