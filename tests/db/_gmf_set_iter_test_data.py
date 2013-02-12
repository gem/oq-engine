# Copyright (c) 2012, GEM Foundation.
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

from django.contrib.gis.geos.point import Point

from openquake.engine.db import models

GMVS = iter([
    0.252294938306868,
    0.00894558476907964,
    0.151132933300216,
    0.0720017584564812,
    0.0477298423601717,
    0.0209473778737383,
    0.0142826375129993,
    0.00810452525440645,
    0.05317724833699,
    0.0149335924490702,
    0.0346846321601914,
    0.02479238699487,
    0.729799582246203,
    0.0141248596268433,
    0.0571210320882165,
    0.0457237221727419,
    0.0851203442596857,
    0.0250737105548348,
    0.0512935367105168,
    0.0466984811965513,
    0.0647094509827673,
    0.0137011674940677,
    0.15689278698026,
    0.0153675056609676,
    0.00509134495507867,
    0.0187720473123872,
    0.0168322906268772,
    0.0267122052571397,
    0.23164352054727,
    0.0264362061113464,
    0.00327192823899427,
    0.00257996695068633,
    0.73468651581123,
    0.130897324686063,
    0.0174152489028615,
    0.00365106296522085,
    0.0200616108690774,
    0.0171761077059498,
    0.00689417423724974,
    0.00319765856661502,
    0.0648335484241611,
    0.0743570850927017,
    0.0114299261012732,
    0.00634299173569184,
    0.0859875177517365,
    0.045303453529642,
    0.11178782406297,
    0.0234734974690576,
    0.0094332009571218,
    0.0038808329934219,
    0.238391507264408,
    0.0685055632598018,
    0.0135523461630997,
    0.0257917244477421,
    0.0277504563008486,
    0.0273839405024425,
    0.0228679600504497,
    0.0228073662258289,
    0.403588413430879,
    0.0158056463110169,
    0.430025587195581,
    0.0386668251408169,
    0.20971835017073,
    0.035511735446577,
    0.0271091261282436,
    0.0131632905700059,
    0.0238479545523245,
    0.0179467836929083,
])

GMFS_GMF_SET_0 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                gmv=GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                gmv=GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=2, gmf_nodes=[
            models._GroundMotionFieldNode(
                gmv=GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=3, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=4, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=5, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=6, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=7, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=8, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=9, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=10, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=11, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=12, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_1 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=2, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_2 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=2, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=3, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=4, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_3 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=2, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=3, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=4, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=5, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=6, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=7, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=8, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=9, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),

]

GMFS_GMF_SET_4 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=2, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=3, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=4, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_5 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, rupture_id=1, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, rupture_id=2, gmf_nodes=[
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.0)),
            models._GroundMotionFieldNode(
                GMVS.next(), location=Point(0.0, 0.5)),
        ]),
]
