/**
 * 
 */
package org.opensha.refFaultParamDb.vo;

/**
 * Returns id and name for fault section in the table
 * @author vipingupta
 *
 */
public class FaultSectionSummary {
	private int sectionId;
	private String sectionName;

	public FaultSectionSummary() { 
	}

	public FaultSectionSummary(int sectionId, String sectionName) {
		setSectionId(sectionId);
		setSectionName(sectionName);
	}

	public int getSectionId() {
		return sectionId;
	}
	public void setSectionId(int sectionId) {
		this.sectionId = sectionId;
	}
	public String getSectionName() {
		return sectionName;
	}
	public void setSectionName(String sectionName) {
		this.sectionName = sectionName;
	}

	public  String getAsString() {
		return getSectionName()+"["+getSectionId()+"]";
	}

	public static FaultSectionSummary getFaultSectionSummary(String faultSectionSummaryAsStr) {
		int index1 = faultSectionSummaryAsStr.indexOf("[");
		int index2 = faultSectionSummaryAsStr.indexOf("]");
		String faultSectionName = faultSectionSummaryAsStr.substring(0, index1);
		int faultSectionId =  Integer.parseInt(faultSectionSummaryAsStr.substring(index1+1, index2));
		return new FaultSectionSummary(faultSectionId, faultSectionName);
	}
}
