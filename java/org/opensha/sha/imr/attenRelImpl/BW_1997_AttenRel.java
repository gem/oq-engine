package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceEpicentralParameter;

public class BW_1997_AttenRel extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener {
	
	// Info by Damiano:
	// In case of this equation the standard deviation is not provided 
	// and therefore the method getStandardDeviation() should return 0
	private final double standardDeviation = 0.0d;
	private DistanceEpicentralParameter distanceEpicentralParameter = new DistanceEpicentralParameter();
	
	/**
	 * Name of equation:
	 * Bakun and Wentworth (1997) [Subduction zones]
	 * Formula:
	 * Immi = 3.67 + 1.17 magnitude - 3.19 log(epicentralDistance)
	 * @param magnitude
	 * @param epicentralDistance
	 * @return I_mmi "Intensity mercalli_modified_intensity"
	 */
	private double getMean(double magnitude, double epicentralDistance) {
		double result = 0.0;
		final float offset = 3.67f;
		final float coefficient1 = 1.17f;
		final float coefficient2 = 3.19f;
		// I_mmi = 3.67 + 1.17 magnitude - 3.19 log(epicentralDistance) 
		result = offset + coefficient1 * magnitude - coefficient2 * Math.log10(epicentralDistance); 
		return result;
	} // getMean()
	
	/**
	 * @return    The standard deviation value
	 */
	@Override
	public double getStdDev() {
		return standardDeviation;
	} // getStdDev()

	@Override
	protected void initEqkRuptureParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void initPropagationEffectParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void initSiteParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void initSupportedIntensityMeasureParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void setPropagationEffectParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	public double getMean() {
		double epicentralDistance = (Double)distanceEpicentralParameter.getValue();
		return getMean(magParam.getValue(), epicentralDistance);
	} // getMean()

	@Override
	public String getShortName() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void setParamDefaults() {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void parameterChange(ParameterChangeEvent event) {
		// TODO Auto-generated method stub
		
	}

} // class BW_1997_AttenRel()
