package org.gem.calc;

import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam.Vs30Type;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class DisaggregationTestHelper
{
	public static final Double[] LAT_BIN_LIMS = {-0.6, -0.3, -0.1, 0.1, 0.3, 0.6};
	public static final Double[] LON_BIN_LIMS = {-0.6, -0.3, -0.1, 0.1, 0.3, 0.6};
	public static final Double[] MAG_BIN_LIMS = {5.0, 6.0, 7.0, 8.0, 9.0};
	public static final Double[] EPS_BIN_LIMS = {-0.5, 0.5, 1.5, 2.5, 3.5};
	public static final double POE = 0.1;
	public static final List<Double> IMLS = 
			Arrays.asList(mapLog(new Double[] {
				0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269,
				0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203,
				0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13}));

	/**
	 * This test data was generated from the calculator prototype test code
	 * provided by Damiano Monelli. This matrix was calculated used the
	 * 'disaggregate' method:
	 * https://github.com/monellid/shaCalcs/blob/master/src/DisaggregationCalculator.java#L120
	 */
	public static final double[][][][][] EXPECTED =
	    {{{{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00040815392254454544, 0.0, 0.0, 0.0, 0.0},
	        {0.00017880421738656526, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00033031500645934085, 0.0, 0.0, 0.0, 0.0},
	        {0.00096880962006368, 0.0, 0.0, 0.0, 0.0},
	        {3.265619304956138e-06, 0.0, 0.0, 0.0, 0.0}},
	       {{5.291337312806191e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0005238770872021465, 0.0, 0.0, 0.0, 0.0},
	        {4.922398807298491e-06, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {2.187389902655355e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {5.9387779675445556e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0021807584091983055, 0.0, 0.0, 0.0, 0.0},
	        {0.00031412557609741836, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.001954803895439453, 0.0, 0.0, 0.0, 0.0},
	        {0.0010117062833150164, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0003583406478519622, 0.0, 0.0, 0.0, 0.0},
	        {0.0005697925501339871, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00012564514357626475, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0005182526144905888, 0.0, 0.0, 0.0, 0.0},
	        {0.0035702792576884925, 0.0, 0.0, 0.0, 0.0},
	        {0.00032454636213785, 0.0, 0.0, 0.0, 0.0}},
	       {{1.029708340282012e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0033485942648865644, 0.0, 0.0, 0.0, 0.0},
	        {0.0007068977944321303, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0006482797703651592, 0.0, 0.0, 0.0, 0.0},
	        {0.00045593837513725397, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {2.6255391209254876e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {7.418437132845631e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0022954934351258663, 0.0, 0.0, 0.0, 0.0},
	        {0.0003179159432500624, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0020629436110407686, 0.0, 0.0, 0.0, 0.0},
	        {0.0009911330835145212, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00037949555026399397, 0.0, 0.0, 0.0, 0.0},
	        {0.0005637710993471957, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.000458824202582562, 0.0, 0.0, 0.0, 0.0},
	        {0.00018559436683360014, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00037378188719363036, 0.0, 0.0, 0.0, 0.0},
	        {0.0009945377198221639, 0.0, 0.0, 0.0, 0.0},
	        {2.3825866794348594e-06, 0.0, 0.0, 0.0, 0.0}},
	       {{6.109370641909876e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.000534275636889609, 0.0, 0.0, 0.0, 0.0},
	        {3.711064967201982e-06, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}}},
	     {{{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {2.1874178902719398e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {5.938853613725545e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0021807922526638486, 0.0, 0.0, 0.0, 0.0},
	        {0.0003141310352733732, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.001954833952925426, 0.0, 0.0, 0.0, 0.0},
	        {0.0010117261859569117, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.000358346142013285, 0.0, 0.0, 0.0, 0.0},
	        {0.0005698033832478792, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.002090343020616003, 0.0, 0.0, 0.0, 0.0},
	        {0.0009000562828100821, 0.0, 0.0, 0.0, 0.0}},
	       {{9.42961504567726e-06, 0.0, 0.0, 0.0, 0.0},
	        {0.007835123571289236, 0.0, 0.0, 0.0, 0.0},
	        {0.007267358659002731, 0.0, 0.0, 0.0, 0.0},
	        {0.00011665674423923497, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0016777374627738805, 0.0, 0.0, 0.0, 0.0},
	        {0.006494525711050783, 0.0, 0.0, 0.0, 0.0},
	        {5.141714720764459e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00147756589199622, 0.0, 0.0, 0.0, 0.0},
	        {9.097383739965634e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0018315691143659476, 0.0, 0.0, 0.0, 0.0},
	        {0.013513810696388637, 0.0, 0.0, 0.0, 0.0},
	        {0.0020186034504789327, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0028415316660589636, 0.0, 0.0, 0.0, 0.0},
	        {0.02656676360980698, 0.0, 0.0, 0.0, 0.0},
	        {0.006483824265441999, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.008139359171404825, 0.0, 0.0, 0.0, 0.0},
	        {0.005098267483983408, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0016961308894844977, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.002531209111842975, 0.0, 0.0, 0.0, 0.0},
	        {0.0009768188778634561, 0.0, 0.0, 0.0, 0.0}},
	       {{4.0368172110441036e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.008859412190156436, 0.0, 0.0, 0.0, 0.0},
	        {0.007377455266556638, 0.0, 0.0, 0.0, 0.0},
	        {0.00010022582303693011, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00198409249487627, 0.0, 0.0, 0.0, 0.0},
	        {0.006545057881903281, 0.0, 0.0, 0.0, 0.0},
	        {3.674220140852504e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.001518785159960585, 0.0, 0.0, 0.0, 0.0},
	        {7.477702019371823e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {3.254711618375456e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00010269572978084829, 0.0, 0.0, 0.0, 0.0},
	        {0.0024076718598163194, 0.0, 0.0, 0.0, 0.0},
	        {0.00032084382909878585, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0021750698775767486, 0.0, 0.0, 0.0, 0.0},
	        {0.0009704251828457982, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00040201170086015336, 0.0, 0.0, 0.0, 0.0},
	        {0.0005567538088024654, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}}},
	     {{{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00012564716953877175, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0005182607196309074, 0.0, 0.0, 0.0, 0.0},
	        {0.003570354825954423, 0.0, 0.0, 0.0, 0.0},
	        {0.0003245544789271061, 0.0, 0.0, 0.0, 0.0}},
	       {{1.0297231943968514e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.003348664083921756, 0.0, 0.0, 0.0, 0.0},
	        {0.0007069191216810913, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0006482930786338765, 0.0, 0.0, 0.0, 0.0},
	        {0.0004559510983623029, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0018315725932598332, 0.0, 0.0, 0.0, 0.0},
	        {0.013513852709675233, 0.0, 0.0, 0.0, 0.0},
	        {0.0020186131436966343, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0028415372146817506, 0.0, 0.0, 0.0, 0.0},
	        {0.026566870032493778, 0.0, 0.0, 0.0, 0.0},
	        {0.006483874083869901, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00813938750456354, 0.0, 0.0, 0.0, 0.0},
	        {0.005098309473562483, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0016961418867191872, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.09358598688420183, 0.0, 0.0, 0.0, 0.0},
	        {0.18108319570886422, 0.0, 0.0, 0.0, 0.0},
	        {0.059180850234161454, 0.0, 0.0, 0.0, 0.0},
	        {0.0004409836814193567, 0.0, 0.0, 0.0, 0.0}},
	       {{0.09459355241507171, 0.0, 0.0, 0.0, 0.0},
	        {0.03729237352369634, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.016981427419011763, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00013137443294502807, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.003287666677625586, 0.0, 0.0, 0.0, 0.0},
	        {0.016280290077728028, 0.0, 0.0, 0.0, 0.0},
	        {0.0020608872467112326, 0.0, 0.0, 0.0, 0.0}},
	       {{0.004275708980847192, 0.0, 0.0, 0.0, 0.0},
	        {0.029406776306808095, 0.0, 0.0, 0.0, 0.0},
	        {0.006111337602809897, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00923025615827644, 0.0, 0.0, 0.0, 0.0},
	        {0.004747555413215914, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0016513574642396359, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00017427901199771503, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0007169612182853976, 0.0, 0.0, 0.0, 0.0},
	        {0.0038966456234966144, 0.0, 0.0, 0.0, 0.0},
	        {0.0003122199206163304, 0.0, 0.0, 0.0, 0.0}},
	       {{2.6588895285990424e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0036609459576346097, 0.0, 0.0, 0.0, 0.0},
	        {0.0006439720104599637, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0007179781964787176, 0.0, 0.0, 0.0, 0.0},
	        {0.0004247738158398073, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}}},
	     {{{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {2.625573633192014e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {7.418533719032646e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0022955302321894192, 0.0, 0.0, 0.0, 0.0},
	        {0.00031792166395182986, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.002062976357606469, 0.0, 0.0, 0.0, 0.0},
	        {0.0009911534232305444, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00037950155800016867, 0.0, 0.0, 0.0, 0.0},
	        {0.0005637822248435008, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.002531209989175088, 0.0, 0.0, 0.0, 0.0},
	        {0.0009768193083168728, 0.0, 0.0, 0.0, 0.0}},
	       {{4.0368185293897505e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.008859415726579162, 0.0, 0.0, 0.0, 0.0},
	        {0.0073774593975702634, 0.0, 0.0, 0.0, 0.0},
	        {0.00010022591928890819, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0019840931854309416, 0.0, 0.0, 0.0, 0.0},
	        {0.006545061689840745, 0.0, 0.0, 0.0, 0.0},
	        {3.6742232536562544e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.001518786000872623, 0.0, 0.0, 0.0, 0.0},
	        {7.477709309084273e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0032876614046432797, 0.0, 0.0, 0.0, 0.0},
	        {0.016280245000700258, 0.0, 0.0, 0.0, 0.0},
	        {0.0020608781395715886, 0.0, 0.0, 0.0, 0.0}},
	       {{0.004275701757327914, 0.0, 0.0, 0.0, 0.0},
	        {0.02940666936696255, 0.0, 0.0, 0.0, 0.0},
	        {0.006111292710644619, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.009230226883176514, 0.0, 0.0, 0.0, 0.0},
	        {0.004747518057544061, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0016513474606975242, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {1.8640855564296568e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.003051419181825595, 0.0, 0.0, 0.0, 0.0},
	        {0.001061296405864084, 0.0, 0.0, 0.0, 0.0}},
	       {{9.40727212185929e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.010006144159064695, 0.0, 0.0, 0.0, 0.0},
	        {0.007461723372912314, 0.0, 0.0, 0.0, 0.0},
	        {8.454550733423895e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.002336421491727081, 0.0, 0.0, 0.0, 0.0},
	        {0.006568319106605788, 0.0, 0.0, 0.0, 0.0},
	        {2.5198636947936297e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0015575433979990048, 0.0, 0.0, 0.0, 0.0},
	        {6.00315529257324e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {3.874184625075927e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00012657408279354956, 0.0, 0.0, 0.0, 0.0},
	        {0.0025303715942357405, 0.0, 0.0, 0.0, 0.0},
	        {0.0003236909015202809, 0.0, 0.0, 0.0, 0.0}},
	       {{7.790708794720282e-07, 0.0, 0.0, 0.0, 0.0},
	        {0.0022926685682553086, 0.0, 0.0, 0.0, 0.0},
	        {0.000946134772698293, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00042540100961694987, 0.0, 0.0, 0.0, 0.0},
	        {0.0005491421984265693, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}}},
	     {{{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0004588246639918235, 0.0, 0.0, 0.0, 0.0},
	        {0.00018559458010879704, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0003737822577785884, 0.0, 0.0, 0.0, 0.0},
	        {0.0009945388782730835, 0.0, 0.0, 0.0, 0.0},
	        {2.382590136579139e-06, 0.0, 0.0, 0.0, 0.0}},
	       {{6.109376207678092e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.000534276270371487, 0.0, 0.0, 0.0, 0.0},
	        {3.7110703264392883e-06, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {3.254672887749346e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00010269451757063013, 0.0, 0.0, 0.0, 0.0},
	        {0.002407636921031583, 0.0, 0.0, 0.0, 0.0},
	        {0.00032083858125414767, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0021750386176475392, 0.0, 0.0, 0.0, 0.0},
	        {0.0009704070092634078, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00040200593914684193, 0.0, 0.0, 0.0, 0.0},
	        {0.0005567438186773134, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00017427634142338943, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0007169504871316648, 0.0, 0.0, 0.0, 0.0},
	        {0.0038965668682009002, 0.0, 0.0, 0.0, 0.0},
	        {0.0003122122662743975, 0.0, 0.0, 0.0, 0.0}},
	       {{2.6588531587559928e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0036608729502696355, 0.0, 0.0, 0.0, 0.0},
	        {0.0006439530485916086, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0007179641419158395, 0.0, 0.0, 0.0, 0.0},
	        {0.0004247622640253117, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {3.8741371605401256e-05, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00012657255052767093, 0.0, 0.0, 0.0, 0.0},
	        {0.0025303335630410145, 0.0, 0.0, 0.0, 0.0},
	        {0.0003236854051632171, 0.0, 0.0, 0.0, 0.0}},
	       {{7.790613868068855e-07, 0.0, 0.0, 0.0, 0.0},
	        {0.0022926344762950294, 0.0, 0.0, 0.0, 0.0},
	        {0.0009461162127624123, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.00042539470186060436, 0.0, 0.0, 0.0, 0.0},
	        {0.0005491319377856705, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}},
	      {{{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.0005153892591158344, 0.0, 0.0, 0.0, 0.0},
	        {0.0001922685581211021, 0.0, 0.0, 0.0, 0.0}},
	       {{0.0, 0.0, 0.0, 0.0, 0.0},
	        {0.00042190908685735935, 0.0, 0.0, 0.0, 0.0},
	        {0.0010194887827308895, 0.0, 0.0, 0.0, 0.0},
	        {1.6451573907084081e-06, 0.0, 0.0, 0.0, 0.0}},
	       {{7.040470193616392e-05, 0.0, 0.0, 0.0, 0.0},
	        {0.0005439549508554621, 0.0, 0.0, 0.0, 0.0},
	        {2.6934394268945045e-06, 0.0, 0.0, 0.0, 0.0},
	        {0.0, 0.0, 0.0, 0.0, 0.0}}}}};

	/**
	 * Map the Math.log() method to each element in the input list
	 * to create a new list.
	 */
	private static Double[] mapLog(Double[] list)
	{
		Double[] result = new Double[list.length];
		for (int i = 0; i < list.length; i++)
		{
			result[i] = Math.log(list[i]);
		}
		return result;
	}
	
	public static Site makeTestSite()
	{
		Site site = new Site(new Location(0.0, 0.0));
		site.addParameter(new StringParameter(Vs30_TypeParam.NAME, Vs30Type.Measured.toString()));
		site.addParameter(new DoubleParameter(Vs30_Param.NAME, 760.0));
		site.addParameter(new DoubleParameter(DepthTo1pt0kmPerSecParam.NAME, 100.0));
		site.addParameter(new DoubleParameter(DepthTo2pt5kmPerSecParam.NAME, 1.0));
		return site;
	}

	public static Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> makeTestImrMap()
	{
		Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap = new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		imrMap.put(TectonicRegionType.ACTIVE_SHALLOW, getTestIMRActiveShallow());
		return imrMap;
	}

	public static Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> makeTestImrMapZeroStdDev()
	{
		Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap = new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		ScalarIntensityMeasureRelationshipAPI imr = new BA_2008_AttenRel(null);
		imr.getParameter(StdDevTypeParam.NAME).setValue(
				StdDevTypeParam.STD_DEV_TYPE_NONE);
		imrMap.put(TectonicRegionType.ACTIVE_SHALLOW, imr);
		return imrMap;
	}

	private static ScalarIntensityMeasureRelationshipAPI getTestIMRActiveShallow()
	{
		ScalarIntensityMeasureRelationshipAPI imr = new BA_2008_AttenRel(null);
		setDefaultImrParams(imr);
		return imr;
	}

	private static ScalarIntensityMeasureRelationshipAPI getTestIMRStableContinental()
	{
		ScalarIntensityMeasureRelationshipAPI imr = new CB_2008_AttenRel(null);
		setDefaultImrParams(imr);
		return imr;
	}

	private static void setDefaultImrParams(ScalarIntensityMeasureRelationshipAPI imr)
	{
		imr.setIntensityMeasure(PGA_Param.NAME);
		imr.getParameter(StdDevTypeParam.NAME).setValue(
				StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(
				SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED);
		imr.getParameter(SigmaTruncLevelParam.NAME).setValue(3.0);
		imr.getParameter(ComponentParam.NAME).setValue(
				ComponentParam.COMPONENT_GMRotI50);
	}

	public static GEM1ERF makeTestERF()
	{
		ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
		srcList.add(makeTestSourceDataActiveShallow());

		double timeSpan = 50.0;
		GEM1ERF erf = GEM1ERF.getGEM1ERF(srcList, timeSpan);
		erf.getParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME).setValue(0.01);
		erf.updateForecast();
		return erf;
	}

	private static GEMSourceData makeTestSourceDataActiveShallow()
	{
		String id = "src1";
		String name = "testSource";
		TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;

		LocationList border = new LocationList();
		border.add(new Location(-0.5, -0.5));
		border.add(new Location(0.5, -0.5));
		border.add(new Location(0.5, 0.5));
		border.add(new Location(-0.5, 0.5));
		Region reg = new Region(border, BorderType.MERCATOR_LINEAR);

		double bValue = 1.0;
		double totCumRate = 0.2;
		double min = 5.05;
		double max = 8.95;
		int num = 41;
		GutenbergRichterMagFreqDist magDist = new GutenbergRichterMagFreqDist(
				bValue, totCumRate, min, max, num);

		double strike = 0.0;
		double dip = 90.0;
		double rake = 0.0;
		FocalMechanism focalMechanism = new FocalMechanism(strike, dip, rake);

		MagFreqDistsForFocalMechs magfreqDistFocMech = new MagFreqDistsForFocalMechs(
				magDist, focalMechanism);

		ArbitrarilyDiscretizedFunc aveRupTopVsMag = new ArbitrarilyDiscretizedFunc();
		double magThreshold = 6.5;
		double topOfRuptureDepth = 0.0;
		aveRupTopVsMag.set(magThreshold, topOfRuptureDepth);
		double aveHypoDepth = 5.0;

		GEMSourceData srcData = new GEMAreaSourceData(id, name, tectReg, reg,
				magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
		return srcData;
	}

	private static GEMSourceData makeTestSourceDataStableCrust()
	{
		String id = "src1";
		String name = "testSource";
		TectonicRegionType tectReg = TectonicRegionType.STABLE_SHALLOW;

		LocationList border = new LocationList();
		border.add(new Location(-0.5, 0.5));
		border.add(new Location(0.5, 0.5));
		border.add(new Location(0.5, 1.5));
		border.add(new Location(-0.5, 1.5));
		Region reg = new Region(border, BorderType.GREAT_CIRCLE);

		double bValue = 1.0;
		double totCumRate = 0.2;
		double min = 5.05;
		double max = 8.95;
		int num = 41;
		GutenbergRichterMagFreqDist magDist = new GutenbergRichterMagFreqDist(
				bValue, totCumRate, min, max, num);

		double strike = 0.0;
		double dip = 90.0;
		double rake = 0.0;
		FocalMechanism focalMechanism = new FocalMechanism(strike, dip, rake);

		MagFreqDistsForFocalMechs magfreqDistFocMech = new MagFreqDistsForFocalMechs(
				magDist, focalMechanism);

		ArbitrarilyDiscretizedFunc aveRupTopVsMag = new ArbitrarilyDiscretizedFunc();
		double magThreshold = 6.5;
		double topOfRuptureDepth = 0.0;
		aveRupTopVsMag.set(magThreshold, topOfRuptureDepth);
		double aveHypoDepth = 5.0;

		GEMSourceData srcData = new GEMAreaSourceData(id, name, tectReg, reg,
				magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
		return srcData;
	}

	public static DiscretizedFuncAPI makeHazardCurve()
	{
		DiscretizedFuncAPI hazardCurve = new ArbitrarilyDiscretizedFunc();
		// initialize the curve our defined list of IMLs,
		// set the corresponding PoEs to 0.0
		for (double d : IMLS)
		{
			hazardCurve.set(d, 0.0);
		}
		try {
			HazardCurveCalculator hcc = new HazardCurveCalculator();
			hcc.getHazardCurve(hazardCurve, makeTestSite(), makeTestImrMap(), makeTestERF());
		} catch (RemoteException e) {
			throw new RuntimeException(e);
		}
		return hazardCurve;
	}

}
