package org.opensha.sha.gui.beans;

import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;

public class IMR_ParamEditor extends ParameterListEditor implements ParameterChangeListener {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	public static final String DEFAULT_NAME = "IMR Params";
	
	private ScalarIntensityMeasureRelationshipAPI imr;
	
	public IMR_ParamEditor() {
		this(null);
	}
	
	public IMR_ParamEditor(ScalarIntensityMeasureRelationshipAPI imr) {
		setTitle(DEFAULT_NAME);
		this.setIMR(imr);
	}
	
	public void setIMR(ScalarIntensityMeasureRelationshipAPI imr) {
		if (imr == this.imr) {
			this.validate();
			return;
		}
		this.imr = imr;
		if (imr == null) {
			this.setParameterList(null);
			this.validate();
			return;
		}
		ParameterList paramList = imr.getOtherParamsList();
		this.setParameterList(paramList);
		for (ParameterAPI<?> param : paramList) {
			if (param.getName().equals(SigmaTruncTypeParam.NAME)) {
				String val = (String)param.getValue();
				toggleSigmaLevelBasedOnTypeValue(val);
				param.addParameterChangeListener(this);
			}
		}
		this.validate();
	}
	
	/**
	 * Set the Tectonic Region Parameter visibility
	 * 
	 * @param visible
	 */
	public void setTRTParamVisible(boolean visible) {
		if (this.imr == null)
			return;
		try {
			// if it doesn't have the param, an exception will be thrown here
			this.imr.getParameter(TectonicRegionTypeParam.NAME);
			// now set it visible/invisible
			this.setParameterVisible(TectonicRegionTypeParam.NAME, visible);
		} catch (ParameterException e) {
			// the IMR doesn't have a TRT param...do nothing
			return;
		}
	}
	
	/**
	 * sigma level is visible or not
	 * @param value
	 */
	private void toggleSigmaLevelBasedOnTypeValue(String value){
		if (!this.parameterList.containsParameter(SigmaTruncLevelParam.NAME))
			return;

		if( value.equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE) ) {
			setParameterVisible( SigmaTruncLevelParam.NAME, false );
		}
		else{
			setParameterVisible( SigmaTruncLevelParam.NAME, true );
			getParameterEditor(SigmaTruncLevelParam.NAME).validate();
		}
		this.validate();
	}

	public void parameterChange(ParameterChangeEvent event) {
		if (event.getParameterName().equals(SigmaTruncTypeParam.NAME)) {
			String val = (String)event.getParameter().getValue();
			toggleSigmaLevelBasedOnTypeValue(val);
		}
	}

}

