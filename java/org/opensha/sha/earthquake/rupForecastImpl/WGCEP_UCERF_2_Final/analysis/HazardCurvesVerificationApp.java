/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.analysis;

import java.io.File;
import java.io.FileOutputStream;
import java.text.DecimalFormat;

import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;

/**
 * This class creates a bunch of hazard curves using MeanUCERF2 for verification with NSHMP.
 * The latitudes and longitudes were provided by Mark Petersen in an email.
 * 
 * We have 2 different latitudes (34.0, 37.7) and 3 Intensity Measure Types(IMT) (PGA, SA at 0.2 sec, SA at 1 sec). 
 * A file is created for each combination. Hence it generates 6 spreadsheets.
 * 
 * IMPORTANT NOTE:  This was run on USGS Mac Server.
 * Please note the method generateHazardCurves() in this class. The call to this 
 * seems to be commented at various places (currently at 6 places). 
 * This was done for using the Mac Server at USGS, Pasadena. We can uncomment one of the method calls 
 * (and keeping the other 5 commented) and run the main() method. We can do this one by one with
 * each method call. So, it enabled us to utilize 6 different processors of the Mac Server and hence faster
 * results.
 * 
 * 
 * @author vipingupta
 *
 */
public class HazardCurvesVerificationApp implements ParameterChangeWarningListener {
	private final static String HAZ_CURVES_DIRECTORY_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/analysis/HazardCurvesVerification/BA08_760";
	private final static DoubleParameter VS_30_PARAM = new DoubleParameter("Vs30", 760.0);
	private final static DoubleParameter DEPTH_2_5KM_PARAM = new DoubleParameter("Depth 2.5 km/sec", 2.0);
	private MeanUCERF2 meanUCERF2;
	private ScalarIntensityMeasureRelationshipAPI imr;
	private DecimalFormat latLonFormat = new DecimalFormat("0.00");
	private ArbitrarilyDiscretizedFunc function; // X-Values function
	private HazardCurveCalculator hazardCurveCalculator;
	
	// First Lat profiling
	private final static double LAT1 = 34.0;
	private final static double MIN_LON1 = -119.0;
	private final static double MAX_LON1 = -115.0;
	
	// Second Lat profiling
	private final static double LAT2 = 37.7;
	private final static double MIN_LON2 = -123.0;
	private final static double MAX_LON2 = -118.0;
	
	// grid spacing in degrees
	private final static double GRID_SPACING = 0.05;

	public HazardCurvesVerificationApp() {
		System.out.println("Setting up ERF...");
		setupERF();
		System.out.println("Setting up IMR...");
		setupIMR();
		
		//		create directory for hazard curves
		File file = new File(HAZ_CURVES_DIRECTORY_NAME);
		if(!file.isDirectory()) file.mkdirs();
		
		// Generate Hazard Curves for PGA
		imr.setIntensityMeasure("PGA");
		createUSGS_PGA_Function();
		String imtString = "PGA";
		//generateHazardCurves(imtString, LAT1, MIN_LON1, MAX_LON1);
		//generateHazardCurves(imtString, LAT2, MIN_LON2, MAX_LON2);
		
		// Generate Hazard Curves for SA 0.2s
		imr.setIntensityMeasure("SA");
		createUSGS_SA_01_AND_02_Function();
		imr.getParameter(PeriodParam.NAME).setValue(0.2);
		imtString = "SA_0.2sec";
		//generateHazardCurves(imtString, LAT1, MIN_LON1, MAX_LON1);
		//generateHazardCurves(imtString, LAT2, MIN_LON2, MAX_LON2);
		
		// Generate hazard curves for SA 1.0s
		imr.setIntensityMeasure("SA");
		imr.getParameter(PeriodParam.NAME).setValue(1.0);
		createUSGS_SA_Function();
		imtString = "SA_1sec";
		//generateHazardCurves(imtString, LAT1, MIN_LON1, MAX_LON1);
		generateHazardCurves(imtString, LAT2, MIN_LON2, MAX_LON2);
	}
	
