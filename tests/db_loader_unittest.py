# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
    Unittests for NRML/CSV input files loaders to the database
"""

import geoalchemy
import unittest

from openquake import java
from openquake.utils import db
from openquake.utils.db import loader as db_loader
from tests.utils import helpers

TEST_SRC_FILE = helpers.get_data_path('example-source-model.xml')

SIMPLE_FAULT_OUTLINE_WKT = \
'''SRID=4326;POLYGON((
-121.7467204676017 37.7997646326561 8.0,
 -121.75532031089188 37.805642887351446 8.0,
 -121.76392151966904 37.81152051630329 8.0,
 -121.77252409429458 37.817397519279645 8.0,
 -121.78112803513002 37.82327389604836 8.0,
 -121.78973334253678 37.82914964637729 8.0,
 -121.79834001687624 37.83502477003418 8.0,
 -121.80694805850989 37.840899266786685 8.0,
 -121.81555746779918 37.84677313640241 8.0,
 -121.82416824510553 37.85264637864887 8.0,
 -121.8327803907904 37.85851899329353 8.0,
 -121.8413939052153 37.86439098010374 8.0,
 -121.85000878874159 37.87026233884681 8.0,
 -121.85862504173078 37.87613306928992 8.0,
 -121.86724266454432 37.88200317120026 8.0,
 -121.8758616575437 37.88787264434489 8.0,
 -121.88448202109029 37.893741488490775 8.0,
 -121.89310375554568 37.89960970340485 8.0,
 -121.90172686127129 37.90547728885395 8.0,
 -121.91035133862856 37.91134424460486 8.0,
 -121.91897718797895 37.91721057042425 8.0,
 -121.92760440968398 37.92307626607874 8.0,
 -121.93623300410509 37.92894133133485 8.0,
 -121.94486297160377 37.93480576595908 8.0,
 -121.95349431254148 37.94066956971779 8.0,
 -121.96212702727968 37.9465327423773 8.0,
 -121.7408574406909 37.805127601704555 8.615661475325659,
 -121.74945681724269 37.811005856369114 8.615661475325659,
 -121.75805755919514 37.816883485290184 8.615661475325659,
 -121.76665966690965 37.82276048823576 8.615661475325659,
 -121.77526314074777 37.82863686497368 8.615661475325659,
 -121.7838679810709 37.834512615271834 8.615661475325659,
 -121.79247418824049 37.84038773889794 8.615661475325659,
 -121.80108176261804 37.846262235619655 8.615661475325659,
 -121.809690704565 37.85213610520459 8.615661475325659,
 -121.8183010144428 37.85800934742025 8.615661475325659,
 -121.82691269261296 37.86388196203413 8.615661475325659,
 -121.83552573943697 37.86975394881354 8.615661475325659,
 -121.84414015527626 37.87562530752581 8.615661475325659,
 -121.85275594049229 37.88149603793812 8.615661475325659,
 -121.8613730954466 37.88736613981767 8.615661475325659,
 -121.86999162050067 37.8932356129315 8.615661475325659,
 -121.8786115160159 37.899104457046576 8.615661475325659,
 -121.88723278235385 37.90497267192984 8.615661475325659,
 -121.89585541987601 37.91084025734815 8.615661475325659,
 -121.90447942894383 37.91670721306824 8.615661475325659,
 -121.91310480991879 37.92257353885682 8.615661475325659,
 -121.92173156316244 37.92843923448049 8.615661475325659,
 -121.93035968903622 37.93430429970579 8.615661475325659,
 -121.93898918790164 37.94016873429921 8.615661475325659,
 -121.9476200601202 37.946032538027104 8.615661475325659,
 -121.95625230605336 37.9518957106558 8.615661475325659,
 -121.73499356221691 37.81049028014264 9.231322950651316,
 -121.7435924717821 37.816368534714854 9.231322950651316,
 -121.75219274666158 37.82224616354356 9.231322950651316,
 -121.76079438721672 37.828123166396765 9.231322950651316,
 -121.76939739380914 37.833999543042324 9.231322950651316,
 -121.77800176680024 37.83987529324812 9.231322950651316,
 -121.7866075065515 37.845750416781826 9.231322950651316,
 -121.7952146134244 37.85162491341116 9.231322950651316,
 -121.80382308778047 37.857498782903704 9.231322950651316,
 -121.81243292998111 37.863372025026976 9.231322950651316,
 -121.82104414038791 37.869244639548455 9.231322950651316,
 -121.8296567193623 37.87511662623547 9.231322950651316,
 -121.8382706672658 37.88098798485532 9.231322950651316,
 -121.84688598445989 37.88685871517524 9.231322950651316,
 -121.8555026713061 37.892728816962354 9.231322950651316,
 -121.86412072816589 37.89859828998376 9.231322950651316,
 -121.87274015540075 37.9044671340064 9.231322950651316,
 -121.88136095337227 37.91033534879725 9.231322950651316,
 -121.8899831224419 37.91620293412311 9.231322950651316,
 -121.89860666297113 37.92206988975077 9.231322950651316,
 -121.90723157532149 37.92793621544689 9.231322950651316,
 -121.91585785985451 37.933801910978126 9.231322950651316,
 -121.92448551693168 37.93966697611097 9.231322950651316,
 -121.93311454691454 37.94553141061192 9.231322950651316,
 -121.94174495016455 37.951395214247356 9.231322950651316,
 -121.95037672704326 37.95725838678357 9.231322950651316,
 -121.72912883193759 37.815852667871994 9.846984425976975,
 -121.73772727426788 37.82173092229024 9.846984425976975,
 -121.74632708182604 37.827608550964996 9.846984425976975,
 -121.75492825497345 37.833485553664225 9.846984425976975,
 -121.76353079407173 37.83936193015581 9.846984425976975,
 -121.77213469948232 37.84523768020759 9.846984425976975,
 -121.78073997156666 37.85111280358732 9.846984425976975,
 -121.78934661068634 37.85698730006264 9.846984425976975,
 -121.79795461720285 37.86286116940118 9.846984425976975,
 -121.80656399147765 37.868734411370426 9.846984425976975,
 -121.81517473387231 37.874607025737866 9.846984425976975,
 -121.82378684474831 37.88047901227085 9.846984425976975,
 -121.83240032446716 37.88635037073665 9.846984425976975,
 -121.84101517339037 37.89222110090252 9.846984425976975,
 -121.84963139187953 37.898091202535575 9.846984425976975,
 -121.85824898029608 37.903960675402914 9.846984425976975,
 -121.86686793900152 37.90982951927148 9.846984425976975,
 -121.87548826835747 37.91569773390824 9.846984425976975,
 -121.88410996872543 37.92156531908002 9.846984425976975,
 -121.89273304046691 37.92743227455357 9.846984425976975,
 -121.90135748394337 37.93329860009559 9.846984425976975,
 -121.90998329951648 37.93916429547269 9.846984425976975,
 -121.91861048754768 37.9450293604514 9.846984425976975,
 -121.92723904839852 37.950893794798226 9.846984425976975,
 -121.93586898243053 37.95675759827952 9.846984425976975,
 -121.94450029000527 37.96262077066159 9.846984425976975,
 -121.72326324961074 37.82121476479418 10.462645901302633,
 -121.73186122445779 37.827093018996855 10.462645901302633,
 -121.74046056444622 37.832970647456 10.462645901302633,
 -121.7490612699374 37.83884764993963 10.462645901302633,
 -121.75766334129301 37.84472402621559 10.462645901302633,
 -121.76626677887448 37.850599776051745 10.462645901302633,
 -121.77487158304334 37.85647489921582 10.462645901302633,
 -121.78347775416111 37.8623493954755 10.462645901302633,
 -121.79208529258933 37.86822326459836 10.462645901302633,
 -121.80069419868951 37.87409650635194 10.462645901302633,
 -121.8093044728232 37.8799691205037 10.462645901302633,
 -121.81791611535193 37.885841106820976 10.462645901302633,
 -121.82652912663721 37.89171246507107 10.462645901302633,
 -121.83514350704057 37.8975831950212 10.462645901302633,
 -121.8437592569236 37.903453296438535 10.462645901302633,
 -121.85237637664785 37.90932276909012 10.462645901302633,
 -121.86099486657476 37.915191612742944 10.462645901302633,
 -121.86961472706595 37.92105982716393 10.462645901302633,
 -121.878235958483 37.926927412119916 10.462645901302633,
 -121.8868585611874 37.932794367377674 10.462645901302633,
 -121.89548253554068 37.9386606927039 10.462645901302633,
 -121.90410788190447 37.94452638786519 10.462645901302633,
 -121.91273460064023 37.95039145262809 10.462645901302633,
 -121.92136269210961 37.956255886759074 10.462645901302633,
 -121.92999215667409 37.962119690024515 10.462645901302633,
 -121.93862299469524 37.967982862190716 10.462645901302633,
 -121.71739681499416 37.82657657081076 11.078307376628292,
 -121.72599432210953 37.83245482473618 11.078307376628292,
 -121.73459319427968 37.838332452918074 11.078307376628292,
 -121.74319343186612 37.844209455124435 11.078307376628292,
 -121.75179503523046 37.8500858311231 11.078307376628292,
 -121.76039800473417 37.85596158068196 11.078307376628292,
 -121.76900234073881 37.86183670356873 11.078307376628292,
 -121.77760804360592 37.86771119955107 11.078307376628292,
 -121.78621511369707 37.873585068396594 11.078307376628292,
 -121.79482355137378 37.87945830987282 11.078307376628292,
 -121.80343335699759 37.88533092374718 11.078307376628292,
 -121.8120445309301 37.89120290978708 11.078307376628292,
 -121.82065707353277 37.89707426775978 11.078307376628292,
 -121.82927098516724 37.9029449974325 11.078307376628292,
 -121.83788626619507 37.90881509857238 11.078307376628292,
 -121.8465029169778 37.91468457094653 11.078307376628292,
 -121.85512093787695 37.92055341432188 11.078307376628292,
 -121.86374032925416 37.92642162846539 11.078307376628292,
 -121.87236109147096 37.9322892131439 11.078307376628292,
 -121.88098322488892 37.93815616812417 11.078307376628292,
 -121.88960672986958 37.94402249317286 11.078307376628292,
 -121.8982316067746 37.94988818805662 11.078307376628292,
 -121.90685785596544 37.95575325254196 11.078307376628292,
 -121.91548547780374 37.96161768639539 11.078307376628292,
 -121.9241144726511 37.96748148938325 11.078307376628292,
 -121.932744840869 37.97334466127188 11.078307376628292,
 -121.71152952784557 37.831938085823225 11.69396885195395,
 -121.7201265669807 37.83781633940973 11.69396885195395,
 -121.72872497108403 37.84369396725268 11.69396885195395,
 -121.73732474051708 37.84957096912008 11.69396885195395,
 -121.74592587564146 37.85544734477976 11.69396885195395,
 -121.75452837681871 37.86132309399963 11.69396885195395,
 -121.76313224441034 37.86719821654739 11.69396885195395,
 -121.77173747877796 37.8730727121907 11.69396885195395,
 -121.78034408028314 37.87894658069717 11.69396885195395,
 -121.78895204928742 37.88481982183431 11.69396885195395,
 -121.79756138615237 37.890692435369616 11.69396885195395,
 -121.80617209123962 37.8965644210704 11.69396885195395,
 -121.81478416491063 37.902435778703975 11.69396885195395,
 -121.82339760752707 37.90830650803755 11.69396885195395,
 -121.83201241945048 37.91417660883828 11.69396885195395,
 -121.8406286010425 37.920046080873256 11.69396885195395,
 -121.84924615266459 37.92591492390942 11.69396885195395,
 -121.85786507467844 37.93178313771372 11.69396885195395,
 -121.86648536744563 37.93765072205299 11.69396885195395,
 -121.87510703132772 37.94351767669401 11.69396885195395,
 -121.88373006668627 37.94938400140345 11.69396885195395,
 -121.89235447388292 37.95524969594792 11.69396885195395,
 -121.90098025327926 37.96111476009397 11.69396885195395,
 -121.90960740523688 37.966979193608076 11.69396885195395,
 -121.91823593011736 37.97284299625661 11.69396885195395,
 -121.92686582828229 37.978706167805875 11.69396885195395,
 -121.70566138792265 37.83729930973308 12.309630327279608,
 -121.71425795882892 37.84317756291894 12.309630327279608,
 -121.72285589461679 37.84905519036125 12.309630327279608,
 -121.73145519564771 37.85493219182795 12.309630327279608,
 -121.74005586228338 37.860808567086956 12.309630327279608,
 -121.74865789488534 37.8666843159061 12.309630327279608,
 -121.75726129381513 37.8725594380531 12.309630327279608,
 -121.76586605943436 37.87843393329566 12.309630327279608,
 -121.7744721921046 37.88430780140135 12.309630327279608,
 -121.78307969218744 37.89018104213769 12.309630327279608,
 -121.79168856004448 37.896053655272155 12.309630327279608,
 -121.80029879603731 37.901925640572095 12.309630327279608,
 -121.80891040052752 37.907796997804816 12.309630327279608,
 -121.81752337387668 37.913667726737486 12.309630327279608,
 -121.82613771644645 37.919537827137326 12.309630327279608,
 -121.83475342859839 37.92540729877137 12.309630327279608,
 -121.84337051069406 37.93127614140658 12.309630327279608,
 -121.85198896309517 37.9371443548099 12.309630327279608,
 -121.86060878616325 37.943011938748185 12.309630327279608,
 -121.86922998025993 37.94887889298818 12.309630327279608,
 -121.8778525457468 37.954745217296576 12.309630327279608,
 -121.88647648298551 37.96061091144 12.309630327279608,
 -121.89510179233764 37.96647597518497 12.309630327279608,
 -121.90372847416484 37.97234040829798 12.309630327279608,
 -121.91235652882867 37.97820421054539 12.309630327279608,
 -121.92098595669077 37.98406738169352 12.309630327279608,
 -121.69979239498296 37.84266024244175 12.925291802605265,
 -121.70838849741173 37.84853849516526 12.925291802605265,
 -121.71698596463537 37.854416122145146 12.925291802605265,
 -121.7255847970154 37.86029312314944 12.925291802605265,
 -121.73418499491355 37.86616949794599 12.925291802605265,
 -121.74278655869134 37.87204524630267 12.925291802605265,
 -121.7513894887103 37.87792036798718 12.925291802605265,
 -121.75999378533214 37.88379486276721 12.925291802605265,
 -121.76859944891841 37.88966873041036 12.925291802605265,
 -121.77720647983072 37.89554197068414 12.925291802605265,
 -121.7858148784307 37.90141458335603 12.925291802605265,
 -121.79442464507997 37.90728656819335 12.925291802605265,
 -121.80303578014009 37.913157924963414 12.925291802605265,
 -121.8116482839727 37.919028653433436 12.925291802605265,
 -121.82026215693944 37.92489875337057 12.925291802605265,
 -121.82887739940193 37.93076822454189 12.925291802605265,
 -121.83749401172173 37.936637066714376 12.925291802605265,
 -121.84611199426057 37.94250527965494 12.925291802605265,
 -121.85473134738001 37.94837286313044 12.925291802605265,
 -121.8633520714417 37.95423981690762 12.925291802605265,
 -121.87197416680722 37.96010614075318 12.925291802605265,
 -121.88059763383829 37.96597183443374 12.925291802605265,
 -121.88922247289645 37.97183689771583 12.925291802605265,
 -121.8978486843434 37.97770133036593 12.925291802605265,
 -121.90647626854076 37.98356513215041 12.925291802605265,
 -121.91510522585013 37.98942830283558 12.925291802605265,
 -121.7467204676017 37.7997646326561 8.0))'''.replace('\n', '')

SIMPLE_FAULT_EDGE_WKT = \
    'SRID=4326;LINESTRING(-121.8229 37.7301 0.0, -122.0388 37.8771 0.0)'


class NrmlModelLoaderTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        """
        One-time setup stuff for this entire test case class.
        """
        super(NrmlModelLoaderTestCase, self).__init__(*args, **kwargs)

        self.src_reader = java.jclass('SourceModelReader')(
            TEST_SRC_FILE, db_loader.SourceModelLoader.DEFAULT_MFD_BIN_WIDTH)
        self.sources = self.src_reader.read()
        self.simple, self.complex, self.area, self.point = self.sources

    def test_get_simple_fault_surface(self):
        surface = db_loader.get_fault_surface(self.simple)
        surface_type = surface.__javaclass__.getName()
        self.assertEqual('org.opensha.sha.faultSurface.StirlingGriddedSurface',
            surface_type)

        # these surfaces are complex objects
        # there is a lot here we can test
        # for now, we only test the overall surface area
        # the test value is derived from our test data
        self.assertEqual(200.0, surface.getSurfaceArea())

    def test_get_complex_fault_surface(self):
        surface = db_loader.get_fault_surface(self.complex)
        surface_type = surface.__javaclass__.getName()
        self.assertEqual(
            'org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface',
            surface_type)

        # as with the simple fault surface, we're only going to test
        # the surface area (for now)
        # the test value is derived from our test data
        self.assertEqual(126615.0, surface.getSurfaceArea())

    def test_get_fault_surface_raises(self):
        """
        Test that the
        :py:function:`openquake.utils.db.loader.get_fault_surface` function
        raises when passed an inappropriate source type.
        """
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.area)
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.point)

    def test_parse_mfd_simple_fault(self):

        expected = {
            'table': 'pshai.mfd_evd',
            'data': {
                'max_val': 6.9500000000000002,
                'total_cumulative_rate': 1.8988435199999998e-05,
                'min_val': 6.5499999999999998,
                'bin_size': 0.10000000000000009,
                'mfd_values': [
                    0.0010614989,
                    0.00088291626999999998,
                    0.00073437776999999999,
                    0.00061082879999999995,
                    0.00050806530000000003],
                'total_moment_rate': 281889786038447.25,
                'owner_id': None}}

        mfd = self.simple.getMfd()

        # Assume that this is an 'evenly discretized' MFD
        # We want to do this check so we know right away if our test data
        # has been altered.
        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual(
            '%s.IncrementalMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        # this is the dict we'll be passing to sqlalchemy to do the db insert
        mfd_insert = db_loader.parse_mfd(self.simple, mfd)

        helpers.assertDictAlmostEqual(self, expected, mfd_insert)

    def test_parse_mfd_complex_fault(self):
        expected = {
            'table': 'pshai.mfd_tgr',
            'data': {
                'b_val': 0.80000000000000004,
                'total_cumulative_rate': 4.933442096397671e-10,
                'min_val': 6.5499999999999998,
                'max_val': 8.9499999999999993,
                'total_moment_rate': 198544639016.43918,
                'a_val': 1.0,
                'owner_id': None}}

        mfd = self.complex.getMfd()

        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual(
            '%s.GutenbergRichterMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        mfd_insert = db_loader.parse_mfd(self.complex, mfd)

        helpers.assertDictAlmostEqual(self, expected, mfd_insert)

    def test_parse_simple_fault_src(self):

        expected = (
            {'table': 'pshai.mfd_evd', 'data': {
                'max_val': 6.9500000000000002,
                'total_cumulative_rate': 1.8988435199999998e-05,
                'min_val': 6.5499999999999998,
                'bin_size': 0.10000000000000009,
                'mfd_values': [
                    0.0010614989, 0.00088291626999999998,
                    0.00073437776999999999, 0.00061082879999999995,
                    0.00050806530000000003],
                'total_moment_rate': 281889786038447.25,
                'owner_id': None}},
            {'table': 'pshai.simple_fault', 'data': {
                'name': u'Mount Diablo Thrust',
                'upper_depth': 8.0,
                'mgf_evd_id': None,
                'mfd_tgr_id': None,
                'outline': \
                    geoalchemy.WKTSpatialElement(SIMPLE_FAULT_OUTLINE_WKT),
                'edge': geoalchemy.WKTSpatialElement(SIMPLE_FAULT_EDGE_WKT),
                'lower_depth': 13.0,
                'gid': u'src01',
                'owner_id': None,
                'dip': 38.0,
                'description': None}},
            {'table': 'pshai.source', 'data': {
                'r_depth_distr_id': None,
                'name': u'Mount Diablo Thrust',
                'tectonic_region': 'active',
                'rake': 90.0,
                'si_type': 'simple',
                'gid': u'src01',
                'simple_fault_id': None,
                'owner_id': None,
                'hypocentral_depth': None,
                'description': None,
                'input_id': None}})

        simple_data = db_loader.parse_simple_fault_src(self.simple)

        # The WKTSpatialElement objects do not make for nice comparisons.
        # So instead, we'll just test the text element of each object
        # to make sure the coords and spatial reference system match.
        # To do that, we need to remove the WKTSpatialElements so
        # we can compare the rest of the dicts for equality.
        exp_outline = expected[1]['data'].pop('outline')
        actual_outline = simple_data[1]['data'].pop('outline')

        self.assertEqual(exp_outline.geom_wkt, actual_outline.geom_wkt)

        exp_edge = expected[1]['data'].pop('edge')
        actual_edge = simple_data[1]['data'].pop('edge')

        self.assertEqual(exp_edge.geom_wkt, actual_edge.geom_wkt)

        # Now we can test the rest of the data.
        for idx, exp in enumerate(expected):
            helpers.assertDictAlmostEqual(self, exp, simple_data[idx])


class CsvLoaderTestCase(unittest.TestCase):
    """
        Main class to execute tests about CSV
    """

    def setUp(self):
        csv_file = "ISC_sampledata1.csv"
        self.csv_path = helpers.get_data_path(csv_file)
        self.db_loader = db_loader.CsvModelLoader(self.csv_path, None, 'eqcat')
        self.db_loader._read_model()
        self.csv_reader = self.db_loader.csv_reader

    def test_input_csv_is_of_the_right_len(self):
        # without the header line is 8892
        expected_len = 8892

        self.assertEqual(len(list(self.csv_reader)), expected_len)

    def test_csv_headers_are_correct(self):
        expected_headers = ['eventid', 'agency', 'identifier', 'year',
            'month', 'day', 'hour', 'minute', 'second', 'time_error',
            'longitude', 'latitude', 'semi_major', 'semi_minor', 'strike',
            'depth', 'depth_error', 'mw_val', 'mw_val_error',
            'ms_val', 'ms_val_error', 'mb_val', 'mb_val_error', 'ml_val',
            'ml_val_error']

        # it's not important that the headers of the csv are in the right or
        # wrong order, by using the DictReader it is sufficient to compare the
        # headers
        expected_headers = sorted(expected_headers)
        csv_headers = sorted(self.csv_reader.next().keys())
        self.assertEqual(csv_headers, expected_headers)

    # Skip the end-to-end test for now, until database on CI system is setup
    # TODO: move the test in db_tests folder
    @helpers.skipit
    def test_csv_to_db_loader_end_to_end(self):
        """
            * Serializes the csv into the database
            * Queries the database for the data just inserted
            * Verifies the data against the csv
            * Deletes the inserted records from the database
        """
        def _pop_date_fields(csv):
            date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
            res = [csv.pop(csv.index(field)) for field in date_fields]
            return res

        def _prepare_date(csv_r, date_fields):
            return [int(csv_r[field]) for field in date_fields]

        def _pop_geometry_fields(csv):
            unused_fields = ['longitude', 'latitude']
            [csv.pop(csv.index(field)) for field in unused_fields]

        def _retrieve_db_data(soup_db):

            # doing some "trickery" with *properties and primary_key, to adapt the
            # code for sqlalchemy 0.7

            # surface join
            surf_join = soup_db.join(soup_db.catalog, soup_db.surface,
                properties={'id_surface': [soup_db.surface.c.id]},
                            exclude_properties=[soup_db.surface.c.id,
                                soup_db.surface.c.last_update],
                primary_key=[soup_db.surface.c.id])

            # magnitude join
            mag_join = soup_db.join(surf_join, soup_db.magnitude,
                properties={'id_magnitude': [soup_db.magnitude.c.id],
                        'id_surface': [soup_db.surface.c.id]},
                            exclude_properties=[soup_db.magnitude.c.id,
                                soup_db.magnitude.c.last_update,
                                soup_db.surface.c.last_update],
                primary_key=[soup_db.magnitude.c.id, soup_db.surface.c.id])

            return mag_join.order_by(soup_db.catalog.eventid).all()

        def _verify_db_data(csv_loader, db_rows):
            # skip the header
            csv_loader.csv_reader.next()
            csv_els = list(csv_loader.csv_reader)
            for csv_row, db_row in zip(csv_els, db_rows):
                csv_keys = csv_row.keys()
                # pops 'longitude', 'latitude' which are used to populate
                # geometry_columns
                _pop_geometry_fields(csv_keys)

                timestamp = _prepare_date(csv_row, _pop_date_fields(csv_keys))
                csv_time = csv_loader._date_to_timestamp(*timestamp)
                # first we compare the timestamps
                self.assertEqual(str(db_row.time), csv_time)

                # then, we cycle through the csv keys and consider some special
                # cases
                for csv_key in csv_keys:
                    db_val = getattr(db_row, csv_key)
                    csv_val = csv_row[csv_key]
                    if not len(csv_val.strip()):
                        csv_val = '-999.0'
                    if csv_key == 'agency':
                        self.assertEqual(str(db_val), str(csv_val))
                    else:
                        self.assertEqual(float(db_val), float(csv_val))


        def _delete_db_data(soup_db,db_rows):
            # cleaning the db
            for db_row in db_rows:
                soup_db.delete(db_row)


        user = 'kpanic'
        password = 'openquake'
        dbname = 'openquake'

        engine = db.create_engine(dbname=dbname, user=user, password=password)

        csv_loader = db_loader.CsvModelLoader(self.csv_path, engine, 'eqcat')
        csv_loader.serialize()
        db_rows = _retrieve_db_data(csv_loader.soup)

        # rewind the file
        csv_loader.csv_fd.seek(0)

        _verify_db_data(csv_loader, db_rows)

        _delete_db_data(csv_loader.soup, db_rows)

        csv_loader.soup.commit()
