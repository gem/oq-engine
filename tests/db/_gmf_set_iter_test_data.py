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

from openquake.db import models

GmfNode = models._GroundMotionFieldNode

GMFS_GMF_SET_0 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.252294938306868, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00894558476907964, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.11131854911474, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0223682586083474, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.290360150438584, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0297621082302423, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.729799582246203, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0141248596268433, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.837385087379053, location=Point(0.0, 0.0)),
            GmfNode(iml=0.040131916333975, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.328400636644465, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0319336733732103, location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_1 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0117398713864872, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0390499446479296, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0109382523204871, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0230615197398488, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.00702385966918216, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00724665535415308, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0397554450304716, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0441674959860695, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.00843781295033736, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0381941951917583, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.129284569809953, location=Point(0.0, 0.0)),
            GmfNode(iml=0.025097286655405, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0150784101686404, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00508448800807087, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.172269661234, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0500832409525922, location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_2 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0203796842600201, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0220399253308172, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.157113441446217, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0146890472244176, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0110853245414907, location=Point(0.0, 0.0)),
            GmfNode(iml=0.013521983331287, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.113752113391882, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0970422555294869, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.212578261020779, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00453065615173714, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.076459538719638, location=Point(0.0, 0.0)),
            GmfNode(iml=0.100556669444449, location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_3 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.410178628234652, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0451753340397958, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0939070838137842, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0218891004204294, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.011317782426051, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00749234793327336, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.507335301608961, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0553408823809459, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.170880889755896, location=Point(0.0, 0.0)),
            GmfNode(iml=0.026316693540413, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0398364270885618, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0427068530989839, location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_4 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0361229675977925, location=Point(0.0, 0.0)),
            GmfNode(iml=0.012804894765289, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0721692982956287, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0335227688680533, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0131771952595381, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00258729131704686, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.069949672425427, location=Point(0.0, 0.0)),
            GmfNode(iml=0.013770941878765, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0267186647787859, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0279766776184393, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0164979527563822, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0111457184841252, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0437759709948324, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0504125700307424, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.112631938499063, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0153332651984324, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0304866506377145, location=Point(0.0, 0.0)),
            GmfNode(iml=0.00965357769063567, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.06855175916980, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0539694908078309, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0478469805140865, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0889264754594754, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0621854272774837, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0205033604884899, location=Point(0.0, 0.5)),
        ]),
]

GMFS_GMF_SET_5 = [
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0367944454564915, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0619917607612886, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0775052093521411, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0105033524140419, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.13363306949104, location=Point(0.0, 0.0)),
            GmfNode(iml=0.015357121403572, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='PGA', sa_period=None, sa_damping=None, gmf_nodes=[
            GmfNode(iml=0.0295813131879398, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0235245373079739, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0109439655865924, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0303660443541952, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.0821669927743517, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0232492409644178, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.349536160049098, location=Point(0.0, 0.0)),
            GmfNode(iml=0.0138081861142056, location=Point(0.0, 0.5)),
        ]),
    models._GroundMotionField(
        imt='SA', sa_period=0.1, sa_damping=5.0, gmf_nodes=[
            GmfNode(iml=0.172571124053305, location=Point(0.0, 0.0)),
            GmfNode(iml=0.149466561556068, location=Point(0.0, 0.5)),
        ]),
]
