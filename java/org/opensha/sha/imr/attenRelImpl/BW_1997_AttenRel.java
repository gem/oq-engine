package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceEpicentralParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;

public class BW_1997_AttenRel extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener {
	private static final Double DISTANCE_EPI_WARN_MIN = 0.0;
	private static final Double DISTANCE_EPI_WARN_MAX = 500.0;
	private static final Double MAG_WARN_MIN = 4.4;
	private static final Double MAG_WARN_MAX = 6.9;
	// UI listener that is only introduced for consistency
	private ParameterChangeWarningListener warningListener = null;
	// Info by Damiano:
	// In case of this equation the standard deviation is not provided 
	// and therefore the method getStandardDeviation() should return 0
	private final double standardDeviation = 0.0d;
	
	/**
	 * Name of equation:
	 * Bakun and Wentworth (1997) [Subduction zones]
	 * Formula:
	 * Immi = 3.67 + 1.17 magnitude - 3.19 log(epicentralDistance)
	 * @param magnitude
	 * @param epicentralDistance
	 * @return I_mmi "Intensity mercalli_modified_intensity"
	 */
	public double getMean(double magnitude, double epicentralDistance) {
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
		magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);
	}

	@Override
	protected void initPropagationEffectParams() {
		distanceEpicentralParameter = new DistanceEpicentralParameter();
		distanceEpicentralParameter = new DistanceEpicentralParameter(0.0);
	    distanceEpicentralParameter.addParameterChangeWarningListener(warningListener);
	    DoubleConstraint warn = new DoubleConstraint(DISTANCE_EPI_WARN_MIN,
	                                                 DISTANCE_EPI_WARN_MAX);
	    warn.setNonEditable();
	    distanceEpicentralParameter.setWarningConstraint(warn);
	    distanceEpicentralParameter.setNonEditable();
	    propagationEffectParams.addParameter(distanceEpicentralParameter);
	 } // initPropagationEffectParams()

	@Override
	protected void initSiteParams() {
		siteParams.clear();
	}

	@Override
	protected void initSupportedIntensityMeasureParams() {
		mmiParam = new MMI_Param();
        mmiParam.setNonEditable();
        mmiParam.addParameterChangeWarningListener(warningListener);
        supportedIMParams.clear();
        supportedIMParams.addParameter(mmiParam);
	}

	@Override
	protected void setPropagationEffectParams() {
		// TODO:
		// Implement this method in an Adapter class.
	}

	@Override
	public double getMean() {
		double epicentralDistance = (Double)distanceEpicentralParameter.getValue();
		return getMean(magParam.getValue(), epicentralDistance);
	} // getMean()

	@Override
	public String getShortName() {
		return null;
	}

	@Override
	public void setParamDefaults() {
		// TODO:
		// Implement this method in an Adapter class.
	}

	@Override
	public void parameterChange(ParameterChangeEvent event) {
		// TODO:
		// Implement this method in an Adapter class.
	}

} // class BW_1997_AttenRel()
