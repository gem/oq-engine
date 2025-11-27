# -*- coding: utf-8 -*-
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class JiEtAl2025Azores(GMPE):
    """
    Implements the Ground Motion Model for the Azores Plateau (Portugal)
    developed by Ji et al. (2025) based on Simulated Scenario Earthquake Records.
    The model is formulated for shallow seismic events ranging 
    from magnitude Mw 5.0 to 6.8, Focal Depth 5–17 km, and RJB up to 150 km on bedrock sites. 

    Reference:
    Ji Kun, Shaghayegh Karimzadeh, Saman Yaghmaei Sabegh, Ruibin Hou,
    Carvalho Alexandra, & Lourenço Paulo B.. (2025).
    Ground motion model using simulated scenario earthquake records in Azores
    Plateau (Portugal) at bedrock.
    Soil Dynamics & Earthquake Engineering, 197, 109521.
    https://doi.org/10.1016/j.soildyn.2025.109521
    """

    # Tectonic region type: assumed active shallow crust; 
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    # Supported intensity measures: PGA, PGV, SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    # Component type: geometric mean (typical for simulated data if not explicitly stated)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    # Supported standard deviation types: total, inter-event, intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    # No Vs30 required (bedrock model)
    REQUIRES_SITES_PARAMETERS = set()

    # Required rupture parameters: magnitude, hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "hypo_depth"}

    # Required distance metric: Rjb
    REQUIRES_DISTANCES = {"rjb"}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Inputs:
            ctx: context object containing mag, rjb, hypo_depth, etc.
        """
        # Magnitude hinge points
        Mh1 = 5.5
        Mh2 = 6.5

        # Pseudo-depth constant used in distance term
        h_const = 3.0

        for m, imt in enumerate(imts):
            # Load coefficients linked to current IMT
            C = self.COEFFS[imt]

            # --- 1. Magnitude Scaling (fmag) ---

            # if M < 5.5:  c2*M + c1
            # if 5.5 <= M < 6.5: c3*(M-5.5) + c2*M + c1
            # if M >= 6.5: c4*(M-6.5) + c3*(M-5.5) + c2*M + c1

            # Base term (common for all magnitudes)
            f_mag = C["c2"] * ctx.mag + C["c1"]

            # First hinge (M >= 5.5)
            f_mag += np.where(ctx.mag >= Mh1, C["c3"] * (ctx.mag - Mh1), 0.0)

            # Second hinge (M >= 6.5)
            f_mag += np.where(ctx.mag >= Mh2, C["c4"] * (ctx.mag - Mh2), 0.0)

            # --- 2. Distance Scaling (fdis) ---

            # fdis = (c5 + c6*(M-4.5)) * log(sqrt(R^2 + 3^2)) + c7 * sqrt(R^2 + Fdepth^2)

            # Geometric spreading coefficient
            slope_geo = C["c5"] + C["c6"] * (ctx.mag - 4.5)

            # Geometric spreading distance (3 km pseudo-depth is fixed)
            r_geo = np.sqrt(ctx.rjb ** 2 + h_const ** 2)
            term_geo = slope_geo * np.log(r_geo)

            # Anelastic attenuation term using approximate slant distance
            r_hypo_approx = np.sqrt(ctx.rjb ** 2 + ctx.hypo_depth ** 2)
            term_anel = C["c7"] * r_hypo_approx

            f_dis = term_geo + term_anel

            # --- 3. Mean prediction (ln Y) ---
            mean[m] = f_mag + f_dis

            # --- 4. Standard deviations ---
            tau[m] = C["tau"]
            phi[m] = C["phi"]
            sig[m] = np.sqrt(tau[m] ** 2 + phi[m] ** 2)

    # Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT    c1                 c2                 c3                 c4                 c5                 c6                 c7                 tau                phi
pga   -4.96708915535545   0.672223287840007 -0.276989292236236  0.0583578621101360 -1.07179692732781  0.172437369807980 -0.0102983602817697 0.236980120274175  0.202708693071518
0.02  -4.91691136987474   0.665702406219193 -0.273901584620427  0.0605481616658419 -1.07384627961283  0.172794337932387 -0.0103167792062967 0.236666343148387  0.204048780957233
0.03  -4.84247071527072   0.656045052943396 -0.269387503570062  0.0637514784760505 -1.07714391865245  0.173385064807256 -0.0103416786253443 0.236203175453200  0.206085682198788
0.05  -4.45275315986674   0.606083224567131 -0.246370388614185  0.0809638304065941 -1.09416637329090  0.176511239134107 -0.0105100858868651 0.233685750300577  0.222456958903459
0.07  -3.90989892704072   0.538881967914159 -0.204327632286716  0.0995181413974921 -1.10101241863761  0.175736108930232 -0.0111333976121632 0.231187002176798  0.247539792076154
0.10  -3.49914531858119   0.498695613156141 -0.164041779914646  0.124546505405421  -1.06629887025290  0.162838097061777 -0.0123511061344311 0.233553349532433  0.269695319566990
0.15  -3.67348114648977   0.549187116624378 -0.156086462359079  0.134667468127294  -0.980415861824312 0.135457334203018 -0.0134260701538668 0.246913754195626  0.265836997352510
0.20  -4.10864446144088   0.628873650363124 -0.192966570576910  0.105548087379453  -0.934983215744768 0.121653783506467 -0.0132111798738809 0.258114275682896  0.246928738497212
0.25  -4.64482340318867   0.717842975729968 -0.239245767027184  0.0651073654174402 -0.906829593473443 0.113080158525795 -0.0126667763853252 0.266968621663372  0.228940816005745
0.30  -5.28257457320302   0.819143571002498 -0.300910403188959  0.0587456536959487 -0.880402182552481 0.107009276627017 -0.0122763510040605 0.274687684359960  0.213929103917908
0.35  -6.02152052624861   0.937338845778299 -0.376004509278418  0.0317596092298837 -0.857363974587456 0.100782016812873 -0.0118689104958076 0.284254976498577  0.201202250962606
0.40  -6.66549023454421   1.03952030692445  -0.442330566774180  0.0146673627378387 -0.850006054688467 0.0978647125161091 -0.0113097521558465 0.291433660541297 0.191067066722068
0.45  -7.28218091506534   1.13740137002579  -0.508944125647674 -0.0238083594104635 -0.850969239627741 0.0979542540656805 -0.0107360514461984 0.297197771526406 0.182862123380182
0.50  -7.93428573560860   1.24010022319132  -0.575018903630375 -0.0502044021087550 -0.846507362263441 0.0959969379819393 -0.0102499795018604 0.302612100290133 0.176204970669932
0.60  -9.23413155490809   1.44135986348444  -0.694648821509520 -0.132349841730783  -0.825671684823805 0.0917769077069652 -0.00972057708163194 0.314617837085380 0.164567266286304
0.70  -10.4125065894592   1.62241030605266  -0.792591989468677 -0.203513090173950  -0.810179344624905 0.0873459944989140 -0.00920818873012090 0.324868795928303 0.155706803625198
0.80  -11.4453648185030   1.77889114331285  -0.876639342886565 -0.279205434676468  -0.803740322759807 0.0878443206257868 -0.00880985954996364 0.331605869197641 0.148982477692131
1.0   -13.2362994875980   2.04373068911682  -0.986491725618872 -0.420380600575133  -0.789381409273985 0.0844125861503426 -0.00793418504865400 0.345743966865382 0.136307103672930
1.2   -14.6136068664800   2.23747462034880  -1.03237584676630  -0.562563541931038  -0.776611962218868 0.0812229193351992 -0.00726086985087434 0.355989586022079 0.124440075160368
1.5   -16.0795885581007   2.42842315723775  -1.04366211115078  -0.725170260681383  -0.772335684911641 0.0836960716206892 -0.00630440163561198 0.368150858891495 0.111468233004069
2.0   -17.5070035971010   2.57756165408822  -0.956026569513148 -0.873242813885683  -0.777730534887090 0.0918622817211007 -0.00469142115446361 0.384725951835023 0.103789691706469
2.5   -18.4113176221174   2.64997760869579  -0.862446196989016 -0.881527588732902  -0.788854448235472 0.0995646573169405 -0.00333285447705191 0.395228339156854 0.101102383653251
3.0   -18.7690990609193   2.63671859844353  -0.737764218719865 -0.819530406582306  -0.802873793348393 0.109303960206381  -0.00248789839985708 0.399257643516076 0.101271043694488
4.0   -18.8048676186723   2.52038298090437  -0.516102686272828 -0.601695335234970  -0.842687684867223 0.130973662786576  -0.00122650853926933 0.400096989113447 0.104030327193461
pgv   -3.32010242991311   1.12745819943232  -0.373893613834902 -0.112943647344538  -1.07977779174574  0.233118785856743  -0.00657639934690607 0.275714874417806  0.123356264698372
""")
