/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

/**
 * This class is used to save the site names, locations and event rates from 
 * Tom Parson's excel sheet
 * 
 * @author vipingupta
 *
 */
public class EventRates  implements java.io.Serializable {
	private String siteName;
	private double latitude;
	private double longitude;
	private double obsEventRate;
	private double obsSigma;
	private double predictedRate;
	private double predictedObsRate;  // this is predictedRate reduced by prob not obs in trench
	private double lower95Conf;
	private double upper95Conf;
	private String faultName;
	
	public EventRates() { }
	
	public EventRates(String siteName, String faultName, double latitude, double longitude,
			double obsEventRate, double obsSigma, double lower95Conf, double upper95Conf) {
		setAll( siteName,  faultName, latitude,  longitude, obsEventRate,  obsSigma, lower95Conf, upper95Conf);
	}
	
	public void setAll(String siteName, String faultName, double latitude, double longitude,
			double obsEventRate, double obsSigma, double lower95Conf, double upper95Conf) {
		setSiteName(siteName);
		this.setFaultName(faultName);
		setLatitude(latitude);
		setLongitude(longitude);
		this.setObsEventRate(obsEventRate);
		this.setObsSigma(obsSigma);
		this.setLower95Conf(lower95Conf);
		this.setUpper95Conf(upper95Conf);
	}
	
	public double getLatitude() {
		return latitude;
	}
	public void setLatitude(double latitude) {
		this.latitude = latitude;
	}
	public double getLongitude() {
		return longitude;
	}
	public void setLongitude(double longitude) {
		this.longitude = longitude;
	}
	public double getObsEventRate() {
		return obsEventRate;
	}
	public void setObsEventRate(double obsEventRate) {
		this.obsEventRate = obsEventRate;
	}
	public double getObsSigma() {
		return obsSigma;
	}
	public void setObsSigma(double obsSigma) {
		this.obsSigma = obsSigma;
	}
	public String getSiteName() {
		return siteName;
	}
	public void setSiteName(String siteName) {
		this.siteName = siteName;
	}

	public double getPredictedRate() {
		return predictedRate;
	}

	public double getPredictedObsRate() {
		return predictedObsRate;
	}

	public void setPredictedRate(double predictedRate) {
		this.predictedRate = predictedRate;
	}

	public void setPredictedObsRate(double predictedObsRate) {
		this.predictedObsRate = predictedObsRate;
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

	public String getFaultName() {
		return faultName;
	}

	public void setFaultName(String faultName) {
		this.faultName = faultName;
	}
}
