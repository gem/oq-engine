# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports :class:`RamadanEtAl2023shallow`,
               :class:`RamadanEtAl2023deep`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _compute_distance(rval2, mval, C, kind):
    """
    Compute the distance function
    """
    if kind == 'shallow':  # equation (2) focal depth h ≤ 5km
        h1 = 1
        mref = 4.8
        rval = np.sqrt(rval2 ** 2 + h1 ** 2)
        return C['c1'] * np.log10(rval) + C['c2'] * (mval - mref) * np.log10(rval)
    elif kind == 'deep':  # equation (2) focal depth h > 5km
        h2 = 5
        mref = 4.8
        rval = np.sqrt(rval2 ** 2 + h2 ** 2)
        return C['c3'] * np.log10(rval) + C['c4'] * (mval - mref) * np.log10(rval) + C['c5'] * rval
    raise ValueError(kind)


def _compute_magnitude(ctx, C):
    """
    Compute the magnitude function, equation (9):
    """
    return C['a'] + C['b'] * ctx.mag


def _get_site_amplification(ctx, C):
    """
    Compute the site amplification function given by FS = eiSi, for
    i = 1,2,3 where Si are the coefficients determined through regression
    analysis, and ei are dummy variables (0 or 1) used to denote the
    different EC8 site classes.
    """
    ssb, ssc = _get_site_type_dummy_variables(ctx)

    return (C['sB'] * ssb) + (C['sC'] * ssc)


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, which classified the ctx into
    different site classes based on the shear wave velocity in the
    upper 30 m (Vs30) according to the EC8 (CEN 2003):
    class A: Vs30 > 800 m/s
    class B: Vs30 = 360 - 800 m/s
    class C: Vs30 = 180 - 360 m/s
    class D: Vs30 < 180 m/s
    """
    ssb = np.zeros(len(ctx.vs30))
    ssc = np.zeros(len(ctx.vs30))
    # Class C; Vs30 < 360 m/s.
    idx = (ctx.vs30 < 360.0)
    ssc[idx] = 1.0
    # Class B; 360 m/s <= Vs30 <= 800 m/s.
    idx = (ctx.vs30 >= 360.0) & (ctx.vs30 < 800.0)
    ssb[idx] = 1.0

    return ssb, ssc


class RamadanEtAl2023shallow(GMPE):
    """
    Implements GMPE developed by Fadel Ramadan, Giovanni Lanzano,
    Sara Sgobba(2023) and submitted as "Vertical seismic ground shaking
    in the volcanic areas of Italy: prediction equations and PSHA
    examples" Soil Dynamics and Earthquake Engineering.

    GMPE derives from earthquakes in the volcanic areas in Italy in the
    magnitude range 3<ML<5 for hypocentral distances <200 km, and for
    rock (EC8-A), stiff soil (EC8-B) and soft soil (EC8-C and EC8-D).

    The GMPE distinguishes between shallow volcano-tectonic events
    related to flank movements (focal depths <5km) and deeper events
    occurring due to regional tectonics (focal depths >5km), considering
    two different attenuations with distances.

    Test tables are generated from a spreadsheet provided by the authors,
    and modified according to OQ format (e.g. conversion from cm/s2 to fractions of g).
    """
    kind = 'shallow'

    #: Supported tectonic region type is 'volcanic'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rhypo.
    REQUIRES_DISTANCES = {'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(ctx.rhypo, ctx.mag, C, self.kind) +
                     _get_site_amplification(ctx, C))

            sigma = np.sqrt(C['tau'] ** 2 + C['phiS2S'] ** 2 + C['phi0'] ** 2)
            phi1 = np.sqrt(C['phiS2S'] ** 2 + C['phi0'] ** 2)
            istddevs = [sigma, C['tau'], phi1]

            # Convert units to g, but only for PGA and SA (not PGV)
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:  # PGV:
                mean[m] = np.log(10.0 ** imean)
            # Return stddevs in terms of natural log scaling
            sig[m], tau[m], phi[m] = np.log(10.0 ** np.array(istddevs))

    # Sigma values in log10
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a                   b                   c1                  c2                  c3                  c4                      c5                      sB                  sC                  tau                 phiS2S              phi0
    pga     1.55618537121447    0.333127019670588   -1.80215414835785   0.489760712316293   -1.42712891076597   0.239145223726140       -0.00602954775925354    0.0849029979895893  0.282416332926826   0.158531365456166   0.257849237110302   0.218785421619145
    pgv     -0.823562722532021  0.564120018641826   -1.58123328827974   0.441957343546818   -1.46869782526347   0.183819014687225       -0.00403706069494924    0.0945375867733048  0.322649894866542   0.111794474452390   0.211984139742539   0.206490964065672
    0.025   1.49253698552105    0.352967194440596   -1.81888669781098   0.471134151636350   -1.43537358277680   0.224666216398449       -0.00613337549791585    0.0834547514388841  0.282665251490508   0.159163212679202   0.259722649999760   0.220391148299680
    0.04    1.52340332752832    0.361871888850407   -1.85382633747974   0.458191682579385   -1.45413965073425   0.209652046551918       -0.00639937786401334    0.0830638006960337  0.276150212985115   0.161792084380257   0.267659802456287   0.222448414991693
    0.05    1.75744248291679    0.322679690570580   -1.87252022766518   0.472080216109852   -1.44452049977985   0.232457295206867       -0.00673689508235783    0.0831537428823732  0.276562816318349   0.166082115086053   0.279566071614903   0.226233335467767
    0.07    2.08046466870254    0.282436248671939   -1.91811861340609   0.502764064718793   -1.44089936515435   0.239745404503315       -0.00746552737970068    0.0740041541213114  0.254347538274426   0.174186527179915   0.303201685267428   0.236899062221400
    0.1     2.45681831357234    0.230907025091366   -1.95901494275549   0.512196416318455   -1.46205356217297   0.249510764460614       -0.00740236678773967    0.0576485824118061  0.238164224896399   0.188993160819513   0.319502820196321   0.228700008209447
    0.15    2.24865135177356    0.277280653590315   -1.92844844845104   0.491864429571195   -1.44263611764468   0.242359474440766       -0.00676221727244252    0.0680899175555899  0.286250284328353   0.196952391896027   0.314668416708834   0.212813532660202
    0.2     2.22043131874787    0.270484910271471   -1.87226996871060   0.489877541228117   -1.38337537850874   0.303340401633281       -0.00600393124906965    0.0685675737645497  0.272760687479625   0.196284277494126   0.297032901819520   0.209877257966932
    0.25    1.95581165398751    0.327129086323127   -1.83910375068622   0.472960933373851   -1.39302439699428   0.304137928691265       -0.00524611966536042    0.0478728458295583  0.265992590549930   0.179984468395150   0.275997895277545   0.207321060780223
    0.3     1.42431662712508    0.431944949795483   -1.80927005855343   0.425933895078030   -1.42183279228429   0.248170995060576       -0.00464975180040887    0.0720783022268137  0.295973680900923   0.175166048198337   0.265638238463579   0.203124052631301
    0.35    0.884771023520400   0.530664005427965   -1.78786659520169   0.362881923971613   -1.41858019810732   0.208508315158859       -0.00423277696319091    0.0807968112301128  0.336413817551598   0.169529448183916   0.253726515988399   0.202751455044725
    0.4     0.222439087794256   0.664427249126763   -1.75574727097258   0.327997697482776   -1.45357207447374   0.145053194031687       -0.00374929506269615    0.0791803129042107  0.323909607077676   0.170223652754985   0.251382148741827   0.202228804455864
    0.45    -0.106591185232871  0.733473681805610   -1.75097840195585   0.312238649588824   -1.48701019107858   0.117419261771302       -0.00372291011823571    0.0849372979970515  0.345958743479481   0.166147265851321   0.240736911729139   0.204033174865472
    0.5     -0.394421489452377  0.794913276519799   -1.75346355169159   0.297518262576494   -1.55096939165345   0.0788125816669681      -0.00326004672501193    0.100146371242976   0.362481285185161   0.162184272467937   0.239613994547163   0.202495177415152
    0.6     -0.922431523795676  0.893058198307089   -1.72149659618465   0.267752931739568   -1.60988405542445   0.0237484929141557      -0.00265390788202489    0.113352566674329   0.364715905170319   0.154396611910407   0.228178431597656   0.199131124937892
    0.7     -1.16808929914921   0.914427714772381   -1.65127901771088   0.277600912537678   -1.57529302690550   0.0440915742626641      -0.00245301007475515    0.105596974722736   0.378268883346709   0.136609106267637   0.225356247819452   0.196092678463843
    0.75    -1.20948521581307   0.909196614632457   -1.62964624738193   0.280153311968537   -1.54787551975125   0.0593757897377989      -0.00268726977455889    0.112908921209560   0.387017647857062   0.137447009288124   0.227027403579023   0.193986201635664
    0.8     -1.32318315558831   0.926904244937200   -1.63373900799406   0.269700719478004   -1.56858551221175   0.0464701245884586      -0.00247986952574131    0.114331899672671   0.396661181437359   0.135646006255393   0.224632479033389   0.193162293096130
    0.9     -1.73220917714665   0.998511774413288   -1.62360119788188   0.248482215548637   -1.61509622490725   -0.00647563651684085    -0.00198840726829246    0.118111820448627   0.396999622781568   0.138511952999162   0.224475216438308   0.186858785306930
    1       -1.80451544136929   0.982426394812571   -1.55679895121856   0.280083948255974   -1.58448845970044   0.0165662335740864      -0.00152007913762867    0.116496865872729   0.404821604363572   0.135700611920302   0.223354669239213   0.188225274144191
    1.2     -1.85081177797649   0.970031827480477   -1.52627648006118   0.314763490837677   -1.62683913588997   0.0301595084001054      -0.000973042918937311   0.116028668352795   0.385957378262433   0.143878161090144   0.225447510173698   0.183863209485497
    1.4     -2.38362660206301   1.05669923695560    -1.49333514610674   0.276966474763392   -1.65061564043184   -0.0329747839564720     -0.00109710019383801    0.112912558107300   0.372785390403438   0.164691435660162   0.219331048490733   0.183329733237713
    1.6     -2.56581357086797   1.07937570786662    -1.50661062095013   0.270270869291938   -1.68559912815205   -0.0358238518718565     -0.000907026176122039   0.124556863309157   0.337398138959883   0.172227226552177   0.221367656548737   0.180483033550181
    1.8     -2.36952674585974   1.00945767185484    -1.47990326180364   0.298055398377998   -1.65511755247358   0.0229035541171763      -0.000934846475767444   0.131261875702567   0.334852812306200   0.171252298361838   0.221092956104580   0.177306530466935
    2       -2.48427003595501   1.01926348928219    -1.48122119382967   0.288038119505369   -1.68523813686047   0.0200224453494581      -0.000599813430603246   0.141640892753419   0.352429899822908   0.172896494539844   0.218744066163145   0.180679264411675
    2.5     -2.89877349526432   1.06588601799483    -1.46453443207766   0.265221518594409   -1.69338397500374   -0.0123192801582618     -0.000763898919690631   0.136856874332350   0.334727303520607   0.184559572843780   0.211840025855318   0.183542648565007
    3       -3.08143026118988   1.05866733022687    -1.40459806340918   0.288115449943811   -1.67509341185465   -0.0269135749422416     -0.000765220896671696   0.124800435640156   0.347319875530159   0.211080495731782   0.216403996426047   0.180633880187356
    3.5     -2.56254071996106   0.903208091846693   -1.34679417451881   0.333130675949184   -1.64898490559263   0.0228896994254513      -0.000720456223244940   0.108687633727651   0.324463700238912   0.219784970042884   0.213480876769815   0.179554056937201
    4       -2.41308409477241   0.829857499033524   -1.29669956348625   0.343961866390586   -1.58691523488863   0.0761699406002622      -0.000976132354147058   0.105069651442751   0.305393680944419   0.215451753324127   0.214141751748811   0.180830008362151
    4.5     -2.32382052146498   0.788251349268690   -1.28127572136419   0.332517569816050   -1.58303513714938   0.0799342609560004      -0.000818314116145689   0.0888456188143767  0.319913231037914   0.205295970667863   0.201922366573869   0.180593068947733
    5       -2.08916683359711   0.706980205347767   -1.25383987171694   0.375546573314401   -1.55672239022568   0.119864070018554       -0.000851691016895212   0.0833328790711912  0.296661208256126   0.202877060713245   0.202136519727228   0.180076594155831
    """)


class RamadanEtAl2023deep(RamadanEtAl2023shallow):
    kind = 'deep'