	/**
	 * This method creates a spreadsheet for the provided latitude and IMT.
	 * For the user provided latitude, it goes over all longitudes and calculates 2% Prob of Exceedance and
	 * 10% probability of exceedance. 
	 * For interpolation purposes, it uses Log-Log interpolation.
	 *
	 */
	private void generateHazardCurves(String imtString, double lat, double minLon, double maxLon) {
		try {
			HSSFWorkbook wb  = new HSSFWorkbook();
			HSSFSheet sheet = wb.createSheet(); // Sheet for displaying the Total Rates
			sheet.createRow(0);
			int numX_Vals = function.getNum();
			for(int i=0; i<numX_Vals; ++i)
				sheet.createRow(i+1).createCell((short)0).setCellValue(function.getX(i));
			
			int twoPercentProbRoIndex = numX_Vals+2;
			int tenPercentProbRoIndex = numX_Vals+3;
			
			sheet.createRow(twoPercentProbRoIndex).createCell((short)0).setCellValue("2% Prob of Exceedance");
			sheet.createRow(tenPercentProbRoIndex).createCell((short)0).setCellValue("10% Prob of Exceedance");
			
			hazardCurveCalculator = new HazardCurveCalculator(); 
			String outputFileName = HAZ_CURVES_DIRECTORY_NAME+"/"+latLonFormat.format(lat)+"_"+imtString+".xls";
			// Do for First Lat
			double twoPercentProb, tenPercentProb;
			int colIndex=1;
			for(double lon=minLon; lon<=maxLon; lon+=GRID_SPACING, ++colIndex) {
				System.out.println("Doing Site:"+latLonFormat.format(lat)+","+latLonFormat.format(lon));
				Site site = new Site(new Location(lat, lon));
				site.addParameter(VS_30_PARAM);
				site.addParameter(DEPTH_2_5KM_PARAM);
				
				// do log of X axis values
				DiscretizedFuncAPI hazFunc = new ArbitrarilyDiscretizedFunc();
				for(int i=0; i<numX_Vals; ++i)
					hazFunc.set(Math.log(function.getX(i)), 1);
				
				// Note here that hazardCurveCalculator accepts the Log of X-Values
				this.hazardCurveCalculator.getHazardCurve(hazFunc, site, imr, meanUCERF2);
				
				// Unlog the X-Values before doing interpolation. The Y Values we get from hazardCurveCalculator are unmodified
				DiscretizedFuncAPI newFunc = new ArbitrarilyDiscretizedFunc();
				for(int i=0; i<numX_Vals; ++i)
					newFunc.set(function.getX(i), hazFunc.getY(i));
				
				twoPercentProb = newFunc.getFirstInterpolatedX_inLogXLogYDomain(0.02);
				tenPercentProb = newFunc.getFirstInterpolatedX_inLogXLogYDomain(0.1);
				
				sheet.getRow(0).createCell((short)colIndex).setCellValue(latLonFormat.format(lon));
				for(int i=0; i<numX_Vals; ++i)
					sheet.createRow(i+1).createCell((short)colIndex).setCellValue(newFunc.getY(i));

				sheet.createRow(twoPercentProbRoIndex).createCell((short)colIndex).setCellValue(twoPercentProb);
				sheet.createRow(tenPercentProbRoIndex).createCell((short)colIndex).setCellValue(tenPercentProb);
				
			}
			FileOutputStream fileOut = new FileOutputStream(outputFileName);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Set up ERF Parameters
	 *
	 */
	private void setupERF() {
		meanUCERF2 = new MeanUCERF2();
		meanUCERF2.setParameter(MeanUCERF2.RUP_OFFSET_PARAM_NAME, new Double(5.0));
		meanUCERF2.setParameter(MeanUCERF2.CYBERSHAKE_DDW_CORR_PARAM_NAME, false);
		meanUCERF2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_INCLUDE);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_RUP_NAME, UCERF2.BACK_SEIS_RUP_CROSSHAIR);
		meanUCERF2.setParameter(UCERF2.FLOATER_TYPE_PARAM_NAME, UCERF2.CENTERED_DOWNDIP_FLOATER);
		meanUCERF2.getTimeSpan().setDuration(50.0);
		meanUCERF2.updateForecast();
	}
	
