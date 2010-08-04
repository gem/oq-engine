/**
 * 
 */
package org.opensha.refFaultParamDb.vo;
import java.util.ArrayList;
import java.util.HashMap;
/**
 * Deformation model. It contains the slip estimates and aseimsic slip factor estimates for the fault sections in
 * this  deformation model.
 * 
 * @author vipingupta
 *
 */
public class DeformationModel {
	private int deformationModelId;
	private ArrayList<Integer> faultSectionIdList = new ArrayList<Integer>();
	private HashMap<Integer, EstimateInstances> slipRatesList= new HashMap<Integer, EstimateInstances>();
	private HashMap<Integer, EstimateInstances> aseismicSlipList = new HashMap<Integer, EstimateInstances>();

	/**
	 * Set the defomation model id
	 * @param deformationModelId
	 */
	public void setDeformationModelId(int deformationModelId) {
		this.deformationModelId = deformationModelId;
	}

	/**
	 * Get the Id for this deformation model
	 * @return
	 */
	public int getDeformationModelId() {
		return this.deformationModelId;
	}

	/**
	 * Add fault section to this deformation model
	 * @param faultSectionId
	 */
	public void addFaultSection(int faultSectionId) {
		this.faultSectionIdList.add(new Integer(faultSectionId));
	}

	/**
	 * Get a list of Ids of all fault sections in this deformation model
	 * 
	 * @return
	 */
	public ArrayList<Integer> getFaultSectionIdList() {
		return this.faultSectionIdList;
	}

	/**
	 * Set the slip rate estimate for this fault section in this deformation model
	 * @param faultSectionId
	 * @param slipRateEstimate
	 */
	public void setSlipRateEstimate(int faultSectionId, EstimateInstances slipRateEstimate) {
		slipRatesList.put(new Integer(faultSectionId), slipRateEstimate);
	}

	/**
	 * Set the aseismic slip factor estimate for this fault section in this deformation model
	 * 
	 * @param faultSectionId
	 * @param aseismicSlipFactorEstimate
	 */
	public void setAseismicSlipFactorEstimate(int faultSectionId, EstimateInstances aseismicSlipFactorEstimate) {
		aseismicSlipList.put(new Integer(faultSectionId), aseismicSlipFactorEstimate);
	}

	/**
	 *Get slip rate estimate for a fault section
	 * @param faultSectionId
	 * @return
	 */
	public EstimateInstances getSlipRateEstimate(int faultSectionId) {
		return (EstimateInstances)slipRatesList.get(new Integer(faultSectionId));
	}

	/**
	 * Get aseismic slip factor estimate for a fault section
	 * @param faultSectionId
	 * @return
	 */
	public EstimateInstances getAseismicSlipEstimate(int faultSectionId) {
		return (EstimateInstances)aseismicSlipList.get(new Integer(faultSectionId));
	}

}
