package org.opensha.gem.GEM1.calc.gemOutput;

import java.util.Date;

public abstract class GEMHazardResults {
	
	private String author;
	private Date calcStartTime;
	private Date calcEndTime;
	private String hardwareName;
	private String codeVersion;
	
	public String getAuthor() {
		return author;
	}
	public void setAuthor(String author) {
		this.author = author;
	}
	public Date getStartTime() {
		return calcStartTime;
	}
	public void setStartTime(Date startTime) {
		calcStartTime = startTime;
	}
	public Date getEndTime() {
		return calcEndTime;
	}
	public void setEndTime(Date endTime) {
		calcEndTime = endTime;
	}
	public String getHardwareName() {
		return hardwareName;
	}
	public void setHardwareName(String hardwareName) {
		this.hardwareName = hardwareName;
	}
	public String getCodeVersion() {
		return codeVersion;
	}
	public void setCodeVersion(String codeVersion) {
		this.codeVersion = codeVersion;
	}
	
	
}
