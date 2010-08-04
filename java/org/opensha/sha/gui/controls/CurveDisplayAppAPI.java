package org.opensha.sha.gui.controls;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

public interface CurveDisplayAppAPI {

	/**
	 * Sets ArbitraryDiscretizedFunc inside list containing all the functions.
	 * @param function ArbitrarilyDiscretizedFunc
	 */
	public void addCurve(ArbitrarilyDiscretizedFunc function);

	/**
	 * Set the X Values from the ArbitrarilyDiscretizedFunc passed as the parameter
	 * @param func
	 */
	public void setCurveXValues(ArbitrarilyDiscretizedFunc func);

	/**
	 * Set the default X Values for the Hazard Curve for the selected IMT.
	 */
	public void setCurveXValues();

	/**
	 * Get the selected IMT from the application, based on which it shows the
	 * default X Values for the chosen IMT.
	 * @return
	 */
	public String getSelectedIMT();

}
