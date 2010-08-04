package org.opensha.sha.gui.beans.event;

import java.util.EventObject;

import org.opensha.commons.param.DependentParameterAPI;

public class IMTChangeEvent extends EventObject {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private DependentParameterAPI<Double> newIMT;
	
	public IMTChangeEvent(Object source,
			DependentParameterAPI<Double> newIMT) {
		super(source);
		this.newIMT = newIMT;
	}

	public DependentParameterAPI<Double> getNewIMT() {
		return newIMT;
	}

}
