/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

import java.util.ArrayList;


/**
 * This class is used to save the segment Rates for the faults
 * @author vipingupta
 *
 */
public class SegRateConstraint  implements java.io.Serializable {
	private String faultName; // fault name
	private int segIndex; // segment index
	private double meanSegRate; // mean Segment rate
	private double stdDevToMean; // Std dev to mean
	private double lower95Conf; // Lower 95% confidence
	private double upper95Conf; // Upper 95% confidence
	
	/**
	 * Save the faultName
	 * @param faultName
	 */
	public SegRateConstraint(String faultName) {
		this.faultName = faultName;
	}
	
	/**
	 * Get the fault name
	 * @return
	 */
	public String getFaultName() {
		return this.faultName;
	}
	
	/**
	 * Set the segment rate
	 * 
	 * @param segIndex
	 * @param meanRate
	 * @param stdDevtoMean
	 */
	public void setSegRate(int segIndex, double meanRate, double stdDevtoMean, double lower95Conf, double upper95Conf) {
		this.segIndex = segIndex;
		this.meanSegRate = meanRate;
		this.stdDevToMean = stdDevtoMean;
		this.lower95Conf = lower95Conf;
		this.upper95Conf = upper95Conf;
	}
	
	
	/**
	 * Get the segment index
	 * @return
	 */
	public int getSegIndex() {
		return this.segIndex;
	}
	
	/**
	 * Get mean Segment rate
	 * @return
	 */
	public double getMean() {
		return this.meanSegRate;
	}
	
	/**
	 * Get StdDev to mean for the rate
	 * @return
	 */
	public double getStdDevOfMean() {
		return this.stdDevToMean;
	}
	
	/**
	   * Get the weight mean and Std Dev
	   * Note: Lower and upper 95 not weight averaged, they are just set NaN
	   * @param mean1
	   * @param mean2
	   * @param sigma1
	   * @param sigma2
	   * @return
	   */
	  public static SegRateConstraint getWeightMean(ArrayList<SegRateConstraint> segRateConstraintList) {
		  double total = 0;
		  double sigmaTotal = 0;
		  String faultName=null;
		  int segIndex = -1;
		  for(int i=0; i<segRateConstraintList.size(); ++i) {
			  SegRateConstraint segRateConstraint = segRateConstraintList.get(i);
			  faultName = segRateConstraint.getFaultName();
			  segIndex = segRateConstraint.getSegIndex();
			  double sigmaSq = 1.0/(segRateConstraint.getStdDevOfMean()*segRateConstraint.getStdDevOfMean());
			  sigmaTotal+=sigmaSq;
			  total+=sigmaSq*segRateConstraint.getMean();
		  }
		  SegRateConstraint finalSegRateConstraint = new SegRateConstraint(faultName);
		  finalSegRateConstraint.setSegRate(segIndex, total/sigmaTotal, Math.sqrt(1.0/sigmaTotal), Double.NaN, Double.NaN);
		  return finalSegRateConstraint;
	  }

	public double getLower95Conf() {
		return lower95Conf;
	}

	public void setLower95Conf(double lower95Conf) {
		this.lower95Conf = lower95Conf;
	}

	public double getUpper95Conf() {
		return upper95Conf;
	}

	public void setUpper95Conf(double upper95Conf) {
		this.upper95Conf = upper95Conf;
	}
	
}
