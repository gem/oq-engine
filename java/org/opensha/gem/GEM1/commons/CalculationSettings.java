package org.opensha.gem.GEM1.commons;

import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.gem.GEM1.scratch.AtkBoo_2006_AttenRel;
import org.opensha.gem.GEM1.scratch.ZhaoEtAl_2006_AttenRel;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.DistanceParams;
import org.opensha.gem.GEM1.util.IMLListParams;
import org.opensha.gem.GEM1.util.IntensityMeasureParams;
import org.opensha.gem.GEM1.util.SiteParams;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CY_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.McVerryetal_2000_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class CalculationSettings {
	
	// ERF 
	private HashMap<SourceType,HashMap<String,Object>> Erf;
	// GMPE
	private HashMap<String,HashMap<String,Object>> Gmpe;
	// Output
	private HashMap<String,Object> Out;
	
	// default parameters for area sources
	private static double area_grid_spacing = 0.1;
	private static String area_rupture_type = GEM1ERF.AREA_SRC_RUP_TYPE_POINT;
	private static double area_lower_seismogenic_depth = 14.0;
	private static MagAreaRelationship area_mag_area_rel = new WC1994_MagAreaRelationship();
	
	// default parameters for point sources
	private static String point_rupture_type = GEM1ERF.GRIDDED_SEIS_RUP_TYPE_POINT;
	private static double point_lower_seismogenic_depth = 14.0;
	private static MagAreaRelationship point_mag_area_rel = new WC1994_MagAreaRelationship();

	// default parameters for fault sources
	private static double fault_grid_spacing = 1.0;
	private static double fault_rupt_offset = 5.0;
	private static MagAreaRelationship fault_mag_area_rel = new WC1994_MagAreaRelationship();
	private static double fault_magAreaStd = 0.0;
	private static double fault_rupt_aspect_ratio = 1.0;
	private static String fault_rupt_floating_type = GEM1ERF.FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP;
	
	// default parameters for subduction fault sources
	private static double sub_fault_grid_spacing = 10.0;
	private static double sub_fault_rupt_offset = 10.0;
	private static MagAreaRelationship sub_fault_mag_area_rel = new WC1994_MagAreaRelationship();
	private static double sub_fault_magAreaStd = 0.0;
	private static double sub_fault_rupt_aspect_ratio = 1.0;
	private static String sub_fault_rupt_floating_type = GEM1ERF.SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP;
	
	
	// default parameters for all Gmpes
	private static String intensity_meas_type = PGA_Param.NAME.toString();
	private static String std_dev_type = StdDevTypeParam.STD_DEV_TYPE_TOTAL;
	private static String sigma_trunc_type= SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
	private static double sigma_trunc_level = 3.0;
	
	// default parameters for NGA Gmpes
//	private static String intensity_meas_typeNGA = PGA_Param.NAME.toString();
//	private static String std_dev_typeNGA = StdDevTypeParam.STD_DEV_TYPE_TOTAL;
//	private static String sigma_trunc_typeNGA= SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
//	private static double sigma_trunc_levelNGA = 3.0;
	private static String componentNGA = ComponentParam.COMPONENT_GMRotI50;
	private static double vs30NGA = 760.0;
	
	// default parameters for McVerry et al.
//	private static String intensity_meas_typeMcVerry = PGA_Param.NAME.toString();
//	private static String std_dev_typeMcVerry = StdDevTypeParam.STD_DEV_TYPE_TOTAL;
//	private static String sigma_trunc_typeMcVerry= SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
//	private static double sigma_trunc_levelMcVerry = 3.0;
	private static String componentMcVerry = ComponentParam.COMPONENT_AVE_HORZ;
	
	// Zhao et al.
	private static String componentZhao = ComponentParam.COMPONENT_AVE_HORZ;
	
	// Atkinson and Boore 2006
	private static String componentAtkBoo = ComponentParam.COMPONENT_GMRotI50;
	private static double vs30AtkBoo = 760.0;
	
    // intensity measure level list
    private ArbitrarilyDiscretizedFunc imlList;
	
    // default time span duration
    private static double TimeSpanDuration = 50.0;
    
    // default number of cpus to be used for calculation
    private static int ncpu = 1;
    
    // default minimum distance to source
    private static double max_dist_source = 200.0;
    
    // boolean to cache sources
    private static boolean sourceCache = false;
    
    public static ArbitrarilyDiscretizedFunc getDefaultIMLVals() {
    	ArbitrarilyDiscretizedFunc imlList = new ArbitrarilyDiscretizedFunc();
    	imlList.set(0.005, 1.0);
		imlList.set(0.007, 1.0);
		imlList.set(0.0098, 1.0);
		imlList.set(0.0137, 1.0);
		imlList.set(0.0192, 1.0);
		imlList.set(0.0269, 1.0);
		imlList.set(0.0376, 1.0);
		imlList.set(0.0527, 1.0);
		imlList.set(0.0738, 1.0);
		imlList.set(0.103, 1.0);
		imlList.set(0.145, 1.0);
		imlList.set(0.203, 1.0);
		imlList.set(0.284, 1.0);
		imlList.set(0.397, 1.0);
		imlList.set(0.556, 1.0);
		imlList.set(0.778, 1.0);
		imlList.set(1.09, 1.0);
		imlList.set(1.52, 1.0);
		imlList.set(2.13, 1.0);
		return imlList;
    }
    
    public static ArbitrarilyDiscretizedFunc getDefaultLogIMLVals() {
    	ArbitrarilyDiscretizedFunc imlList = getDefaultIMLVals();
    	ArbitrarilyDiscretizedFunc imlLogList = new ArbitrarilyDiscretizedFunc();
    	for (int i=0; i<imlList.getNum(); i++) {
    		imlLogList.set(Math.log(imlList.getX(i)), 1.0);
    	}
    	return imlLogList;
    }
    
	// the constructor set default values
	public CalculationSettings() {
		
		Erf = new HashMap<SourceType,HashMap<String,Object>>();
		Gmpe = new HashMap<String,HashMap<String,Object>>();
		Out = new HashMap<String,Object>();
		
		// set intentity measure level list
		imlList = getDefaultLogIMLVals();
		
		
		//*********** calculation settings for ERF instantiation **********//
		
		// hashmap for area sources
	    HashMap<String,Object> areaSourceCalcSet = new HashMap<String,Object>();
	    // source modeling type
	    areaSourceCalcSet.put(GEM1ERF.AREA_SRC_RUP_TYPE_NAME,area_rupture_type);
	    // lower seismogenic depth
	    areaSourceCalcSet.put(GEM1ERF.AREA_SRC_LOWER_SEIS_DEPTH_PARAM_NAME,area_lower_seismogenic_depth);
	    // source discretization
	    areaSourceCalcSet.put(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME,area_grid_spacing);
	    // magnitude scaling relationship
	    areaSourceCalcSet.put(GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME,area_mag_area_rel.getName());
	    Erf.put(SourceType.AREA_SOURCE, areaSourceCalcSet);
	    
	    // hashmap for point sources
	    HashMap<String,Object> gridSourceCalcSet = new HashMap<String,Object>();
	    // source modeling type
	    gridSourceCalcSet.put(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME,point_rupture_type);
	    // lower seismogenic depth
	    gridSourceCalcSet.put(GEM1ERF.GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_NAME,point_lower_seismogenic_depth);
	    // mag scaling relationship
	    gridSourceCalcSet.put(GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME,point_mag_area_rel.getName());
	    Erf.put(SourceType.GRID_SOURCE, gridSourceCalcSet);
	    
	    // hashmap for fault source calculation settings
	    HashMap<String,Object> faultSourceCalcSet = new HashMap<String,Object>();
	    // rupture offset
	    faultSourceCalcSet.put(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME,fault_rupt_offset);
	    // fault discretization
	    faultSourceCalcSet.put(GEM1ERF.FAULT_DISCR_PARAM_NAME,fault_grid_spacing);
	    // mag scaling relationship
	    faultSourceCalcSet.put(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME,fault_mag_area_rel.getName());
	    // standard deviation
	    faultSourceCalcSet.put(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME,fault_magAreaStd);
	    // rupture aspect ratio
	    faultSourceCalcSet.put(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME,fault_rupt_aspect_ratio);
	    // rupture floating type
	    faultSourceCalcSet.put(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME,fault_rupt_floating_type);
	    Erf.put(SourceType.FAULT_SOURCE, faultSourceCalcSet);
	    
	    // hashmap for fault source calculation settings
	    HashMap<String,Object> subFaultSourceCalcSet = new HashMap<String,Object>();
	    // rupture offset
	    subFaultSourceCalcSet.put(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME,sub_fault_rupt_offset);
	    // fault discretization
	    subFaultSourceCalcSet.put(GEM1ERF.SUB_DISCR_PARAM_NAME,sub_fault_grid_spacing);
	    // mag scaling relationship
	    subFaultSourceCalcSet.put(GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME,sub_fault_mag_area_rel.getName());
	    // standard deviation
	    subFaultSourceCalcSet.put(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME,sub_fault_magAreaStd);
	    // rupture aspect ratio
	    subFaultSourceCalcSet.put(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME,sub_fault_rupt_aspect_ratio);
	    // rupture floating type
	    subFaultSourceCalcSet.put(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME,sub_fault_rupt_floating_type);
	    Erf.put(SourceType.SUBDUCTION_FAULT_SOURCE, subFaultSourceCalcSet);
	    
		//********* calculation settings for output ********//
		
		Out.put(TimeSpan.DURATION, TimeSpanDuration);
		Out.put(IMLListParams.IML_LIST.toString(),imlList);
		Out.put(SiteParams.SITE_LIST.toString(),new ArrayList<Site>());
		Out.put(DistanceParams.MAX_DIST_SOURCE.toString(), max_dist_source);
		Out.put(CpuParams.CPU_NUMBER.toString(),ncpu);
		
		Out.put(IntensityMeasureParams.INTENSITY_MEAS_TYPE.toString(), intensity_meas_type);
		Out.put(StdDevTypeParam.NAME, std_dev_type);
		Out.put(SigmaTruncTypeParam.NAME,sigma_trunc_type);
		Out.put(SigmaTruncLevelParam.NAME, sigma_trunc_level);
	    
	    
	    //********* calculation settings for GMPE instantiation ***********//
	    // calculation parameters for NGA relationships: B&A, C&B, C&Y 2008
	    HashMap<String,Object> gmpeCalcSetNGA = new HashMap<String,Object>();
//	    gmpeCalcSetNGA.put(IntensityMeasureParams.INTENSITY_MEAS_TYPE.toString(), intensity_meas_typeNGA);
//	    gmpeCalcSetNGA.put(StdDevTypeParam.NAME, std_dev_typeNGA);
//	    gmpeCalcSetNGA.put(SigmaTruncTypeParam.NAME,sigma_trunc_typeNGA);
//	    gmpeCalcSetNGA.put(SigmaTruncLevelParam.NAME, sigma_trunc_levelNGA);
	    gmpeCalcSetNGA.put(ComponentParam.NAME,componentNGA);
	    gmpeCalcSetNGA.put(Vs30_Param.NAME, vs30NGA);
	    // B&A 2008
		Gmpe.put(BA_2008_AttenRel.SHORT_NAME, gmpeCalcSetNGA);
		// C&B 2008
		Gmpe.put(CB_2008_AttenRel.SHORT_NAME, gmpeCalcSetNGA);
		// C&Y 2008
		Gmpe.put(CY_2008_AttenRel.SHORT_NAME, gmpeCalcSetNGA);
		
		// calculation parameters for McVerry et al. 2000
		HashMap<String,Object> gmpeCalcSetMcVerry2000 = new HashMap<String,Object>();
//		gmpeCalcSetMcVerry2000.put(IntensityMeasureParams.INTENSITY_MEAS_TYPE.toString(), intensity_meas_typeMcVerry);
//		gmpeCalcSetMcVerry2000.put(StdDevTypeParam.NAME, std_dev_typeMcVerry);
//		gmpeCalcSetMcVerry2000.put(SigmaTruncTypeParam.NAME,sigma_trunc_typeMcVerry);
//		gmpeCalcSetMcVerry2000.put(SigmaTruncLevelParam.NAME, sigma_trunc_levelMcVerry);
		gmpeCalcSetMcVerry2000.put(ComponentParam.NAME,componentMcVerry);
		// McVerry 2000 et al.
		Gmpe.put(McVerryetal_2000_AttenRel.SHORT_NAME, gmpeCalcSetMcVerry2000);
		
		// Calculation Parameters for Zhao et al. (2000)
		HashMap<String,Object> gmpeCalcSetZhao2000 = new HashMap<String,Object>();
		gmpeCalcSetZhao2000.put(ComponentParam.NAME,componentZhao);
		Gmpe.put(ZhaoEtAl_2006_AttenRel.SHORT_NAME, gmpeCalcSetZhao2000);
		
		// Calculation Parameters for Atkinson and Boore 2006
		HashMap<String,Object> gmpeCalcSetAB2006 = new HashMap<String,Object>();
		gmpeCalcSetAB2006.put(ComponentParam.NAME,componentAtkBoo);
		gmpeCalcSetAB2006.put(Vs30_Param.NAME, vs30AtkBoo);
		Gmpe.put(AtkBoo_2006_AttenRel.SHORT_NAME, gmpeCalcSetAB2006);
	}
    
	public HashMap<SourceType, HashMap<String, Object>> getErf() {
		return Erf;
	}

	public void setErf(HashMap<SourceType, HashMap<String, Object>> erf) {
		Erf = erf;
	}

	public HashMap<String, HashMap<String, Object>> getGmpe() {
		return Gmpe;
	}

	public void setGmpe(HashMap<String, HashMap<String, Object>> gmpe) {
		Gmpe = gmpe;
	}

	public HashMap<String, Object> getOut() {
		return Out;
	}

	public void setOut(HashMap<String, Object> out) {
		Out = out;
	}

	public boolean isSourceCache() {
		return sourceCache;
	}
	
	public void setSourceCache(boolean cache) {
		sourceCache = cache;
	}
}
