package org.opensha.gem.GEM1.calc.gemHazardMaps;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazardLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe2;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;


public class GemCalcSetup {

	private String inputDir;
	private String outputDir;
	private CalculationSettings calcSettings;
	private GemGmpe gemGmpeLT;
	
	/**
	 * 
	 * @param inputDir relative path 
	 * @param outputDir
	 */
	public GemCalcSetup (String inputDir, String outputDir) {
		this.inputDir = inputDir;
		this.outputDir = outputDir;
		this.calcSettings = new CalculationSettings();
		this.gemGmpeLT = new GemGmpe();
	}
	
	/**
	 * 
	 * @param fileName
	 * @return
	 */
	public BufferedReader getInputBufferedReader(String fileName) {
		String myClass = '/'+getClass().getName().replace('.', '/')+".class";
		URL myClassURL = getClass().getResource(myClass);
		String inputfile = this.inputDir+fileName;
		System.out.println(inputfile);
		if ("jar" == myClassURL.getProtocol()) {
			 inputfile = inputfile.substring(inputfile.lastIndexOf("./")+1);
		}
		BufferedReader reader = new BufferedReader(new InputStreamReader(GemComputeHazardLogicTree.class.getResourceAsStream(inputfile)));
		return reader;
	}
	
	/**
	 * 
	 * @param fileName
	 * @return
	 */
	public String getOutputPath(String fileName) {
		String outPath = "";
		// 
		String myClass = '/'+getClass().getName().replace('.', '/')+".class";
		URL myClassURL = getClass().getResource(myClass);
		if ("jar" == myClassURL.getProtocol()) {
			outPath = "./Out/";
		} else {
			URL outURL = GemComputeHazardLogicTree.class.getResource(fileName);
			String path = outURL.getPath();
			System.out.println(path);
			outPath = path.replaceAll("/GEM1/bin/","/GEM1/");
		}
		return outPath; 
	}
	
	/**
	 * 
	 * @return
	 */
	public ArrayList<Double[]> setUpMDFilter() {
		ArrayList<Double[]> lst = new ArrayList<Double[]>();
		double mmin = 5.0;
		double mmax = 7.0;
		double step = 0.2;
		HashMap<String, HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> map = 
			gemGmpeLT.getGemLogicTree().getEBMap();
		
		//
		ArbitrarilyDiscretizedFunc fun = new ArbitrarilyDiscretizedFunc();
		Double[] dst = {1.0,10.0,25.0,45.0,70.0,100.0,140.0,190.0,240.0}; 
		for (int i=0; i<dst.length; i++){
			fun.set(dst[i],0.0);
		}
		
		for (String str: map.keySet()){
			// Get Hash Map
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> mapImr = map.get(str);
			// 
			ScalarIntensityMeasureRelationshipAPI imr = mapImr.get(TectonicRegionType.ACTIVE_SHALLOW);
			System.out.println(imr.getName());
			// Set parameters
			((WarningDoubleParameter)imr.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(760.0);
			imr.setIntensityMeasure(PGA_Param.NAME);
			//
			Iterator<Parameter> iter = imr.getMeanIndependentParamsIterator();
			String dstStr = "";
			while (iter.hasNext()) {
				String strTmp = iter.next().getName();
				if (strTmp.matches("Distance.*")) {
					System.out.println("-----"+strTmp);
					dstStr = strTmp;
				}
			}
			//
			double gmThres = 0.005;
			//
			double mTmp = mmin; 
			while (mTmp <= mmax){
				for (int i=0; i<dst.length; i++){
					// Set magnitude
					((WarningDoubleParameter)imr.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mTmp));
					// Set distance
					((WarningDoublePropagationEffectParameter)imr.getParameter(dstStr)).
						setValueIgnoreWarning(new Double(dst[i]));
					double val = Math.exp(imr.getMean() + 2.0*imr.getStdDev());
					fun.set(dst[i],val);
				}
				double dstThres = 0.0;
				if (gmThres<fun.getMinY()){
					dstThres = fun.getMaxX();
				} else {
					dstThres = fun.getFirstInterpolatedX(gmThres);
				}
					
				System.out.printf("mag %6.2f dst %6.2f\n",mTmp,dstThres);
				mTmp += step;
			}
		}
		
		return lst;
	}
	
	/**
	 * 
	 * @return
	 */
	public GemGmpe getGmpeLT(){
		return this.gemGmpeLT;
	}
	
	/**
	 * 
	 * @return
	 */
	public GemGmpe2 getGmpeLT111(){
		return new GemGmpe2();
	}

	/**
	 * 
	 * @return
	 */
	public CalculationSettings getcalcSett(){
		return this.calcSettings;
	}
	
	
}
