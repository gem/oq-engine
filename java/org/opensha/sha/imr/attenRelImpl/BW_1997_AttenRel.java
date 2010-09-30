package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceEpicentralParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceHypoParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

public class BW_1997_AttenRel extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener
{
	// Note:
	// In case of this equation the standard deviation is not provided 
	// and therefore the method getStandardDeviation() should return 0
	private final double standardDeviation = 0.0d;
	private static final Double DISTANCE_EPI_WARN_MIN = 0.0;
	private static final Double DISTANCE_EPI_WARN_MAX = 500.0;
	private static final Double MAG_WARN_MIN = 4.4;
	private static final Double MAG_WARN_MAX = 6.9;

	// By now the calculator does not observe parameter changes.
	// So this is a UI listener that is only introduced for consistency.
	private ParameterChangeWarningListener warningListener = null;
   // Rupture magnitude
    private double mag;
    // Standard Dev type
    private String stdDevType;
    // See above: unused UI stuff
    private boolean parameterChange;
    
	@Override
	protected void initSupportedIntensityMeasureParams() {
		mmiParam = new MMI_Param();
	    mmiParam.setNonEditable();
	    mmiParam.addParameterChangeWarningListener(warningListener);
	    supportedIMParams.clear();
	    supportedIMParams.addParameter(mmiParam);
	}

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
	protected void initOtherParams() {
        super.initOtherParams();
        StringConstraint stdDevTypeConstraint = new StringConstraint();
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
        stdDevTypeConstraint.setNonEditable();
        stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);
        otherParams.addParameter(stdDevTypeParam);
	}
	
	@Override
	protected void setPropagationEffectParams() {
		if ((this.site != null) && (this.eqkRupture != null)) {
			distanceEpicentralParameter.setValue(eqkRupture, site);
        }
	}

	@Override
	public double getMean() {
		double epicentralDistance = (Double)distanceEpicentralParameter.getValue();
		return getMean(magParam.getValue(), epicentralDistance);
	} // getMean()

    /**
     * Sets the eqkRupture related parameters (magParam) based on the passed
     * eqkRupture. The internally held eqkRupture object is set
     * to the passed parameter. Warning constraints are not ignored.
     * 
     * @param eqkRupture
     * 
     */
    public void setEqkRupture(EqkRupture eqkRupture)
            throws InvalidRangeException {
        magParam.setValue(new Double(eqkRupture.getMag()));
        this.eqkRupture = eqkRupture;
        setPropagationEffectParams();
    }

    /**
     * Sets the internally held Site object to the passed site parameter.
     * 
     * @param site
     * 
     */
    public void setSite(Site site) throws ParameterException {
        this.site = site;
        setPropagationEffectParams();
    }

	@Override
	public String getShortName() {
		return null;
	}

	
	@Override
	public void setParamDefaults() {
        magParam.setValueAsDefault();
        distanceEpicentralParameter.setValueAsDefault();
        mmiParam.setValueAsDefault();
        stdDevTypeParam.setValueAsDefault();
	}

	@Override
	public void parameterChange(ParameterChangeEvent event) {
        String pName = event.getParameterName();
        Object val = event.getNewValue();
        parameterChange = true;
        if(pName.equals(DistanceRupParameter.NAME)) {
            double rEpi = ((Double) val).doubleValue();
        } else if (pName.equals(MagParam.NAME)) {
            mag = ((Double) val).doubleValue();
        } else if (pName.equals(StdDevTypeParam.NAME)) {
            stdDevType = (String) val;
        }
	}
		
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

} // class BW_1997_AttenRel()
