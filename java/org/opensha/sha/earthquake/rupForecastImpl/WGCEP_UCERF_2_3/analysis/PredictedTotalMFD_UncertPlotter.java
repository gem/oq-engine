/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.awt.Color;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.StringTokenizer;

import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2_TimeIndependentEpistemicList;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * This class reads the TotMFDs.txt file located in WGCEP_UCERF_2_3/data/logicTreeMFDs/
 * and make Total MFD Uncertainity plots. The plots were included in UCERF2 report and hence 
 * steps to generate plots are available in an email to Ned.
 * 
 *  It assumes that the text file already exists.
 * The text file is created  by LogicTreeMFDsPlotter class.
 * 
 * 
 * @author vipingupta
 *
 */
public class PredictedTotalMFD_UncertPlotter  implements GraphWindowAPI{

	private final static String X_AXIS_LABEL = "Magnitude";
	private final static String Y_AXIS_LABEL = "Cumulative Rate (per year)";
	
	private ArrayList<IncrementalMagFreqDist> totMFDsList;

	
	private final static String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/logicTreeMFDs/";
	private final static String TOT_MFD_FILENAME = PATH+"TotMFDs.txt";
	

	private final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLACK, 1); // Tot MFDs
	private final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.GREEN, 2); // median, 2.5%, 97.5%
	private final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLUE, 2); // mean
	
	private final PlotCurveCharacterstics PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.RED, 2); // best fit MFD
	private final PlotCurveCharacterstics PLOT_CHAR8 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS,
		      Color.RED, 5); // observed MFD

		
	private ArrayList funcs = new ArrayList();
	private ArrayList<PlotCurveCharacterstics> plottingFeaturesList = new ArrayList<PlotCurveCharacterstics>();
	private ArrayList<ArbDiscrEmpiricalDistFunc> rateWtFuncList;
	private UCERF2_TimeIndependentEpistemicList ucerf2List = new UCERF2_TimeIndependentEpistemicList();
	
	private boolean drawIndividualBranches;
	/**
	 *  it just reads the data from the file wihtout recalculation
	 * 
	 */
	public PredictedTotalMFD_UncertPlotter (boolean drawIndividualBranches) {
		this.drawIndividualBranches = drawIndividualBranches;
		totMFDsList = new ArrayList<IncrementalMagFreqDist>();
		readMFDsFromFile(TOT_MFD_FILENAME, this.totMFDsList);
		plotPredTotalMFD_Uncert();
	}
	
	/**
	 * Read MFDs from file
	 * 
	 * @param fileName
	 * @param mfdList
	 */
	private void readMFDsFromFile(String fileName, ArrayList<IncrementalMagFreqDist> mfdList) {
		try {
			FileReader fr = new FileReader(fileName);
			BufferedReader br = new BufferedReader(fr);
			String line = br.readLine();
			IncrementalMagFreqDist mfd = null;
			double mag, rate;
			while(line!=null) {
				if(line.startsWith("#")) {
					mfd = new IncrementalMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
					mfdList.add(mfd);
				} else {
					StringTokenizer tokenizer = new StringTokenizer(line);
					mag = Double.parseDouble(tokenizer.nextToken());
					rate = Double.parseDouble(tokenizer.nextToken());
					mfd.set(mag, rate);
				}
				line = br.readLine();
			}
			br.close();
			fr.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
		

	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList getPlottingFeatures() {
		 return this.plottingFeaturesList;
	}
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getCurveFunctionList()
	 */
	public ArrayList getCurveFunctionList() {
		return this.funcs;
	}
	
	
	private void plotPredTotalMFD_Uncert() {
		funcs  = new ArrayList();
		plottingFeaturesList = new ArrayList<PlotCurveCharacterstics>();
		// Avg MFDs
		rateWtFuncList = new ArrayList<ArbDiscrEmpiricalDistFunc>();
		for(int i=0; i<UCERF2.NUM_MAG; ++i) {
			rateWtFuncList.add(new ArbDiscrEmpiricalDistFunc());
		}
		
		doWeightedSum();
		
		
		// mean MFD
		IncrementalMagFreqDist meanMfd = new IncrementalMagFreqDist(UCERF2.MIN_MAG-UCERF2.DELTA_MAG/2, UCERF2.MAX_MAG-UCERF2.DELTA_MAG/2, UCERF2. NUM_MAG);
		for(int magIndex=0; magIndex<UCERF2.NUM_MAG; ++magIndex) {
			meanMfd.set(magIndex, rateWtFuncList.get(magIndex).getMean());
		}
		meanMfd.setInfo("Mean");
		funcs.add(meanMfd);
		plottingFeaturesList.add(this.PLOT_CHAR3);
		//		 median MFD
		IncrementalMagFreqDist medianMfd = new IncrementalMagFreqDist(UCERF2.MIN_MAG-UCERF2.DELTA_MAG/2, UCERF2.MAX_MAG-UCERF2.DELTA_MAG/2, UCERF2. NUM_MAG);
		for(int magIndex=0; magIndex<UCERF2.NUM_MAG; ++magIndex) {
			medianMfd.set(magIndex, rateWtFuncList.get(magIndex).getMedian());
		}
		medianMfd.setInfo("Median");
		funcs.add(medianMfd);
		plottingFeaturesList.add(this.PLOT_CHAR2);
		//		 97.5 percentile MFD
		IncrementalMagFreqDist percentile97_5Mfd = new IncrementalMagFreqDist(UCERF2.MIN_MAG-UCERF2.DELTA_MAG/2, UCERF2.MAX_MAG-UCERF2.DELTA_MAG/2,UCERF2. NUM_MAG);
		for(int magIndex=0; magIndex<UCERF2.NUM_MAG; ++magIndex) {
			percentile97_5Mfd.set(magIndex, rateWtFuncList.get(magIndex).getInterpolatedFractile(0.975));
		}
		percentile97_5Mfd.setInfo("97.5 percentile");
		funcs.add(percentile97_5Mfd);
		plottingFeaturesList.add(this.PLOT_CHAR2);
		//		 2.5 percentile MFD
		IncrementalMagFreqDist percentile2_5Mfd = new IncrementalMagFreqDist(UCERF2.MIN_MAG-UCERF2.DELTA_MAG/2, UCERF2.MAX_MAG-UCERF2.DELTA_MAG/2,UCERF2. NUM_MAG);
		for(int magIndex=0; magIndex<UCERF2.NUM_MAG; ++magIndex) {
			percentile2_5Mfd.set(magIndex, rateWtFuncList.get(magIndex).getInterpolatedFractile(0.025));
		}
		percentile2_5Mfd.setInfo("2.5 percentile");
		funcs.add(percentile2_5Mfd);
		plottingFeaturesList.add(this.PLOT_CHAR2);
		
		// Karen's observed data
		UCERF2 ucerf2 = new UCERF2();
		boolean includeAfterShocks = ucerf2.areAfterShocksIncluded();
		
		ArrayList obsMFD = ucerf2.getObsCumMFD(includeAfterShocks);		
		funcs.add(obsMFD.get(0));
		this.plottingFeaturesList.add(PLOT_CHAR7);
		// historical cum dist
		funcs.addAll(obsMFD);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		Collections.reverse(funcs);
		Collections.reverse(plottingFeaturesList);
		
		GraphWindow graphWindow= new GraphWindow(this);
		graphWindow.setPlotLabel("Mag Freq Dist");
		graphWindow.plotGraphUsingPlotPreferences();
		graphWindow.setVisible(true);
		
		return ;
	}
	
	 
	
	/**
	 * Do Weighted Sum
	 * 
	 * @param paramIndex
	 * @param weight
	 */
	private void doWeightedSum() {
		
		int numBranches = ucerf2List.getNumERFs();
		for(int i=0; i<numBranches; ++i) {
			double wt = ucerf2List.getERF_RelativeWeight(i);
			
			EvenlyDiscretizedFunc mfd  = totMFDsList.get(i).getCumRateDistWithOffset();
			mfd.setInfo("Cumulative MFD for a logic tree branch :"+(i+1));
			if(drawIndividualBranches) {
				funcs.add(mfd);
				plottingFeaturesList.add(this.PLOT_CHAR1);
			}
			for(int magIndex=0; magIndex<UCERF2.NUM_MAG; ++magIndex) {
				rateWtFuncList.get(magIndex).set(mfd.getY(magIndex), wt);
			}
			
			System.out.println(i+"\t"+mfd.getX(20)+"\t"+mfd.getY(20)+"\t"+wt);
		}
	}
	

	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXLog()
	 */
	public boolean getXLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return true;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXAxisLabel()
	 */
	public String getXAxisLabel() {
		return X_AXIS_LABEL;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYAxisLabel()
	 */
	public String getYAxisLabel() {
		return Y_AXIS_LABEL;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#isCustomAxis()
	 */
	public boolean isCustomAxis() {
		return true;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinX()
	 */
	public double getMinX() {
		return 5.0;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		return 9.255;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		return 1e-4;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		return 10;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}
	
	
	public static void main(String []args) {
		PredictedTotalMFD_UncertPlotter mfdPlotter1 = new PredictedTotalMFD_UncertPlotter(false);
		PredictedTotalMFD_UncertPlotter mfdPlotter2 = new PredictedTotalMFD_UncertPlotter(true);
	}
}

