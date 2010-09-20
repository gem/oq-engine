package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

public class BW_1997_AttenRel extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener {
	
	/**
	 * Name of equation:
	 * Bakun and Wentworth (1997) [Subduction zones]
	 * Formula:
	 * Immi = 3.67 + 1.17 magnitude - 3.19 log(epicentralDistance)
	 * @param magnitude
	 * @param epicentralDistance
	 * @return Immi
	 */
	public double getMean(double magnitude, double epicentralDistance) {
		double result = 0.0;
		final float offset = 3.67f;
		final float coefficient1 = 1.17f;
		final float coefficient2 = 3.19f;
		// Immi = 3.67 + 1.17 magnitude - 3.19 log(epicentralDistance) 
		result = offset + coefficient1 * magnitude - coefficient2 * Math.log10(epicentralDistance); 
		return result;
	} // getMean()

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
		// TODO Auto-generated method stub
		return 0;
	}

	@Override
	public double getStdDev() {
		// TODO Auto-generated method stub
		return 0;
	}

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