	/**
	 * Set up IMR parameters
	 *
	 */
	private void setupIMR() {
		imr = new BA_2008_AttenRel(this);
		imr.setParamDefaults();
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
		imr.getParameter(SigmaTruncLevelParam.NAME).setValue(3.0);
		/*
		imr = new CB_2008_AttenRel(this);
		imr.setParamDefaults();
		imr.getParameter(CB_2008_AttenRel.SIGMA_TRUNC_TYPE_NAME).setValue(CB_2008_AttenRel.SIGMA_TRUNC_TYPE_1SIDED);
		imr.getParameter(CB_2008_AttenRel.SIGMA_TRUNC_LEVEL_NAME).setValue(3.0);
		*/
	}
	

	/**
	 *  Function that must be implemented by all Listeners for
	 *  ParameterChangeWarnEvents.
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void parameterChangeWarning(ParameterChangeWarningEvent e) {
		String S = " : parameterChangeWarning(): ";
		WarningParameterAPI param = e.getWarningParameter();
		param.setValueIgnoreWarning(e.getNewValue());
	}
	
	
	  /**
	   * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	   * the y values are modified with the values entered by the user
	   */
	  private void createUSGS_PGA_Function(){
	    function= new ArbitrarilyDiscretizedFunc();
	    function.set(.005,1);
	    function.set(.007,1);
	    function.set(.0098,1);
	    function.set(.0137,1);
	    function.set(.0192,1);
	    function.set(.0269,1);
	    function.set(.0376,1);
	    function.set(.0527,1);
	    function.set(.0738,1);
	    function.set(.103,1);
	    function.set(.145,1);
	    function.set(.203,1);
	    function.set(.284,1);
	    function.set(.397,1);
	    function.set(.556,1);
	    function.set(.778,1);
	    function.set(1.09,1);
	    function.set(1.52,1);
	    function.set(2.13,1);
	  }

	  
	  /**
	   * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	   * the y values are modified with the values entered by the user
	   */
	  private void createUSGS_SA_01_AND_02_Function(){
	    function= new ArbitrarilyDiscretizedFunc();
	                   
	    function.set(.005,1);
	    function.set(.0075,1);
	    function.set(.0113 ,1);
	    function.set(.0169,1);
	    function.set(.0253,1);
	    function.set(.0380,1);
	    function.set(.0570,1);
	    function.set(.0854,1);
	    function.set(.128,1);
	    function.set(.192,1);
	    function.set(.288,1);
	    function.set(.432,1);
	    function.set(.649,1);
	    function.set(.973,1);
	    function.set(1.46,1);
	    function.set(2.19,1);
	    function.set(3.28,1);
	    function.set(4.92,1);
	    function.set(7.38,1);
	    
	  }
	  
	  /**
	   * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	   * the y values are modified with the values entered by the user
	   */
	  private void createUSGS_SA_Function(){
	    function= new ArbitrarilyDiscretizedFunc();
	 
	    function.set(.0025,1);
	    function.set(.00375,1);
	    function.set(.00563 ,1);
	    function.set(.00844,1);
	    function.set(.0127,1);
	    function.set(.0190,1);
	    function.set(.0285,1);
	    function.set(.0427,1);
	    function.set(.0641,1);
	    function.set(.0961,1);
	    function.set(.144,1);
	    function.set(.216,1);
	    function.set(.324,1);
	    function.set(.487,1);
	    function.set(.730,1);
	    function.set(1.09,1);
	    function.set(1.64,1);
	    function.set(2.46,1);
	    function.set(3.69,1);
	    function.set(5.54,1);
	  }
	
	public static void main(String []args) {
		new HazardCurvesVerificationApp();
	}
}
